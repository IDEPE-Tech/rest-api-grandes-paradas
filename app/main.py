"""Grandes Paradas API main module.

Provides FastAPI application with six endpoints:
    * /hello    : simple health check
    * /ug/{ug_number} : returns information for a specific UG
    * /optimizer-parameters : receives optimization parameters and returns acknowledgment
    * /calendar/edit-maintenance : edits maintenance days in saved calendar with a json (ug, maintenance, old_days, new_days)
    * /optimize : measures number of iterations within a time span
    * /calendar : generates or retrieves randomized UG maintenance periods (param: generate=false)
"""

from fastapi import FastAPI, HTTPException
import time
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from random import randint, choice
from typing import Any, List
from pydantic import BaseModel

# Add optimizer-grandes-paradas directory to Python path
# Works both locally and in Docker container
optimizer_path = Path(__file__).parent / "optimizer-grandes-paradas"

if optimizer_path.exists() and str(optimizer_path) not in sys.path:
    sys.path.insert(0, str(optimizer_path))

from optimize_module import Optimizer, constants

# ---------- Pydantic Models ----------


class EditMaintenanceRequest(BaseModel):
    """Modelo para edição de dias de manutenção."""
    ug: str
    maintenance: str
    old_days: List[int]
    new_days: List[int]


app = FastAPI(title="Grandes Paradas API")


@app.get("/hello")
async def hello() -> dict[str, str]:
    """Return a simple greeting.

    Acts as a health-check endpoint for the API.
    """
    return {"message": "hello"}


@app.get("/ug/{ug_number}")
async def get_ug_info(ug_number: int) -> dict[str, Any]:
    """Retorna as informações de uma UG específica.

    Parameters
    ----------
    ug_number : int
        Número da UG (1-50)

    Returns
    -------
    dict
        Dicionário com as informações da UG:
            • ``ug``: número da UG
            • ``cf``: número da casa de força
            • ``portico``: número do pórtico
            • ``island``: número da ilha
            • ``bladesNumber``: número de pás
            • ``voltage``: tensão em kV
            • ``localization``: localização (MD, ME, LR)
            • ``producer``: fabricante (GE, VOITH, ANDRITZ)

    Raises
    ------
    HTTPException
        404 se a UG não for encontrada
    """
    # Busca a UG na lista UGS_INFO
    ug_info = next((ug for ug in constants.UGS_INFO if ug["ug"] == ug_number), None)

    if ug_info is None:
        raise HTTPException(
            status_code=404,
            detail=f"UG {ug_number} não encontrada. UGs disponíveis: 1-50"
        )

    return ug_info


@app.post("/optimizer-parameters")
async def optimizer_parameters(parameters: dict[str, Any]) -> dict[str, str]:
    """Recebe parâmetros de otimização em formato JSON e retorna acknowledgment.

    Parameters
    ----------
    parameters : dict[str, Any]
        JSON com parâmetros de otimização (estrutura a ser definida)

    Returns
    -------
    dict
        Dicionário com acknowledgment:
            • ``status``: status da requisição
            • ``message``: mensagem de confirmação
    """
    # Por enquanto, apenas retorna um acknowledgment
    # TODO: Implementar lógica de otimização real

    return {
        "status": "received",
        "message": "Parâmetros de otimização recebidos com sucesso. Processamento será implementado em breve."
    }


@app.put("/calendar/edit-maintenance")
async def edit_maintenance(request: EditMaintenanceRequest) -> dict[str, str]:
    """Edita os dias de uma manutenção específica no calendário salvo.

    Parameters
    ----------
    request : EditMaintenanceRequest
        Dados da edição contendo:
            • ``ug``: número da UG (formato string, ex: "01", "25")
            • ``maintenance``: código da manutenção (ex: "AR", "CK")
            • ``old_days``: lista dos dias atuais a serem substituídos
            • ``new_days``: lista dos novos dias

    Returns
    -------
    dict
        Dicionário com resultado da operação:
            • ``status``: status da operação
            • ``message``: mensagem descritiva

    Raises
    ------
    HTTPException
        404 se o arquivo calendario_manutencao.json não existir
        404 se a UG ou manutenção não for encontrada
        400 se os dias antigos não coincidirem com os salvos
        500 se houver erro ao salvar o arquivo
    """
    filename = "calendario_manutencao.json"

    # Verificar se o arquivo existe
    if not os.path.exists(filename):
        raise HTTPException(
            status_code=404,
            detail="Arquivo calendario_manutencao.json não encontrado. Gere um calendário primeiro."
        )

    try:
        # Ler o arquivo atual
        with open(filename, 'r', encoding='utf-8') as f:
            calendar_data = json.load(f)

        activities = calendar_data.get("activities", [])

        # Encontrar a atividade específica
        target_activity = None
        for activity in activities:
            if activity["ug"] == request.ug and activity["maintenance"] == request.maintenance:
                target_activity = activity
                break

        if not target_activity:
            raise HTTPException(
                status_code=404,
                detail=f"Manutenção '{request.maintenance}' para UG '{request.ug}' não encontrada."
            )

        # Verificar se os dias antigos coincidem
        current_days = set(target_activity["days"])
        old_days_set = set(request.old_days)

        if not old_days_set.issubset(current_days):
            missing_days = old_days_set - current_days
            raise HTTPException(
                status_code=400,
                detail=f"Dias {sorted(missing_days)} não encontrados na manutenção atual. "
                f"Dias atuais: {sorted(current_days)}"
            )

        # Realizar a edição
        # Remover os dias antigos
        new_days_list = [day for day in target_activity["days"]
                         if day not in old_days_set]
        # Adicionar os novos dias
        new_days_list.extend(request.new_days)
        # Ordenar e remover duplicatas
        target_activity["days"] = sorted(list(set(new_days_list)))

        # Atualizar timestamp
        calendar_data["last_modified"] = datetime.now().isoformat()

        # Salvar o arquivo atualizado
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(calendar_data, f, indent=2, ensure_ascii=False)

        return {
            "status": "success",
            "message": f"Manutenção '{request.maintenance}' da UG '{request.ug}' editada com sucesso. "
                      f"Substituídos {len(request.old_days)} dias por {len(request.new_days)} novos dias."
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao editar manutenção: {e}"
        )


# ---------- Optimize Endpoint ----------


@app.post("/optimize")
def optimize(n: int) -> dict[str, float | int]:
    """Busy-loop for *n* seconds and return executed iterations.

    Parameters
    ----------
    n : int
        Target duration in seconds for which the busy loop should run.

    Returns
    -------
    dict
        Dictionary with:
            • ``n``: number of iterations performed
            • ``elapsed_seconds``: actual elapsed time in seconds
    """
    start = time.perf_counter()
    counter = 0

    while time.perf_counter() - start < n:
        counter += 1

    elapsed = time.perf_counter() - start
    return {"n": counter, "elapsed_seconds": elapsed}


# ---------- Calendar Endpoint ----------


@app.get("/calendar")
def generate_calendar(generate: bool = False) -> list[dict[str, Any]]:
    """Generate or retrieve maintenance periods per generating unit (UG).

    Parameters
    ----------
    generate : bool, optional
        Se True, gera um novo calendário aleatório e salva no arquivo.
        Se False (padrão), retorna o calendário salvo em calendario_manutencao.json.
        Se o arquivo não existir e generate=False, retorna erro 404.

    Returns
    -------
    list[dict[str, Any]]
        Lista de dicionários; cada dicionário agrega um ou mais períodos
        contínuos de manutenção para uma UG sob um código de manutenção específico.

    Response schema (per item):
        - ``ug``: zero-padded string from "01" to "50"
        - ``maintenance``: string, one of the values defined in ``MAINTENANCE_CODES``
        - ``days``: list[int], days in 1..365 sorted ascending; may contain
          multiple continuous segments if more than one period was generated

    Rules (quando generate=True):
        - For each UG, randomly select 1 to 5 maintenance specifications.
        - For each selected specification, generate 1 to 2 independent periods.
        - Each period has a random continuous duration between 20 and 100 days.
        - Periods may overlap (even within the same UG/spec).
        - Calendar is automatically saved to calendario_manutencao.json.

    Raises
    ------
    HTTPException
        404 se generate=False e o arquivo calendario_manutencao.json não existir
    """
    filename = "calendario_manutencao.json"

    # Se generate=False, tentar ler o arquivo existente
    if not generate:
        if os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    calendar_data = json.load(f)
                return calendar_data.get("activities", [])
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Erro ao ler arquivo de calendário: {e}"
                )
        else:
            raise HTTPException(
                status_code=404,
                detail="Arquivo calendario_manutencao.json não encontrado. Use generate=true para criar um novo calendário."
            )

    # Se generate=True, gerar novo calendário
    num_units = 50
    num_days_in_year = 365
    activities: list[dict[str, Any]] = []

    for unit_number in range(1, num_units + 1):
        # Randomly choose how many different maintenance codes this UG will have
        num_activities = randint(1, 5)
        for _ in range(num_activities):
            specification = choice(list(constants.MAINTENANCES_TYPES.keys()))

            # For this specification, generate 1 to 2 independent periods
            num_periods = randint(1, 2)
            days: list[int] = []
            for _ in range(num_periods):
                duration = randint(20, 100)
                start_day = randint(1, num_days_in_year - duration + 1)
                for day_number in range(start_day, start_day + duration):
                    days.append(day_number)

            days.sort()
            activities.append({
                "ug": f"{unit_number:02d}",
                "maintenance": specification,
                "days": days,
            })

    # Salvar novo calendário
    calendar_data = {
        "generated_at": datetime.now().isoformat(),
        "total_activities": len(activities),
        "activities": activities
    }

    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(calendar_data, f, indent=2, ensure_ascii=False)
        print(f"Novo calendário salvo em: {filename}")
    except Exception as e:
        print(f"Erro ao salvar arquivo: {e}")

    return activities
