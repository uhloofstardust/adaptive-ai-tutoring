# Open questions

Everything here is blocked on a decision, not on work. Grouped by where
it came from. Each one says what we would do with each answer, so a
one-word reply is enough.

---

## A. From the last meeting's notes, which we could not resolve

**A1. "model 1: plain BKT / model 2: p(T) depends on prereq" is written
beside the word *tutor*. Did you mean the tutor, or the student?**

Today only the **student** has those two variants: S1 uses one p(T), S2
drops to `pT_low` until its prerequisites are truly known. No tutor in
`MASTERY_MODELS` gates p(T) on prerequisites.

If you meant the tutor as well, note it cannot see the true prerequisite
state, so it would have to gate on *its own belief* about the
prerequisites. That is a few lines of code, but it makes the tutor's
transition probability depend on its own output, which is a genuinely
different model and worth confirming before we build it. It would also
add a third factor to the 2x2.

**A2. "Give each concept its own p(T)" (the mail) against one pair of
values for every concept (the board). Which?**

The mail said each concept should have its own p(T). The board showed
p(T) = 0.2 after prerequisites are mastered and 0.05 otherwise, the same
two numbers for all eight concepts, which is what is implemented.

If you want per-concept values: hand-set, or drawn from a distribution?
Either way we would put them in `data/curriculum_abstract.json`, so you
can change them in the meeting without a code edit.

**A3. "Abstract concepts C1 C2 C3 C4 C5 C6". A literal rename, or was the
point just that they be subject-free?**

The curriculum is currently `A1, A2` then `B1, B2, B3` then `C1, C2` then
`D1`: the letter is the tier, so depth is readable from the name. A flat
`C1..C6` would lose that, and six concepts cannot make the depth 3 to 4
you circled on the same page. If the intent was only "no subject matter",
that is already satisfied.

**A4. One word in the notes we cannot read: "redo sanity check 2 ... redo
with psup = 6". What is psup?**

Worth noting the problem that prompted it appears to be gone. At 120
questions nothing is unresolved at any threshold, 240 of 240 concepts are
declared, and every learner reaches all eight concepts within 300
questions. If `psup` meant something else, tell us and we will run it.

---

## B. Decisions the new results force

**B1. S1's scheduler effect is a small cost, not zero. Report it or bury
it?**

We previously said Q2 costs S1 nothing. That was wrong. Across six
independent 400-learner blocks the contrast is **+1.09 questions**, a
cost of about one question in fifty-five, in the same direction as the
2x2 already showed. It is real but tiny, and no single run can resolve
its sign.

Report it as a finding with that caveat, or note it once and move on?

**B2. Is a two-percent gain worth an adapting tutor?**

Against an oracle tutor handed each learner's own parameters, adapting
to **p(S)** buys about two percent of the Brier score, and only once
learners are widely spread (+0.0019 +/-0.0013 at spread +/-0.15, nothing
resolvable at +/-0.05 or +/-0.10). Adapting to **p(guess)** buys nothing
detectable at any spread. The best single fixed tutor is always the one
at the true centre.

So the honest answer to "should the tutor help" is: only for p(S), only
under wide heterogeneity, and only by about two percent. Is that a yes or
a no for you?

**B3. The declaration rule is a step function. Does that change what you
want measured?**

A concept is declared mastered when the belief crosses 0.9, which takes
an integer number *k* of consecutive correct answers (k = 3 at the
current parameters). Over the swept grids k runs 2,2,3,3,4 for p(G),
3,3,3,3,3 for p(S), and 3,3,3,3,2 for p(T). p(S) never crosses a boundary
at all, so its apparent insensitivity for premature declarations is
partly a property of the grid rather than of the parameter.

This means cross-parameter sensitivity comparisons here are closer to
counting threshold crossings than to derivatives. Options: (a) report
sensitivity only within a parameter, never across; (b) soften the
declaration rule so it is not a step; (c) treat k itself as the quantity
of interest. We would take (a) as the default.

**B4. The description document is 7 pages. Your note says 2 to 3.**

It grew because the two new studies went into it. We would rather not
reach 3 pages by deleting correct findings. Trim to 3 and lose the
detail, keep it at 7, or keep it at 7 and write a separate 2-page
summary?

---

## C. Still open from 15 September

**C1.** Check 1 counts a "moment" only when the concept was just asked,
because beliefs on concepts not being asked do not change and counting
them every step would repeat the same pair. Is that the right population?

**C2.** The false-alarm rate is premature declarations divided by all
declarations, which is the tutor-user's question. Would you rather see it
divided by all concepts, or by concepts not known at the start?

**C3.** A false alarm is permanent: once declared, a concept leaves the
ZPD and is never asked again, so the student can never learn it. Add a
review rule now, or note it and leave it for the scheduler work?
