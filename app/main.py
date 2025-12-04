"""Grandes Paradas API main module.

Provides FastAPI application with six endpoints:
    * /hello    : simple health check
    * /ug/{ug_number} : returns information for a specific UG
    * /optimizer-parameters : receives optimization parameters and returns acknowledgment
    * /calendar/edit-maintenance : edits maintenance days in saved calendar with a json (ug, maintenance, old_days, new_days)
    * /optimize : measures number of iterations within a time span
    * /calendar : generates or retrieves randomized UG maintenance periods (param: generate=false)
"""

from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import time
import sys
from pathlib import Path
from random import randint, choice
from typing import Any, List

# Add optimizer-grandes-paradas directory to Python path
optimizer_path = Path(__file__).parent / "optimizer-grandes-paradas"

if optimizer_path.exists() and str(optimizer_path) not in sys.path:
    sys.path.insert(0, str(optimizer_path))

from optimize_module import Optimizer, constants

# Import database modules
from database import get_db, init_db
from schemas import EditMaintenanceRequest, CalendarActivityResponse
import crud

app = FastAPI(title="Grandes Paradas API")


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    await init_db()


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
    ug_info = next(
        (ug for ug in constants.UGS_INFO if ug["ug"] == ug_number), None)

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
async def edit_maintenance(
    request: EditMaintenanceRequest,
    db: AsyncSession = Depends(get_db)
) -> dict[str, str]:
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
        404 se não houver calendário ativo
        404 se a UG ou manutenção não for encontrada
        400 se os dias antigos não coincidirem com os salvos
        500 se houver erro ao atualizar
    """
    try:
        success = await crud.update_activity_days(
            db=db,
            ug=request.ug,
            maintenance=request.maintenance,
            old_days=request.old_days,
            new_days=request.new_days
        )

        if not success:
            # Check if calendar exists
            calendar = await crud.get_active_calendar(db)
            if not calendar:
                raise HTTPException(
                    status_code=404,
                    detail="Nenhum calendário ativo encontrado. Gere um calendário primeiro."
                )

            # Check if activity exists or if old days don't match
            from models import CalendarActivity
            from sqlalchemy import select

            result = await db.execute(
                select(CalendarActivity)
                .where(CalendarActivity.calendar_id == calendar.id)
                .where(CalendarActivity.ug == request.ug)
                .where(CalendarActivity.maintenance == request.maintenance)
            )
            activity = result.scalar_one_or_none()

            if not activity:
                raise HTTPException(
                    status_code=404,
                    detail=f"Manutenção '{request.maintenance}' para UG '{request.ug}' não encontrada."
                )

            # Old days don't match
            current_days = set(activity.days)
            old_days_set = set(request.old_days)
            missing_days = old_days_set - current_days
            raise HTTPException(
                status_code=400,
                detail=f"Dias {sorted(missing_days)} não encontrados na manutenção atual. "
                f"Dias atuais: {sorted(current_days)}"
            )

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
async def generate_calendar(
    generate: bool = False,
    db: AsyncSession = Depends(get_db)
) -> list[dict[str, Any]]:
    """Generate or retrieve maintenance periods per generating unit (UG).

    Parameters
    ----------
    generate : bool, optional
        Se True, gera um novo calendário aleatório e salva no banco de dados.
        Se False (padrão), retorna o calendário ativo do banco de dados.
        Se não houver calendário ativo e generate=False, gera automaticamente um novo calendário.

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
        - Calendar is automatically saved to database, replacing the previous active calendar.
    """
    # Se generate=False, tentar ler o calendário ativo do banco
    if not generate:
        activities = await crud.get_calendar_activities(db)
        if activities:
            # Activities are already sorted in crud.get_calendar_activities
            return [activity.model_dump() for activity in activities]
        else:
            # Se não houver calendário, gerar automaticamente
            print("Nenhum calendário ativo encontrado. Gerando novo calendário automaticamente.")
            generate = True

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

    # Salvar novo calendário no banco de dados
    try:
        await crud.create_calendar(db=db, activities=activities)
        print(f"Novo calendário salvo no banco de dados com {len(activities)} atividades.")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao salvar calendário no banco de dados: {e}"
        )

    # Sort activities: first by UG (numeric), then by maintenance (alphabetical)
    sorted_activities = sorted(
        activities,
        key=lambda act: (int(act["ug"]), act["maintenance"])
    )
    return sorted_activities
