"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from src.recommender import load_songs, recommend_songs


# ---------------------------------------------------------------------------
# Step 2 — Taste Profiles
# ---------------------------------------------------------------------------
# Three distinct listener archetypes, each with a label for display.
# All numeric targets are on a 0.0–1.0 scale unless noted (tempo is BPM).

PROFILES = {
    # --- Profile 1: High-Energy Pop ---
    # A listener who loves upbeat, danceable pop anthems.
    "High-Energy Pop": {
        "favorite_genre": "pop",
        "favorite_mood": "happy",
        "target_energy": 0.90,          # very high drive
        "likes_acoustic": False,         # prefers produced / electronic sound
        "target_tempo_bpm": 128,         # classic dance-pop BPM
        "target_valence": 0.85,          # bright and positive
        "target_danceability": 0.90,     # made for the dance floor
        "target_acousticness": 0.08,     # heavily produced, minimal acoustic
    },

    # --- Profile 2: Chill Lofi ---
    # A listener who uses music as a focus/study aid—soft, mellow, unhurried.
    "Chill Lofi": {
        "favorite_genre": "lofi",
        "favorite_mood": "chill",
        "target_energy": 0.38,           # low-key, never overwhelming
        "likes_acoustic": True,          # warm acoustic textures preferred
        "target_tempo_bpm": 76,          # slow and laid-back
        "target_valence": 0.58,          # slightly positive but understated
        "target_danceability": 0.60,     # gentle groove, not a dance track
        "target_acousticness": 0.78,     # high acoustic character
    },

    # --- Profile 3: Deep Intense Rock ---
    # A listener who craves powerful, electric rock/metal energy.
    "Deep Intense Rock": {
        "favorite_genre": "rock",
        "favorite_mood": "intense",
        "target_energy": 0.88,           # high drive; lofi sits ~0.35–0.42
        "likes_acoustic": False,         # prefers electric/produced sound
        "target_tempo_bpm": 145,         # fast; lofi sits ~72–82 BPM
        "target_valence": 0.50,          # mid-valence: edgy but not joyless
        "target_danceability": 0.68,     # rhythmic but not dance-floor pop
        "target_acousticness": 0.10,     # low; lofi sits ~0.71–0.86
    },
}

# ---------------------------------------------------------------------------
# Step 2 (System Evaluation) — Adversarial / Edge-Case Profiles
# ---------------------------------------------------------------------------
# These profiles are deliberately conflicting or extreme to probe whether the
# scoring logic produces unexpected or unfair results.
#
# Findings / observations are noted inline as comments.

ADVERSARIAL_PROFILES = {
    # --- Edge Case A: Conflicting Energy vs. Mood ---
    # High energy (0.9) combined with a "sad" mood don't co-occur naturally in
    # the dataset. Expect the mood penalty to apply but energy similarity to
    # pull high-energy tracks to the top anyway — revealing that continuous
    # features outweigh categorical mood match.
    "Conflicting Energy + Sad Mood": {
        "favorite_genre": "pop",
        "favorite_mood": "sad",          # no songs in dataset have mood=sad
        "target_energy": 0.90,
        "likes_acoustic": False,
        "target_tempo_bpm": 128,
        "target_valence": 0.15,          # very low valence (dark/sad feel)
        "target_danceability": 0.85,
        "target_acousticness": 0.08,
    },

    # --- Edge Case B: All Extremes at Once ---
    # Maximum values for every continuous dimension simultaneously.
    # No single song will be a perfect match; tests whether the scorer
    # degrades gracefully or produces a clear winner despite imperfect fits.
    "All-Max Extremes": {
        "favorite_genre": "electronic",
        "favorite_mood": "euphoric",
        "target_energy": 1.0,
        "likes_acoustic": False,
        "target_tempo_bpm": 200,         # at the ceiling used in tempo_sim formula
        "target_valence": 1.0,
        "target_danceability": 1.0,
        "target_acousticness": 0.0,
    },

    # --- Edge Case C: All Zeros / Minimum ---
    # Minimum values everywhere. The formula `1 - abs(song - target)` will
    # reward songs close to 0.0. Checks for negative scores or rank inversions.
    "All-Min Zeros": {
        "favorite_genre": "ambient",
        "favorite_mood": "melancholic",
        "target_energy": 0.0,
        "likes_acoustic": True,
        "target_tempo_bpm": 0,
        "target_valence": 0.0,
        "target_danceability": 0.0,
        "target_acousticness": 1.0,
    },

    # --- Edge Case D: Genre / Mood Mismatch with Strong Continuous Match ---
    # The genre and mood don't exist in the dataset ("reggae"/"romantic"),
    # but continuous targets closely match the reggae track "Island Pulse".
    # Tests whether categorical misses can be overcome by strong continuous
    # similarity — could reveal genre-label bias in the scorer.
    "Genre Mismatch, Strong Continuous": {
        "favorite_genre": "classical",   # scarce in dataset (1 song)
        "favorite_mood": "romantic",     # no songs with mood=romantic except r&b
        "target_energy": 0.50,
        "likes_acoustic": True,
        "target_tempo_bpm": 76,
        "target_valence": 0.80,
        "target_danceability": 0.72,
        "target_acousticness": 0.65,
    },

    # --- Edge Case E: likes_acoustic vs. Low acousticness target ---
    # likes_acoustic=True but target_acousticness=0.05 — the acoustic bonus
    # fires for high-acoustic songs while the continuous term penalises them.
    # Tests for internal contradiction between Layer 2 and Layer 3 scoring.
    "Acoustic Flag Contradiction": {
        "favorite_genre": "rock",
        "favorite_mood": "intense",
        "target_energy": 0.88,
        "likes_acoustic": True,          # wants acoustic bonus
        "target_tempo_bpm": 145,
        "target_valence": 0.50,
        "target_danceability": 0.68,
        "target_acousticness": 0.05,     # but also wants very low acousticness
    },
}


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
        print_recommendations(label, recs)

    # --- Run adversarial / edge-case profiles ---
    print("\n" + "#" * 60)
    print("  SYSTEM EVALUATION — ADVERSARIAL / EDGE-CASE PROFILES")
    print("#" * 60)
    for label, prefs in ADVERSARIAL_PROFILES.items():
        recs = recommend_songs(prefs, songs, k=5)
        print_recommendations(label, recs)


if __name__ == "__main__":
    main()
