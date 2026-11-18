"""Genera el dataset sintetico de reclamos de ConectaMX.

Produce:
  data/clientes.csv          ~50 clientes ficticios, sin modelo, con semilla fija.
  data/reclamos.csv          600 reclamos (500 train / 100 test), filtrados y verificados.
  data/reclamos_crudos.csv   todo lo generado, con el veredicto del verificador.

Como funciona, en tres pasos:
  1. Nosotros elegimos las etiquetas (categoria, urgencia, producto) y gpt-4o-mini redacta
     un reclamo que corresponda a esas etiquetas.
  2. El modelo a veces se desvia: le pedimos "cancelacion" y escribe un reclamo de cobro.
     Asi que un verificador (gpt-4o) lee cada texto A CIEGAS, sin ver la etiqueta, y lo
     clasifica de nuevo.
  3. Nos quedamos solo con los reclamos donde el verificador coincide con la etiqueta.
     Si a una categoria le faltan ejemplos, generamos mas y repetimos.

Uso local (la clave sale de .env, que esta en .gitignore):
    .venv/bin/python3 scripts/generar_dataset.py
"""
from __future__ import annotations

import itertools
import random
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Literal

import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

SEED = 42
MODELO_GENERADOR = "gpt-4o-mini"
MODELO_VERIFICADOR = "gpt-4o"
POR_COMBINACION = 13         # ~69 combinaciones x 13 = ~900 crudos en la primera ronda
TOTAL = 600
TEST = 100
MAX_RONDAS = 4
PROB_NUMERO_CLIENTE = 0.3    # parte de los reclamos menciona su numero de cliente

# Precios por millon de tokens (entrada, salida), en USD. Solo para reportar el costo.
PRECIOS = {"gpt-4o-mini": (0.15, 0.60), "gpt-4o": (2.50, 10.00)}

CATEGORIAS = {
    "facturacion": "cobros de mas, cobros duplicados, cargos que no reconoce, factura incorrecta",
    "falla_servicio": "el servicio no funciona, se cae, no hay señal o no hay conexion",
    "velocidad": "el servicio funciona pero lento, no llega a la velocidad contratada",
    "cancelacion": "quiere dar de baja el servicio; el motivo principal del mensaje es irse",
    "atencion": "mala atencion: nadie le contesta, lo transfieren, no cumplen lo prometido",
    "equipo": "problemas con el modem, router, decodificador o el celular que le dieron",
}
URGENCIAS = {
    "alta": "esta sin servicio total, le cobraron mucho dinero de mas, o se va hoy mismo",
    "media": "problema real que le molesta pero puede esperar unos dias",
    "baja": "molestia menor o consulta con un poco de queja",
}
PRODUCTOS = {
    "fibra": "internet en casa por fibra optica",
    "movil": "linea de celular",
    "tv": "television de paga",
    "paquete": "paquete de internet, telefono y tv juntos",
}
# Combinaciones que no tienen sentido y confunden al generador.
IMPOSIBLES = {("velocidad", "tv")}

ORDEN_URGENCIA = {"baja": 0, "media": 1, "alta": 2}

TONOS = ["enojado", "educado", "cansado", "ironico", "apurado", "confundido", "formal",
         "muy coloquial"]
LARGOS = ["una sola linea", "dos o tres oraciones", "un parrafo corto"]

# Rechazamos cualquier texto con voseo o modismos argentinos.
VOSEO = re.compile(
    r"\b(?:vos|ten[eé]s|pod[eé]s|quer[eé]s|sab[eé]s|fijate|acordate|che|laburo|boludo)\b",
    re.IGNORECASE,
)

RAIZ = Path(__file__).resolve().parent.parent
DATA = RAIZ / "data"


# ---------------------------------------------------------------------------
# Clientes ficticios: codigo puro, sin modelo
# ---------------------------------------------------------------------------
NOMBRES = ["Ana", "Luis", "Mariana", "Jorge", "Sofia", "Carlos", "Fernanda", "Ricardo",
           "Daniela", "Alejandro", "Valeria", "Miguel", "Paola", "Andres", "Gabriela"]
APELLIDOS = ["Hernandez", "Garcia", "Martinez", "Lopez", "Gonzalez", "Perez", "Rodriguez",
             "Sanchez", "Ramirez", "Torres", "Flores", "Rivera"]
PLANES = {
    "fibra": [("Fibra 200", 449.0), ("Fibra 500", 649.0), ("Fibra 1000", 899.0)],
    "movil": [("Movil 10 GB", 199.0), ("Movil Ilimitado", 399.0)],
    "tv": [("TV Basica", 249.0), ("TV Premium", 549.0)],
    "paquete": [("Triple Play", 999.0), ("Doble Play", 749.0)],
}


def generar_clientes(rng: random.Random) -> pd.DataFrame:
    filas = []
    for i in range(50):
        producto = rng.choice(list(PLANES))
        plan, monto = rng.choice(PLANES[producto])
        duplicado = 1 if i % 4 == 0 else 0                    # 1 de cada 4 con cobro doble
        dias_sin = rng.choice([0, 0, 0, 1, 2, 5]) if i % 3 == 0 else 0
        filas.append({
            "numero_cliente": 1001 + i,
            "nombre": f"{rng.choice(NOMBRES)} {rng.choice(APELLIDOS)}",
            "producto": producto,
            "plan": plan,
            "monto_mensual_mxn": monto,
            "ultimo_cobro_mxn": monto * (2 if duplicado else 1),
            "cobros_duplicados": duplicado,
            "dias_sin_servicio": dias_sin,
            "antiguedad_meses": rng.randint(1, 96),
        })
    return pd.DataFrame(filas)


def cliente_para(clientes: pd.DataFrame, categoria: str, producto: str,
                 rng: random.Random) -> int:
    """Elige un cliente coherente con el reclamo, para que la tool de codigo lo confirme."""
    pool = clientes[clientes["producto"] == producto]
    if categoria == "facturacion" and (pool["cobros_duplicados"] > 0).any():
        pool = pool[pool["cobros_duplicados"] > 0]
    if categoria == "falla_servicio" and (pool["dias_sin_servicio"] > 0).any():
        pool = pool[pool["dias_sin_servicio"] > 0]
    if pool.empty:
        pool = clientes
    return int(rng.choice(pool["numero_cliente"].tolist()))


# ---------------------------------------------------------------------------
# Paso 1: el generador escribe el texto para etiquetas que elegimos nosotros
# ---------------------------------------------------------------------------
class Lote(BaseModel):
    reclamos: list[str]


SISTEMA_GENERADOR = (
    "Escribes reclamos realistas de clientes de ConectaMX, una empresa de telecomunicaciones "
    "ficticia de Mexico. Escribes en espanol de Mexico, como escribe la gente real por chat "
    "o por correo: a veces con faltas de ortografia, sin acentos o en minusculas. Usas tu, "
    "nunca vos. Montos en pesos mexicanos. Nunca escribes la categoria ni la urgencia de "
    "forma literal: el texto solo cuenta el problema. Cada reclamo trata UN problema "
    "principal, el que se te pide, y deja claro de que producto habla."
)


def pedir_lote(client: OpenAI, categoria: str, urgencia: str, producto: str,
               specs: list[dict]):
    lineas = []
    for n, s in enumerate(specs, 1):
        extra = (f" Menciona de forma natural que su numero de cliente es {s['numero']}."
                 if s["numero"] else " No menciones numero de cliente.")
        lineas.append(f"{n}. Tono {s['tono']}, largo: {s['largo']}.{extra}")
    usuario = (
        f"Escribe {len(specs)} reclamos distintos entre si.\n"
        f"Producto de todos: {producto} ({PRODUCTOS[producto]}).\n"
        f"Problema principal de todos: {CATEGORIAS[categoria]}.\n"
        f"Urgencia de todos: {URGENCIAS[urgencia]}.\n"
        "Cada uno con una situacion concreta distinta. Uno por item, en este orden:\n"
        + "\n".join(lineas)
    )
    resp = client.chat.completions.parse(
        model=MODELO_GENERADOR,
        messages=[{"role": "system", "content": SISTEMA_GENERADOR},
                  {"role": "user", "content": usuario}],
        response_format=Lote,
        temperature=1.0,
    )
    return resp.choices[0].message.parsed.reclamos, resp.usage


# ---------------------------------------------------------------------------
# Paso 2: el verificador clasifica a ciegas
# ---------------------------------------------------------------------------
class Veredicto(BaseModel):
    categoria: Literal["facturacion", "falla_servicio", "velocidad", "cancelacion",
                       "atencion", "equipo"]
    urgencia: Literal["alta", "media", "baja"]
    producto: Literal["fibra", "movil", "tv", "paquete"]


SISTEMA_VERIFICADOR = (
    "Clasificas reclamos de clientes de una empresa de telecomunicaciones de Mexico.\n"
    "categoria (el problema PRINCIPAL del mensaje, una sola):\n"
    + "\n".join(f"- {k}: {v}" for k, v in CATEGORIAS.items())
    + "\nurgencia:\n"
    + "\n".join(f"- {k}: {v}" for k, v in URGENCIAS.items())
    + "\nproducto:\n"
    + "\n".join(f"- {k}: {v}" for k, v in PRODUCTOS.items())
)


def verificar(client: OpenAI, texto: str):
    resp = client.chat.completions.parse(
        model=MODELO_VERIFICADOR,
        messages=[{"role": "system", "content": SISTEMA_VERIFICADOR},
                  {"role": "user", "content": texto}],
        response_format=Veredicto,
        temperature=0.0,
    )
    return resp.choices[0].message.parsed, resp.usage


# ---------------------------------------------------------------------------
# Orquestacion
# ---------------------------------------------------------------------------
class Contador:
    def __init__(self) -> None:
        self.tokens = {m: [0, 0] for m in PRECIOS}

    def sumar(self, modelo: str, uso) -> None:
        self.tokens[modelo][0] += uso.prompt_tokens
        self.tokens[modelo][1] += uso.completion_tokens

    def costo(self) -> float:
        return sum(i / 1e6 * PRECIOS[m][0] + o / 1e6 * PRECIOS[m][1]
                   for m, (i, o) in self.tokens.items())


def generar_ronda(client, trabajos, contador) -> list[dict]:
    filas, fallidos = [], 0
    with ThreadPoolExecutor(max_workers=8) as pool:
        futuros = {pool.submit(pedir_lote, client, c, u, p, s): (c, u, p, s)
                   for c, u, p, s in trabajos}
        for fut in as_completed(futuros):
            c, u, p, specs = futuros[fut]
            try:
                textos, uso = fut.result()
            except Exception as e:  # una combinacion fallida no tira todo
                fallidos += 1
                print(f"  fallo {c}/{u}/{p}: {type(e).__name__}", file=sys.stderr)
                continue
            contador.sumar(MODELO_GENERADOR, uso)
            for texto, spec in zip(textos, specs):
                numero = spec["numero"]
                # El CSV nunca puede decir algo que el texto no dice.
                if numero and str(numero) not in texto:
                    numero = None
                filas.append({"numero_cliente": numero, "texto": texto.strip(),
                              "categoria": c, "urgencia": u, "producto": p})
    print(f"  generados {len(filas)} textos ({fallidos} lotes fallidos)")
    return filas


def verificar_filas(client, filas, contador) -> None:
    with ThreadPoolExecutor(max_workers=16) as pool:
        futuros = {pool.submit(verificar, client, f["texto"]): f for f in filas}
        for fut in as_completed(futuros):
            fila = futuros[fut]
            try:
                v, uso = fut.result()
            except Exception as e:
                print(f"  fallo verificacion: {type(e).__name__}", file=sys.stderr)
                fila.update(v_categoria=None, v_urgencia=None, v_producto=None, aceptado=False)
                continue
            contador.sumar(MODELO_VERIFICADOR, uso)
            dist = abs(ORDEN_URGENCIA[v.urgencia] - ORDEN_URGENCIA[fila["urgencia"]])
            fila.update(
                v_categoria=v.categoria, v_urgencia=v.urgencia, v_producto=v.producto,
                # Categoria y producto tienen que coincidir exacto. La urgencia es mas
                # subjetiva: aceptamos un escalon de diferencia, nunca alta contra baja.
                aceptado=(v.categoria == fila["categoria"]
                          and v.producto == fila["producto"] and dist <= 1),
            )


def armar_trabajos(clientes, rng, por_combinacion, categorias) -> list:
    trabajos = []
    for c, u, p in itertools.product(categorias, URGENCIAS, PRODUCTOS):
        if (c, p) in IMPOSIBLES:
            continue
        specs = []
        for _ in range(por_combinacion):
            numero = (cliente_para(clientes, c, p, rng)
                      if rng.random() < PROB_NUMERO_CLIENTE else None)
            specs.append({"tono": rng.choice(TONOS), "largo": rng.choice(LARGOS),
                          "numero": numero})
        trabajos.append((c, u, p, specs))
    return trabajos


def limpiar(df: pd.DataFrame) -> pd.DataFrame:
    df = df[~df["texto"].str.contains(VOSEO)]
    clave = df["texto"].str.lower().str.replace(r"[^a-z0-9ñ ]", "", regex=True).str[:60]
    return df[~clave.duplicated()]


def main() -> int:
    load_dotenv(RAIZ / ".env")
    client = OpenAI()   # lee OPENAI_API_KEY del entorno, cargado desde .env
    try:
        client.models.retrieve(MODELO_GENERADOR)
    except Exception as e:
        print(f"La clave de OpenAI no funciona: {type(e).__name__}. Revisa .env.", file=sys.stderr)
        return 1

    rng = random.Random(SEED)
    DATA.mkdir(exist_ok=True)
    clientes = generar_clientes(rng)
    clientes.to_csv(DATA / "clientes.csv", index=False)
    print(f"clientes.csv: {len(clientes)} filas")

    por_cat = TOTAL // len(CATEGORIAS)
    contador = Contador()
    todas: list[dict] = []
    faltan = list(CATEGORIAS)
    por_combinacion = POR_COMBINACION

    for ronda in range(1, MAX_RONDAS + 1):
        print(f"\nRonda {ronda}: generando para {faltan}")
        nuevas = generar_ronda(client, armar_trabajos(clientes, rng, por_combinacion, faltan),
                               contador)
        verificar_filas(client, nuevas, contador)
        todas.extend(nuevas)
        crudos = pd.DataFrame(todas)
        # Guardamos lo crudo en cada ronda: si algo falla despues, no se pierde lo pagado.
        crudos.to_csv(DATA / "reclamos_crudos.csv", index=False)

        buenos = limpiar(crudos[crudos["aceptado"]])
        conteo = buenos["categoria"].value_counts()
        print("  aceptados por categoria:", conteo.reindex(list(CATEGORIAS), fill_value=0).to_dict())
        faltan = [c for c in CATEGORIAS if conteo.get(c, 0) < por_cat]
        if not faltan:
            break
        # Para la ronda siguiente, solo las categorias cortas, con lotes mas chicos.
        por_combinacion = 6
    else:
        print(f"\nAVISO: tras {MAX_RONDAS} rondas siguen cortas: {faltan}", file=sys.stderr)

    # Recorte a 100 por categoria, mezclando urgencias, y split 500/100 estratificado.
    df = pd.concat([g.sample(n=min(len(g), por_cat), random_state=SEED)
                    for _, g in buenos.groupby("categoria")])
    df = df.sample(frac=1, random_state=SEED).reset_index(drop=True)
    grupos = list(df.groupby("categoria"))
    test_idx = pd.Index([])
    for i, (_, g) in enumerate(grupos):
        n_test = TEST // len(grupos) + (1 if i < TEST % len(grupos) else 0)
        test_idx = test_idx.append(g.sample(n=n_test, random_state=SEED).index)
    df["split"] = "train"
    df.loc[test_idx, "split"] = "test"
    df.insert(0, "id", range(1, len(df) + 1))
    df["numero_cliente"] = df["numero_cliente"].astype("Int64")
    df = df[["id", "split", "numero_cliente", "texto", "categoria", "urgencia", "producto"]]
    df.to_csv(DATA / "reclamos.csv", index=False)

    crudos = pd.DataFrame(todas)
    print(f"\nreclamos.csv: {len(df)} filas")
    print(f"crudos {len(crudos)}, aceptados por el verificador {int(crudos['aceptado'].sum())} "
          f"({crudos['aceptado'].mean():.0%})")
    print("rechazo por categoria pedida:",
          (1 - crudos.groupby("categoria")["aceptado"].mean()).round(2).to_dict())
    print(df["split"].value_counts().to_dict())
    print(df["urgencia"].value_counts().to_dict())
    print(df["producto"].value_counts().to_dict())
    print(f"con numero de cliente: {int(df['numero_cliente'].notna().sum())}")
    print(f"costo aprox USD {contador.costo():.3f}  tokens {contador.tokens}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
