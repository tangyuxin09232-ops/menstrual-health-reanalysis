"""Draw the README figure from the aggregate tables in results/."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"
BLUE, ORANGE, AQUA, GRAY = "#2a78d6", "#eb6834", "#1baf7a", "#8a8984"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                     "axes.edgecolor": GRID, "axes.labelcolor": MUTED,
                     "xtick.color": MUTED, "ytick.color": MUTED, "text.color": INK})


def cv_auc(results: Path, figures: Path) -> None:
    m = pd.read_csv(results / "model_comparison.csv")
    ablation = results / "dysmenorrhea_without_family_history.csv"
    series = [
        ("four_criteria_composite", "Four-criterion composite (primary, course definition)", BLUE, "o", True),
        ("dysmenorrhea", "Dysmenorrhea (secondary)", ORANGE, "s", True),
        ("cycle_or_bleeding_abnormality", "Cycle or bleeding abnormality (sensitivity)", AQUA, "D", True),
    ]
    models = list(dict.fromkeys(m["model"]))
    fig, ax = plt.subplots(figsize=(8.4, 4.6))
    offsets = [-0.27, -0.09, 0.09, 0.27]
    for off, (key, label, colour, marker, filled) in zip(offsets, series):
        sub = m[m["outcome"] == key].set_index("model").loc[models]
        ys = [i + off for i in range(len(models))]
        ax.errorbar(sub["cv_auc_mean"], ys, xerr=sub["cv_auc_sd_across_folds"], fmt=marker,
                    color=colour, ms=7, mfc=colour, mec="white", mew=1, elinewidth=1.4,
                    capsize=0, label=label)
    if ablation.exists():
        a = pd.read_csv(ablation).set_index("model").loc[models]
        ys = [i + offsets[3] for i in range(len(models))]
        ax.errorbar(a["cv_auc_mean"], ys, xerr=a["cv_auc_sd_across_folds"], fmt="s", color=ORANGE,
                    ms=7, mfc="white", mec=ORANGE, mew=1.5, elinewidth=1.0, capsize=0, alpha=0.9,
                    label="Dysmenorrhea without family-history questions")
    ax.axvline(0.5, color=GRAY, lw=1, ls=(0, (4, 3)))
    ax.text(0.503, len(models) - 0.42, "chance (0.5)", color=MUTED, fontsize=9)
    ax.set_yticks(range(len(models)))
    ax.set_yticklabels(models)
    ax.set_ylim(len(models) - 0.35, -0.55)
    ax.set_xlim(0.35, 0.85)
    ax.set_xlabel("Cross-validated ROC-AUC (mean, bars = SD across 50 folds)")
    ax.grid(axis="x", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.tick_params(length=0)
    ax.legend(loc="lower center", bbox_to_anchor=(0.45, -0.46), ncol=2, frameon=False, fontsize=9)
    ax.set_title("Cross-validated discrimination across outcomes and predictor sets",
                 loc="left", fontsize=11, color=INK)
    fig.tight_layout()
    fig.savefig(figures / "fig2_cv_auc.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=Path("results"))
    parser.add_argument("--figures", type=Path, default=Path("figures"))
    args = parser.parse_args()
    args.figures.mkdir(parents=True, exist_ok=True)
    cv_auc(args.results, args.figures)
    print(f"Figures written to {args.figures.resolve()}")


if __name__ == "__main__":
    main()
