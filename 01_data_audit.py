import pandas as pd

df = pd.read_csv("data/indian_roads_dataset.csv")

print("Rows:", df.shape[0])
print("Columns:", df.shape[1])

print(df.head())

print("\n--- COLUMN NAMES ---")
print(df.columns.tolist())

print("\n--- DATA TYPES ---")
print(df.dtypes)

print("\n--- MISSING VALUES ---")
print(df.isnull().sum())

print("\n--- DUPLICATE ROWS ---")
print(df.duplicated().sum())

print("\n--- ACCIDENT SEVERITY ---")
print(df["accident_severity"].value_counts())

print("\n--- WEATHER ---")
print(df["weather"].value_counts())

print("\n--- ROAD TYPE ---")
print(df["road_type"].value_counts())

print("\n--- TRAFFIC DENSITY ---")
print(df["traffic_density"].value_counts())

print("\n--- CITIES ---")
print(df["city"].value_counts())

print("\n--- RISK SCORE ---")
print(df["risk_score"].describe())

print("\n--- UNIQUE RISK SCORES ---")
print(sorted(df["risk_score"].unique()))

print("\n--- RISK SCORE BY SEVERITY ---")
print(df.groupby("accident_severity")["risk_score"].agg(["count", "mean", "min", "max"]))

print("\n--- RISK SCORE BY WEATHER ---")
print(df.groupby("weather")["risk_score"].agg(["count", "mean", "min", "max"]))

print("\n--- RISK SCORE BY TRAFFIC DENSITY ---")
print(df.groupby("traffic_density")["risk_score"].agg(["count", "mean", "min", "max"]))

print("\n--- RISK SCORE CORRELATION ---")
print(df[["risk_score", "vehicles_involved", "casualties",
          "latitude", "longitude", "hour"]].corr()["risk_score"].sort_values(ascending=False))

print("\n--- UNIQUE RISK SCORES FOR EACH COMBINATION ---")

check = df.groupby(
    ["accident_severity", "weather", "traffic_density"]
)["risk_score"].nunique()

print(check)

print("\n--- RISK SCORE SAMPLE ---")

print(
    df[
        ["accident_severity", "weather", "traffic_density",
         "vehicles_involved", "casualties", "risk_score"]
    ].sort_values("risk_score").head(30)
)
print("\n--- RISK SCORE BY CASUALTIES ---")
print(
    df.groupby("casualties")["risk_score"]
      .agg(["count", "mean", "min", "max"])
      .head(20)
)

print("\n--- RISK SCORE BY VEHICLES INVOLVED ---")
print(
    df.groupby("vehicles_involved")["risk_score"]
      .agg(["count", "mean", "min", "max"])
)

print("\n--- RISK SCORE BY HOUR ---")
print(
    df.groupby("hour")["risk_score"]
      .agg(["count", "mean", "min", "max"])
)
print("\n--- COORDINATE CHECK ---")

print("Latitude:")
print(df["latitude"].describe())

print("\nLongitude:")
print(df["longitude"].describe())

print("\nSample coordinates:")
print(df[["city", "state", "latitude", "longitude"]].head(20))
# Select only Bangalore accidents
bangalore_df = df[df["city"] == "Bangalore"].copy()

print("\n--- BANGALORE DATASET ---")
print("Rows:", bangalore_df.shape[0])
print("Columns:", bangalore_df.shape[1])

print("\nCities included:")
print(bangalore_df["city"].value_counts())

print("\nCoordinates:")
print(bangalore_df[["latitude", "longitude"]].describe())

# Save Bangalore-only dataset
bangalore_df.to_csv("data/bangalore_accidents.csv", index=False)

print("\nBangalore dataset saved successfully!")
import matplotlib.pyplot as plt

plt.figure(figsize=(8, 8))

plt.scatter(
    bangalore_df["longitude"],
    bangalore_df["latitude"],
    s=8,
    alpha=0.5
)

plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.title("Accident Locations in Bengaluru")

plt.show()