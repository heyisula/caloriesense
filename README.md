<div align="center">

# 🔥 Calorie Sense

### AI-Powered Calorie Prediction & Adaptive Fitness Coaching

*Smart Calories. Smarter Fitness.*

<br/>

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![TensorFlow](https://img.shields.io/badge/TensorFlow-2.x-FF6F00?style=for-the-badge&logo=tensorflow&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.x-000000?style=for-the-badge&logo=flask&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini_AI-Flash-8E75B2?style=for-the-badge&logo=google&logoColor=white)
![OpenWeather](https://img.shields.io/badge/OpenWeather-Live_API-EB6E4B?style=for-the-badge&logo=openweathermap&logoColor=white)

<br/>

![ANN Test R²](https://img.shields.io/badge/ANN_Test_R²-0.9757-brightgreen?style=flat-square)
![ANN Test MAE](https://img.shields.io/badge/ANN_Test_MAE-20.83_kcal-blue?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)
![Status](https://img.shields.io/badge/Status-Active-success?style=flat-square)

</div>

---

## Overview

**Calorie Sense** is a full-stack AI fitness platform built with Flask and TensorFlow. It does two things unusually well:

- 🌦️ **Context-aware calorie prediction** — an ANN predicts kcal burned from your exercise inputs *plus* live weather data fetched automatically from OpenWeatherMap. Cold and hot environments genuinely change how many calories you burn, and the model accounts for that.

- 🤖 **Personalised AI coaching** — a Gemini-powered fitness coach reads your health profile (BMI, hypertension, diabetes), matches you against a peer-reviewed recommendation dataset, and delivers structured workout plans and dietary guidance tailored specifically to you.

---

## Screenshots

| Home | Calorie Prediction | Prediction Result |
|:---:|:---:|:---:|
| ![Home page](docs/Images/Front%20Page.png) | ![Calorie prediction input](docs/Images/CaloriePrediction.png) | ![Calories burned result](docs/Images/CaloriesBurned.png) |

| AI Coach — Profile Setup | AI Coach — Session Start | AI Coach — Workout Plan |
|:---:|:---:|:---:|
| ![AI assistant profile input](docs/Images/AssistantInput.png) | ![AI assistant interface](docs/Images/AssistantInterface.png) | ![AI assistant response](docs/Images/AssistantResponse.png) |

---

## Table of Contents

- [System Architecture](#system-architecture)
- [Model Performance](#model-performance)
- [Datasets](#datasets)
  - [What We Used and Why](#what-we-used-and-why)
  - [Why We Dropped the Primary Dataset](#why-we-dropped-the-primary-dataset)
  - [The Target Variable Problem — and How We Fixed It](#the-target-variable-problem--and-how-we-fixed-it)
  - [Why Weather Belongs in the Model](#why-weather-belongs-in-the-model)
- [AI Fitness Coach](#ai-fitness-coach)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [References](#references)

---

## System Architecture

```
User Browser
    │
    ├── index.html       ← Landing page, system overview
    ├── calorie.html     ← Calorie prediction module
    └── AI.html          ← Gemini fitness coach
         │
         ▼
    Flask (app.py)
         │
         ├── /api/weather          ← ip-api.com → OpenWeatherMap → {city, temp, condition}
         ├── /api/predict_calorie  ← StandardScaler → ANN (.keras) → kcal
         ├── /api/start            ← Profile input → BMI → gym_lookup.json match
         └── /api/chat             ← Gemini API (gemini-flash) with grounded system prompt
              │
              ├── out/models/ann.keras          (production prediction model)
              ├── out/models/scaler.pkl         (fitted StandardScaler)
              ├── data/JSON/gym_lookup.json     (Mendeley recommendation lookup)
              └── data/JSON/exercises.json      (ExerciseDB exercise library)
```

---

## Model Performance

All models were trained on the same 80/20 stratified split of the cleaned and fixed exercise dataset. The ANN was selected for production due to the best balance of test accuracy and train/test gap (generalisation).

### Comparison Across All Models

| Model | Train R² | Test R² | Δ R² (Gap) | Train MAE | Test MAE | Train RMSE | Test RMSE | Diagnosis |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **ANN** ✅ | **0.9767** | **0.9757** | **0.0011** | 19.99 | **20.83** | 25.97 | **26.86** | ✅ Good fit |
| XGBoost (tuned) | 0.9872 | 0.9742 | 0.0130 | 14.26 | 21.42 | 19.25 | 27.62 | ✅ Good fit |
| XGBoost | 0.9820 | 0.9728 | 0.0092 | 17.69 | 22.58 | 22.86 | 28.38 | ✅ Good fit |
| RF (tuned) | 0.9909 | 0.9697 | 0.0212 | 12.40 | 22.59 | 16.26 | 29.99 | ✅ Good fit |
| Random Forest | 0.9884 | 0.9660 | 0.0224 | 14.05 | 24.89 | 18.35 | 31.74 | ✅ Good fit |
| Ridge (Poly) | 0.9444 | 0.9428 | 0.0016 | 31.39 | 32.15 | 40.16 | 41.16 | ✅ Good fit |

> **Why ANN over XGBoost (tuned) despite a marginally higher test MAE?**  
> The XGBoost tuned model has a Δ R² gap of 0.013 vs. the ANN's 0.0011 — more than 10× larger. A smaller train/test gap means the ANN generalises more consistently to unseen data, which matters more in a live inference setting than a 0.6 kcal difference in MAE.

### Feature Importance (ANN Input Features)

Features were selected by combining Random Forest importance scores with permutation importance, then keeping the top 7 by combined score.

| Feature | RF Importance | Permutation Importance | Combined Score |
|---|:---:|:---:|:---:|
| Exercise Duration | 1.000 | 1.000 | **1.000** |
| Heart Rate | 0.655 | 0.593 | **0.624** |
| Gender | 0.223 | 0.343 | **0.283** |
| Max HR Percentage | 0.129 | 0.084 | **0.107** |
| Workload (Intensity × Duration) | 0.084 | 0.084 | **0.084** |
| Weather — Rainy | 0.001 | 0.001 | **0.001** |
| Weather — Sunny | 0.000 | 0.000 | **0.000** |

> Weather features rank low in importance scores because the Keytel formula (which generates the target) does not mathematically include weather — the weather multipliers are applied on top of it. The features are retained and meaningful at inference time; they simply explain less variance than physiological inputs by design. See [Why Weather Belongs in the Model](#why-weather-belongs-in-the-model).

### Training Diagnostic Plots

<details>
<summary>Click to expand training plots</summary>

| Plot | Description |
|---|---|
| ![Learning curve](out/ann_learning_curve.png) | ANN loss over epochs (train vs. validation) |
| ![Actual vs predicted](out/act_vs_pred_and_residuals.png) | Actual vs. predicted calories + residual distribution |
| ![Model comparison](out/performance.png) | R², MAE, RMSE comparison across all models |
| ![Train vs test R²](out/train_vs_test_r2_scatter.png) | Train/test R² scatter — generalisation check |
| ![Overfit analysis](out/overfit_underfit_analysis.png) | Overfitting / underfitting analysis |
| ![Correlation heatmap](out/correlation_heatmap.png) | Feature correlation heatmap (post-fix) |
| ![Feature selection](out/feature_selection.png) | Combined feature importance scores |
| ![Calorie distribution](out/calories_burned_distribution.png) | Target variable distribution after Keytel fix |

</details>

---

## Datasets

### What We Used and Why

| # | Dataset | Source | Role |
|---|---------|--------|------|
| 2 | Exercise & Fitness Metrics | [Kaggle](https://www.kaggle.com/datasets/aakashjoshi123/exercise-and-fitness-metrics-dataset) | ANN training data (target replaced with Keytel values) |
| 3 | Fitness Exercises (ExerciseDB) | [Kaggle](https://www.kaggle.com/datasets/exercisedb/fitness-exercises-dataset) | Runtime exercise lookup for AI coach |
| 4 | Mendeley Gym Recommendation | [Mendeley Data](https://data.mendeley.com/datasets/zw8mtbm5b9/1) | Profile-to-plan matching for AI coach |
| 5 | OpenWeather API | [openweathermap.org](https://openweathermap.org/api) | Live weather context at inference time |

---

### Why We Dropped the Primary Dataset

The [Gym Members Exercise Dataset](https://www.kaggle.com/datasets/valakhorasani/gym-members-exercise-dataset) was the original intended training source. After merging it with Dataset 2, two critical issues emerged:

- **Incompatible calorie distributions** — the two datasets had fundamentally different calorie ranges and distributions. Merging created a bimodal target that no single regression model can fit cleanly.
- **~80% null values** — several key features (Max\_BPM, Resting\_BPM, Fat\_Percentage, Water\_Intake) became almost entirely missing after the merge, making imputation unreliable and the feature space inconsistent.

Dataset 1 was dropped entirely. Dataset 2 was used exclusively for model training after fixing its target variable.

---

### The Target Variable Problem — and How We Fixed It

> **TL;DR:** The original `Calories_Burned` column in `exercise_dataset.csv` was random noise. We replaced it with values from the Keytel et al. (2005) validated formula before any model training.

**Statistical proof it was noise:**

| Diagnostic | Value | Interpretation |
|---|---|---|
| Max feature correlation | 0.036 | Effectively zero |
| Any model's R² | ≈ −0.03 | Worse than predicting the mean |
| KS test p-value | 0.49 | Indistinguishable from uniform random |
| All features' shared variance | 0.9% | No predictable signal |

A negative R² is not a pipeline bug — it is the mathematically guaranteed result when the target has no relationship to any input. No ML model can achieve R² > 0 on a random target.

**The fix — Keytel et al. (2005):**

The `Calories_Burned` column was replaced using the Keytel formula, the standard validated equation in exercise science, calibrated from real human trials and reproduced in wearable devices (Polar, Garmin):

```
Male:   Cal = Duration_min × (−55.0969 + 0.6309×HR + 0.1988×Weight + 0.2017×Age) / 4.184
Female: Cal = Duration_min × (−20.4022 + 0.4472×HR − 0.05741×Weight + 0.074×Age) / 4.184
```

Exercise Intensity is applied as an adjustment multiplier. Small Gaussian noise (σ ≈ 5%) is added to ensure the distribution reflects real-world variation rather than being a perfect deterministic output.

**Before vs. after the fix:**

| Feature | Correlation Before | Correlation After |
|---|:---:|:---:|
| Exercise Duration | +0.02 | **+0.67** |
| Heart Rate | −0.04 | **+0.59** |
| Exercise Intensity | +0.01 | **+0.18** |

These correlations are physically meaningful and consistent with exercise physiology literature. The regenerated target is not fabricated — it uses the same formula that was validated across 115 subjects in the original study (see [References](#references)).

---

### Why Weather Belongs in the Model

After the Keytel fix, weather still has near-zero correlation with the target because the base formula doesn't include environmental factors. The weather multipliers are applied on top of the formula output to encode two well-documented physiological mechanisms:

**❄️ Cold / Rainy → Thermogenesis**  
Your body burns extra calories to maintain core temperature (37°C). Wijers et al. (2008) measured a statistically significant **+2.8% increase in 24-hour energy expenditure** from mild cold exposure. Marlatt et al. (2019) found lean individuals can increase metabolic rate by up to **+17% above basal** before shivering begins.

**☀️ Hot / Sunny → Cardiovascular Strain**  
The heart must simultaneously supply blood to working muscles and to the skin for heat dissipation. The National Academies of Sciences confirm muscular metabolism increases 5–15× during heat exercise. Girard et al. (2023) documented physiological strain increases of **5–20%** depending on temperature and humidity.

The multipliers used in this project (5–8%) sit at the **conservative lower bound** of the ranges documented in the above studies — appropriate for general fitness exercise rather than extreme environmental conditions. The effect is U-shaped: both cold and hot conditions increase burn above a comfortable baseline (~18–22°C / Cloudy).

---

## AI Fitness Coach

The coach module works in five steps:

```
1. Profile intake     → Name, sex, age, height, weight, hypertension, diabetes
2. BMI calculation    → Auto-computed; mapped to Underweight / Normal / Overweight / Obese
3. Plan lookup        → Profile matched against gym_lookup.json (from Mendeley dataset)
4. System prompt      → Built from profile + matched plans + full ExerciseDB library
5. Gemini chat        → Free-form Q&A grounded in the user's specific health data
```

Health condition flags (Hypertension, Diabetes) trigger mandatory safety reminders in every response. The coach explicitly defers to a doctor for any clinical concerns and will never give unsafe medical advice.

---

## Project Structure

```
caloriesense/
│
├── gui/
│   ├── app.py                    # Flask app — routes, ANN inference, Gemini API
│   ├── templates/
│   │   ├── index.html            # Landing page
│   │   ├── calorie.html          # Calorie prediction UI
│   │   └── ai.html               # AI fitness coach UI
│   └── static/
│       ├── style.css             # Dark-theme glassmorphism styles
│       └── script.js             # Frontend logic, weather fetch, prediction calls
│
├── data/
│   ├── Calorie Prediction/
│   │   └── exercise_dataset.csv  # Dataset 2 (Calories_Burned replaced with Keytel values)
│   ├── Recomendation/
│   │   ├── Fitness Exercises Dataset/
│   │   └── Mendeley Gym Recommendation Dataset/
│   └── JSON/
│       ├── gym_lookup.json       # Pre-processed Mendeley lookup (keyed by health profile)
│       └── exercises.json        # Pre-processed ExerciseDB library
│
├── out/
│   ├── models/
│   │   ├── ann.keras             # Production ANN (TensorFlow SavedModel)
│   │   ├── scaler.pkl            # StandardScaler fitted on training data
│   │   ├── feature_list.pkl      # Ordered feature names for inference
│   │   ├── pipeline_metadata.json
│   │   ├── train_test_accuracy_summary.csv
│   │   ├── rf.pkl / rf_tuned.pkl
│   │   ├── xgb.pkl / xgb_tuned.pkl
│   │   └── ridge_poly.pkl
│   └── *.png                     # Training diagnostic plots
│
├── retrain.ipynb                 # Training notebook v1
├── retrainV2.ipynb               # Training notebook v2
├── retrainV3.ipynb               # Training notebook v3 (final pipeline)
├── json_convert.py               # Converts raw CSVs → gym_lookup.json / exercises.json
├── location_based_weather.py     # Standalone weather utility (ip-api → OpenWeatherMap)
├── .env                          # API keys (never committed)
└── docs/
    └── Images/                   # UI screenshots
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- A [Gemini API key](https://aistudio.google.com/app/apikey)
- An [OpenWeather API key](https://openweathermap.org/api)

### Installation

```bash
# Clone the repository
git clone https://github.com/heyisula/caloriesense.git
cd caloriesense

# Install dependencies
pip install flask tensorflow scikit-learn xgboost joblib requests python-dotenv google-genai numpy

# Configure API keys (see Environment Variables below)
```

### Running

```bash
cd gui
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

> **Note:** The trained model artefacts in `out/models/` must be present. If retraining from scratch, run `retrainV3.ipynb` end-to-end first.

---

## Environment Variables

Create a `.env` file in the **project root** (not inside `gui/`):

```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash-lite
OPENWEATHER_API_KEY=your_openweather_api_key_here
```

> The `.env` file is listed in `.gitignore` and will never be committed to version control.

---

## References

1. **Keytel formula — calorie estimation from heart rate**  
   Keytel, L.R., Goedecke, J.H., Noakes, T.D., Hiiloskorpi, H., Laukkanen, R., van der Merwe, L., & Lambert, E.V. (2005). *Prediction of energy expenditure from heart rate monitoring during submaximal exercise.* Journal of Sports Sciences, 23(3), 289–297.  
   [PubMed](https://pubmed.ncbi.nlm.nih.gov/15966347/) · [Semantic Scholar](https://www.semanticscholar.org/paper/Prediction-of-energy-expenditure-from-heart-rate-Keytel-Goedecke/2f647f62e650bf7df32546e541af3cf155297749) · [ResearchGate](https://www.researchgate.net/publication/7777759)  
   *Validated on 115 subjects, 18–45 years, 47–120 kg across three exercise intensities (35%, 62%, 80% VO₂max).*

2. **Cold-induced thermogenesis — cold/rainy weather increases calorie burn**  
   Wijers, S.L.J., Saris, W.H.M., & van Marken Lichtenbelt, W.D. (2008). *Human skeletal muscle mitochondrial uncoupling is associated with cold induced adaptive thermogenesis.* PLoS ONE, 4(3).  
   [PMC free text](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC2258415/)

   Marlatt, K.L., et al. (2019). *Quantification of the capacity for cold-induced thermogenesis in young men with and without obesity.* Journal of Clinical Endocrinology & Metabolism.  
   [PMC free text](https://pmc.ncbi.nlm.nih.gov/articles/PMC6733495/)

3. **Cardiovascular strain — hot/sunny weather increases calorie burn**  
   National Academies of Sciences. *Nutritional Needs in Hot Environments — Physiological Responses to Exercise in the Heat.*  
   [NCBI Bookshelf](https://www.ncbi.nlm.nih.gov/books/NBK236240/)

   Girard, O., et al. (2023). *Delineating the impacts of air temperature and humidity for endurance exercise.* Experimental Physiology.  
   [PMC free text](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10103870/)

---

## License

[MIT](LICENSE) © heyisula
