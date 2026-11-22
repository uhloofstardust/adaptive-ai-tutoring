"""The grids. Proposed values come from part 6.1 of the changes PDF.
Labeled arms sit outside the ordering rule on purpose and are never pooled with the proposed grid."""
import itertools

CAPS = (.6, .7, .85, 1.)
GS, JS = (.25, .35, .45, .55), (.6, .7, .9)


def pairs_full():
    out = []
    for f in (.05, .10, .15, .20):
        for b in sorted({0., .01, .02, .05, f}):
            out.append((f, b))
    return out


def one_concept():
    cells = [dict(arm='proposed', g=g, J=J, f=f, bH=b, c=c)
             for g, J, (f, b), c in itertools.product(GS, JS, pairs_full(), CAPS)]
    assert len(cells) == 4 * 3 * 19 * 4
    cells += [dict(arm='bH_above_f', g=g, J=J, f=f, bH=b, c=c)
              for g, J, (f, b), c in itertools.product(GS, JS, ((.05, .10), (.10, .15)), CAPS)]
    cells += [dict(arm='slow_row', g=.135, J=.9, f=.03, bH=b, c=c)
              for b, c in itertools.product((0., .02, .03, .05), (.6, 1.))]
    cells += [dict(arm='cap_table', g=.45, J=.9, f=.10, bH=0., c=c) for c in (.5, .75, .78, .8, .82, .9, .95)]
    cells += [dict(arm='J1', g=.45, J=1., f=.10, bH=b, c=c)
              for b, c in itertools.product((0., .02, .05), CAPS)]
    for i, x in enumerate(cells):
        x['sid'] = i
    return cells


def graph():
    cells = [dict(arm='joint', g=g, J=J, f=f, bH=b, c=c)
             for g, J, f, b, c in itertools.product(GS, JS, (.05, .10, .20), (0., .02, .05), CAPS)]
    assert len(cells) == 4 * 3 * 3 * 3 * 4
    cells += [dict(arm='bH_eq_f', g=.45, J=.9, f=f, bH=f, c=c) for f, c in itertools.product((.10, .20), CAPS)]
    cells += [dict(arm='bH_above_f', g=.45, J=.9, f=f, bH=b, c=c)
              for (f, b), c in itertools.product(((.05, .10), (.10, .15)), CAPS)]
    cells += [dict(arm='slow_row', g=.135, J=.9, f=.03, bH=b, c=c)
              for b, c in itertools.product((0., .02, .05), (.6, 1.))]
    cells += [dict(arm='cap_table', g=.45, J=.9, f=.10, bH=0., c=c) for c in (.5, .75, .78, .8, .82, .9, .95)]
    cells += [dict(arm='J1', g=.45, J=1., f=.10, bH=0., c=c) for c in CAPS]
    for i, x in enumerate(cells):
        x['sid'] = i
    return cells


def arms():
    cells = [dict(arm='speed_start', g=.45, J=.9, f=.10, bH=b, c=c, speed=l, m0=m)
             for b, c, l, m in itertools.product((0., .05), CAPS, (1., .5, .25), (.05, .3, .65))]
    assert len(cells) == 72
    for i, x in enumerate(cells):
        x['sid'] = i
    return cells


THRS = (.20, .30, .35, .40, .45, .50, .55, .60, .65, .70, .75)
HOLD = list(range(4242, 4442))
TUNE = list(range(7000, 7100))
CT1000 = list(range(4242, 5242))
CHAIN_PLANS = ('easy', 'hard', 'random', 'switch', 'easyfirst', 'e3h', 'k2', 'k4', 'k8', 'k12', 'k16')
CT_200 = ('easyfirst', 'e3h', 'k16', 'easy', 'hard', 'switch')
CT_200_ARMS = ('easyfirst', 'e3h')
