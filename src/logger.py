import logging
from pathlib import Path

_LOG_FILE = Path(__file__).parent.parent / "logs" / "recommender.log"

_LOG_FILE.parent.mkdir(exist_ok=True)

_logger = logging.getLogger("recommender")
_logger.setLevel(logging.DEBUG)

if not _logger.handlers:
    _fmt = logging.Formatter("%(asctime)s  %(levelname)-8s  %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    _fh = logging.FileHandler(_LOG_FILE, encoding="utf-8")
    _fh.setLevel(logging.DEBUG)
    _fh.setFormatter(_fmt)

    _ch = logging.StreamHandler()
    _ch.setLevel(logging.DEBUG)
    _ch.setFormatter(_fmt)

    _logger.addHandler(_fh)
    _logger.addHandler(_ch)

LOW_CONFIDENCE_THRESHOLD = 3.0


def log_run(profile_label: str, profile: dict, recommendations: list) -> None:
    """Log a recommendation run and warn if the top score is below the confidence threshold."""
    genre = profile.get("favorite_genre", "?")
    mood = profile.get("favorite_mood", "?")
    energy = profile.get("target_energy", "?")

    _logger.info(
        "RUN | profile=%r | genre=%s | mood=%s | energy=%.2f | results=%d",
        profile_label,
        genre,
        mood,
        energy,
        len(recommendations),
    )

    if not recommendations:
        _logger.warning("RUN | profile=%r | no recommendations returned", profile_label)
        return

    top_song, top_score, _ = recommendations[0]
    _logger.info(
        "TOP | profile=%r | #1=%r | artist=%r | score=%.2f",
        profile_label,
        top_song["title"],
        top_song["artist"],
        top_score,
    )

    if top_score < LOW_CONFIDENCE_THRESHOLD:
        _logger.warning(
            "LOW CONFIDENCE | profile=%r | top_score=%.2f < %.1f",
            profile_label,
            top_score,
            LOW_CONFIDENCE_THRESHOLD,
        )
