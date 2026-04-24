# VibeMatch — Music Recommender Simulation

A content-based music recommender built from scratch in Python. The system scores a catalog of 18 songs against a user taste profile, retrieves genre context from a local RAG (Retrieval-Augmented Generation) engine, logs every run with confidence flagging, and returns the top-K matches with a full scoring explanation.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [System Architecture](#2-system-architecture)
3. [How the Scoring Works](#3-how-the-scoring-works)
4. [RAG Engine](#4-rag-engine)
5. [Logging](#5-logging)
6. [Data](#6-data)
7. [File Structure](#7-file-structure)
8. [Setup and Installation](#8-setup-and-installation)
9. [Running the App](#9-running-the-app)
10. [Running the Tests](#10-running-the-tests)
11. [Sample Output](#11-sample-output)
12. [Profile Screenshots](#12-profile-screenshots)
13. [Known Biases and Limitations](#13-known-biases-and-limitations)
14. [Reflection](#14-reflection)

---

## 1. Project Overview

VibeMatch simulates the content-based filtering layer that sits at the core of real music recommenders like Spotify Discover Weekly. A user describes their taste as a set of numeric preferences — energy level, tempo, valence, danceability, acousticness, genre, and mood — and the system finds the songs that match best.

Unlike production recommenders, VibeMatch has no play history, no user-to-user comparisons, and no learning over time. Every recommendation is fully explainable: the system shows exactly which features contributed to a song's score and by how much.

**What was built:**

| Component | File | Purpose |
|---|---|---|
| Scoring engine | `src/recommender.py` | Loads songs, scores every song against the user profile, returns top-K |
| RAG engine | `src/rag_engine.py` | Embeds genre knowledge files, retrieves relevant context per recommendation |
| Logger | `src/logger.py` | Logs every run to console + file; warns when top score is below 3.0 |
| Runner | `src/main.py` | Wires everything together across 8 taste profiles |
| Tests | `tests/` | 6 tests covering the recommender, RAG retrieval, and logger |

---

## 2. System Architecture

![System Architecture](assets/architecture.png)

**Data flow in plain language:**

1. `src/main.py` loads the song catalog from `data/songs.csv` and defines the user taste profiles.
2. For each profile, `recommend_songs()` scores all 18 songs and returns the top 5.
3. `log_run()` records the run — profile name, genre, mood, energy, top song, top score — to both the console and `logs/recommender.log`. If the top score is below 3.0, a `WARNING` is emitted.
4. For each of the top-5 songs, `retrieve_context()` queries a local ChromaDB vector store and returns the closest matching genre description from `data/knowledge_base/`.
5. `print_recommendations()` displays the rank, title, artist, score, scoring reasons, and genre context for every result.

---

## 3. How the Scoring Works

Every song is scored against the user's preferences in three layers. All scores are additive; the songs with the highest totals are recommended.

### Layer 1 — Categorical bonuses

| Match | Points |
|---|---|
| `song.genre == user.favorite_genre` | +0.5 |
| `song.mood == user.favorite_mood` | +1.0 |

Genre is a small bonus. Mood is slightly larger. Both are binary — partial matches score zero.

### Layer 2 — Continuous similarity

For each numeric feature: `similarity = 1.0 − |song_value − target_value|`

| Feature | Weight | Notes |
|---|---|---|
| `energy` | × 3.0 | Highest weight — immediately felt by the listener |
| `tempo_bpm` | × 0.8 | Normalized to 0–1 by dividing by 200 before differencing |
| `valence` | × 0.6 | Emotional brightness; important but subjective |
| `acousticness` | × 0.6 | Strongly felt (electric vs. acoustic) |
| `danceability` | × 0.5 | Secondary alignment signal |

### Layer 3 — Acoustic preference bonus

```
if user.likes_acoustic is False and song.acousticness < 0.3:  +0.5
if user.likes_acoustic is True  and song.acousticness > 0.7:  +0.5
```

### Full formula

```
score = (genre_match × 0.5)
      + (mood_match  × 1.0)
      + (1 − |energy       − target_energy|)        × 3.0
      + (1 − |tempo_bpm/200 − target_tempo/200|)    × 0.8
      + (1 − |valence      − target_valence|)       × 0.6
      + (1 − |danceability − target_danceability|)  × 0.5
      + (1 − |acousticness − target_acousticness|)  × 0.6
      + acoustic_bonus (0 or 0.5)
```

**Maximum possible score: ~7.5 points**

---

## 4. RAG Engine

`src/rag_engine.py` adds a knowledge retrieval layer on top of the scoring results. After the top songs are chosen, the system looks up a plain-language description of each song's genre and appends it to the output.

### Knowledge base

`data/knowledge_base/` contains 10 `.txt` files — one per genre — each describing the genre's sonic characteristics, energy range, typical mood, and listener profile. Genres covered: classical, country, electronic, jazz, lofi, metal, pop, reggae, rnb, rock.

### How retrieval works

1. **Ingestion (first run only):** All 10 genre files are read, embedded using `all-MiniLM-L6-v2` (via ChromaDB's ONNX runtime), and stored in a persistent ChromaDB collection at `data/chroma_store/`. Subsequent runs load from disk — no re-embedding.
2. **Query:** `retrieve_context(song_genre, song_mood)` builds a natural-language query — e.g. `"electronic music energetic mood"` — and retrieves the most similar chunk by cosine similarity.
3. **Output:** The retrieved description is printed below the scoring reasons for each recommended song.

### Why ONNX instead of PyTorch sentence-transformers

Loading `sentence_transformers` directly caused a segmentation fault in the Anaconda Python environment due to a Keras 3 / PyTorch native library conflict. ChromaDB ships the same `all-MiniLM-L6-v2` model as a self-contained ONNX binary, which produces identical embeddings without the PyTorch dependency.

---

## 5. Logging

`src/logger.py` uses Python's standard `logging` module with two handlers: a `FileHandler` writing to `logs/recommender.log` and a `StreamHandler` writing to the console. Both share the same formatted output:

```
2026-04-24 00:05:44  INFO      RUN | profile='High-Energy Pop' | genre=pop | mood=happy | energy=0.90 | results=5
2026-04-24 00:05:44  INFO      TOP | profile='High-Energy Pop' | #1='Sunrise City' | artist='Neon Echo' | score=7.10
2026-04-24 00:05:47  WARNING   LOW CONFIDENCE | profile='All-Min Zeros' | top_score=2.99 < 3.0
```

**Low-confidence threshold:** If the top score is below `3.0`, a `WARNING` is logged. This threshold was chosen because a score below 3.0 means the system failed to earn a meaningful mood or genre bonus and produced poor continuous similarity across most features — a genuine signal that no good match exists for this profile in the current catalog.

The `logs/` directory is created automatically on first run.

---

## 6. Data

### Song catalog — `data/songs.csv`

18 songs, each with 10 attributes:

| Column | Type | Range |
|---|---|---|
| `id` | int | 1–18 |
| `title` | string | — |
| `artist` | string | — |
| `genre` | string | 15 genres |
| `mood` | string | happy, chill, intense, relaxed, focused, moody, melancholic, romantic, euphoric |
| `energy` | float | 0.0–1.0 |
| `tempo_bpm` | float | 60–180 |
| `valence` | float | 0.0–1.0 |
| `danceability` | float | 0.0–1.0 |
| `acousticness` | float | 0.0–1.0 |

**Known gaps:** No song has `mood=sad`. 8 of 18 songs have energy above 0.7 — high-energy tracks are overrepresented.

### Knowledge base — `data/knowledge_base/`

10 hand-written genre descriptions. Each file is one paragraph and is stored as a single embedding — no chunking needed at this scale.

---

## 7. File Structure

```
applied-ai-system-final/
├── assets/                          # All images
│   ├── architecture.png
│   ├── screenshot_terminal.png
│   └── profile_*.png                # 8 profile output screenshots
├── data/
│   ├── songs.csv                    # 18-song catalog
│   ├── knowledge_base/              # 10 genre .txt files for RAG
│   └── chroma_store/                # Auto-generated ChromaDB vector store
├── logs/
│   └── recommender.log              # Auto-generated on first run
├── src/
│   ├── recommender.py               # Song dataclass, scoring, load_songs, recommend_songs
│   ├── rag_engine.py                # ChromaDB ingestion and retrieve_context()
│   ├── logger.py                    # Dual-output logger with low-confidence warning
│   └── main.py                      # Runner: profiles, recommendations, output
├── tests/
│   ├── test_recommender.py          # Recommender unit tests
│   └── test_rag.py                  # RAG and logger tests
├── model_card.md
├── reflection.md
└── requirements.txt
```

---

## 8. Setup and Installation

**Requirements:** Python 3.10+

```bash
# 1. Clone the repo and enter the project directory
git clone <repo-url>
cd applied-ai-system-final

# 2. Create and activate a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
.venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt
```

**Dependencies:**

| Package | Version | Used for |
|---|---|---|
| `chromadb` | 1.5.8 | Vector store + ONNX embeddings |
| `sentence-transformers` | 2.7.0 | Model name reference (`all-MiniLM-L6-v2`) |
| `pandas` | 2.2.2 | CSV reading |
| `streamlit` | 1.37.1 | Future UI layer |
| `pytest` | 7.4.4 | Test runner |

> **Note on first run:** ChromaDB downloads the `all-MiniLM-L6-v2` ONNX model (~79 MB) on first use and caches it at `~/.cache/chroma/`. Subsequent runs are instant.

---

## 9. Running the App

```bash
python -m src.main
```

This runs all 8 taste profiles — 3 standard and 5 adversarial — and prints ranked recommendations with scoring breakdowns and RAG-retrieved genre context for each result. Logs are written to `logs/recommender.log`.

---

## 10. Running the Tests

```bash
pytest
```

**Test coverage:**

| Test file | Tests | What is covered |
|---|---|---|
| `tests/test_recommender.py` | 2 | `Recommender.recommend()` returns sorted results; `explain_recommendation()` returns a non-empty string |
| `tests/test_rag.py` | 4 | ChromaDB collection loads without error; `retrieve_context()` returns a non-empty string; low-confidence warning fires when top score < 3.0; logger creates a log file on disk |

---

## 11. Sample Output

```
============================================================
  🎵  TOP RECOMMENDATIONS — High-Energy Pop
============================================================

  #1  Sunrise City
       by Neon Echo  |  Pop  |  Happy
       Score: 7.10
       ────────────────────────────────────────
         • genre match (+0.5)
         • mood match (+1.0)
         • energy similarity (+2.76)
         • tempo similarity (+0.76)
         • valence similarity (+0.59)
         • danceability similarity (+0.45)
         • acousticness similarity (+0.54)
         • acoustic bonus: non-acoustic preference match (+0.5)

       Genre context:
         Pop music is defined by its polished, radio-friendly sound built around
         catchy hooks, melodic choruses, and repetitive song structures...
```

---

## 12. Profile Screenshots

### Standard Taste Profiles

**High-Energy Pop** — upbeat pop fan, high danceability, bright valence, fast tempo

![High-Energy Pop](assets/profile_highenergy_pop.png)

---

**Chill Lofi** — study/focus listener, warm acoustics, slow tempo, acoustic preference

![Chill Lofi](assets/profile_chill_lofi.png)

---

**Deep Intense Rock** — electric rock fan, high energy, fast tempo, low acousticness

![Deep Intense Rock](assets/profile_deep_intense_rock.png)

---

### Adversarial / Edge-Case Profiles

**Conflicting Energy + Sad Mood** — `energy: 0.9` paired with `mood: sad` (no songs in catalog have `mood=sad`); reveals that energy similarity outweighs a 0-point mood miss

![Conflicting Energy + Sad Mood](assets/profile_conflicting_energy_plus_sad_mood.png)

---

**All-Max Extremes** — every feature at its ceiling (`energy: 1.0`, `tempo: 200 BPM`); confirms the system degrades gracefully with no crashes, returning the closest real song

![All-Max Extremes](assets/profile_allmax_extremes.png)

---

**All-Min Zeros** — every feature at zero; confirms no negative scores are produced; low-energy acoustic tracks rise to the top

![All-Min Zeros](assets/profile_allmin_zeros.png)

---

**Genre Mismatch, Strong Continuous** — `favorite_genre: classical` (1 song in catalog), `mood: romantic` (absent); shows that strong continuous feature matches can overcome missing categorical bonuses

![Genre Mismatch, Strong Continuous](assets/profile_genre_mismatch_strong_continuous.png)

---

**Acoustic Flag Contradiction** — `likes_acoustic: True` but `target_acousticness: 0.05`; Layer 2 and Layer 3 pull in opposite directions, exposing the silent scoring contradiction

![Acoustic Flag Contradiction](assets/profile_acoustic_flag_contradiction.png)

---

## 13. Known Biases and Limitations

**Energy dominance.** Energy carries a ×3.0 weight — higher than any other feature. In practice the recommender behaves more like an "energy sorter" than a genuine taste-matcher. A pop listener asking for happy, danceable songs will consistently see workout-coded intense tracks ranked above mood-matched pop songs if their energy values are closer to the target.

**Mood matching is all-or-nothing.** "Relaxed" and "chill" feel similar to a human but score 0 against each other because the match is exact string equality. Any mood mismatch forfeits the full 1.0 point.

**Small catalog amplifies genre gaps.** 18 songs means genres with 1–2 entries (metal, country, reggae) quickly exhaust their options. A user with niche taste runs out of genre matches immediately.

**No diversity enforcement.** The top 5 results frequently cluster in the same genre or energy range. There is no mechanism to force variety.

**RAG coverage is limited to 10 genres.** Songs tagged with genres outside the knowledge base (e.g., "indie pop") fall back to the nearest genre by cosine similarity — silently, with no indication to the user that the description is approximate.

**Knowledge base descriptions encode listener stereotypes.** Each genre file was written by hand and reflects generalizations (e.g., electronic music is for "club-goers and festival attendees"). These are statistical averages, not universal truths.

---

## 14. Reflection

**What this project revealed about recommender systems**

The biggest surprise was how much energy dominates everything. I expected genre to matter most — if someone says they like jazz, they want jazz. But because energy carries a ×3.0 multiplier, a song that closely matches the user's target energy will outscore a genre-matched song almost every time. The system was doing exactly what I designed it to do. The bias was in the weights, not the code.

The adversarial profiles made this concrete. *Gym Hero* — an intense workout track — kept appearing near the top for a "happy pop" listener because its energy of 0.93 sits very close to the target of 0.90. No amount of genre or mood mismatch could overcome that continuous similarity.

**How this mirrors real-world AI**

Real recommenders like Spotify's have the same structural problem at larger scale. When an algorithm surfaces a song that feels slightly off, it is usually because one feature dimension is overweighted, not because the model is broken. The difference is that Spotify can observe whether you skip the song and adjust — VibeMatch cannot. Static weights are a design choice that trades adaptability for explainability.

**AI collaboration**

Claude Code was used as a pair programmer for the RAG engine, logger, and test suite. The most concrete time saving was a native library diagnosis: `sentence_transformers` caused a segmentation fault in the Anaconda environment due to a Keras 3 / PyTorch conflict. Claude identified the root cause from the stack trace and suggested using ChromaDB's ONNX backend — same model, no PyTorch dependency. What could have been hours of environment debugging took minutes.

AI was less useful for design decisions: what the confidence threshold should be, how to weight the features, what the knowledge base entries should actually say. Those required understanding the project's purpose, not just its code.

The practical rule that emerged: use AI to close the gap between a clear idea and working code. Keep the idea-forming and the result verification on the human side.

**Further reading**

- [Model Card](model_card.md) — full bias analysis, evaluation findings, and RAG design rationale
- [Reflection](reflection.md) — profile-by-profile comparison of how the scoring system behaved across all 8 taste profiles
