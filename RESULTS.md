# CareGap: measured results

Measured 2026-08-19. Stack: Python 3.12, FastAPI, pydantic, pandas, pytest. All data is 100% synthetic and seeded (`datagen/generator.py`, `seed=42`); no real PHI. The measure logic is HEDIS-style and simplified, not NCQA-certified (representative code sets and windows, not the full certified value sets).

Every number below comes from an actual run on this machine, and the machine-readable values are committed under `results/*.json`.

## About the data path

I used a dependency-free seeded generator rather than Synthea's Java pipeline, for two reasons: no Java runtime was available in the environment I built this in, and a seeded generator reproduces the cohort byte-identically from a seed while giving exact control over the gold cohort's edge cases. The generator emits FHIR R4 `Bundle` JSON shaped like Synthea output (Patient / Condition / Observation / Procedure), so the same loader (`caregap/fhir_loader.py`) parses both. Generated bundles are additionally validated as schema-conformant FHIR R4B via `fhir.resources` in `tests/test_fhir_schema.py`, and every bundle and patient carries a `SYNTHETIC` data-classification tag.

Distribution knobs (prevalence, control rates) are illustrative, not calibrated to any real population, so the population rates below are emergent artifacts of those knobs. They measure the engine's arithmetic, not a real population's health.

## How to reproduce

```bash
# 0. setup
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

# 1. generate the SYNTHETIC FHIR cohort (1,000 members, seed 42) -> data/synthetic_fhir/
python -m scripts.generate_data --n 1000 --seed 42

# 2. run the full test suite (measure logic + edge cases, gaps, outreach, eval, API)
pytest -q                              # -> 192 passed
pytest --cov=caregap --cov=datagen --cov=eval --cov-report=term   # -> 97%

# 3. run every benchmark + the gold-cohort eval -> results/*.json + summary.json
python -m bench.run_all

# individual pieces:
python -m eval.run_eval                # gold-cohort precision/recall/accuracy -> results/eval.json
python -m bench.population             # population denom/num/rate per measure
python -m bench.throughput             # members/sec
python -m bench.latency                # /measures + /care-gaps p50/p95

# 4. serve the API
uvicorn caregap.api:app --port 8000
curl -s localhost:8000/health
curl -s localhost:8000/measures
curl -s localhost:8000/members/syn-00000/care-gaps
curl -s 'localhost:8000/gaps?measure=CBP'
curl -s 'localhost:8000/outreach?limit=20'
```

## Cohort scale (`results/population.json`)

| Item | Value |
|---|---|
| Members (synthetic) | 1,000 |
| FHIR resources parsed | 2,594 (Patient / Condition / Observation / Procedure) |
| Measurement year | 2025 |
| Seed | 42 (fully reproducible) |
| Data classification | SYNTHETIC (no PHI) |

## Measures implemented

| ID | Measure | Eligible population | Numerator (compliant) | Windows / thresholds |
|---|---|---|---|---|
| CBP | Controlling High Blood Pressure | 18-85 w/ hypertension (I10) | most recent BP in year < 140/90 | measurement year |
| GSD | Glycemic Status (HbA1c) for Diabetes | 18-75 w/ diabetes (E10/E11) | most recent A1c in year < 8.0% | measurement year; poor control > 9.0% |
| EED | Eye Exam for Diabetes | 18-75 w/ diabetes | diabetic retinal/dilated eye exam | measurement year |
| BCS | Breast Cancer Screening | women 50-74 (excl. bilateral mastectomy) | mammogram in look-back | 27-month window (Oct 1 two yrs prior -> Dec 31) |
| COL | Colorectal Cancer Screening | 45-75 | any modality in its window | colonoscopy 10y · sigmoidoscopy 5y · CT colonography 5y · FIT-DNA 3y · FIT 1y |

Age is evaluated as of December 31 of the measurement year (HEDIS convention).

## Gap classification vs the gold cohort (`results/eval.json`)

The gold cohort is 26 hand-authored synthetic members, each carrying a known correct status per measure (`not_eligible` / `compliant` / `gap`), covering the edge cases I wanted pinned: age boundaries (85 vs 86 for CBP; 75 vs 76 for GSD/EED/COL; 74 vs 75 for BCS; 45 vs 44 for COL), out-of-window results (BP/A1c/eye-exam/mammogram/colonoscopy dated before the window), missing data (eligible but no result), poor control (A1c > 9%), sex ineligibility (male for BCS), a clinical exclusion (bilateral mastectomy), and a deceased member. Every gold member flows through the real FHIR loader, and the engine's output is compared to the labels. Positive class = open gap.

| Measure | Eligible (denominator in gold) | True gaps | TP | FP | FN | TN | Precision | Recall | Accuracy |
|---|---|---|---|---|---|---|---|---|---|
| CBP | 5 | 3 | 3 | 0 | 0 | 23 | 1.000 | 1.000 | 1.000 |
| GSD | 6 | 4 | 4 | 0 | 0 | 22 | 1.000 | 1.000 | 1.000 |
| EED | 6 | 3 | 3 | 0 | 0 | 23 | 1.000 | 1.000 | 1.000 |
| BCS | 6 | 3 | 3 | 0 | 0 | 23 | 1.000 | 1.000 | 1.000 |
| COL | 19 | 5 | 5 | 0 | 0 | 21 | 1.000 | 1.000 | 1.000 |
| Overall | (per measure above) | 18 | 18 | 0 | 0 | 112 | 1.000 | 1.000 | 1.000 |

Accuracy is the strict 3-way (`not_eligible`/`compliant`/`gap`) exact-match over all 130 = 26 members x 5 measures evaluations. Precision/recall are for the gap class, where a wrong eligibility call (e.g. flagging a gap for a not-eligible member) is correctly counted as a false positive.

Worth being explicit about what the 1.000s mean: these labels are hand-authored ground truth, so a correct engine reproduces them exactly, and that is what the figures show. This is a correctness/regression eval of the measure logic and its edge cases, not a generalization benchmark and not a claim of real-world clinical accuracy. There is no held-out or noisy real data here (using real member data would be forbidden PHI). The value is that all 130 classifications, including every edge case, are pinned and re-verified on each run.

## Population measure rates, full 1,000-member cohort (`results/population.json`)

| Measure | Denominator | Numerator | Rate | Open gaps | Extra |
|---|---|---|---|---|---|
| CBP | 331 | 170 | 51.36% | 161 | |
| GSD | 147 | 78 | 53.06% | 69 | poor control: 49 |
| EED | 147 | 93 | 63.27% | 54 | |
| BCS | 228 | 166 | 72.81% | 62 | |
| COL | 613 | 397 | 64.76% | 216 | |

| Aggregate | Value |
|---|---|
| Total open care gaps | 562 |
| Members with >=1 open gap | 427 of 1,000 |

Rates are emergent from the generator's illustrative knobs (see the data-path note); they are the engine's real arithmetic over the synthetic cohort, not a real-world statistic.

## Throughput (`results/throughput.json`)

| Metric | Value |
|---|---|
| Members processed / sec (engine compute path) | 345,717 (best of 5; mean 343,814) |
| Member x measure classifications / sec | 1,728,583 |
| Cohort size | 1,000 · 5 measures each |

Scope note: this times the engine classification path (all 5 measures per member) over an already-loaded in-memory cohort, and excludes FHIR JSON parsing and disk I/O. The number is high because member records are small and the logic is pure dictionary/date comparisons; it is not an end-to-end system figure.

## API latency (`results/latency.json`)

| Endpoint | p50 | p95 | p99 | mean |
|---|---|---|---|---|
| `GET /measures` (aggregates all 5 measures over 1,000 members) | 2.162 ms | 2.288 ms | 2.331 ms | 2.174 ms |
| `GET /members/{id}/care-gaps` (one member) | 0.668 ms | 0.704 ms | 0.744 ms | 0.671 ms |

200 measured requests each, 20 warm-up excluded. Measured in-process via FastAPI's `TestClient` (ASGI), so the HTTP/TCP network socket is excluded; the numbers reflect the service's real per-request work (parse -> measure engine -> envelope). `/measures` recomputes the full population on every call (no caching), which is why it is slower than the single-member endpoint.

## Tests

| Metric | Value |
|---|---|
| Tests | 192 passed |
| Coverage (`caregap` + `datagen` + `eval`) | 97% |

Covers: FHIR parsing, all 5 measures' eligible/compliant/gap logic, every edge case (age boundary, out-of-window, missing data, poor control, sex, mastectomy exclusion, deceased), gap detection + weighted outreach ordering, precision/recall/accuracy math, the gold-cohort eval run, generator determinism, and every API endpoint (incl. 404/422).

## Notes and limitations

- Synthetic seeded data only; deterministic generator, never real PHI.
- HEDIS-style and simplified, not NCQA-certified: representative code sets and windows; the real measures use larger certified value sets and additional exclusions/continuous-enrollment rules not modeled here.
- Gold-cohort precision/recall = 1.000 is a correctness/regression result, not a generalization or real-world-accuracy claim (see the gold-cohort section).
- Throughput excludes FHIR parsing and I/O (engine compute path only).
- Latency is in-process (TestClient), not over a network socket.
- EED is simplified: it requires an exam in the measurement year, while the certified measure also credits a prior-year negative-retinopathy screen.
- Not built: dashboard UI, Stars projected-rating rollup, FHIR `MeasureReport` output, real claims (837/835) ingestion, ML risk models, auth/HIPAA infrastructure.
