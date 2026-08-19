# CareGap — HEDIS-style Quality-Measure & Care-Gap Engine (Medicare Advantage Stars)

A **HEDIS-style quality-measure + care-gap engine** over **SYNTHETIC FHIR** members: it
ingests FHIR R4 bundles → parses them into a clinical model → computes **5 real
Medicare-Advantage quality measures** as denominator / numerator / rate → detects each
member's **open care gaps** with reasons → produces a **risk-prioritized outreach
worklist** → serves it all behind a **FastAPI** service. Benchmarked for
gap-classification precision/recall against a **hand-built gold cohort**, plus
population rates, throughput, and API latency.

> Built for a **Humana — Technology Internship** target (healthcare data / API;
> Medicare Advantage **Stars / HEDIS** quality). Stars ratings are Humana's most
> business-critical engineering domain: they identify members with **open care gaps**
> (overdue preventive/chronic care) and drive outreach. This project reproduces that
> pipeline end to end.

> ## ⚠️ Data & scope notes (read me)
> - **100% SYNTHETIC, seeded data** (`datagen/`). **No real PHI — ever.** Every FHIR
>   bundle, patient, and API response is tagged `SYNTHETIC`.
> - **Measure logic is HEDIS-STYLE / simplified — NOT NCQA-certified.** It uses
>   representative code sets and windows, not the full certified value sets.
> - **Gold-cohort precision/recall (1.000) is a correctness/regression result** on
>   hand-authored ground truth, **not** a real-world-accuracy or generalization claim.
> - Full methodology + every measured number: **[RESULTS.md](RESULTS.md)**; raw JSON in
>   `results/`; résumé bullets in **[BULLETS.md](BULLETS.md)**.

## Measured results (2026-08-19, synthetic seeded data)

| Metric | Value |
|---|---|
| Measures implemented | **5** — CBP, GSD (A1c), EED (eye exam), BCS, COL |
| Gold-cohort gap precision / recall / accuracy | **1.000 / 1.000 / 1.000** (26 members, 130 evals — correctness eval) |
| Cohort | **1,000** synthetic members · **2,594** FHIR resources · measurement year 2025 |
| Population rates | CBP **51.4%** · GSD **53.1%** · EED **63.3%** · BCS **72.8%** · COL **64.8%** |
| Total open care gaps | **562** across **427** of 1,000 members |
| Throughput | **345,717 members/sec** (engine compute path) |
| API latency | `/measures` p95 **2.29 ms** · `/care-gaps` p95 **0.70 ms** (in-process) |
| Tests | **192 passed**, **97%** coverage |

## Architecture

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
  outreach.py          risk-prioritized worklist (gap-count × Stars weight)
  store.py             in-memory member repository (repository pattern)
  api.py               FastAPI: /health /measures /members/{id}/care-gaps /gaps /outreach
  tabular.py           pandas view of population results
eval/
  metrics.py           precision / recall / accuracy / F1 math
  run_eval.py          engine vs gold cohort -> results/eval.json
bench/
  population.py        denom/num/rate + total gaps over the full cohort
  throughput.py        members/sec
  latency.py           /measures + /care-gaps p50/p95 (in-process TestClient)
  run_all.py           run everything -> results/*.json + summary.json
tests/                 192 tests (loader, measures + edge cases, gaps, outreach, eval, API, generator)
results/*.json         committed measured numbers (2026-08-19)
```

## Quickstart

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

python -m scripts.generate_data --n 1000 --seed 42   # SYNTHETIC cohort -> data/synthetic_fhir/
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
| `GET /outreach?limit=N` | risk-prioritized outreach worklist (gap-count × Stars weight) |

Every response uses a consistent envelope `{success, data, error, meta}` and every
`meta` carries `"synthetic": true` + `"data_classification": "SYNTHETIC"`.

```bash
curl -s localhost:8000/measures
# CBP: denominator 331, numerator 170, rate 0.5136, open_gaps 161 ...

curl -s 'localhost:8000/outreach?limit=1'
# top member ranked by weighted open-gap priority (CBP/GSD triple-weighted)
```

## The 5 measures (HEDIS-style, simplified)

| ID | Measure | Denominator | Compliant if | Window |
|---|---|---|---|---|
| **CBP** | Controlling High Blood Pressure | 18–85 w/ hypertension | most recent BP < 140/90 | measurement year |
| **GSD** | Glycemic Status (HbA1c) for Diabetes | 18–75 w/ diabetes | most recent A1c < 8.0% | measurement year |
| **EED** | Eye Exam for Diabetes | 18–75 w/ diabetes | diabetic retinal/dilated eye exam | measurement year |
| **BCS** | Breast Cancer Screening | women 50–74 (excl. mastectomy) | mammogram in window | 27-month look-back |
| **COL** | Colorectal Cancer Screening | 45–75 | colonoscopy/FIT/sigmoid/CT/FIT-DNA | 10y/1y/5y/5y/3y |

Each measure documents its own spec in `caregap/measures/<id>.py`. Age is evaluated as
of December 31 of the measurement year (HEDIS convention).

## Tech stack

Python 3.12 · FastAPI + uvicorn · pydantic · pandas · pytest + coverage ·
`fhir.resources` (schema-validation test only). Free/local, CPU-only, no external API
keys, **no PHI**.

## License / disclaimer

Synthetic-data demonstration project. Not a certified NCQA/HEDIS engine and not for
clinical or production use. Contains no real patient data.
