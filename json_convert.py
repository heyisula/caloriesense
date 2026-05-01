import pandas as pd
import json
import os
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Loading the recommendation data files
GYM_FILE = "data/Recomendation/Mendeley Gym Recommendation Dataset/gym recommendation.xlsx"
EX_FILE  = "data/Recomendation/Fitness Exercises Dataset/exercises_flat.csv"

print(f"Loading gym data from: {GYM_FILE}")
df = pd.read_excel(GYM_FILE)
print(f"  Raw rows loaded   : {len(df)}")
print(f"  Columns           : {df.columns.tolist()}")


# Deduplication of the gym recommendation data because many rows are repeated for the same user profile combinations. We only keep one row per unique profile combination to optimize the lookup for the chatbot (Sex, Age, Hypertension, Diabetes, BMI Level,Fitness Goal, Fitness Type) are columns are repeadted but the Exercises, Equipment, Diet and Recommendation are IDENTICAL So we are dropping the duplicates based on the unique combinations of the key columns.


KEY_COLS = [
    "Sex","Age","Hypertension","Diabetes","Level","Fitness Goal","Fitness Type"
]

dedup = df.drop_duplicates(subset=KEY_COLS).reset_index(drop=True)
print(f"  After dedup       : {len(dedup)} unique profiles  "
      f"(removed {len(df) - len(dedup)} duplicate rows)")


#  Building the lookup dictionary. The key is a string formed by concatenating the values of the key columns with a separator (ex: "Male|25|No|No|Normal|Weight Gain|Muscular Fitness") and the value is a dictionary containing the exercises, equipment, diet and recommendation for that profile. This allows the chatbot to quickly look up the recommendations based on the user's profile in O(1)

gym_lookup = {}

for _, row in dedup.iterrows():
    key = "|".join([
        str(row["Sex"]),str(int(row["Age"])),str(row["Hypertension"]),str(row["Diabetes"]),str(row["Level"]),str(row["Fitness Goal"]),str(row["Fitness Type"]),
    ])
    gym_lookup[key] = {
        "exercises" : str(row["Exercises"]),"equipment" : str(row["Equipment"]),"diet" : str(row["Diet"]),"recommendation" : str(row["Recommendation"]),
    }
print(f"  Lookup entries    : {len(gym_lookup)}")

#  gym_lookup.json
with open("data/JSON/gym_lookup.json", "w", encoding="utf-8") as f:
    json.dump(gym_lookup, f, indent=2, ensure_ascii=False)
size_kb = os.path.getsize("data/JSON/gym_lookup.json") / 1024
print(f"gym_lookup.json written  ({size_kb:.1f} KB)")


# Loading the exercises file

print(f"\nLoading exercises from: {EX_FILE}")
ex = pd.read_csv(EX_FILE)
print(f"  Rows loaded : {len(ex)}")
print(f"  Columns     : {ex.columns.tolist()}")


#  Building exercises list by keeping only the fields the chatbot actually needs dropping the gifUrl field because it is not useful in a text chat and it would increase the size of the JSON file unnecessarily. The chatbot will only use the id, name, target muscles, body part, equipment, secondary muscles and instructions for each exercise.

exercises = []
for _, row in ex.iterrows():
    exercises.append({
        "id" : str(row["exerciseId"]),"name" : str(row["name"]),"target_muscles" : str(row["target_muscles"]),"body_part" : str(row["body_part_category"]),"equipment" : str(row["equipment_needed"]),"secondary_muscles" : str(row["secondaryMuscles"]),"instructions" : str(row["instructions"]),
    })

# exercises.json

with open("data/JSON/exercises.json", "w", encoding="utf-8") as f:
    json.dump(exercises, f, indent=2, ensure_ascii=False)

size_kb = os.path.getsize("data/JSON/exercises.json") / 1024
print(f"exercises.json written  ({size_kb:.1f} KB)")


print("\nData Justification lookup for Male, Age 25, No conditions, Normal BMI")
sample_keys = [k for k in gym_lookup if k.startswith("Male|25|No|No|Normal")]
for key in sample_keys:
    val = gym_lookup[key]
    print(f"\n  KEY : {key}")
    print(f"  Exercises  : {val['exercises'][:80]}...")
    print(f"  Equipment  : {val['equipment']}")
    print(f"  Diet       : {val['diet'][:80]}...")

print(f"\nOnly {len(sample_keys)} rows passed to Gemini for this user")

print(f"    gym_lookup.json   — {len(gym_lookup)} unique profile entries")
print(f"    exercises.json    — {len(exercises)} exercises")
