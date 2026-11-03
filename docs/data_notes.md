# Data notes

## Source and design

- Cross-sectional questionnaire survey of female university students, run as a course project in an epidemiology field-practice module. The 436 analysed responses are the valid responses after the course team's exclusions (chronic disease; extreme menstrual blood-loss values).
- The design documents planned stratified sampling by year of study. In the event the questionnaire was distributed online through group chats and personal networks, so the sample is a **convenience sample from a single university**; it is not representative of any population.
- The design documents describe anonymous, voluntary participation with no names or student numbers collected.

## Fields

- 85 columns: demographics, menstrual indices (cycle, bleeding, PBAC, flow level, regularity, dysmenorrhea), `x1`–`x68` questionnaire items, a product-brand item, and a stored `class` column. This repository derives its outcomes from the underlying fields instead of reading `class` (see `outcome_definitions.md`).
- Most `x` fields are coded categories. They are one-hot encoded for prediction. Univariable categorical tests use cross-tabulations of the original categories. In the multivariable logistic model, ordinal answers enter as a linear trend per one-step increase in the answer code (the direction of some codes is not documented in the workbook; see the dictionary).
- Multi-select questions are stored as one 0/1 column per option. Their column headers (e.g. `12(家庭)`) identify the question number; the English labels in [`variable_dictionary.csv`](variable_dictionary.csv) marked *inferred* are my reading of those headers.
- `x57` ("other special diet") has no variation and is skipped by the univariable scan.
- One respondent has no age; age is median-imputed inside each training fold for prediction, and that respondent is omitted from the multivariable model (435 complete cases).

## What is excluded from the predictors

- Every menstrual index used to define or closely tied to the outcomes: cycle length, bleeding length, PBAC (raw and z-scored), flow level, self-reported regularity, dysmenorrhea, the stored `class` column.
- `x58`–`x60` and `x63`: behaviours reported *during* menstruation, which may be consequences rather than antecedents.
- Height and weight (BMI is kept).

## What this dataset cannot support

Causal claims, clinical screening claims, or population prevalence. PBAC and the cycle and bleeding lengths are recalled by respondents. Multiple comparisons are handled by Benjamini–Hochberg correction within each outcome's 70-test family; the 16-term logistic models are interpretive, not confirmatory.
