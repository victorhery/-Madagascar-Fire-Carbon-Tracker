from dataclasses import dataclass

from app.models import FireDetection
from app.repositories import FireRepositoryInterface
from app.services import FireDataSourceInterface


@dataclass
class PollFirmsResult:
    """Résumé d'une exécution du job, utile pour les logs et les tests."""

    fetched: int = 0
    created: int = 0
    duplicates_skipped: int = 0


async def run_poll_firms(
    fetcher: FireDataSourceInterface,
    repo: FireRepositoryInterface,
    day_range: int = 1,
) -> PollFirmsResult:
    """
    Récupère les détections récentes via `fetcher`, puis les insère en base
    via `repo`, en sautant explicitement celles déjà connues plutôt que de
    laisser échouer un commit sur la contrainte unique (plus lisible, et
    évite qu'un doublon dans le lot fasse échouer toute la transaction).

    Dépend uniquement des deux interfaces (principe D) : ni FIRMS, ni
    SQLAlchemy, ni httpx ne sont mentionnés ici -> testable avec de purs
    mocks, sans réseau ni base de données réelle.
    """
    raw_detections = await fetcher.fetch_recent(day_range=day_range)

    result = PollFirmsResult(fetched=len(raw_detections))

    for raw in raw_detections:
        existing = repo.get_by_natural_key(
            latitude=raw.latitude,
            longitude=raw.longitude,
            acq_date=raw.acq_date,
            acq_time=raw.acq_time,
            satellite=raw.satellite,
        )
        if existing is not None:
            result.duplicates_skipped += 1
            continue

        fire = FireDetection(
            latitude=raw.latitude,
            longitude=raw.longitude,
            brightness=raw.brightness,
            confidence=raw.confidence,
            frp=raw.frp,
            acq_date=raw.acq_date,
            acq_time=raw.acq_time,
            satellite=raw.satellite,
        )
        repo.create(fire)
        result.created += 1

    return result
