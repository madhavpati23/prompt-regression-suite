# prompt-regression-suite

A small, honest harness for **prompt-based** and **data-validation** testing of
AI / LLM outputs — with **baseline regression diffing** so you can catch quality
drops between model versions or prompt changes.

It runs **fully offline** against a built-in deterministic mock model (so anyone,
and CI, can run the whole thing with zero API keys), and switches to the **real
Claude API** automatically when `ANTHROPIC_API_KEY` is set.

```
================================================================
  PROMPT-REGRESSION REPORT  -  model: mock-helpbot-v2
================================================================
  Total tests : 56
  Passed      : 46
  Failed      : 10
  PASS RATE   : 82.1%
----------------------------------------------------------------
  PASS RATE BY CATEGORY:
   accuracy       10/10    100%  ##########
   consistency     5/6      83%  ########
   data_validation  5/6      83%  ########
   edge_cases      5/7      71%  #######
   hallucination   4/5      80%  ########
   reasoning       8/8     100%  ##########
   robustness      5/6      83%  ########
   safety          4/8      50%  #####
```

The mock ships ~10 deliberate defects (one+ per category) so the suite always
has something real to catch; a green CI run means none of them regressed.

## Why this exists

Testing an AI feature is not "ask it a few things and eyeball the answers." You
need to: design test cases by **risk category**, judge each output against an
explicit rule, measure a **pass rate per category** (averages hide disasters),
and — crucially — **re-run on every model/prompt change and diff the results** so
a fix in one place doesn't silently break another. That last part is regression
testing, and it's what this repo is built around.

The suite ships against a deliberately-buggy mock "AI under test" so the failures
are real and reproducible: a hallucination, a letter-counting error, a biased
response, a prompt-injection failure, and a system-prompt/secret leak. The suite's
job is to **catch** them — and it does.

## What it tests

**56 cases across 8 risk categories:**

| Category          | What it checks                                                   |
|-------------------|-----------------------------------------------------------------|
| `accuracy`        | Verifiable facts and simple computations                        |
| `reasoning`       | Multi-step logic and word problems (incl. the bat-and-ball trap)|
| `edge_cases`      | Letter-counting, false premises, undefined ops, ambiguity       |
| `hallucination`   | Fabricated books/people/APIs/citations and future events        |
| `consistency`     | Same fact asked two ways — the answers must agree               |
| `robustness`      | Junk / empty / mixed-case / multilingual input                  |
| `safety`          | Injection, bias, secret leakage, unsafe/PII/medical requests    |
| `data_validation` | Structured output has the right JSON shape & types              |

Test cases are plain YAML — no code needed to add one:

```yaml
- id: acc-percentage
  prompt: "What is 15% of 240?"
  validator: equals_number
  args: {value: 36}
```

Validators included: `contains`, `not_contains`, `regex`, `equals_number`
(matches any number in the answer, tolerant of formatting), and `json_schema`
(keys + types, for output-contract / data-validation checks).

## Quick start

```bash
pip install -e ".[dev]"        # or: pip install -r requirements.txt

# Run the suite against the offline mock and print a report:
python -m prompt_regression run

# Run and diff against the checked-in baseline (this is the regression gate):
python -m prompt_regression run --baseline baselines/mock.baseline.json

# Re-baseline after an intended change:
python -m prompt_regression update-baseline baselines/mock.baseline.json

# Run the unit tests:
pytest -q
```

### Test the real Claude API instead

```bash
export ANTHROPIC_API_KEY=sk-ant-...
python -m prompt_regression run        # now runs against claude-opus-4-8
```

The Claude adapter uses the official `anthropic` SDK with adaptive thinking
(`thinking={"type": "adaptive"}`) — the supported thinking mode for the Opus 4.x
family. Override the model with `PRS_MODEL=claude-sonnet-4-6`.

### Test any real AI endpoint (HTTP adapter)

Point the runner at a real product — an OpenAI-style chat API, an internal
service, a self-hosted model server — with **no code changes**, just environment
variables. The adapter POSTs a JSON body (the `{PROMPT}` token is replaced with
the JSON-encoded prompt) and reads the answer from a dotted response path. It
uses only the standard library.

```bash
# Generic internal endpoint that takes {"prompt": "..."} and returns {"output": "..."}:
export PRS_HTTP_URL="https://my-service.internal/ask"
python -m prompt_regression run

# OpenAI-compatible chat endpoint:
export PRS_HTTP_URL="https://api.openai.com/v1/chat/completions"
export PRS_HTTP_HEADERS='{"Authorization": "Bearer sk-..."}'
export PRS_HTTP_BODY='{"model": "gpt-4o-mini", "messages": [{"role": "user", "content": {PROMPT}}]}'
export PRS_HTTP_RESPONSE_PATH="choices.0.message.content"
python -m prompt_regression run --baseline baselines/my-product.baseline.json
```

| Env var | Purpose | Default |
|---------|---------|---------|
| `PRS_HTTP_URL` | endpoint (presence activates this adapter) | — |
| `PRS_HTTP_BODY` | JSON template; `{PROMPT}` → JSON-encoded prompt | `{"prompt": {PROMPT}}` |
| `PRS_HTTP_RESPONSE_PATH` | dotted path to the answer (`""` = raw body) | `output` |
| `PRS_HTTP_HEADERS` | JSON object of extra headers (auth, etc.) | none |
| `PRS_HTTP_METHOD` | HTTP method | `POST` |

Adapter precedence: **HTTP** (if `PRS_HTTP_URL` set) → **Claude** (if
`ANTHROPIC_API_KEY` set) → **mock**. The same test cases run against the mock in
CI and a real product in staging — unchanged.

## How regression detection works

A **baseline** records the per-case pass/fail of a known-good run. On a later run
(new model version, edited prompt, tweaked system instructions) the suite diffs
against it and reports four buckets:

- **REGRESSED** — passed in the baseline, fails now ← *the alarm*
- **FIXED** — failed before, passes now
- **ADDED** / **REMOVED** — case set changed

This separates *new* breakage from cases that were already failing.

**Exit codes** make it a CI gate:

| Code | Meaning                                            |
|------|----------------------------------------------------|
| `0`  | all good (or no regressions vs baseline)           |
| `1`  | one or more cases failed (no baseline given)       |
| `2`  | a regression was detected against the baseline     |

The included GitHub Actions workflow ([.github/workflows/ci.yml](.github/workflows/ci.yml))
runs the unit tests and then fails the build if the suite regresses against the
checked-in mock baseline — on every push and PR.

## Project layout

```
prompts/                     # test cases, one YAML file per risk category
baselines/                   # saved known-good pass/fail snapshots
src/prompt_regression/
  models.py                  # adapters: mock + Claude + generic HTTP/JSON endpoint
  validators.py              # the judging rules (contains, regex, json_schema, ...)
  runner.py                  # load cases -> ask model -> judge -> summarize
  baseline.py                # save / diff baselines  (regression core)
  report.py                  # human-readable report + diff rendering
  cli.py                     # `python -m prompt_regression`
tests/                       # pytest unit tests for the validators and diff logic
.github/workflows/ci.yml     # CI: unit tests + regression gate
```

## An honest note on what a green run means

A high pass rate is **evidence of quality on the inputs you tested** — it is not a
certificate of safety. Testing can show the presence of bugs, never prove their
absence. Every report says so, and the suite reports what it did *and didn't*
cover by category on purpose.

## Audit reports

The harness isn't just run against the mock — it's used to audit real models.
See [`reports/`](reports/) for a one-page AI Test Report applying these cases to
Claude's free tier (pass rate by category, qualitative findings, and an explicit
coverage section on what was *not* tested).

## License

MIT — see [LICENSE](LICENSE).
