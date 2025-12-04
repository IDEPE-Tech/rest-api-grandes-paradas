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
async def optimizer_parameters(
    parameters: dict[str, Any],
    db: AsyncSession = Depends(get_db)
) -> dict[str, str]:
    """Recebe parâmetros de otimização em formato JSON e salva no banco de dados.

    Parameters
    ----------
    parameters : dict[str, Any]
        JSON com parâmetros de otimização:
            • ``method``: "AG" ou "ACO" (obrigatório)
            • ``mode``: "params" ou "time" (obrigatório)
            • ``n_pop``: int (opcional, necessário para AG)
            • ``n_gen``: int (opcional, necessário para AG + params)
            • ``n_ants``: int (opcional, necessário para ACO)
            • ``n_iter``: int (opcional, necessário para ACO + params)
            • ``time``: int (opcional, necessário para mode="time")

    Returns
    -------
    dict
        Dicionário com acknowledgment:
            • ``status``: status da requisição
            • ``message``: mensagem de confirmação

    Raises
    ------
    HTTPException
        400 se os parâmetros forem inválidos
        500 se houver erro ao salvar
    """
    try:
        # Validate parameters by creating Optimizer instance
        # This will raise validation errors if parameters are invalid
        optm = Optimizer(**parameters)
        
        # Save to database
        await crud.create_or_update_optimizer(
            db=db,
            method=optm.method,
            mode=optm.mode,
            n_pop=optm.n_pop,
            n_gen=optm.n_gen,
            n_ants=optm.n_ants,
            n_iter=optm.n_iter,
            time=optm.time
        )
        
        return {
            "status": "success",
            "message": "Parâmetros de otimização salvos com sucesso no banco de dados."
        }
    except Exception as e:
        # If it's a validation error from Pydantic, return 400
        error_msg = str(e)
        if "inválido" in error_msg or "obrigatório" in error_msg or "invalid" in error_msg.lower():
            raise HTTPException(
                status_code=400,
                detail=f"Parâmetros inválidos: {error_msg}"
            )
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao salvar parâmetros de otimização: {error_msg}"
        )


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
async def optimize(
    db: AsyncSession = Depends(get_db)
) -> dict[str, float]:
    """Run the optimizer and update the calendar with the optimized schedule.

    Uses the active optimizer parameters from the database. If no optimizer
    configuration exists, creates one with default parameters (AG, time mode, n_pop=50, time=60).

    Returns
    -------
    dict
        Dictionary with:
            • ``elapsed_seconds``: actual elapsed time in seconds
    """
    # Get optimizer parameters from database (always returns a config, creates default if needed)
    optimizer_config = await crud.get_active_optimizer(db)
    
    # Create optimizer instance
    optm = Optimizer(
        method=optimizer_config.method,
        mode=optimizer_config.mode,
        n_pop=optimizer_config.n_pop,
        n_gen=optimizer_config.n_gen,
        n_ants=optimizer_config.n_ants,
        n_iter=optimizer_config.n_iter,
        time=optimizer_config.time
    )
    
    # Run optimizer and get final result
    final_update = None
    for update in optm.solve():
        if update["status"] == "completed":
            final_update = update
            break
    
    if not final_update or "schedule" not in final_update:
        raise HTTPException(
            status_code=500,
            detail="Optimizer did not return a valid schedule"
        )
    
    # Convert schedule format from optimizer to database format
    # Optimizer returns: ug as int (1-50), days as 0-indexed (0-364)
    # Database expects: ug as zero-padded string ("01"-"50"), days as 1-indexed (1-365)
    activities = []
    for activity in final_update["schedule"]:
        activities.append({
            "ug": f"{activity['ug']:02d}",  # Convert int to zero-padded string
            "maintenance": activity["maintenance"],
            "days": [day + 1 for day in activity["days"]]  # Convert 0-indexed to 1-indexed
        })
    
    # Save schedule to database as new calendar
    try:
        await crud.create_calendar(db=db, activities=activities)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error saving optimized calendar to database: {e}"
        )
    
    return {"elapsed_seconds": final_update["elapsed_seconds"]}


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
