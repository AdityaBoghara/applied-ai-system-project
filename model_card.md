# Model Card: Music Recommender Simulation

## 1. Model Name

**VibeMatch 1.0**

---

## 2. Goal / Task

VibeMatch tries to predict which songs a user will enjoy based on their taste preferences. It ranks every song in a small catalog and returns the top 5 best matches. The goal is to surface songs that feel right for the user's mood, energy level, and genre taste — like a friend picking songs for your playlist.

---

## 3. Intended Use

**Designed for:** Exploring how rule-based music recommenders work. It is a classroom simulation, not a production product.

**Assumptions it makes:** The user can describe their taste as a single genre, a single mood, a target energy level, and whether they like acoustic music. It assumes those preferences are stable and consistent.

**Not designed for:** Real-world deployment, personalization based on listening history, or users with complex or mixed tastes. It should not be used as a standalone recommendation engine for an actual music app.

---

## 4. How the Model Works

The system scores each song against the user's preferences and picks the top 5.

Scoring happens in three layers:

**Layer 1 — Category bonuses.** If the song's genre matches the user's favorite genre, it gets a small bonus. If the mood matches, it gets a slightly bigger bonus.

**Layer 2 — How close the numbers are.** The model compares numbers like energy level, tempo, happiness (valence), danceability, and acousticness. The closer a song's number is to the user's target, the higher the score. Energy carries the most weight — it matters three times as much as danceability.

**Layer 3 — Acoustic preference.** If the user likes acoustic music and the song is very acoustic, it gets a bonus. Same for non-acoustic songs matching non-acoustic listeners.

All the scores are added together. The songs with the highest totals are recommended.

---

## 5. Data

The catalog has **18 songs** from 15 different genres including pop, lofi, rock, jazz, classical, hip-hop, metal, reggae, folk, and electronic.

Each song has 10 attributes: a title, artist, genre, mood label, and 5 numeric values (energy, tempo in BPM, valence, danceability, and acousticness).

**Limits:**
- Only 18 songs. Users with niche tastes quickly run out of good matches.
- Moods represented: happy, chill, intense, relaxed, focused, moody, melancholic, romantic, euphoric. There is no "sad" song — so a user who prefers sad music never gets a mood bonus.
- High-energy songs are overrepresented. 8 of 18 songs have energy above 0.7. Only 4 are below 0.4.
- No song metadata beyond what is listed (no lyrics, release year, or artist popularity).

---

## 6. Strengths

The system works best when the user's preferences are clear and consistent.

- **Opposite profiles get opposite results.** A high-energy pop listener and a chill lofi listener get completely different top-5 lists with no overlap. That is the expected behavior.
- **Extreme profiles don't crash.** When tested with impossible targets (energy = 1.0, tempo = 200 BPM), the system still returned the closest real songs instead of failing.
- **Low-energy listeners get quiet songs.** Classical and lofi profiles consistently surface *Velvet Strings*, *Library Rain*, and *Midnight Coding* — songs that genuinely fit those vibes.

---

## 7. Limitations and Bias

**Energy Dominance and the High-Energy Filter Bubble**

The scoring system disproportionately rewards songs that match the user's target energy level. Energy carries the highest weight (×3.0) of any single feature. In practice this means the recommender works more like an "energy sorter" than a genuine taste-matcher. A pop fan who prefers high energy will consistently see rock and metal tracks ranked above pop songs simply because their energy values are closer to the target.

This is made worse by the dataset: 8 of 18 songs have energy above 0.7, while only 4 fall below 0.4. Low-energy listeners face a much smaller pool of viable candidates and quickly exhaust their options.

The weight-shift experiment confirmed this. Doubling the energy multiplier caused the "Genre Mismatch, Strong Continuous" adversarial profile to surface *Island Pulse* (a reggae track) ahead of songs in the user's stated genre purely on energy proximity. A single continuous feature silently overrode a categorical preference.

A fairer design would normalize all feature weights so that no single dimension accounts for more than ~25% of a song's maximum possible score.

---

## 8. Evaluation

**Profiles Tested**

Three standard taste profiles were tested — High-Energy Pop, Chill Lofi, and Deep Intense Rock — along with five adversarial edge-case profiles designed to probe failure modes: Conflicting Energy + Sad Mood, All-Max Extremes, All-Min Zeros, Genre Mismatch with Strong Continuous Match, and Acoustic Flag Contradiction.

**What We Looked For**

For standard profiles, the goal was to check whether the top-5 results actually felt like songs that person would enjoy — right genre, right vibe, nothing jarring. For adversarial profiles, the goal was to deliberately break the system and observe where it failed gracefully versus where it produced clearly wrong results.

**What Surprised Us**

*Gym Hero* kept appearing near the top for profiles that had nothing to do with gym or intense workouts. It ranked #2 for High-Energy Pop even though the user wanted "happy pop," not intensity — because its energy (0.93) is extremely close to the target (0.90). The system could not tell the difference between a happy danceable track and a workout-coded intense one.

A second surprise: the "Genre Mismatch, Strong Continuous" adversarial profile set `favorite_genre = "classical"`, but *Island Pulse* (a reggae track) climbed into the top 3 because every one of its continuous numbers happened to land close to the target values. A perfect numerical match outweighed the genre label.

Finally, the weight-shift experiment showed that halving the genre weight had almost no visible impact on well-represented profiles like Chill Lofi, suggesting the original weights were already energy-heavy enough that genre mattered very little.

---

## 9. Ideas for Improvement

1. **Balance the feature weights.** Energy should not dominate everything else. Capping energy's contribution and raising genre's weight would make the recommender actually respect what genre the user asked for.

2. **Expand the dataset.** 18 songs is too small. Adding more songs — especially in underrepresented moods like "sad," "romantic," and "euphoric" — would help users with niche tastes get genuinely good matches instead of running out of options.

3. **Add diversity to the top results.** Right now the top 5 songs often cluster in the same genre or energy range. A diversity penalty that forces at least one different genre per recommendation would make the output feel less like a filter bubble.

---

## 10. Personal Reflection

Building VibeMatch showed me that recommender systems are really just ranking machines — and the ranking is only as good as the weights you choose. I expected genre to matter most, but energy ended up controlling almost everything because of how it was weighted. That was a surprise.

The adversarial profiles were the most interesting part. I learned that "breaking" a system on purpose is one of the best ways to understand how it actually works. Seeing *Gym Hero* appear on playlists it had no business being on made the energy bias concrete in a way that reading the code alone never would have.

This changed how I think about music apps like Spotify. When an algorithm surfaces a song that feels slightly off, it is probably not random — some feature is being overweighted, and the system is doing exactly what it was designed to do. The bias is in the design, not a glitch.

---

## 11. RAG Design

**What was added**

VibeMatch 1.0 now includes a Retrieval-Augmented Generation (RAG) layer. After the scoring engine picks the top-K songs, the system looks up a short plain-language description of each song's genre and appends it to the printed explanation. The goal is to give the user context about *why* a genre fits their request, not just a list of numeric reasons.

**How it works**

Ten `.txt` files in `data/knowledge_base/` — one per genre — each contain a paragraph describing that genre's sonic character, typical energy range, mood, and listener profile. On first run, `src/rag_engine.py` reads all ten files, converts them to vector embeddings using the `all-MiniLM-L6-v2` model (run via ChromaDB's ONNX runtime, so no PyTorch required), and stores them in a local ChromaDB collection at `data/chroma_store/`. On every subsequent run, the collection is loaded from disk — ingestion only happens once.

At query time, `retrieve_context(song_genre, song_mood)` builds a short natural-language query — for example, `"electronic music energetic mood"` — embeds it, and returns the knowledge base chunk with the highest cosine similarity to that query. That chunk is then printed under each recommended song.

**Design decisions and trade-offs**

*One document per genre, no chunking.* Each knowledge base file is a single paragraph. Chunking it into smaller pieces would only return fragments of the same text and add complexity with no real benefit at this scale.

*Cosine similarity over Euclidean distance.* Text meaning lives in the direction of an embedding vector, not its magnitude. Cosine similarity captures "these two phrases are about the same topic" better than raw distance, which can be thrown off by sentence length.

*Query construction is genre-first.* The query string leads with the genre name because the knowledge base is indexed by genre. Mood is appended to help the model pull a description that matches the emotional context, but genre is the primary retrieval signal.

*ChromaDB with ONNX instead of PyTorch sentence-transformers.* During development, loading `sentence_transformers` directly caused a native library segfault in the Anaconda environment (a known Keras 3 / PyTorch conflict). ChromaDB ships the same `all-MiniLM-L6-v2` model as an ONNX binary, which runs cleanly without the full PyTorch stack. The embeddings produced are identical — only the inference runtime differs.

---

## 12. Biases in the RAG Layer

**Knowledge base coverage is limited to 10 genres**

The knowledge base only covers the genres that appear most often in the 18-song catalog. Songs tagged with genres that have no matching file — like `"indie pop"` — are handled by cosine similarity falling back to the nearest genre description. That fallback is usually reasonable (indie pop retrieves the pop description) but it is silent: the user sees a pop description with no indication that the genre was approximate.

**Descriptions encode listener stereotypes**

Each knowledge base entry was written by hand and reflects generalizations about who listens to a genre. The electronic music entry, for example, mentions "club-goers and festival attendees" as the typical audience. This is a statistical average, not a universal truth — plenty of electronic music listeners are neither. Any downstream text generation or summarization that reads these descriptions would inherit those stereotypes.

**Query construction assumes genre names are stable and shared**

`retrieve_context` builds its query from the genre string stored in the song catalog. If a song is tagged `"rnb"` but the knowledge base file is named `rnb.txt`, the retrieval works. If a future song is tagged `"R&B"` or `"neo-soul"`, the similarity match degrades. There is no normalization layer between the catalog's genre labels and the knowledge base's file names.

**The embedding model was not trained on music-specific text**

`all-MiniLM-L6-v2` is a general-purpose sentence embedding model trained on broad English text. It understands words like "syncopated," "valence," and "danceability" in their general dictionary sense — not the precise music-production meanings those terms carry. A model fine-tuned on music descriptions, reviews, or lyrics would likely produce more accurate retrievals for edge cases where genre vocabulary is technical or genre-specific.

---

## 13. AI Collaboration

**How Claude was used**

Claude Code (Anthropic's AI coding assistant) was used as a pair programmer throughout the second phase of this project, covering the RAG engine, the logger, and the test suite.

The workflow was conversational: I described what each file should do in plain language — its inputs, outputs, and constraints — and Claude generated a working draft. I then read the code, ran it, and either accepted it or redirected. Claude did not have access to my environment's state between turns, so diagnosing problems required me to paste error output and explain context.

**Where it saved the most time**

The most concrete example was an environment failure: loading `sentence_transformers` directly caused a segmentation fault due to a Keras 3 / PyTorch conflict in the Anaconda Python installation. That kind of native library crash can take hours to trace manually. Claude identified the root cause from the error trace, explained why ChromaDB's ONNX backend produces identical embeddings without triggering the conflict, and suggested the fix. The total time to resolution was a few minutes instead of a few hours.

Writing `tests/test_rag.py` was also faster with AI assistance. Claude suggested using pytest's `caplog` fixture to capture log records in memory for the low-confidence warning test — an approach I would have arrived at eventually, but not immediately.

**Where human judgment was still required**

Claude consistently produced code that was syntactically correct and ran without errors. It was less reliable on *design* questions: how much weight to give each test case, whether the logger should use `WARNING` or `ERROR` for low-confidence results, what the threshold should actually be. Those decisions required understanding the project's purpose, not just its code — and that stayed with me.

The RAG knowledge base entries were also written entirely by hand. Claude could generate genre descriptions, but the entries needed to reflect the actual catalog's moods and energy ranges, not generic facts about a genre. Delegating that to AI would have produced descriptions that sounded right but did not match the data.

**What this changed about how I think about AI tools**

AI pair programming is fastest when the task has a clear specification and a testable output. "Write a function that loads `.txt` files and stores them in ChromaDB" has both — Claude can produce it, and I can verify it in under a minute. "Decide how the scoring system should weight genre versus energy" has neither — it requires judgment that the tool cannot supply.

The practical lesson: use AI to close the gap between a clear idea and working code. Keep the idea-forming and the verification on the human side.
