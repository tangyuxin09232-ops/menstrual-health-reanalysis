"""Generate FAKE survey-shaped records so the pipeline can be run without private data.

The records are random draws with the same column layout as the real workbook.
Nothing here represents study observations or findings.
"""

from pathlib import Path

import numpy as np
import pandas as pd

SEED, N = 2026, 436


def main() -> None:
    rng = np.random.default_rng(SEED)
    frame = pd.DataFrame({
        "年龄": rng.integers(18, 27, N), "年级": rng.integers(1, 7, N),
        "专业": rng.integers(1, 7, N), "民族": rng.choice([1, 2], N, p=[0.9, 0.1]),
        "身高": rng.integers(150, 178, N), "体重": rng.integers(42, 80, N),
    })
    frame["BMI"] = (frame["体重"] / (frame["身高"] / 100) ** 2).round(2)
    frame["初潮年龄"] = rng.integers(1, 6, N)
    frame["月经周期总体规律性"] = rng.choice([1, 2], N, p=[0.75, 0.25])
    frame["月经周期长度"] = rng.choice([1, 2, 3], N, p=[0.05, 0.81, 0.14])
    frame["月经出血期长度"] = rng.choice([1, 2, 3], N, p=[0.03, 0.91, 0.06])
    frame["月经量PBAC得分"] = np.round(rng.lognormal(4.6, 0.7, N)).clip(5, 900)
    frame["经量等级（1过少，2正常，3过多）"] = 2
    frame["class2"] = rng.choice([1, 2], N, p=[0.62, 0.38])
    for index in range(1, 69):
        frame[f"x{index}"] = rng.integers(1, 4, N)
    frame["x4"] = rng.choice([1, 2], N, p=[0.2, 0.8])
    frame["近三个月最常用月经用品品牌"] = rng.integers(1, 13, N)
    pbac = frame["月经量PBAC得分"]
    composite = ((frame["月经周期长度"] != 2) | (frame["月经出血期长度"] != 2)
                 | (pbac > 150) | (pbac < 37) | (frame["class2"] == 1))
    frame["class"] = np.where(composite, 1, 2)
    frame["Z月经量PBAC得分"] = (pbac - pbac.mean()) / pbac.std()
    # A weak artificial signal, only so the workflow has something to find.
    frame.loc[rng.random(N) < 0.15, "class2"] = 1
    destination = Path("data/synthetic_survey.xlsx")
    destination.parent.mkdir(parents=True, exist_ok=True)
    frame.to_excel(destination, index=False)
    print(f"Wrote FAKE example data to {destination}")


if __name__ == "__main__":
    main()
