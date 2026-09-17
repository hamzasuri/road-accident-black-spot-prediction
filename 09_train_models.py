import pandas as pd
import numpy as np
import re
import joblib

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix
)

from xgboost import XGBClassifier


print("===================================")
print("LOADING ML FEATURES")
print("===================================")

df = pd.read_csv(
    "data/ml_features.csv"
)

print("Dataset loaded!")
print("Rows:", len(df))
print("Columns:", len(df.columns))


# --------------------------------------------------
# 1. SEPARATE FEATURES AND TARGET
# --------------------------------------------------

X = df.drop(
    columns=["risk_level", "risk_score"]
).copy()

y = df["risk_level"].copy()


# --------------------------------------------------
# 2. CLEAN FEATURE NAMES
# --------------------------------------------------

print("\nCleaning feature names...")

clean_names = []

for column in X.columns:

    # Convert to string
    name = str(column)

    # Replace characters that XGBoost does not allow
    name = re.sub(
        r"[\[\]<>]",
        "_",
        name
    )

    # Replace spaces
    name = name.replace(
        " ",
        "_"
    )

    # Replace commas
    name = name.replace(
        ",",
        "_"
    )

    clean_names.append(name)


X.columns = clean_names

print(
    "Feature names cleaned:",
    len(X.columns)
)


# --------------------------------------------------
# 3. CONVERT TARGET TO NUMBERS
# --------------------------------------------------

label_map = {
    "Low": 0,
    "Medium": 1,
    "High": 2,
    "Critical": 3
}

y = y.map(label_map)


print("\nFeature shape:", X.shape)
print("Target shape:", y.shape)


# --------------------------------------------------
# 4. CHECK FOR MISSING VALUES
# --------------------------------------------------

print("\nChecking missing values...")

missing = X.isnull().sum().sum()

print(
    "Total missing values:",
    missing
)

if missing > 0:

    X = X.fillna(0)

    print(
        "Missing values filled."
    )

else:

    print(
        "No missing values! ✅"
    )


# --------------------------------------------------
# 5. TRAIN / TEST SPLIT
# --------------------------------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print("\nTraining samples:", len(X_train))
print("Testing samples:", len(X_test))


# --------------------------------------------------
# 6. RANDOM FOREST
# --------------------------------------------------

print("\n===================================")
print("TRAINING RANDOM FOREST")
print("===================================")

rf_model = RandomForestClassifier(
    n_estimators=200,
    max_depth=12,
    random_state=42,
    class_weight="balanced"
)

rf_model.fit(
    X_train,
    y_train
)

rf_predictions = rf_model.predict(
    X_test
)

rf_accuracy = accuracy_score(
    y_test,
    rf_predictions
)

print("\nRandom Forest Accuracy:")
print(
    round(rf_accuracy * 100, 2),
    "%"
)

print("\nRandom Forest Classification Report:")

print(
    classification_report(
        y_test,
        rf_predictions,
        target_names=[
            "Low",
            "Medium",
            "High",
            "Critical"
        ],
        zero_division=0
    )
)


# --------------------------------------------------
# 7. XGBOOST
# --------------------------------------------------

print("\n===================================")
print("TRAINING XGBOOST")
print("===================================")

xgb_model = XGBClassifier(
    n_estimators=200,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    objective="multi:softmax",
    num_class=4,
    eval_metric="mlogloss",
    random_state=42
)

xgb_model.fit(
    X_train,
    y_train
)

xgb_predictions = xgb_model.predict(
    X_test
)

xgb_accuracy = accuracy_score(
    y_test,
    xgb_predictions
)

print("\nXGBoost Accuracy:")
print(
    round(xgb_accuracy * 100, 2),
    "%"
)

print("\nXGBoost Classification Report:")

print(
    classification_report(
        y_test,
        xgb_predictions,
        target_names=[
            "Low",
            "Medium",
            "High",
            "Critical"
        ],
        zero_division=0
    )
)


# --------------------------------------------------
# 8. MODEL COMPARISON
# --------------------------------------------------

print("\n===================================")
print("MODEL COMPARISON")
print("===================================")

print(
    "Random Forest:",
    round(rf_accuracy * 100, 2),
    "%"
)

print(
    "XGBoost:",
    round(xgb_accuracy * 100, 2),
    "%"
)


if xgb_accuracy > rf_accuracy:

    best_model = xgb_model
    best_model_name = "XGBoost"
    best_predictions = xgb_predictions

else:

    best_model = rf_model
    best_model_name = "Random Forest"
    best_predictions = rf_predictions


print("\nBest model:", best_model_name)


# --------------------------------------------------
# 9. CONFUSION MATRIX
# --------------------------------------------------

print("\n===================================")
print("CONFUSION MATRIX")
print("===================================")

print(
    confusion_matrix(
        y_test,
        best_predictions
    )
)


# --------------------------------------------------
# 10. SAVE MODELS
# --------------------------------------------------

joblib.dump(
    rf_model,
    "data/random_forest_model.pkl"
)

joblib.dump(
    xgb_model,
    "data/xgboost_model.pkl"
)

# Save feature names too
joblib.dump(
    list(X.columns),
    "data/model_features.pkl"
)


print("\nModels saved:")

print(
    "data/random_forest_model.pkl"
)

print(
    "data/xgboost_model.pkl"
)

print(
    "data/model_features.pkl"
)


# --------------------------------------------------
# 11. FINAL MESSAGE
# --------------------------------------------------

print("\n===================================")
print("MODEL TRAINING COMPLETE!")
print("===================================")