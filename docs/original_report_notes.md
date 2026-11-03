# How this reanalysis relates to the original course report

The original report was written by the course team. It is not reproduced here and I do not have the code, random seeds or split assignments behind it, so **this repository is a reanalysis, not a replication**, and its numbers are not expected to match the report's.

## What the original did

- Descriptive statistics and group comparisons; multivariable logistic regression; decision tree, random forest, Naive Bayes and SVM classifiers.
- Two outcomes: a composite "menstrual disorder" label and dysmenorrhea.
- Mutual-information feature selection to 48 variables, and combined oversampling with noise removal (reported as SMOTE-ENN) for class balance, with a 131-respondent test set.

## What changes here

| Aspect | Original report | This reanalysis |
| --- | --- | --- |
| Composite outcome | Taken from the stored label column | Re-derived from cycle length, bleeding length, PBAC and dysmenorrhea under the course's final definition (384 / 52); cycle or bleeding only (288 / 148) as a sensitivity analysis |
| Predictors | Included behaviours reported during menstruation | Menstrual indices and `x58–x60`, `x63` excluded (see `data_notes.md`) |
| Feature selection | Documents do not state whether it preceded the train/test split | Top-30 selection inside every training fold |
| Class imbalance | Oversampling | Class weights; no resampling |
| Evaluation | Single held-out test set | 5-fold CV repeated 10 times, permutation check, ablation |
| Hyperparameters | Not documented | Fixed, listed in `src/analyze.py` |

## Differences in findings

Results differ from the original report's in several places, and the reasons are a combination of the changes in the table, not any single one.

- **Composite-outcome discrimination.** The original documents report AUCs of roughly 0.60–0.77 for the composite outcome, depending on the document. Under the definition used here the five methods score 0.46–0.58, with wide uncertainty because only 52 respondents are negative.
- **Household insecticide use.** Reported in the original as a leading factor; here no statistically significant association was detected in the three univariable analyses (univariable p = 0.97, 0.89, 0.18).
- **Maternal dysmenorrhea history.** Reported in the original as the strongest dysmenorrhea factor (OR 9.5 in a model with 65 degrees of freedom). Here the adjusted OR is 6.9 (95% CI 4.0–11.9) in a 16-term model; the direction and dominance agree, the magnitude differs with the model.
- **Dysmenorrhea discrimination.** The original reports AUCs of about 0.62–0.69; here 0.63–0.68. The ranges overlap, but the source scores vary across documents and the workflows differ, so this does not establish replication.

Reported AUCs also differ between documents of the original (for example, 0.64 and 0.77 for the same SVM), which is another reason not to compare scores one-to-one.
