# Project Tasks

## Must Do

- [ ] Implement `load_songs` in `src/recommender.py` so it reads `data/songs.csv` and returns song records.
- [ ] Implement the song scoring logic in `src/recommender.py` so each song gets a meaningful recommendation score.
- [ ] Implement `recommend_songs` in `src/recommender.py` so it ranks songs, returns the top `k`, and includes explanations.
- [ ] Implement `Recommender.recommend` in `src/recommender.py` so the object-oriented API matches the tests.
- [ ] Implement `Recommender.explain_recommendation` in `src/recommender.py` so it returns a non-empty explanation string.
- [ ] Make sure the functional API used by `src/main.py` and the class-based API used by `tests/test_recommender.py` stay consistent.
- [ ] Run the test suite and fix any failures in `tests/test_recommender.py`.

## Should Do

- [ ] Verify the printed output in `src/main.py` looks clear and readable.
- [ ] Add or improve tests for CSV loading and scoring behavior.
- [ ] Check that the recommendation logic handles edge cases like `k` larger than the number of songs.

## Documentation

- [ ] Replace the placeholder text in `README.md` with a real summary of how the recommender works.
- [ ] Fill out `model_card.md` with the model name, intended use, data description, strengths, limitations, evaluation, future work, and reflection.

## Optional

- [ ] If you want a GUI, add a Streamlit app that lets a user pick preferences and see recommendations.
- [ ] Add more songs to `data/songs.csv` if you want richer recommendation results.