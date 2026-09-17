import os
import joblib
import pandas as pd
import numpy as np


# ============================================================
# PATH SETUP
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


# ============================================================
# LOAD TRAINED MODEL
# ============================================================

model = joblib.load(
    os.path.join(
        BASE_DIR,
        "data",
        "xgboost_model.pkl"
    )
)


# ============================================================
# LOAD MODEL FEATURE NAMES
# ============================================================

model_features = joblib.load(
    os.path.join(
        BASE_DIR,
        "data",
        "model_features.pkl"
    )
)


# ============================================================
# RISK LEVEL NAMES
# ============================================================

RISK_NAMES = {
    0: "Low",
    1: "Medium",
    2: "High",
    3: "Critical"
}


# ============================================================
# PREDICTION FUNCTION
# ============================================================

def predict_risk(data):

    # Make a copy so the original DataFrame is not modified
    X = data.copy()

    # Remove target columns if they exist
    X = X.drop(
        columns=["risk_level", "risk_score"],
        errors="ignore"
    )

    # --------------------------------------------------------
    # Make sure every feature used during training exists
    # --------------------------------------------------------

    for feature in model_features:

        if feature not in X.columns:
            X[feature] = 0

    # --------------------------------------------------------
    # Keep EXACT same feature order as training
    # --------------------------------------------------------

    X = X[model_features]

    # --------------------------------------------------------
    # Replace missing values
    # --------------------------------------------------------

    X = X.fillna(0)

    # ========================================================
    # PREDICT CLASS
    # ========================================================

    predicted_class = model.predict(X)

    # ========================================================
    # GET CLASS PROBABILITIES
    # ========================================================

    probabilities = model.predict_proba(X)

    # ========================================================
    # CONVERT CLASS NUMBER TO RISK LEVEL
    # ========================================================

    risk_levels = [
        RISK_NAMES[int(x)]
        for x in predicted_class
    ]

    # ========================================================
    # CALCULATE RISK SCORE 0-100
    # ========================================================

    class_scores = np.array([
        0,
        33.33,
        66.67,
        100
    ])

    risk_scores = (
        probabilities * class_scores
    ).sum(axis=1)

    risk_scores = np.clip(
        risk_scores,
        0,
        100
    )

    # ========================================================
    # CALCULATE CONFIDENCE
    # ========================================================

    confidence = (
        probabilities.max(axis=1) * 100
    )

    # ========================================================
    # CREATE RESULT DATAFRAME
    # ========================================================

    result = pd.DataFrame({

        "risk_score": np.round(
            risk_scores,
            2
        ),

        "risk_level": risk_levels,

        "confidence": np.round(
            confidence,
            2
        )
    })

    return result


# ============================================================
# TEST THE MODULE
# ============================================================

if __name__ == "__main__":

    print("======================================")
    print("ML PREDICTION MODULE TEST")
    print("======================================")

    # --------------------------------------------------------
    # Load feature dataset
    # --------------------------------------------------------

    test_data = pd.read_csv(
        os.path.join(
            BASE_DIR,
            "data",
            "ml_features.csv"
        )
    )

    print(
        "\nTest samples:",
        len(test_data)
    )

    # --------------------------------------------------------
    # Generate predictions
    # --------------------------------------------------------

    results = predict_risk(
        test_data
    )

    print(
        "\nPredictions generated:",
        len(results)
    )

    # --------------------------------------------------------
    # Display risk distribution
    # --------------------------------------------------------

    print("\nRisk distribution:")

    print(
        results["risk_level"].value_counts()
    )

    # --------------------------------------------------------
    # Display sample predictions
    # --------------------------------------------------------

    print("\nSample predictions:")

    print(
        results.head(10)
    )

    # --------------------------------------------------------
    # Success message
    # --------------------------------------------------------

    print("\n======================================")
    print("ML MODULE TEST SUCCESSFUL! ✅")
    print("======================================")