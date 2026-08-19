# Résumé Bullets — CareGap (filled strictly from measured results)

> Measured 2026-08-19 on **SYNTHETIC seeded** FHIR data (1,000 members, seed 42),
> measurement year 2025. Every number traces to `results/*.json`. Unmeasured values are
> the literal `___`. Measure logic is **HEDIS-style / simplified, NOT NCQA-certified**.
> Honesty tags below.

## Filled bullets

- Built a **HEDIS-style Medicare-Advantage care-gap engine** (Humana Stars quality) over
  **synthetic FHIR** members computing **5 quality measures** (BP control, diabetes A1c,
  diabetic eye exam, breast- & colorectal-cancer screening) at **1.00 precision / 1.00
  recall** vs a hand-built 26-member gold cohort — **no PHI**.
  <br>_(MEASURED: 5 measures; gold-cohort gap precision=recall=accuracy=1.000 over 130 = 26×5 evaluations, TP=18/FP=0/FN=0/TN=112. **Honesty:** the gold cohort is hand-authored ground truth, so 1.000 is a **correctness/regression** result validating measure logic + edge cases — NOT a generalization or real-world-accuracy claim; measure logic is HEDIS-style/simplified, not NCQA-certified; data is SYNTHETIC.)_

- Detected **562 open care gaps** across **427 members** (of 1,000) with per-gap reasons
  and a **risk-prioritized outreach worklist** (gap-count × Stars weight, CBP/GSD
  triple-weighted), surfacing denominator/numerator/rate per measure via a FastAPI
  service (`/measures`, `/members/{id}/care-gaps`, `/gaps`, `/outreach`).
  <br>_(MEASURED: 562 total open gaps; 427/1,000 members with ≥1 gap; population rates CBP 51.4% · GSD 53.1% · EED 63.3% · BCS 72.8% · COL 64.8%. SYNTHETIC data; rates are emergent from the generator's illustrative knobs, not a real population statistic.)_

- Processed **345,717 members/sec** (engine compute path) with `/measures` p95 **2.29
  ms**, validated by **192 passing tests** covering measure logic + edge cases (age
  boundaries, out-of-window results, missing data, poor control, sex ineligibility,
  clinical exclusion), fully reproducible on seeded synthetic data.
  <br>_(MEASURED: 345,717 members/sec best of 5 (mean 343,814); /measures p95 2.288 ms, /care-gaps p95 0.704 ms; 192 tests pass, 97% coverage. **Honesty:** throughput excludes FHIR parsing + I/O (engine classification path only); latency measured **in-process via FastAPI TestClient**, excludes the network socket.)_

## Measured-value ledger

| Placeholder | Value | Status |
|---|---|---|
| quality measures | 5 (CBP, GSD, EED, BCS, COL) | MEASURED |
| gold-cohort precision / recall / accuracy | 1.000 / 1.000 / 1.000 | MEASURED (correctness eval, hand-labeled truth) |
| gold cohort size | 26 members / 130 evaluations | MEASURED |
| cohort size | 1,000 members / 2,594 FHIR resources | MEASURED |
| total open care gaps | 562 | MEASURED |
| members with ≥1 gap | 427 / 1,000 | MEASURED |
| population rates | CBP 51.4 / GSD 53.1 / EED 63.3 / BCS 72.8 / COL 64.8 (%) | MEASURED |
| poor-control diabetics (GSD extra) | 49 | MEASURED |
| throughput | 345,717 members/sec (engine path) | MEASURED |
| /measures p50 / p95 | 2.162 / 2.288 ms | MEASURED (in-process TestClient) |
| /care-gaps p50 / p95 | 0.668 / 0.704 ms | MEASURED (in-process TestClient) |
| tests / coverage | 192 passed / 97% | MEASURED |

## Honesty tags

- ✅ MEASURED on **SYNTHETIC seeded** FHIR data (1,000 members, seed 42), reproducible.
- ⚠️ Measure logic is **HEDIS-style / simplified — NOT NCQA-certified** (representative
  code sets/windows, not the full certified value sets).
- ⚠️ Gold-cohort **precision/recall = 1.000 is a correctness/regression result** on
  hand-authored ground truth — not a generalization or clinical-accuracy claim.
- ⚠️ Throughput = **engine compute path** (excludes FHIR parsing + I/O).
- ⚠️ Latency measured **in-process** (FastAPI TestClient / ASGI), excludes network socket.
- ❌ **No real PHI / member data** — forbidden and never used.
