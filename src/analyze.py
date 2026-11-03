"""Reanalysis of the survey with corrected outcome definitions.

Steps
  1. descriptive summary
  2. univariable scan of every predictor (Benjamini-Hochberg across all tests)
  3. multivariable logistic regression on a small, ecologically organised set
  4. five classifiers under repeated stratified cross-validation, with all
     preprocessing and feature selection fitted inside the training folds

Only aggregate tables are written. No individual record leaves the workbook.
"""

from __future__ import annotations

import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import MonteCarloMethod, chi2_contingency, fisher_exact, mannwhitneyu
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import SelectKBest, VarianceThreshold, f_classif
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, confusion_matrix, roc_auc_score
from sklearn.model_selection import RepeatedStratifiedKFold, StratifiedKFold
from sklearn.naive_bayes import GaussianNB
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from statsmodels.stats.multitest import multipletests

from common import OUTCOMES, SEED, add_outcomes, load, predictor_columns

N_FOLDS, N_REPEATS, K_FEATURES = 5, 10, 30
N_PERMUTATIONS = 200

# Multivariable model: one or two variables per ecological domain, chosen by the
# analyst for interpretability (not a registered plan). Ordinal answers enter as
# a linear trend per one-step increase in the workbook's answer code.
LOGISTIC_TERMS = [
    ("age", "Age, per year", "numeric"),
    ("bmi", "BMI, per kg/m2", "numeric"),
    ("menarche_age", "Age at menarche, per code step", "numeric"),
    ("x4", "Household insecticide used in dormitory (yes vs no)", "yes1"),
    ("x5", "Frequent second-hand smoke (yes vs no)", "yes1"),
    ("x6", "Systematic menstrual-health education (yes vs no)", "yes1"),
    ("x21", "Perceived adequacy of school/societal support, per code step", "numeric"),
    ("x25", "Perceived stress level, per code step", "numeric"),
    ("x34", "Negative mood in past month (vs positive)", "yes1"),
    ("x45", "Sugary drinks per week, per code step", "numeric"),
    ("x47", "Coffee/strong tea/energy drinks per week, per code step", "numeric"),
    ("x61", "Sedentary frequency, per code step", "numeric"),
    ("x62", "Exercise habit, per code step", "numeric"),
    ("x65", "Alcohol use, per code step", "numeric"),
    ("x67", "Mother's dysmenorrhea history (yes vs no)", "yes1"),
    ("x68", "Family history of menstrual disease (yes vs no)", "yes1"),
]


# ---------------------------------------------------------------- descriptives
def describe(df: pd.DataFrame, out: Path) -> None:
    rows = [{"measure": "respondents", "value": len(df)}]
    for key, label in OUTCOMES.items():
        rows.append({"measure": f"{key}: positive", "value": int(df[key].sum())})
        rows.append({"measure": f"{key}: negative", "value": int((1 - df[key]).sum())})
        rows.append({"measure": f"{key}: percent positive", "value": round(100 * df[key].mean(), 1)})
    for col in ("age", "bmi", "menarche_age"):
        values = pd.to_numeric(df[col], errors="coerce")
        rows += [
            {"measure": f"{col}: mean", "value": round(values.mean(), 2)},
            {"measure": f"{col}: sd", "value": round(values.std(), 2)},
            {"measure": f"{col}: missing", "value": int(values.isna().sum())},
        ]
    pd.DataFrame(rows).to_csv(out / "descriptive_summary.csv", index=False)


# -------------------------------------------------------- univariable scan
def association_test(values: pd.Series, outcome: pd.Series, rng_seed: int) -> dict:
    table = pd.crosstab(values, outcome)
    if table.shape[0] < 2 or table.shape[1] < 2:
        return {}
    _, p_chi, _, expected = chi2_contingency(table)
    min_expected = float(expected.min())
    if min_expected >= 5:
        test, p = "Pearson chi-square", p_chi
    elif table.shape == (2, 2):
        test, p = "Fisher exact", fisher_exact(table.to_numpy())[1]
    else:
        test = "Monte Carlo chi-square (10000 resamples)"
        p = chi2_contingency(
            table, correction=False,
            method=MonteCarloMethod(n_resamples=10000, rng=np.random.default_rng(rng_seed)),
        )[1]
    return {"n_levels": int(table.shape[0]), "test": test, "p_value": float(p),
            "min_expected_cell": round(min_expected, 2)}


def univariable_scan(df: pd.DataFrame, outcome: str, out: Path) -> None:
    numeric, categorical = predictor_columns(df)
    rows = []
    y = df[outcome]
    for col in numeric:
        v = pd.to_numeric(df[col], errors="coerce")
        keep = v.notna()
        p = mannwhitneyu(v[keep][y[keep] == 1], v[keep][y[keep] == 0]).pvalue
        rows.append({"variable": col, "n_levels": np.nan, "test": "Mann-Whitney U",
                     "p_value": float(p), "min_expected_cell": np.nan})
    for i, col in enumerate(categorical):
        res = association_test(df[col], y, SEED + i)
        if res:
            rows.append({"variable": col, **res})
    scan = pd.DataFrame(rows)
    scan["p_bh_fdr"] = multipletests(scan["p_value"], method="fdr_bh")[1]
    scan = scan.sort_values("p_value")
    scan.insert(0, "n_tests_in_family", len(scan))
    scan.to_csv(out / f"univariable_scan_{outcome}.csv", index=False)


# ---------------------------------------------------- multivariable logistic
def logistic_model(df: pd.DataFrame, outcome: str, out: Path) -> None:
    X = pd.DataFrame(index=df.index)
    labels = {}
    for col, label, kind in LOGISTIC_TERMS:
        v = pd.to_numeric(df[col], errors="coerce")
        X[col] = (v == 1).astype(float) if kind == "yes1" else v
        labels[col] = label
    data = pd.concat([X, df[outcome]], axis=1).dropna()
    y = data.pop(outcome)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        fit = sm.GLM(y, sm.add_constant(data), family=sm.families.Binomial()).fit()
    ci = fit.conf_int()
    result = pd.DataFrame({
        "term": fit.params.index,
        "description": [labels.get(t, "Intercept") for t in fit.params.index],
        "odds_ratio": np.exp(fit.params.to_numpy()),
        "ci_low": np.exp(ci[0].to_numpy()),
        "ci_high": np.exp(ci[1].to_numpy()),
        "p_value": fit.pvalues.to_numpy(),
    })
    result["n_complete_cases"] = len(data)
    result["events"] = int(y.sum())
    result["parameters"] = data.shape[1] + 1
    result["numerical_warning"] = bool(caught) or bool((result["odds_ratio"] > 100).any()
                                                       or (result["odds_ratio"] < 0.01).any())
    result.to_csv(out / f"logistic_{outcome}.csv", index=False)


# ------------------------------------------------------------ prediction
def build_pipeline(estimator, numeric: list[str], categorical: list[str]) -> Pipeline:
    preprocess = ColumnTransformer([
        ("num", Pipeline([("impute", SimpleImputer(strategy="median")),
                          ("scale", StandardScaler())]), numeric),
        ("cat", Pipeline([("impute", SimpleImputer(strategy="most_frequent")),
                          ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))]),
         categorical),
    ])
    return Pipeline([
        ("preprocess", preprocess),
        ("constant", VarianceThreshold()),
        ("select", SelectKBest(score_func=f_classif, k=K_FEATURES)),
        ("model", estimator),
    ])


def estimators() -> dict:
    return {
        "Logistic regression": LogisticRegression(max_iter=2000, class_weight="balanced"),
        "Decision tree": DecisionTreeClassifier(max_depth=4, min_samples_leaf=10,
                                                class_weight="balanced", random_state=SEED),
        "Random forest": RandomForestClassifier(n_estimators=200, min_samples_leaf=3,
                                                class_weight="balanced", random_state=SEED, n_jobs=4),
        "Naive Bayes": GaussianNB(),
        "SVM (RBF)": SVC(kernel="rbf", class_weight="balanced", random_state=SEED),
    }


def score_of(pipe: Pipeline, x: pd.DataFrame) -> np.ndarray:
    return pipe.predict_proba(x)[:, 1] if hasattr(pipe, "predict_proba") else pipe.decision_function(x)


def cross_validate_models(df: pd.DataFrame, outcome: str, drop: tuple[str, ...] = (),
                          models: dict | None = None) -> pd.DataFrame:
    numeric, categorical = predictor_columns(df, drop)
    x, y = df[numeric + categorical], df[outcome]
    splitter = RepeatedStratifiedKFold(n_splits=N_FOLDS, n_repeats=N_REPEATS, random_state=SEED)
    rows = []
    for name, estimator in (models or estimators()).items():
        folds = []
        for train, test in splitter.split(x, y):
            pipe = build_pipeline(estimator, numeric, categorical).fit(x.iloc[train], y.iloc[train])
            score = score_of(pipe, x.iloc[test])
            pred = pipe.predict(x.iloc[test])
            tn, fp, fn, tp = confusion_matrix(y.iloc[test], pred, labels=[0, 1]).ravel()
            folds.append({
                "auc": roc_auc_score(y.iloc[test], score),
                "balanced_accuracy": balanced_accuracy_score(y.iloc[test], pred),
                "sensitivity": tp / (tp + fn), "specificity": tn / (tn + fp),
            })
        f = pd.DataFrame(folds)
        per_repeat = f["auc"].to_numpy().reshape(N_REPEATS, N_FOLDS).mean(axis=1)
        rows.append({
            "outcome": outcome, "model": name, "n": len(df), "n_positive": int(y.sum()),
            "n_predictors_before_selection": len(numeric) + len(categorical),
            "cv_auc_mean": f["auc"].mean(), "cv_auc_sd_across_folds": f["auc"].std(ddof=1),
            "cv_auc_sd_across_repeats": per_repeat.std(ddof=1),
            "cv_balanced_accuracy_mean": f["balanced_accuracy"].mean(),
            "cv_sensitivity_mean": f["sensitivity"].mean(),
            "cv_specificity_mean": f["specificity"].mean(),
            "n_folds_total": len(f),
        })
    return pd.DataFrame(rows)


def permutation_check(df: pd.DataFrame, outcome: str) -> dict:
    """AUC of the logistic pipeline when outcome labels are shuffled (null reference)."""
    numeric, categorical = predictor_columns(df)
    x, y = df[numeric + categorical], df[outcome].to_numpy()
    cv = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=SEED)
    est = LogisticRegression(max_iter=2000, class_weight="balanced")

    def oof_auc(labels: np.ndarray) -> float:
        aucs = []
        for train, test in cv.split(x, labels):
            pipe = build_pipeline(est, numeric, categorical).fit(x.iloc[train], labels[train])
            aucs.append(roc_auc_score(labels[test], score_of(pipe, x.iloc[test])))
        return float(np.mean(aucs))

    observed = oof_auc(y)
    rng = np.random.default_rng(SEED)
    null = np.array([oof_auc(rng.permutation(y)) for _ in range(N_PERMUTATIONS)])
    return {"outcome": outcome, "observed_5fold_auc": observed,
            "null_mean_auc": float(null.mean()),
            "null_95th_percentile": float(np.quantile(null, 0.95)),
            "permutation_p": float((1 + (null >= observed).sum()) / (1 + len(null))),
            "n_permutations": N_PERMUTATIONS}


def family_history_ablation(df: pd.DataFrame) -> pd.DataFrame:
    """How much of the dysmenorrhea signal remains without family-history questions?"""
    frame = cross_validate_models(df, "dysmenorrhea", drop=("x67", "x68"))
    frame["dropped_predictors"] = "x67, x68"
    return frame


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True, help="Private survey workbook")
    parser.add_argument("--out", type=Path, default=Path("results"))
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    df = add_outcomes(load(args.data))
    describe(df, args.out)
    for outcome in OUTCOMES:
        univariable_scan(df, outcome, args.out)
        logistic_model(df, outcome, args.out)
        print("association done:", outcome, flush=True)

    frames = []
    for outcome in OUTCOMES:
        frames.append(cross_validate_models(df, outcome))
        print("prediction done:", outcome, flush=True)
    pd.concat(frames, ignore_index=True).to_csv(args.out / "model_comparison.csv", index=False)

    pd.DataFrame([permutation_check(df, o) for o in
                  ("four_criteria_composite", "dysmenorrhea", "cycle_or_bleeding_abnormality")]
                 ).to_csv(args.out / "permutation_check.csv", index=False)
    family_history_ablation(df).to_csv(args.out / "dysmenorrhea_without_family_history.csv", index=False)
    print(f"Aggregate outputs written to {args.out.resolve()}")


if __name__ == "__main__":
    main()
