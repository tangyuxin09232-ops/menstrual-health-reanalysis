"""Shared loading code and outcome definitions.

The survey workbook is private and is never part of this repository. The
workbook uses Chinese column names; they are mapped to English names here.
Outcomes are derived from the underlying questionnaire fields; the stored
`class` column is not used.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42

RENAME = {
    "年龄": "age", "年级": "grade", "专业": "major", "民族": "ethnicity",
    "身高": "height_cm", "体重": "weight_kg", "BMI": "bmi", "初潮年龄": "menarche_age",
    "class": "provided_class",
    "月经周期总体规律性": "cycle_regularity", "月经周期长度": "cycle_length_code",
    "月经出血期长度": "bleeding_length_code", "月经量PBAC得分": "pbac_score",
    "经量等级（1过少，2正常，3过多）": "flow_level",
    "class2": "dysmenorrhea_code",
    "近三个月最常用月经用品品牌": "pad_brand",
    "Z月经量PBAC得分": "pbac_z",
}

# Fields that define, or are measured on the same menstrual indices as, the outcomes.
# They are never used as predictors.
OUTCOME_FIELDS = [
    "provided_class", "cycle_regularity", "cycle_length_code", "bleeding_length_code",
    "pbac_score", "pbac_z", "flow_level", "dysmenorrhea_code",
]
# Behaviours reported *during* menstruation may be consequences rather than antecedents.
DURING_MENSTRUATION = ["x58", "x59", "x60", "x63"]

NUMERIC_PREDICTORS = ["age", "bmi", "menarche_age"]
CATEGORICAL_PREDICTORS = (
    ["grade", "major", "ethnicity", "pad_brand"]
    + [f"x{i}" for i in range(1, 69) if f"x{i}" not in DURING_MENSTRUATION]
)

OUTCOMES = {
    # Primary outcome: the course project's final four-criterion definition. Any of: cycle
    # length outside 21-35 d, bleeding length outside 3-7 d, PBAC < 37 or > 150,
    # self-reported dysmenorrhea. (Codes: 2 = normal range in the workbook.)
    "four_criteria_composite": "Four-criterion composite (primary, course definition)",
    # Secondary outcome: self-reported dysmenorrhea (code 1 = yes).
    "dysmenorrhea": "Dysmenorrhea (secondary)",
    # Sensitivity analysis: the menstrual-pattern criteria only, without dysmenorrhea.
    "cycle_or_bleeding_abnormality": "Cycle or bleeding abnormality (sensitivity)",
}


def load(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path).rename(columns=RENAME)
    needed = {"dysmenorrhea_code", "cycle_length_code",
              "bleeding_length_code", "pbac_score", "x4", "age", "bmi"}
    absent = sorted(needed - set(df.columns))
    if absent:
        raise ValueError(f"Expected fields not found: {absent}")
    return df


def add_outcomes(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    cycle_bleed = (
        (out["cycle_length_code"] != 2) | (out["bleeding_length_code"] != 2)
        | (out["pbac_score"] > 150) | (out["pbac_score"] < 37)
    )
    dysmen = out["dysmenorrhea_code"] == 1
    out["cycle_or_bleeding_abnormality"] = cycle_bleed.astype(int)
    out["dysmenorrhea"] = dysmen.astype(int)
    out["four_criteria_composite"] = (cycle_bleed | dysmen).astype(int)
    return out


def predictor_columns(df: pd.DataFrame, drop: tuple[str, ...] = ()) -> tuple[list[str], list[str]]:
    numeric = [c for c in NUMERIC_PREDICTORS if c in df.columns and c not in drop]
    categorical = [c for c in CATEGORICAL_PREDICTORS if c in df.columns and c not in drop]
    return numeric, categorical
