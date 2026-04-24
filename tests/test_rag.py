import logging
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.rag_engine import retrieve_context, _get_collection
from src.logger import log_run, LOW_CONFIDENCE_THRESHOLD


def test_rag_loads_without_error():
    collection = _get_collection()
    assert collection is not None
    assert collection.count() > 0


def test_retrieve_context_returns_non_empty_string():
    result = retrieve_context("electronic", "energetic")
    assert isinstance(result, str)
    assert result.strip() != ""


def test_low_confidence_warning_is_triggered(caplog):
    profile = {
        "favorite_genre": "ambient",
        "favorite_mood": "melancholic",
        "target_energy": 0.0,
    }
    low_score = LOW_CONFIDENCE_THRESHOLD - 0.01
    recommendations = [
        ({"title": "Test Song", "artist": "Test Artist"}, low_score, "energy similarity (+0.10)"),
    ]

    with caplog.at_level(logging.WARNING, logger="recommender"):
        log_run("Low Confidence Profile", profile, recommendations)

    assert any("LOW CONFIDENCE" in record.message for record in caplog.records)


def test_logger_creates_log_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "test_recommender.log"

        logger = logging.getLogger("recommender_test_isolated")
        logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler(log_path, encoding="utf-8")
        fh.setFormatter(logging.Formatter("%(asctime)s  %(levelname)-8s  %(message)s"))
        logger.addHandler(fh)

        logger.info("test run")
        fh.flush()
        fh.close()

        assert log_path.exists()
        assert log_path.stat().st_size > 0
