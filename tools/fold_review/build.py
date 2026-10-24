# Build the two pages from data.json. Run from the repo root after tools/fold_review/extract.py.
import json, pathlib
d = json.load(open('tools/fold_review/data.json'))
head = '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
def page(tpl, data):
    body = open(tpl).read().replace('/*DATA*/null', json.dumps(data, separators=(',', ':')))
    i = body.index('</style>') + len('</style>')   # title, fonts and style go in <head>
    return head + body[:i] + '\n</head>\n<body>\n' + body[i:] + '\n</body>\n</html>\n'
student = {'generated': d['generated'], 'versions': {k: v for k, v in d['versions'].items() if k == max(d['versions'], key=lambda s: [int(x) for x in s[1:].split('.')])}}
pathlib.Path('steps').mkdir(exist_ok=True); pathlib.Path('review').mkdir(exist_ok=True)
open('steps/index.html', 'w').write(page('tools/fold_review/student_template.html', student))
open('review/index.html', 'w').write(page('tools/fold_review/template.html', d))
print('steps/index.html (students, newest version only) and review/index.html (staff, all versions) written')
