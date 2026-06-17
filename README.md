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
  Total tests : 13
  Passed      : 6
  Failed      : 7
  PASS RATE   : 46.2%
----------------------------------------------------------------
  PASS RATE BY CATEGORY:
   accuracy        6/6     100%  ##########
   data_validation  0/2       0%
   edge_cases      0/2       0%
   safety          0/3       0%
```

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

| Category          | What it checks                                              |
|-------------------|-------------------------------------------------------------|
| `accuracy`        | Verifiable facts and simple computations                    |
| `edge_cases`      | Letter-counting, false premises ("who won a future event?") |
| `safety`          | Refusal under prompt injection, bias, system-prompt leakage |
| `data_validation` | Structured output has the right JSON shape & types          |

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
  models.py                  # adapters: deterministic mock + real Claude API
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

## License

MIT — see [LICENSE](LICENSE).
