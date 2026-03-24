# CalorieSense — Project Status & What To Do Next

## Current State

Your [train.ipynb](file:///d:/Projects/GitHub/caloriesense/train.ipynb) has **4 cells** that cover the very first stage only:

| Cell | What it does | Status |
|------|-------------|--------|
| 1 | Import libraries | ✅ Done |
| 2 | Load all 4 datasets | ✅ Done |
| 3 | Preview `.head(3)` of each dataset | ✅ Done |
| 4 | Missing value check (all clean) | ✅ Done |
| 5 | Descriptive statistics `.describe()` | ✅ Done |

**You are currently at the end of Step 1 (Data Loading & Initial Inspection).** Everything below still needs to be built.

---

## Datasets Summary

| # | Dataset | Rows | Key Columns | Role per Proposal |
|---|---------|------|-------------|-------------------|
| 1 | Gym Members Exercise Tracking | 973 | Age, Gender, Weight, Height, BPM, Session_Duration, **Calories_Burned**, Workout_Type, BMI | **Primary training dataset** |
| 2 | Exercise & Fitness Metrics | 3,864 | Age, Gender, Duration, Heart_Rate, BMI, Weather_Conditions, Exercise_Intensity, **Calories_Burn** | **Secondary training dataset** (adds weather & intensity context) |
| 3 | Fitness Exercises (Library) | 30 | Exercise Name, Target Muscles, Body Part, Equipment, Instructions | **Runtime lookup** for exercise recommendations (NOT for model training) |
| 4 | Mendeley Gym Recommendation | 14,589 | Age, Height, Weight, BMI, Hypertension, Diabetes, Fitness Goal, Exercises, Diet, Recommendation | **AI Coaching lookup table** (NOT for model training) |

> [!IMPORTANT]
> **Datasets 1 & 2** are for training the calorie prediction model. **Datasets 3 & 4** are lookup/reference tables used at runtime in the web app — they should NOT be used for model training.

---

## What To Do Next (Proposal Roadmap)

According to your project proposal, here is the **exact sequence** you need to follow in [train.ipynb](file:///d:/Projects/GitHub/caloriesense/train.ipynb):

### Phase 1: Data Preprocessing *(next step)*
- [ ] Merge/align Dataset 1 & Dataset 2 (harmonize column names like `Calories_Burned` ↔ `Calories Burn`, `Gender` encoding, etc.)
- [ ] Encode categorical variables (`Gender`, `Workout_Type`, `Weather_Conditions`)
- [ ] Check for duplicates & outliers
- [ ] Create a unified training DataFrame

### Phase 2: Exploratory Data Analysis (EDA)
- [ ] Correlation heatmap
- [ ] Scatter plots (Duration vs Calories, Heart Rate vs Calories, etc.)
- [ ] Feature distribution histograms
- [ ] Pairwise comparisons

### Phase 3: Feature Engineering & Selection
- [ ] Feature importance analysis (heart rate, duration, weight, body temperature)
- [ ] Create/remove features as needed
- [ ] Train/test split (e.g. 80/20)

### Phase 4: Model Training & Comparison
Train **4 models** and compare:
- [ ] Linear Regression
- [ ] Random Forest Regression
- [ ] Gradient Boosting (XGBoost)
- [ ] Artificial Neural Network (ANN)

### Phase 5: Model Evaluation
Evaluate each model using:
- [ ] MAE (Mean Absolute Error)
- [ ] RMSE (Root Mean Squared Error)
- [ ] R² Score
- [ ] Cross-validation
- [ ] Create comparison table/chart of all models

### Phase 6: Save Best Model
- [ ] Serialize the best-performing model (e.g. `joblib` or `pickle`) → save to `out/` folder
- [ ] Save the preprocessing pipeline too (scalers, encoders)

### Phase 7: Web Application *(separate from notebook)*
- [ ] Build web app with user input form
- [ ] Integrate saved model for predictions
- [ ] Add OpenWeather API for live weather data
- [ ] Query Dataset 3 for exercise recommendations
- [ ] Query Dataset 4 for AI coaching recommendations
- [ ] Add visual fitness insight charts

---

## Summary

**You've completed ~15% of the ML side** (data loading & inspection). The immediate next step is **Data Preprocessing** — merging & cleaning Datasets 1 and 2 into a unified training set.
