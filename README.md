# wp-bench-results

Published [WP-Bench](https://github.com/WordPress/wp-bench) run outputs and the
leaderboard built from them.

**Leaderboard:** https://wpbench-leaderboard.space.fast/

## Layout

| Path | What |
| --- | --- |
| `results/` | Raw `wp-bench run` outputs, copied from the harness's `output/` folder unchanged: `results_<timestamp>.json` (the run payload) and the matching `results_<timestamp>.jsonl` (streamed per-test records). Nothing else lives here. |
| `site/` | The static leaderboard page. `build_data.py` turns `results/` plus this repo's git history into `site/data/leaderboard.json`; `index.html` renders it. No backend, no API calls at view time. |
| `examples/synthetic/` | Randomly generated runs for developing the page. Never shown on the leaderboard. |
| `tests/` | Shape checks for `results/` and a staleness check for the page data. |

A payload is either a single-model run (`metadata` with `model`, `scores`, `usage`
plus per-test `results`) or a multi-model run (`metadata` plus `models`). The
leaderboard ranks each model's latest **full** run per suite and scoring version;
partial runs (`--limit`, `--categories`), older runs and other suites stay visible
but greyed out. Who published a run, and when, is the commit that added its file.

## Publishing a run

1. Run the benchmark: `wp-bench run --config wp-bench.yaml` (see the
   [wp-bench README](https://github.com/WordPress/wp-bench#readme)). The harness
   writes `output/results_<timestamp>.json` and `.jsonl`.
2. Check the model is not already listed for that suite — on the leaderboard, or:

   ```sh
   curl -s https://raw.githubusercontent.com/joaopamaral/wp-bench-results/main/site/data/leaderboard.json \
     | jq -r '.runs[] | [.model, .suite, .scoring_version, .run_date, .scores.overall] | @tsv'
   ```

3. Fork this repo, copy both files into `results/`, and commit them. The commit is
   the run's attribution, so say in the message where the run was discussed.
4. Rebuild the page data and commit it too:

   ```sh
   python3 site/build_data.py
   ```

5. Run `pytest -q` and open a pull request. CI checks the file shapes and that the
   data file is current.

Everything under `results/` is public. Run outputs contain the generated code and
grader output for every test; make sure your harness config did not put anything
private in prompts or environment before publishing.

## Developing the page

```sh
python3 site/build_data.py --results-dir examples/synthetic --output site/data/leaderboard.json
python3 -m http.server --directory site 8000   # open http://localhost:8000
git checkout site/data/leaderboard.json         # restore the real data before committing
```
