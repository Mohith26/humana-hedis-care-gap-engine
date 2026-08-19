# CareGap

A HEDIS-style quality-measure and care-gap engine over synthetic FHIR data. Stars ratings are how Medicare Advantage plans are scored, and underneath them sit quality measures that boil down to: which members are overdue for preventive or chronic care, and who should be contacted first. I wanted to build that pipeline end to end, so CareGap ingests FHIR R4 bundles, parses them into a clinical model, computes 5 real Medicare Advantage quality measures as denominator / numerator / rate, detects each member's open care gaps with reasons, produces a risk-prioritized outreach worklist, and serves it all behind a FastAPI service.

Everything runs on 100% synthetic, seeded data generated in-repo. There is no real PHI anywhere, and every bundle, patient, and API response is tagged `SYNTHETIC`. The measure logic is HEDIS-style and simplified, not NCQA-certified: representative code sets and windows, not the full certified value sets.

## The 5 measures

| ID | Measure | Denominator | Compliant if | Window |
|---|---|---|---|---|
| CBP | Controlling High Blood Pressure | 18-85 w/ hypertension | most recent BP < 140/90 | measurement year |
| GSD | Glycemic Status (HbA1c) for Diabetes | 18-75 w/ diabetes | most recent A1c < 8.0% | measurement year |
| EED | Eye Exam for Diabetes | 18-75 w/ diabetes | diabetic retinal/dilated eye exam | measurement year |
| BCS | Breast Cancer Screening | women 50-74 (excl. mastectomy) | mammogram in window | 27-month look-back |
| COL | Colorectal Cancer Screening | 45-75 | colonoscopy/FIT/sigmoid/CT/FIT-DNA | 10y/1y/5y/5y/3y |

Each measure documents its own logic in `caregap/measures/<id>.py`. Age is evaluated as of December 31 of the measurement year, following the HEDIS convention.

## Numbers (measured 2026-08-19, synthetic seeded data)

| Metric | Value |
|---|---|
| Gold-cohort gap precision / recall / accuracy | 1.000 / 1.000 / 1.000 (26 members, 130 evals; a correctness eval, see below) |
| Cohort | 1,000 synthetic members · 2,594 FHIR resources · measurement year 2025 |
| Population rates | CBP 51.4% · GSD 53.1% · EED 63.3% · BCS 72.8% · COL 64.8% |
| Total open care gaps | 562 across 427 of 1,000 members |
| Throughput | 345,717 members/sec (engine compute path) |
| API latency | `/measures` p95 2.29 ms · `/care-gaps` p95 0.70 ms (in-process) |
| Tests | 192 passed, 97% coverage |

The perfect gold-cohort scores are a correctness/regression result on hand-authored ground truth (26 members whose correct status per measure is known by construction, covering the edge cases), not a real-world accuracy or generalization claim. Full methodology in [RESULTS.md](RESULTS.md); raw JSON in `results/`.

## How it's put together

```
data/synthetic_fhir/   SYNTHETIC FHIR R4 bundles (generated; gitignored). samples/ has 5 committed.
datagen/
  generator.py         seeded synthetic FHIR R4 cohort generator (Synthea-shaped, no PHI)
  fhir_factory.py      builders for FHIR Patient/Condition/Observation/Procedure/Bundle
  gold_cohort.py       26 hand-authored members w/ KNOWN status per measure (edge cases)
caregap/
  codes.py             explicit code sets (ICD-10 / LOINC / CPT / CPT-II)
  model.py             immutable clinical model (Member/Condition/Observation/Procedure)
  fhir_loader.py       FHIR R4 Bundle JSON -> clinical model (defensive, no external FHIR runtime)
  measures/            cbp · gsd · eed · bcs · col  (each: denom/num/rate + per-member status)
  engine.py            run all measures -> per-member statuses + population results
  gaps.py              eligible & not-compliant -> open care gap (+ reason)
  outreach.py          risk-prioritized worklist (gap-count x Stars weight)
  store.py             in-memory member repository (repository pattern)
  api.py               FastAPI: /health /measures /members/{id}/care-gaps /gaps /outreach
  tabular.py           pandas view of population results
eval/                  precision/recall/accuracy math + engine-vs-gold-cohort runner
bench/                 population rates, throughput, latency, run_all -> results/*.json
tests/                 192 tests (loader, measures + edge cases, gaps, outreach, eval, API, generator)
results/*.json         committed measured numbers (2026-08-19)
```

Stack: Python 3.12, FastAPI + uvicorn, pydantic, pandas, pytest + coverage, `fhir.resources` (used in a schema-validation test only). Free, local, CPU-only, no external API keys, no PHI.

## Running it

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

python -m scripts.generate_data --n 1000 --seed 42   # synthetic cohort -> data/synthetic_fhir/
pytest -q                                             # 192 passed
python -m bench.run_all                               # (re)generate results/*.json
uvicorn caregap.api:app --port 8000                   # serve the API
open http://localhost:8000/docs                       # OpenAPI UI
```

## API

| Endpoint | Purpose |
|---|---|
| `GET /health` | cohort size + measurement year + synthetic tag |
| `GET /measures` | denominator / numerator / rate + open gaps per measure |
| `GET /members/{id}/care-gaps` | a member's per-measure status + open gaps (with reasons) |
| `GET /gaps?measure=CBP` | population open gaps for one measure |
| `GET /outreach?limit=N` | risk-prioritized outreach worklist (gap-count x Stars weight) |

Every response uses a consistent envelope `{success, data, error, meta}` and every `meta` carries `"synthetic": true` plus `"data_classification": "SYNTHETIC"`.

```bash
curl -s localhost:8000/measures
# CBP: denominator 331, numerator 170, rate 0.5136, open_gaps 161 ...

curl -s 'localhost:8000/outreach?limit=1'
# top member ranked by weighted open-gap priority (CBP/GSD triple-weighted)
```

## Limitations

- Synthetic seeded data only; the generator's prevalence and control-rate knobs are illustrative, so the population rates are artifacts of those knobs, not statistics about any real population.
- HEDIS-style and simplified, not NCQA-certified. Real measures use larger certified value sets plus exclusions and continuous-enrollment rules not modeled here. EED in particular is simplified: it requires an exam in the measurement year, while the certified measure also credits a prior-year negative-retinopathy screen.
- The 1.000 gold-cohort precision/recall is a correctness/regression result on hand-authored labels, not a generalization claim; there is no held-out or noisy real data (real member data would be PHI).
- Throughput times the engine classification path over an already-loaded in-memory cohort, excluding FHIR JSON parsing and disk I/O.
- Latency is measured in-process (FastAPI `TestClient`), not over a network socket.
- Not built: dashboard UI, Stars projected-rating rollup, FHIR `MeasureReport` output, real claims (837/835) ingestion, ML risk models, auth/HIPAA infrastructure.

## Disclaimer

Synthetic-data demonstration project. Not a certified NCQA/HEDIS engine and not for clinical or production use. Contains no real patient data.
