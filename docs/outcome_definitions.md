# Outcome definitions

All outcomes are operational definitions built from questionnaire answers. They are **not clinical diagnoses**.

| Field in workbook | Meaning used here |
| --- | --- |
| `月经周期长度` (cycle length) | code 2 = within 21–35 days; any other code = outside that range |
| `月经出血期长度` (bleeding length) | code 2 = within 3–7 days; any other code = outside that range |
| `月经量PBAC得分` | Pictorial Blood-loss Assessment Chart score; abnormal if < 37 or > 150 (cut-offs as cited in the course notes from Hong Kong PBAC work) |
| `class2` | dysmenorrhea; code 1 = yes (269 respondents, matching the course report) |

## Outcomes analysed

1. **Four-criterion composite (primary):** cycle outside range OR bleeding length outside range OR PBAC < 37 or > 150 OR dysmenorrhea. 384 positive, 52 negative. This is the definition on the course's final presentation. With only 52 negatives, estimates are imprecise, so the two outcomes below are reported alongside it.
2. **Dysmenorrhea (secondary):** `class2 == 1`. 269 / 167.
3. **Cycle or bleeding abnormality (sensitivity):** the first three criteria only. 288 / 148.

The earlier five-criterion version of the course definition also contained self-reported cycle regularity; the final course definition dropped it, and so does this repository.

## How the outcomes are derived

All outcomes are computed directly from the four fields above (`src/common.py`, function `add_outcomes`). The label column stored in the analysis workbook (`class`) is **not used**: it is not needed, and it is excluded from the predictors together with every other field that defines or closely tracks an outcome. Because the composite is built from the same fields as the final course definition, it reproduces the 384 / 52 split shown in the course's results.
