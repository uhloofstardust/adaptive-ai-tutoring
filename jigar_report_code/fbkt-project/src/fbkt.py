"""Forgetting BKT (BKT-F): classical BKT with a full transition
matrix. After every opportunity a not-yet-mastered student learns
with probability P(T), and a mastered student FORGETS with
probability P(F). Classical BKT is the special case P(F) = 0.

Only the transition step changes:

    pL'' = pL' * (1 - P(F)) + (1 - pL') * P(T)

Prediction and the Bayes update are identical to classical BKT.
Self-test: reproduces a hand-worked trace to six decimals.
"""


class FBKT:
    def __init__(self, pL0, pT, pS, pG, pF):
        self.pL0, self.pT, self.pS, self.pG, self.pF = pL0, pT, pS, pG, pF

    def predict_correct(self, pL):
        return pL * (1 - self.pS) + (1 - pL) * self.pG

    def update(self, pL, obs):
        if obs == 1:
            num = pL * (1 - self.pS)
            rest = (1 - pL) * self.pG
        else:
            num = pL * self.pS
            rest = (1 - pL) * (1 - self.pG)
        return num / (num + rest)

    def transition(self, pL):
        return pL * (1 - self.pF) + (1 - pL) * self.pT

    def trace(self, seq):
        """Predict-before-update probabilities along a sequence."""
        pL, preds = self.pL0, []
        for obs in seq:
            preds.append(self.predict_correct(pL))
            pL = self.transition(self.update(pL, obs))
        return preds


if __name__ == "__main__":
    # hand-worked: L0=0.3 T=0.1 S=0.1 G=0.2 F=0.05, sequence (1, 1, 0)
    m = FBKT(0.3, 0.1, 0.1, 0.2, 0.05)
    expect = [
        # (predict, pL after transition)
        (0.410000, 0.659756),
        (0.661829, 0.862604),
        (0.803823, 0.473750),
    ]
    pL = m.pL0
    print(" t  obs    predict   P(L) after")
    for t, (obs, (e_pred, e_after)) in enumerate(zip([1, 1, 0], expect), 1):
        pred = m.predict_correct(pL)
        pL = m.transition(m.update(pL, obs))
        print(f"{t:2d}  {obs:3d}   {pred:.6f}     {pL:.6f}")
        assert abs(pred - e_pred) < 1e-6, (t, pred, e_pred)
        assert abs(pL - e_after) < 1e-6, (t, pL, e_after)

    # with pF = 0 the model must be exactly classical BKT
    from bkt import BKT
    c = BKT(0.3, 0.1, 0.1, 0.2)
    f0 = FBKT(0.3, 0.1, 0.1, 0.2, 0.0)
    seq = [1, 0, 1, 1, 0, 1, 1, 1]
    pc_L, pf_L, worst = c.p_L0, f0.pL0, 0.0
    for obs in seq:
        worst = max(worst, abs(c.predict_correct(pc_L)
                               - f0.predict_correct(pf_L)))
        pc_L = c.transition(c.update(pc_L, obs))
        pf_L = f0.transition(f0.update(pf_L, obs))
        worst = max(worst, abs(pc_L - pf_L))
    assert worst < 1e-15, worst
    print("\nself-test PASSED: hand-worked forgetting trace matches; "
          "pF=0 reduces exactly to classical BKT")
