import asyncio
import logging
import sys
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.scheduling import create_scheduler, run_immediate_jobs
from app.api.routes import alerts, carbon, fires, stats


logger = logging.getLogger("platform")


def _running_under_pytest() -> bool:
    return "pytest" in sys.modules


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        force=True,
    )


def _report_initial_jobs_result(task: asyncio.Task) -> None:
    if task.cancelled():
        return

    exception = task.exception()

    if exception is not None:
        logger.error(
            "Échec des tâches initiales.",
            exc_info=(
                type(exception),
                exception,
                exception.__traceback__,
            ),
        )
    else:
        logger.info("Premier passage des tâches automatiques terminé.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    if _running_under_pytest():
        yield
        return

    _configure_logging()

    scheduler = create_scheduler()
    scheduler.start()
    app.state.scheduler = scheduler

    logger.info("Scheduler démarré.")

    for job in scheduler.get_jobs():
        logger.info(
            "Tâche planifiée : %s | prochaine exécution : %s",
            job.id,
            job.next_run_time,
        )

    initial_task = asyncio.create_task(
        run_immediate_jobs(),
        name="initial_background_jobs",
    )
    initial_task.add_done_callback(_report_initial_jobs_result)
    app.state.initial_jobs_task = initial_task

    logger.info("Premier passage FIRMS et estimations lancé en arrière-plan.")

    try:
        yield
    finally:
        if not initial_task.done():
            initial_task.cancel()
            try:
                await initial_task
            except asyncio.CancelledError:
                pass

        scheduler.shutdown(wait=False)
        logger.info("Arrêt du scheduler demandé.")


app = FastAPI(
    title="Madagascar FireCarbon Tracker API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(fires.router)
app.include_router(stats.router)
app.include_router(carbon.router)
app.include_router(alerts.router)


@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Vérifie que l'API et la connexion à la base fonctionnent.
    """
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    return {
        "status": "ok" if db_ok else "degraded",
        "database": "connected" if db_ok else "unreachable",
    }