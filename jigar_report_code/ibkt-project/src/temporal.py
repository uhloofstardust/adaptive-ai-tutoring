"""Within-student temporal split for individualized BKT.

Why not the by-student split of the classical project: a held-out
student has no past data, so per-student parameters cannot be
estimated for them and iBKT would reduce to plain BKT on the test
set. A deployed tutor personalizes from what it has already seen of
each student, so the honest protocol is temporal: for every student,
the first TRAIN_FRAC of their interactions (chronological, over
their whole timeline) are the PAST and the rest are the FUTURE. All
fitting uses the past only; all evaluation happens on the future.
Both plain BKT and iBKT are compared under this identical protocol.
"""
import numpy as np
import pandas as pd

DATA = "data/cleaned.csv"
TRAIN_FRAC = 0.7


def load_split():
    """Returns the cleaned dataframe with an is_future column added.

    For each student, the first ceil-free floor(0.7 * n) rows (at
    least 1) of their chronological timeline are past, the rest are
    future. Students with a single row contribute past only.
    """
    df = pd.read_csv(DATA).sort_values(["user_id", "order_id"],
                                       kind="mergesort").reset_index(drop=True)
    pos = df.groupby("user_id").cumcount()
    n = df.groupby("user_id")["user_id"].transform("size")
    n_past = np.maximum(1, np.floor(n * TRAIN_FRAC)).astype(int)
    df["is_future"] = (pos >= n_past).to_numpy()
    return df


def past_skill_sequences(df):
    """skill_id -> list of 0/1 arrays (one per student, past rows only),
    for fitting the per-skill parameters. Order inside each array is
    chronological."""
    past = df[~df["is_future"]]
    seqs = {}
    for (skill, user), g in past.groupby(["skill_id", "user_id"], sort=False):
        seqs.setdefault(skill, []).append(g["correct"].to_numpy())
    return seqs


def pair_sequences(df):
    """(user_id, skill_id) -> (past array, future array), chronological.

    The belief for a pair is later run through the past part first
    (no scoring) and then continues onto the future part (scored),
    identically for both models.
    """
    pairs = {}
    for (user, skill), g in df.groupby(["user_id", "skill_id"], sort=False):
        fut = g["is_future"].to_numpy()
        obs = g["correct"].to_numpy()
        pairs[(user, skill)] = (obs[~fut], obs[fut])
    return pairs


if __name__ == "__main__":
    df = load_split()
    n_past = (~df["is_future"]).sum()
    n_fut = df["is_future"].sum()
    print(f"rows: {len(df)}  past: {n_past} ({n_past/len(df):.1%})  "
          f"future: {n_fut} ({n_fut/len(df):.1%})")
    print(f"students: {df['user_id'].nunique()}, "
          f"students with future rows: "
          f"{df.loc[df['is_future'], 'user_id'].nunique()}")

    seqs = past_skill_sequences(df)
    fitable = sum(1 for s in seqs.values() if len(s) >= 50)
    rows_cov = sum(sum(len(a) for a in s) for s in seqs.values()
                   if len(s) >= 50)
    print(f"skills with >=50 past students: {fitable} / {len(seqs)}")
    print(f"past rows in those skills: {rows_cov} ({rows_cov/n_past:.1%})")

    pairs = pair_sequences(df)
    split_pairs = sum(1 for p, f in pairs.values() if len(p) and len(f))
    fut_only = sum(1 for p, f in pairs.values() if len(f) and not len(p))
    print(f"(student, skill) pairs: {len(pairs)}, with both past and "
          f"future: {split_pairs}, future-only (cold start): {fut_only}")
