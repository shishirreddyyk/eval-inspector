# eval-inspector
![run comparison](docs/diff.png)

An eval set, a run of model outputs, and the screen that tells you what broke.

Python/FastAPI graders + a React/TypeScript UI. Point it at a directory of run
files, get per-case pass/fail with the reason, and diff two runs against each
other when you swap models.

## Why it exists

A pass rate is a bad summary of an eval. It hides three things, and this tool
was built around all three:

- **Which case broke, and why.** Every verdict traces to a named check and a
  named string: `must_not_include "lifetime" - appeared in output`. No judge
  model, no "seems worse", no rerun to find out.
- **Cases the run never answered.** Skip your three hardest cases and the pass
  rate goes *up*. Unanswered cases are reported separately and kept out of the
  numerator and denominator, not quietly dropped. In the diff they get their own
  `dropped` status rather than counting as still-passing.
- **Why a failure happened, in a human's words.** Tag a failure
  (`hallucination`, `missing-citation`, ...) and the tags aggregate. That is the
  part that tells you what to fix next; the number only tells you that something is wrong.

## Sample data

Ships with an 8-case policy eval and two real-shaped runs. The newer model is
faster on every case and worse on three:

```
gemini-2.0-flash   8/8 passing
gemini-2.5-flash   4/7 passing   3 regressed, 1 dropped
  regressed  warranty-length     invented "extendable to lifetime coverage"
  regressed  no-invented-policy  invented a price-match policy that does not exist
  regressed  cite-source         dropped the [section N] citation
  dropped    empty-context       never answered
```

That is the shape of a model swap that looks like a win on latency and is a loss
on reliability.

## Run it

```bash
# api
cd api && pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# web (proxies /api to :8000)
cd web && npm install && npm run dev
```

## Data format

`data/eval_set.jsonl` - one case per line:

```json
{"case_id": "warranty-length", "question": "How long is the standard warranty?",
 "must_include": ["12 months"], "must_not_include": ["lifetime"], "tags": ["policy"]}
```

Checks: `must_include`, `must_not_include`, `regex`, `exact`. A case with no
checks raises instead of passing - a silently-passing empty case is worse than a
missing one.

`data/runs/<run_id>.jsonl` - optional header line, then one output per case:

```json
{"model": "gemini-2.5-flash", "created_at": "2026-07-16T09:31:00Z"}
{"case_id": "warranty-length", "output": "Products carry a 12 months warranty...", "latency_ms": 620}
```

Drop a new file in `data/runs/` and it shows up. Runs are files, not database
rows, so they diff in git and travel with the repo.

## API

```
GET  /api/runs                 list runs with pass rates
GET  /api/runs/{run_id}        per-case verdicts, failing checks, unanswered cases
GET  /api/diff?a=&b=           case-by-case comparison, regressions sorted first
POST /api/tags                 {run_id, case_id, tag, note}
GET  /api/tags                 tag counts across all runs
```

## Tests

```bash
cd api && python -m pytest -q      # 24 tests
cd web && npm run build            # tsc -b + vite build
```

The suite covers each check kind, the "any failing check fails the case" rule,
the empty-case guard, JSONL errors that name the offending line, duplicate
case_ids, the regression/dropped classification against the sample runs, and the
API contract including tag replacement.

## Known limits

- Deterministic checks only. Substring and regex checks miss paraphrase - a
  correct answer worded differently fails. An LLM judge is the obvious next step
  and needs a labeled set to calibrate against first, or you are evaluating the
  judge.
- Runs are graded on request rather than cached; fine at hundreds of cases, not
  at hundreds of thousands.
- Tags live in SQLite next to the API. Single user, no auth.
- No run *execution* - this grades and inspects outputs you already have.
