import pandas as pd

df = pd.read_csv("data/bangalore_accident_data.csv")

print("Rows:", df.shape[0])
print("Columns:", df.shape[1])

print("\n--- COLUMNS ---")
print(df.columns.tolist())

print("\n--- FIRST 5 ROWS ---")
print(df.head())

print("\n--- DATA TYPES ---")
print(df.dtypes)

print("\n--- MISSING VALUES ---")
print(df.isnull().sum())

print("\n--- DUPLICATES ---")
print(df.duplicated().sum())

print("\n--- SEVERITY ---")
print(df["severity"].value_counts())

print("\n--- ACCIDENT TYPE ---")
print(df["accident_type"].value_counts())

print("\n--- PEAK HOURS ---")
print(df["peak_hours"].value_counts())

print("\n--- ROAD CONDITION ---")
print(df["road_condition"].value_counts())

print("\n--- WEATHER FACTOR ---")
print(df["weather_factor"].value_counts())

print("\n--- INCIDENTS ---")
print(df["incidents"].describe())

print("\n--- HOTSPOTS SORTED BY INCIDENTS ---")
print(df[["location", "incidents", "severity"]]
      .sort_values("incidents", ascending=False)
      .to_string(index=False))