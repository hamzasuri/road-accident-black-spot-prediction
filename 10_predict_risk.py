import pandas as pd
import numpy as np
import joblib
import re


print("======================================")
print("ROAD ACCIDENT RISK PREDICTION")
print("======================================")


# --------------------------------------------------
# 1. LOAD FEATURE DATA
# --------------------------------------------------

print("\nLoading feature data...")

features = pd.read_csv(
    "data/ml_features.csv"
)

road_data = pd.read_csv(
    "data/ml_training_dataset_final.csv"
)

print("Feature rows:", len(features))
print("Road rows:", len(road_data))


# --------------------------------------------------
# 2. CHECK ROW ALIGNMENT
# --------------------------------------------------

if len(features) != len(road_data):

    raise ValueError(
        "Feature and road datasets have different row counts!"
    )

print("Row alignment verified! ✅")


# --------------------------------------------------
# 3. LOAD TRAINED XGBOOST MODEL
# --------------------------------------------------

print("\nLoading XGBoost model...")

model = joblib.load(
    "data/xgboost_model.pkl"
)

model_features = joblib.load(
    "data/model_features.pkl"
)

print("XGBoost model loaded!")

print(
    "Expected features:",
    len(model_features)
)


# --------------------------------------------------
# 4. PREPARE FEATURE DATA
# --------------------------------------------------

X = features.drop(
    columns=[
        "risk_level",
        "risk_score"
    ]
).copy()


# --------------------------------------------------
# 5. CLEAN FEATURE NAMES
# --------------------------------------------------

print("\nCleaning feature names...")

clean_names = []

for column in X.columns:

    name = str(column)

    # Remove characters that XGBoost does not allow
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
# 6. MAKE SURE ALL MODEL FEATURES EXIST
# --------------------------------------------------

missing_features = [
    feature
    for feature in model_features
    if feature not in X.columns
]


if len(missing_features) > 0:

    print("\nMissing model features:")

    for feature in missing_features:
        print("-", feature)

    raise ValueError(
        "Some model features are missing!"
    )


print(
    "All model features found! ✅"
)


# --------------------------------------------------
# 7. ARRANGE FEATURES IN CORRECT ORDER
# --------------------------------------------------

X = X[
    model_features
].copy()


print(
    "Prediction feature shape:",
    X.shape
)


# --------------------------------------------------
# 8. CHECK MISSING VALUES
# --------------------------------------------------

missing_count = X.isnull().sum().sum()

print(
    "Missing feature values:",
    missing_count
)


if missing_count > 0:

    X = X.fillna(0)

    print(
        "Missing values filled."
    )

else:

    print(
        "No missing values! ✅"
    )


# --------------------------------------------------
# 9. GENERATE CLASS PREDICTIONS
# --------------------------------------------------

print("\nGenerating predictions...")

predicted_class = model.predict(
    X
)

predicted_probabilities = model.predict_proba(
    X
)


# --------------------------------------------------
# 10. CONVERT CLASS TO RISK LEVEL
# --------------------------------------------------

risk_names = {
    0: "Low",
    1: "Medium",
    2: "High",
    3: "Critical"
}


predicted_levels = [
    risk_names[int(value)]
    for value in predicted_class
]


# --------------------------------------------------
# 11. CALCULATE RISK SCORE
# --------------------------------------------------

class_scores = np.array([
    0,
    33.33,
    66.67,
    100
])


model_risk_scores = (
    predicted_probabilities
    * class_scores
).sum(axis=1)


model_risk_scores = np.clip(
    model_risk_scores,
    0,
    100
)


# --------------------------------------------------
# 12. CREATE PREDICTION DATASET
# --------------------------------------------------

predictions = road_data[
    [
        "u",
        "v",
        "key",
        "road_length",
        "highway",
        "lanes",
        "maxspeed",
        "oneway"
    ]
].copy()


predictions[
    "predicted_risk_score"
] = (
    model_risk_scores.round(2)
)


predictions[
    "predicted_risk_level"
] = predicted_levels


# --------------------------------------------------
# 13. ADD MODEL CONFIDENCE
# --------------------------------------------------

predictions[
    "prediction_confidence"
] = (
    predicted_probabilities.max(
        axis=1
    ) * 100
).round(2)


# --------------------------------------------------
# 14. SAVE PREDICTIONS
# --------------------------------------------------

predictions.to_csv(
    "data/road_risk_predictions.csv",
    index=False
)


# --------------------------------------------------
# 15. DISPLAY RESULTS
# --------------------------------------------------

print("\n======================================")
print("PREDICTIONS GENERATED!")
print("======================================")

print(
    "Road segments predicted:",
    len(predictions)
)


print("\nPredicted risk distribution:")

print(
    predictions[
        "predicted_risk_level"
    ].value_counts()
)


print("\nAverage predicted risk score:")

print(
    round(
        predictions[
            "predicted_risk_score"
        ].mean(),
        2
    )
)


print("\nTop 10 highest-risk road segments:")

top_risk = predictions.sort_values(
    "predicted_risk_score",
    ascending=False
).head(10)


print(
    top_risk[
        [
            "u",
            "v",
            "road_length",
            "highway",
            "lanes",
            "maxspeed",
            "predicted_risk_score",
            "predicted_risk_level",
            "prediction_confidence"
        ]
    ]
)


# --------------------------------------------------
# 16. FINAL MESSAGE
# --------------------------------------------------

print("\nSaved to:")
print(
    "data/road_risk_predictions.csv"
)


print("\n======================================")
print("RISK PREDICTION COMPLETE!")
print("======================================")