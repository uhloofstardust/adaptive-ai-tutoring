"""Commas for counts of 1,000 or more printed from the study's key files, so every large count in the report has the same form. Writes gen_fmt.tex."""
import os, re
HERE = os.path.dirname(os.path.abspath(__file__)); U = os.path.dirname(HERE)
tex = open(os.path.join(HERE, 'main.tex')).read(); used = set(re.findall(r'\\V\{([^}]+)\}', tex))
out = []
for f in ('story/gen.tex', 'shared/sweep_gen.tex'):
    for k, v in re.findall(r'csname v@([^\\]+)\\endcsname\{([^}]*)\}', open(os.path.join(U, f)).read()):
        if k in used and re.fullmatch(r'\d{4,}(\.\d+)?', v):
            a, _, b = v.partition('.'); out.append((k, f'{int(a):,}' + ('.' + b if b else '')))
with open(os.path.join(HERE, 'gen_fmt.tex'), 'w') as fh:
    for k, v in sorted(out):
        fh.write('\\expandafter\\def\\csname v@' + k + '\\endcsname{' + v + '}\n')
print(sorted(out))
