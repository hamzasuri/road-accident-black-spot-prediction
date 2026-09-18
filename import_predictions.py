import pandas as pd
from psycopg2.extras import execute_values
from backend.app.db import conn


def parse_number(value):
    """
    Converts OSM-style values into a single integer.

    Examples:
    40          -> 40
    40.0        -> 40
    ['40']      -> 40
    ['40', '50'] -> 40
    unknown     -> None
    """

    if pd.isna(value):
        return None

    value = str(value).strip()

    if value.lower() in ["unknown", "nan", "none", ""]:
        return None

    # Handle values like ['40', '50']
    if value.startswith("[") and value.endswith("]"):
        value = value.strip("[]")
        value = value.split(",")[0].strip()
        value = value.strip("'\"")

    try:
        return int(float(value))
    except ValueError:
        return None


print("Loading prediction data...")

df = pd.read_csv("data/road_risk_predictions.csv")

print(f"Prediction rows: {len(df)}")

rows = []

for _, row in df.iterrows():

    lanes = parse_number(row["lanes"])
    maxspeed = parse_number(row["maxspeed"])

    rows.append((
        int(row["u"]),
        int(row["v"]),
        int(row["key"]),
        row["road_length"],
        row["highway"],
        lanes,
        maxspeed,
        row["oneway"],
        row["predicted_risk_score"],
        row["predicted_risk_level"],
        row["prediction_confidence"]
    ))


print("Prepared rows:", len(rows))

cursor = conn.cursor()

print("Inserting predictions into PostgreSQL...")

execute_values(
    cursor,
    """
    INSERT INTO road_segments (
        u,
        v,
        key,
        road_length,
        highway,
        lanes,
        maxspeed,
        oneway,
        risk_score,
        risk_level,
        prediction_confidence
    )
    VALUES %s
    """,
    rows
)

conn.commit()

cursor.close()

print()
print("======================================")
print("IMPORT SUCCESSFUL!")
print("======================================")
print(f"{len(rows)} predictions inserted successfully!")