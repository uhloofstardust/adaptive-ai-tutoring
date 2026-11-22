"""Preprocess ASSISTments 2009-10 skill builder data for BKT.

Pipeline: drop missing skill_id -> keep main problems (original==1)
-> dedup on (order_id, skill_id), safe because correct is constant
within groups (verified; asserted below) -> sort -> save.
"""
import pandas as pd

RAW = "data/skill_builder_data.csv"
OUT = "data/cleaned.csv"

df = pd.read_csv(RAW, encoding="latin-1", low_memory=False)
print(f"raw rows:                 {len(df):>7}")

df = df.dropna(subset=["skill_id"])
print(f"after dropping no-skill:  {len(df):>7}")

df = df[df["original"] == 1]
print(f"after dropping scaffold:  {len(df):>7}")

# Safety: dedup must not have to choose between conflicting labels
assert df.groupby(["order_id", "skill_id"])["correct"].nunique().max() == 1

df = df.drop_duplicates(subset=["order_id", "skill_id"], keep="first")
print(f"after (order,skill) dedup:{len(df):>7}")

df["skill_id"] = df["skill_id"].astype(int)
df = df.sort_values(["user_id", "order_id"], kind="mergesort")

cols = ["user_id", "skill_id", "correct", "order_id"]
df[cols].to_csv(OUT, index=False)
print(f"\nsaved {OUT}")
print(f"students: {df['user_id'].nunique()}, skills: {df['skill_id'].nunique()}")
