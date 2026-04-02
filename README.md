# 🎵 Music Recommender Simulation

## Project Summary

In this project you will build and explain a small music recommender system.

Your goal is to:

- Represent songs and a user "taste profile" as data
- Design a scoring rule that turns that data into recommendations
- Evaluate what your system gets right and wrong
- Reflect on how this mirrors real world AI recommenders

This system loads a catalog of 18 songs from `data/songs.csv`, scores every song against a user taste profile, and returns the top-k highest-scoring songs with an explanation for each recommendation.

---

## How The System Works

This is a purely content-based recommender. There is no play history, no user-to-user comparison, and no learning over time. Every song in the catalog is scored independently against the user's stated preferences, then the list is sorted and the top results are returned.

**Data flow:**

```mermaid
flowchart TD
    A([🎧 User Preferences\ngenre · mood · energy\ntempo · valence · acousticness]) --> B

    B[load_songs\ndata/songs.csv] --> C[Song Catalog\n18 songs as list of dicts]

    C --> D{For each song\nin catalog}
    A --> D

    D --> E[score_song\nsong · user_prefs]

    E --> F1[+2.0 Genre match?]
    E --> F2[+1.0 Mood match?]
    E --> F3[+1.5 × Energy similarity]
    E --> F4[+0.8 × Tempo similarity]
    E --> F5[+0.6 × Valence similarity]
    E --> F6[+0.5 Acousticness bonus]

    F1 & F2 & F3 & F4 & F5 & F6 --> G[Total Score\n0.0 – 7.5 pts]

    G --> H[scored_songs list\nsong · score · explanation]

    H --> I{More songs?}
    I -- Yes --> D
    I -- No, all 18 scored --> J

    J[Sort by score\ndescending]
    J --> K[Slice top K\ndefault k=5]
    K --> L([Output\nTitle · Score · Because: ...])
```

---

### Algorithm Recipe (Finalized)

Scoring happens in three layers:

**Layer 1 — Categorical matches (binary: 1 if match, 0 if not)**

| Rule | Points | Rationale |
|------|--------|-----------|
| `song.genre == user.favorite_genre` | **+2.0** | Genre is the strongest identity signal — a rock fan rarely wants classical regardless of other features |
| `song.mood == user.favorite_mood` | **+1.0** | Mood matters but is secondary; a chill song in the wrong genre still fits mood |

**Layer 2 — Continuous similarity (proximity formula applied per feature)**

For each numeric feature: `similarity = 1.0 - abs(song_value - target_value)`

| Feature | Max Weight | Notes |
|---------|------------|-------|
| `energy` | **× 1.5** | Most immediately felt — a workout user notices a 0.3-energy lofi track instantly |
| `tempo_bpm` (normalized ÷ 200) | **× 0.8** | Normalize raw BPM to 0–1 before differencing; listeners tolerate ±20 BPM easily |
| `valence` | **× 0.6** | Emotional positivity/negativity — important but subjective |
| `danceability` | **× 0.5** | Nice-to-have alignment |
| `acousticness` | **× 0.6** | Strongly felt (electric vs. acoustic) but partly captured by genre already |

**Layer 3 — Acoustic preference bonus (conditional)**

```
if user.likes_acoustic == False and song.acousticness < 0.3:  +0.5
if user.likes_acoustic == True  and song.acousticness > 0.7:  +0.5
```

**Maximum possible score: ~7.5 points**

Full formula:

```
score = (genre_match × 2.0)
      + (mood_match  × 1.0)
      + (1 - |energy      - target_energy|)      × 1.5
      + (1 - |tempo_bpm/200 - target_tempo/200|) × 0.8
      + (1 - |valence     - target_valence|)     × 0.6
      + (1 - |danceability - target_danceability|) × 0.5
      + (1 - |acousticness - target_acousticness|) × 0.6
      + acoustic_bonus (0 or 0.5)
```

### Ranking Rule

```python
recommendations = sorted(scored_songs, key=lambda x: x[1], reverse=True)[:k]
```

Scoring and ranking are kept separate so diversity rules (e.g., cap 1 song per artist) can be added to the ranking step without touching the scoring logic.

---

### Known Biases and Limitations

- **Genre over-prioritization:** With a 2.0 flat bonus for a genre match, a mediocre rock song will outscore an excellent folk song even if the folk song perfectly matches every audio feature. A user with niche genre preferences may get a narrow, repetitive list.
- **Mood is all-or-nothing:** "Relaxed" and "chill" feel similar to a human but score 0 against each other because matching is exact string equality. Any mood mismatch loses the full 1.0 point.
- **Small catalog amplifies genre gaps:** With only 18 songs, genres with 1–2 representatives (reggae, metal, country) can only ever surface those songs for matching users, offering no variety.
- **No novelty or diversity:** The algorithm always returns the closest matches. A user who loves rock will always see the same top rock songs — there is no mechanism to surface a surprising but fitting pick from another genre.
- **Static user profile:** Preferences are fixed at run time. Real listeners shift between moods throughout the day; this system has no way to reflect that.

---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python -m src.main
```

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.

---

## Experiments You Tried

Use this section to document the experiments you ran. For example:

- What happened when you changed the weight on genre from 2.0 to 0.5
- What happened when you added tempo or valence to the score
- How did your system behave for different types of users

---

## Limitations and Risks

Summarize some limitations of your recommender.

Examples:

- It only works on a tiny catalog
- It does not understand lyrics or language
- It might over favor one genre or mood

You will go deeper on this in your model card.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Write 1 to 2 paragraphs here about what you learned:

- about how recommenders turn data into predictions
- about where bias or unfairness could show up in systems like this


---

## 7. `model_card_template.md`

Combines reflection and model card framing from the Module 3 guidance. :contentReference[oaicite:2]{index=2}  

```markdown
# 🎧 Model Card - Music Recommender Simulation

## 1. Model Name

Give your recommender a name, for example:

> VibeFinder 1.0

---

## 2. Intended Use

- What is this system trying to do
- Who is it for

Example:

> This model suggests 3 to 5 songs from a small catalog based on a user's preferred genre, mood, and energy level. It is for classroom exploration only, not for real users.

---

## 3. How It Works (Short Explanation)

Describe your scoring logic in plain language.

- What features of each song does it consider
- What information about the user does it use
- How does it turn those into a number

Try to avoid code in this section, treat it like an explanation to a non programmer.

---

## 4. Data

Describe your dataset.

- How many songs are in `data/songs.csv`
- Did you add or remove any songs
- What kinds of genres or moods are represented
- Whose taste does this data mostly reflect

---

## 5. Strengths

Where does your recommender work well

You can think about:
- Situations where the top results "felt right"
- Particular user profiles it served well
- Simplicity or transparency benefits

---

## 6. Limitations and Bias

Where does your recommender struggle

Some prompts:
- Does it ignore some genres or moods
- Does it treat all users as if they have the same taste shape
- Is it biased toward high energy or one genre by default
- How could this be unfair if used in a real product

---

## 7. Evaluation

How did you check your system

Examples:
- You tried multiple user profiles and wrote down whether the results matched your expectations
- You compared your simulation to what a real app like Spotify or YouTube tends to recommend
- You wrote tests for your scoring logic

You do not need a numeric metric, but if you used one, explain what it measures.

---

## 8. Future Work

If you had more time, how would you improve this recommender

Examples:

- Add support for multiple users and "group vibe" recommendations
- Balance diversity of songs instead of always picking the closest match
- Use more features, like tempo ranges or lyric themes

---

## 9. Personal Reflection

A few sentences about what you learned:

- What surprised you about how your system behaved
- How did building this change how you think about real music recommenders
- Where do you think human judgment still matters, even if the model seems "smart"

