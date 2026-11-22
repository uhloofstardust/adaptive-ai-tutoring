"""Per-skill answer sequences + global student-level train/test split."""
import numpy as np
import pandas as pd

SEED = 42
DATA = "data/cleaned.csv"


def load_df():
    df = pd.read_csv(DATA)
    return df.sort_values(["user_id", "order_id"], kind="mergesort")


def split_students(df, test_frac=0.2, seed=SEED):
    """Returns the set of held-out test student ids."""
    students = np.sort(df["user_id"].unique())
    rng = np.random.default_rng(seed)
    n_test = int(len(students) * test_frac)
    return set(rng.choice(students, size=n_test, replace=False).tolist())


def build_sequences(df):
    """skill_id -> {user_id: np.array of 0/1, chronological}."""
    seqs = {}
    for (skill, user), g in df.groupby(["skill_id", "user_id"], sort=False):
        seqs.setdefault(skill, {})[user] = g["correct"].to_numpy()
    return seqs


if __name__ == "__main__":
    df = load_df()
    test_ids = split_students(df)
    seqs = build_sequences(df)

    lengths = np.array([len(s) for users in seqs.values() for s in users.values()])
    print(f"students: {df['user_id'].nunique()}, skills: {len(seqs)}")
    print(f"(student, skill) sequences: {len(lengths)}")
    print(f"seq length mean {lengths.mean():.1f}, median {np.median(lengths):.0f}, "
          f"p90 {np.percentile(lengths, 90):.0f}, max {lengths.max()}")
    print(f"test students: {len(test_ids)} ({len(test_ids)/df['user_id'].nunique():.1%})")

    test_rows = df["user_id"].isin(test_ids).sum()
    print(f"test rows: {test_rows} ({test_rows/len(df):.1%})")

    fitable, covered = 0, 0
    for skill, users in seqs.items():
        n_train = sum(1 for u in users if u not in test_ids)
        if n_train >= 50:
            fitable += 1
            covered += sum(len(s) for s in users.values())
    print(f"skills with >=50 train students: {fitable} / {len(seqs)}")
    print(f"rows in those skills: {covered} ({covered/len(df):.1%})")
