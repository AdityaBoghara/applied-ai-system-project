"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from recommender import load_songs, recommend_songs


def main() -> None:
    songs = load_songs("data/songs.csv") 

    # --- Taste Profile (Step 2) ---
    # Represents a listener who enjoys high-energy, electric rock/metal vibes.
    # All numeric targets are on a 0.0–1.0 scale unless noted (tempo is BPM).
    user_prefs = {
        "favorite_genre": "rock",          # primary genre anchor
        "favorite_mood": "intense",        # preferred emotional character
        "target_energy": 0.88,             # high drive; lofi sits ~0.35–0.42
        "likes_acoustic": False,           # prefers electric/produced sound
        "target_tempo_bpm": 145,           # fast; lofi sits ~72–82 BPM
        "target_valence": 0.50,            # mid-valence: edgy but not joyless
        "target_danceability": 0.68,       # rhythmic but not dance-floor pop
        "target_acousticness": 0.10,       # low; lofi sits ~0.71–0.86
    }

    recommendations = recommend_songs(user_prefs, songs, k=5)

    print("\nTop recommendations:\n")
    for rec in recommendations:
        # You decide the structure of each returned item.
        # A common pattern is: (song, score, explanation)
        song, score, explanation = rec
        print(f"{song['title']} - Score: {score:.2f}")
        print(f"Because: {explanation}")
        print()


if __name__ == "__main__":
    main()
