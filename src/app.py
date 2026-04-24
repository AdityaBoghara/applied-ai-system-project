import sys
import os
from pathlib import Path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from src.recommender import load_songs, recommend_songs
from src.rag_engine import retrieve_context
from src.logger import log_run

_SONGS_CSV = Path(__file__).parent.parent / "data" / "songs.csv"

# ── page config ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="VibeMatch", page_icon="🎵", layout="wide")

# ── data ─────────────────────────────────────────────────────────────────────
@st.cache_data
def get_songs():
    return load_songs(str(_SONGS_CSV))

SONGS = get_songs()

CATALOG_GENRES = sorted({s["genre"] for s in SONGS})
CATALOG_MOODS  = sorted({s["mood"]  for s in SONGS})

PROFILES = {
    "High-Energy Pop": {
        "favorite_genre": "pop", "favorite_mood": "happy",
        "target_energy": 0.90, "likes_acoustic": False,
        "target_tempo_bpm": 128, "target_valence": 0.85,
        "target_danceability": 0.90, "target_acousticness": 0.08,
    },
    "Chill Lofi": {
        "favorite_genre": "lofi", "favorite_mood": "chill",
        "target_energy": 0.38, "likes_acoustic": True,
        "target_tempo_bpm": 76, "target_valence": 0.58,
        "target_danceability": 0.60, "target_acousticness": 0.78,
    },
    "Deep Intense Rock": {
        "favorite_genre": "rock", "favorite_mood": "intense",
        "target_energy": 0.88, "likes_acoustic": False,
        "target_tempo_bpm": 145, "target_valence": 0.50,
        "target_danceability": 0.68, "target_acousticness": 0.10,
    },
    "Conflicting Energy + Sad Mood": {
        "favorite_genre": "pop", "favorite_mood": "sad",
        "target_energy": 0.90, "likes_acoustic": False,
        "target_tempo_bpm": 128, "target_valence": 0.15,
        "target_danceability": 0.85, "target_acousticness": 0.08,
    },
    "All-Max Extremes": {
        "favorite_genre": "electronic", "favorite_mood": "euphoric",
        "target_energy": 1.0, "likes_acoustic": False,
        "target_tempo_bpm": 200, "target_valence": 1.0,
        "target_danceability": 1.0, "target_acousticness": 0.0,
    },
    "All-Min Zeros": {
        "favorite_genre": "ambient", "favorite_mood": "melancholic",
        "target_energy": 0.0, "likes_acoustic": True,
        "target_tempo_bpm": 0, "target_valence": 0.0,
        "target_danceability": 0.0, "target_acousticness": 1.0,
    },
    "Genre Mismatch, Strong Continuous": {
        "favorite_genre": "classical", "favorite_mood": "romantic",
        "target_energy": 0.50, "likes_acoustic": True,
        "target_tempo_bpm": 76, "target_valence": 0.80,
        "target_danceability": 0.72, "target_acousticness": 0.65,
    },
    "Acoustic Flag Contradiction": {
        "favorite_genre": "rock", "favorite_mood": "intense",
        "target_energy": 0.88, "likes_acoustic": True,
        "target_tempo_bpm": 145, "target_valence": 0.50,
        "target_danceability": 0.68, "target_acousticness": 0.05,
    },
    "Custom": None,
}

ADVERSARIAL = {
    "Conflicting Energy + Sad Mood", "All-Max Extremes", "All-Min Zeros",
    "Genre Mismatch, Strong Continuous", "Acoustic Flag Contradiction",
}

# ── sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.title("🎵 VibeMatch")
st.sidebar.markdown("Content-based music recommender with RAG context.")
st.sidebar.divider()

profile_name = st.sidebar.selectbox("Taste profile", list(PROFILES.keys()))

if profile_name == "Custom":
    st.sidebar.markdown("**Build your own profile**")
    fav_genre    = st.sidebar.selectbox("Favorite genre", CATALOG_GENRES, index=CATALOG_GENRES.index("pop"))
    fav_mood     = st.sidebar.selectbox("Favorite mood",  CATALOG_MOODS,  index=CATALOG_MOODS.index("happy"))
    energy       = st.sidebar.slider("Target energy", 0.0, 1.0, 0.7)
    tempo        = st.sidebar.slider("Target tempo (BPM)", 0, 200, 120)
    valence      = st.sidebar.slider("Target valence", 0.0, 1.0, 0.6)
    danceability = st.sidebar.slider("Target danceability", 0.0, 1.0, 0.7)
    acousticness = st.sidebar.slider("Target acousticness", 0.0, 1.0, 0.2)
    likes_acoustic = st.sidebar.checkbox("Likes acoustic?", value=False)
    prefs = {
        "favorite_genre": fav_genre, "favorite_mood": fav_mood,
        "target_energy": energy, "likes_acoustic": likes_acoustic,
        "target_tempo_bpm": tempo, "target_valence": valence,
        "target_danceability": danceability, "target_acousticness": acousticness,
    }
else:
    prefs = PROFILES[profile_name]

k = st.sidebar.slider("Number of recommendations (k)", 1, 10, 5)
st.sidebar.divider()
run = st.sidebar.button("Get Recommendations", type="primary", use_container_width=True)

# ── main area ─────────────────────────────────────────────────────────────────
st.title("🎵 VibeMatch — Music Recommender")

if not run:
    st.markdown(
        "Select a taste profile in the sidebar and click **Get Recommendations**."
    )
    st.divider()

    col1, col2, col3 = st.columns(3)
    col1.metric("Songs in catalog", 18)
    col2.metric("Genres covered", 10)
    col3.metric("Scoring layers", 3)
    st.stop()

# ── run recommender ───────────────────────────────────────────────────────────
recs = recommend_songs(prefs, SONGS, k=k)
log_run(profile_name, prefs, recs)

# ── header ────────────────────────────────────────────────────────────────────
badge = "⚠️ Adversarial Profile" if profile_name in ADVERSARIAL else "✅ Standard Profile"
st.subheader(f"{profile_name}   {badge}")

top_score = recs[0][1] if recs else 0
LOW = 3.0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Genre", prefs["favorite_genre"].capitalize())
col2.metric("Mood", prefs["favorite_mood"].capitalize())
col3.metric("Target energy", f"{prefs['target_energy']:.2f}")
conf_label = "Top score"
conf_delta = "Low confidence" if top_score < LOW else "Good match"
col4.metric(conf_label, f"{top_score:.2f}", delta=conf_delta,
            delta_color="inverse" if top_score < LOW else "normal")

if top_score < LOW:
    st.warning(
        f"Top score {top_score:.2f} is below the confidence threshold ({LOW}). "
        "No strong match exists in the catalog for this profile.",
        icon="⚠️",
    )

st.divider()

# ── recommendation cards ──────────────────────────────────────────────────────
for rank, (song, score, explanation) in enumerate(recs, start=1):
    reasons = [r.strip() for r in explanation.split(";") if r.strip()]
    context = retrieve_context(song["genre"], song["mood"])

    with st.container(border=True):
        left, right = st.columns([3, 1])

        with left:
            st.markdown(f"### #{rank} — {song['title']}")
            st.markdown(
                f"**{song['artist']}** &nbsp;·&nbsp; "
                f"{song['genre'].capitalize()} &nbsp;·&nbsp; "
                f"{song['mood'].capitalize()}"
            )

        with right:
            st.metric("Score", f"{score:.2f}", label_visibility="visible")

        st.markdown("**Scoring breakdown**")
        reason_cols = st.columns(min(len(reasons), 4))
        for i, reason in enumerate(reasons):
            reason_cols[i % 4].markdown(f"- {reason}")

        if context:
            with st.expander("Genre context (from RAG knowledge base)"):
                st.markdown(context)
