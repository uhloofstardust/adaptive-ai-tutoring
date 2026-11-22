"""Classical Bayesian Knowledge Tracing, from scratch.

Per time step: predict P(correct) BEFORE seeing the answer, then
Bayes-update P(L) on the observed answer, then apply the learning
transition P(T). Self-test verifies against a hand-worked example.
"""
import numpy as np


class BKT:
    def __init__(self, p_L0, p_T, p_S, p_G):
        self.p_L0, self.p_T, self.p_S, self.p_G = p_L0, p_T, p_S, p_G

    def predict_correct(self, p_L):
        """P(next answer correct | current belief)."""
        return p_L * (1 - self.p_S) + (1 - p_L) * self.p_G

    def update(self, p_L, correct):
        """Bayes update of P(L) given the observed answer."""
        if correct == 1:
            num = p_L * (1 - self.p_S)
            den = num + (1 - p_L) * self.p_G
        else:
            num = p_L * self.p_S
            den = num + (1 - p_L) * (1 - self.p_G)
        return num / den

    def transition(self, p_L):
        """Unmastered student may learn from the opportunity."""
        return p_L + (1 - p_L) * self.p_T

    def trace(self, seq):
        """Returns (predictions, beliefs) for an answer sequence.

        predictions[t] = P(correct) emitted BEFORE seeing seq[t]
        beliefs[t]     = P(L) after update + transition at step t
        """
        p_L = self.p_L0
        preds, beliefs = [], []
        for obs in seq:
            preds.append(self.predict_correct(p_L))   # predict FIRST
            p_L = self.transition(self.update(p_L, obs))
            beliefs.append(p_L)
        return np.array(preds), np.array(beliefs)


if __name__ == "__main__":
    model = BKT(p_L0=0.3, p_T=0.1, p_S=0.1, p_G=0.2)
    seq = [1, 1, 0]
    preds, beliefs = model.trace(seq)

    print(f"{'t':>2} {'obs':>4} {'predict':>10} {'P(L) after':>12}")
    for t, (o, p, b) in enumerate(zip(seq, preds, beliefs), 1):
        print(f"{t:>2} {o:>4} {p:>10.6f} {b:>12.6f}")

    assert np.allclose(preds,   [0.410000, 0.684878, 0.843462], atol=1e-6)
    assert np.allclose(beliefs, [0.692683, 0.919231, 0.628501], atol=1e-6)
    print("\nself-test PASSED: matches hand-worked example")
