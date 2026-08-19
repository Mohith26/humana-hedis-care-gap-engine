"""Explicit clinical code sets used by the measures.

Codes are real-world identifiers (ICD-10-CM, LOINC, CPT/HCPCS/CPT-II) chosen to be
faithful to how each HEDIS-style measure is defined, but the *value sets are
simplified* (a representative subset), NOT the full NCQA-certified value sets.

Code systems (FHIR canonical URLs) are declared so the FHIR loader can match on
system + code rather than bare code strings.
"""

from __future__ import annotations

# --- FHIR code system canonical URLs -------------------------------------
SYSTEM_ICD10 = "http://hl7.org/fhir/sid/icd-10-cm"
SYSTEM_LOINC = "http://loinc.org"
SYSTEM_CPT = "http://www.ama-assn.org/go/cpt"
SYSTEM_HCPCS = "urn:oid:2.16.840.1.113883.6.285"
SYSTEM_SNOMED = "http://snomed.info/sct"

# --- Diagnosis value sets (ICD-10-CM) ------------------------------------
# Essential (primary) hypertension.
HYPERTENSION_ICD10: frozenset[str] = frozenset({"I10"})

# Diabetes mellitus (type 1 + type 2), representative subset.
DIABETES_ICD10: frozenset[str] = frozenset(
    {"E10.9", "E11.9", "E11.65", "E11.21", "E11.22", "E11.40", "E10.65"}
)

# --- LOINC observation codes ---------------------------------------------
# Blood pressure panel + components.
LOINC_BP_PANEL = "85354-9"
LOINC_SYSTOLIC = "8480-6"
LOINC_DIASTOLIC = "8462-4"

# HbA1c (Hemoglobin A1c / Hemoglobin.total in Blood).
HBA1C_LOINC: frozenset[str] = frozenset({"4548-4", "4549-2", "17856-6"})

# --- Procedure value sets ------------------------------------------------
# EED — diabetic retinal / dilated eye exam (eye-exam CPT + CPT-II screening codes).
EYE_EXAM_CODES: frozenset[str] = frozenset(
    {"92002", "92004", "92012", "92014", "67028", "2022F", "2024F", "2026F", "2033F"}
)

# BCS — mammography (screening + diagnostic).
MAMMOGRAM_CODES: frozenset[str] = frozenset(
    {"77067", "77066", "77065", "77063", "77061", "77062", "77052", "77057"}
)

# BCS exclusion — bilateral mastectomy (removes member from denominator).
BILATERAL_MASTECTOMY_CPT: frozenset[str] = frozenset({"19303", "19304", "19305", "19306", "19307"})
BILATERAL_MASTECTOMY_ICD10: frozenset[str] = frozenset({"Z90.13"})

# COL — colorectal cancer screening modalities, each with its own look-back window.
COLONOSCOPY_CODES: frozenset[str] = frozenset(
    {"45378", "45380", "45384", "45385", "45386", "45388", "45390", "45391", "45392", "44388", "44389", "44392", "44394"}
)
FIT_FOBT_CODES: frozenset[str] = frozenset({"82270", "82274"})  # + LOINC below
FIT_FOBT_LOINC: frozenset[str] = frozenset({"2335-8", "27396-1", "57905-2"})
FLEX_SIGMOIDOSCOPY_CODES: frozenset[str] = frozenset({"45330", "45331", "45333", "45338", "45346", "45347"})
CT_COLONOGRAPHY_CODES: frozenset[str] = frozenset({"74263"})
FIT_DNA_CODES: frozenset[str] = frozenset({"81528"})  # Cologuard (sDNA-FIT)
