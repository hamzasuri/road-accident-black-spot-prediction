import pandas as pd
from ml.predict import predict_risk


def predict(data):
    df = pd.DataFrame([data])

    result = predict_risk(df)

    return result.to_dict(orient="records")