"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from src.recommender import load_songs, recommend_songs
from src.rag_engine import retrieve_context
from src.logger import log_run
from src.profiles import PROFILES, ADVERSARIAL_PROFILES


def print_recommendations(label: str, recommendations: list) -> None:
    width = 60
    print("\n" + "=" * width)
    print(f"  🎵  TOP RECOMMENDATIONS — {label}")
    print("=" * width)

    for rank, rec in enumerate(recommendations, start=1):
        song, score, explanation = rec
        reasons = [r.strip() for r in explanation.split(";") if r.strip()]

        print(f"\n  #{rank}  {song['title']}")
        print(f"       by {song['artist']}  |  {song['genre'].capitalize()}  |  {song['mood'].capitalize()}")
        print(f"       Score: {score:.2f}")
        print(f"       {'─' * 40}")
        for reason in reasons:
            print(f"         • {reason}")

        context = retrieve_context(song["genre"], song["mood"])
        if context:
            print(f"\n       Genre context:")
            print(f"         {context}")
        print()

    print("=" * width + "\n")


def main() -> None:
    songs = load_songs("data/songs.csv")

    # --- Run standard taste profiles ---
    print("\n" + "#" * 60)
    print("  STANDARD TASTE PROFILES")
    print("#" * 60)
    for label, prefs in PROFILES.items():
        recs = recommend_songs(prefs, songs, k=5)
        log_run(label, prefs, recs)
        print_recommendations(label, recs)

    # --- Run adversarial / edge-case profiles ---
    print("\n" + "#" * 60)
    print("  SYSTEM EVALUATION — ADVERSARIAL / EDGE-CASE PROFILES")
    print("#" * 60)
    for label, prefs in ADVERSARIAL_PROFILES.items():
        recs = recommend_songs(prefs, songs, k=5)
        log_run(label, prefs, recs)
        print_recommendations(label, recs)


if __name__ == "__main__":
    main()
