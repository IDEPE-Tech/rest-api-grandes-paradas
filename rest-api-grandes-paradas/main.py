from fastapi import FastAPI
import time

app = FastAPI(title="Hello API")


@app.get("/hello")
async def hello():
    """Endpoint de saúde que retorna uma saudação simples."""
    return {"message": "hello"}


# Endpoint que executa um loop de `n` iterações (query param) e devolve o tempo em segundos
@app.post("/optimize")
def optimize(n: int):
    """Executa um for com *n* repetições e retorna o tempo decorrido.

    Exemplo de chamada: /optimize?n=100000
    """

    start = time.perf_counter()
    for _ in range(n):
        pass  # operação simulada
    end = time.perf_counter()

    elapsed = end - start
    return {"n": n, "elapsed_seconds": elapsed}


# ---------- Calendar Endpoint ----------

from random import randint, choice


@app.get("/calendar")
def generate_calendar():
    """Gera aleatoriamente uma matriz 50x365 indicando manutenção (1) ou não (0).

    Algoritmo:
    1. Inicia dia = 0.
    2. Enquanto dia < 365:
         • Seleciona uma UG aleatória (0-49).
         • Seleciona duração aleatória entre 1 e 10, ajustada para não ultrapassar 365.
         • Marca 1 para essa UG durante *duração* dias a partir de *dia*.
         • Incrementa dia += duração.
    Dessa forma, sempre existe exatamente uma UG em manutenção por dia.
    """

    total_ugs = 50
    total_days = 365

    # Matriz preenchida com zeros
    matrix = [[0 for _ in range(total_days)] for _ in range(total_ugs)]

    day = 0
    while day < total_days:
        ug = randint(0, total_ugs - 1)  # escolhe UG
        duration = randint(1, 10)
        # Ajusta duração para não ultrapassar o limite do ano
        duration = min(duration, total_days - day)

        # Marca manutenção
        for d in range(day, day + duration):
            matrix[ug][d] = 1

        day += duration

    return {"calendar": matrix} 