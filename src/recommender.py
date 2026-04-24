from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import csv

@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        # TODO: Implement recommendation logic
        return self.songs[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        # TODO: Implement explanation logic
        return "Explanation placeholder"

def load_songs(csv_path: str) -> List[Dict]:
    """
    Loads songs from a CSV file.
    Required by src/main.py
    """
    songs = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            songs.append({
                "id": int(row["id"]),
                "title": row["title"],
                "artist": row["artist"],
                "genre": row["genre"],
                "mood": row["mood"],
                "energy": float(row["energy"]),
                "tempo_bpm": float(row["tempo_bpm"]),
                "valence": float(row["valence"]),
                "danceability": float(row["danceability"]),
                "acousticness": float(row["acousticness"]),
            })
    return songs

def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """Return a numeric score and list of reason strings for a song against user preferences."""
    score = 0.0
    reasons = []

    # Layer 1 — Categorical matches
    if song["genre"] == user_prefs["favorite_genre"]:
        score += 0.5
        reasons.append("genre match (+0.5)")

    if song["mood"] == user_prefs["favorite_mood"]:
        score += 1.0
        reasons.append("mood match (+1.0)")

    # Layer 2 — Continuous similarity: similarity = 1.0 - abs(song_value - target_value)
    energy_sim = (1.0 - abs(song["energy"] - user_prefs["target_energy"])) * 3.0
    score += energy_sim
    reasons.append(f"energy similarity (+{energy_sim:.2f})")

    tempo_sim = (1.0 - abs(song["tempo_bpm"] / 200 - user_prefs["target_tempo_bpm"] / 200)) * 0.8
    score += tempo_sim
    reasons.append(f"tempo similarity (+{tempo_sim:.2f})")

    valence_sim = (1.0 - abs(song["valence"] - user_prefs["target_valence"])) * 0.6
    score += valence_sim
    reasons.append(f"valence similarity (+{valence_sim:.2f})")

    dance_sim = (1.0 - abs(song["danceability"] - user_prefs["target_danceability"])) * 0.5
    score += dance_sim
    reasons.append(f"danceability similarity (+{dance_sim:.2f})")

    acoustic_sim = (1.0 - abs(song["acousticness"] - user_prefs["target_acousticness"])) * 0.6
    score += acoustic_sim
    reasons.append(f"acousticness similarity (+{acoustic_sim:.2f})")

    # Layer 3 — Acoustic preference bonus
    if not user_prefs["likes_acoustic"] and song["acousticness"] < 0.3:
        score += 0.5
        reasons.append("acoustic bonus: non-acoustic preference match (+0.5)")
    elif user_prefs["likes_acoustic"] and song["acousticness"] > 0.7:
        score += 0.5
        reasons.append("acoustic bonus: acoustic preference match (+0.5)")

    return (score, reasons)

def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """Score every song in the catalog, sort by score descending, and return the top-k results."""
    scored = []
    for song in songs:
        score, reasons = score_song(user_prefs, song)
        explanation = "; ".join(reasons)
        scored.append((song, score, explanation))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:k]
