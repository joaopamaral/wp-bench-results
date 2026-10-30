# Repository Guidelines

This repo stores published WP-Bench run outputs and the leaderboard page built from them. Keep the data raw and the page static.

## Layout
- `results/`: raw `wp-bench run` outputs only — `results_<timestamp>.json` plus its `.jsonl`, copied from the harness `output/` folder unchanged. Never edit, rename or hand-write these files. Its git history is the leaderboard change log.
- `site/`: `build_data.py` (stdlib Python, reads `results/` and `git log`) writes `site/data/leaderboard.json`; `index.html` renders it with no build step, no backend and no API calls.
- `examples/synthetic/`: generated runs for page development. Never copy them into `results/`.
- `tests/`: `pytest -q`.

## Publishing a run
- **Before running the benchmark, check whether the model already has a run** for the suite: read `site/data/leaderboard.json` (`.runs[] | [.model, .suite, .scoring_version, .run_date, .scores.overall]`). If it does, do not re-run by default — report the existing result to the user and ask whether a fresh run is wanted (new suite or scoring version, or they explicitly ask for one).
- Copy `output/results_<timestamp>.json` and `.jsonl` into `results/` and commit them first; that commit is the run's attribution, so link the discussion in the message. Then run `python3 site/build_data.py`, commit the regenerated `site/data/leaderboard.json`, run `pytest -q`, and open a pull request against `main`.
- Never publish a run whose output could contain private data (prompts, environment, hostnames, keys). Scan the files before committing.

## Changing the page
- Keep `index.html` dependency-free and static; everything it needs must come from `site/data/leaderboard.json`. If the page needs a new field, add it in `build_data.py`, rebuild, and commit both.
- Rank only comparable runs: same suite, same scoring version, full test coverage. Anything else is shown greyed out, never ranked.
- Lint: `ruff check site tests && ruff format --check site tests`; types: `mypy site tests --ignore-missing-imports`.

## Commits & pull requests
- Conventional Commits (`feat:`, `fix:`, `chore:`, `data:` for new runs). Small, focused PRs; a run PR contains the two output files and the regenerated data file, nothing else.
