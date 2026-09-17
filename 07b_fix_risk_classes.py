import pandas as pd
import numpy as np

print("Loading ML training dataset...")

df = pd.read_csv("data/ml_training_dataset.csv")

print("Rows loaded:", len(df))


# --------------------------------------------------
# 1. CREATE A HISTORICAL RISK INDEX
# --------------------------------------------------

print("\nCreating historical risk index...")


# Accident frequency
frequency = df["accident_count"]

# Severity
severity = df["severity_score"]

# Casualties
casualties = df["total_casualties"]


# Rank-based normalization
# This prevents a few extreme values from dominating.

df["frequency_rank"] = frequency.rank(pct=True)

df["severity_rank"] = severity.rank(pct=True)

df["casualty_rank"] = casualties.rank(pct=True)


# Combined historical risk
df["risk_score"] = (
    0.40 * df["frequency_rank"]
    + 0.40 * df["severity_rank"]
    + 0.20 * df["casualty_rank"]
) * 100


# --------------------------------------------------
# 2. CREATE RISK CLASSES USING PERCENTILES
# --------------------------------------------------

def classify_risk(score):

    if score <= 25:
        return "Low"

    elif score <= 50:
        return "Medium"

    elif score <= 75:
        return "High"

    else:
        return "Critical"


df["risk_level"] = df["risk_score"].apply(classify_risk)


# --------------------------------------------------
# 3. SHOW DISTRIBUTION
# --------------------------------------------------

print("\nNew risk distribution:")

print(
    df["risk_level"].value_counts()
    .sort_index()
)


# --------------------------------------------------
# 4. SHOW RISK SCORE STATISTICS
# --------------------------------------------------

print("\nRisk score statistics:")

print(
    df["risk_score"].describe()
)


# --------------------------------------------------
# 5. SAVE
# --------------------------------------------------

df.to_csv(
    "data/ml_training_dataset_v2.csv",
    index=False
)

print("\n===================================")
print("NEW ML DATASET CREATED!")
print("===================================")

print("Rows:", len(df))

print("\nSaved to:")
print("data/ml_training_dataset_v2.csv")