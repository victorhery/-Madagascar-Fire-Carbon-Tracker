import datetime
from unittest.mock import AsyncMock

import pytest

from app.jobs.poll_firms import run_poll_firms
from app.models import FireDetection
from app.repositories import SQLAlchemyFireRepository
from app.services import RawFireDetection


def make_raw(**overrides) -> RawFireDetection:
    defaults = dict(
        latitude=-21.45,
        longitude=47.08,
        acq_date=datetime.date(2026, 8, 1),
        acq_time="1415",
        satellite="VIIRS_SNPP_NRT",
        brightness=310.5,
        confidence="high",
        frp=12.3,
    )
    defaults.update(overrides)
    return RawFireDetection(**defaults)


@pytest.mark.asyncio
async def test_run_poll_firms_creates_new_detections(db_session):
    fetcher = AsyncMock()
    fetcher.fetch_recent = AsyncMock(
        return_value=[make_raw(acq_time="1000"), make_raw(acq_time="1415")]
    )
    repo = SQLAlchemyFireRepository(db_session)

    result = await run_poll_firms(fetcher, repo, day_range=1)

    assert result.fetched == 2
    assert result.created == 2
    assert result.duplicates_skipped == 0
    assert db_session.query(FireDetection).count() == 2


@pytest.mark.asyncio
async def test_run_poll_firms_skips_already_known_detections(db_session):
    """
    Une détection déjà en base (même clé naturelle) ne doit pas être
    recréée -> vérifie le dédoublonnage explicite, indépendamment de la
    UniqueConstraint testée en Phase 1.
    """
    repo = SQLAlchemyFireRepository(db_session)
    repo.create(FireDetection(
        latitude=-21.45, longitude=47.08, acq_date=datetime.date(2026, 8, 1),
        acq_time="1415", satellite="VIIRS_SNPP_NRT",
    ))

    fetcher = AsyncMock()
    fetcher.fetch_recent = AsyncMock(
        return_value=[
            make_raw(acq_time="1415"),  # déjà en base -> doublon
            make_raw(acq_time="1730"),  # nouvelle -> à créer
        ]
    )

    result = await run_poll_firms(fetcher, repo, day_range=1)

    assert result.fetched == 2
    assert result.created == 1
    assert result.duplicates_skipped == 1
    assert db_session.query(FireDetection).count() == 2  # 1 pré-existante + 1 nouvelle


@pytest.mark.asyncio
async def test_run_poll_firms_handles_empty_fetch(db_session):
    fetcher = AsyncMock()
    fetcher.fetch_recent = AsyncMock(return_value=[])
    repo = SQLAlchemyFireRepository(db_session)

    result = await run_poll_firms(fetcher, repo, day_range=1)

    assert result.fetched == 0
    assert result.created == 0
    assert result.duplicates_skipped == 0


@pytest.mark.asyncio
async def test_run_poll_firms_passes_day_range_to_fetcher(db_session):
    fetcher = AsyncMock()
    fetcher.fetch_recent = AsyncMock(return_value=[])
    repo = SQLAlchemyFireRepository(db_session)

    await run_poll_firms(fetcher, repo, day_range=3)

    fetcher.fetch_recent.assert_awaited_once_with(day_range=3)
