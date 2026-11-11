"""Rebuild the Executive Board section of about.html from scripts/board.json.

Usage (from the site folder):
    python scripts/build_board.py
    python scripts/build_rumi_kb.py   # so RUMi knows the new board

Only the <section id="team"> block of about.html is replaced. Pending positions
("name": null) stay in board.json and are not shown.
"""
import html, json, os, re, sys, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'scripts', 'board.json')
PAGE = os.path.join(ROOT, 'about.html')
HOME = os.path.join(ROOT, 'index.html')
LINKEDIN = 'https://www.linkedin.com/in/ama-uprm-36a961203/'

EN = 'zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty'.split()
ES = 'cero un dos tres cuatro cinco seis siete ocho nueve diez once doce trece catorce quince dieciséis diecisiete dieciocho diecinueve veinte'.split()


def num(n, words):
    return words[n] if n < len(words) else str(n)


def esc(s):
    return html.escape(s, quote=True)


def initials(name):
    parts = [p for p in re.split(r'\s+', name) if p and not re.fullmatch(r'[A-Z]\.', p)]
    return (parts[0][0] + (parts[-1][0] if len(parts) > 1 else '')).upper()


def card(p):
    name = p['name']
    if p.get('photo'):
        ph = f'<div class="ph has-img" data-bg="url({esc(p["photo"])})" role="img" aria-label="{esc(name)}"></div>'
    else:
        ph = f'<div class="ph initials" role="img" aria-label="{esc(name)}"><span aria-hidden="true">{esc(initials(name))}</span></div>'
    mail = p.get('email') or 'ama@uprm.edu?subject=' + urllib.parse.quote('For ' + name)
    return (f'<div class="member">{ph}<h4>{esc(name)}</h4>'
            f'<span data-en="{esc(p["en"])}" data-es="{esc(p["es"])}">{esc(p["en"])}</span>'
            f'<a href="mailto:{esc(mail)}" data-en="Email" data-es="Correo">Email</a></div>')


def group(g):
    people = [p for p in g['people'] if p.get('name')]
    if not people:
        return ''
    cls = 'team-group reveal' + (' faculty' if g.get('faculty') else '')
    return (f'    <div class="{cls}" id="team-{g["id"]}"><h3 data-en="{esc(g["en"])}" data-es="{esc(g["es"])}">{esc(g["en"])}</h3>\n'
            f'      <div class="team-grid stagger">{"".join(card(p) for p in people)}</div></div>\n')


def build(data):
    groups = data['groups']
    students = sum(1 for g in groups if not g.get('faculty') for p in g['people'] if p.get('name'))
    faculty = sum(1 for g in groups if g.get('faculty') for p in g['people'] if p.get('name'))
    depts = sum(1 for g in groups if not g.get('faculty') and g['id'] != 'executive' and any(p.get('name') for p in g['people']))
    sub_en = (f'An executive team and {num(depts, EN)} departments: {num(students, EN)} students, plus '
              f'{num(faculty, EN)} faculty advisors. Write to any of us by email, or follow the chapter on')
    sub_es = (f'Un equipo ejecutivo y {num(depts, ES)} departamentos: {num(students, ES)} estudiantes y '
              f'{num(faculty, ES)} consejeros académicos. Escríbele a cualquiera por correo o sigue al capítulo en')
    title_en, title_es = f'Executive Board {data["year"]}', f'Junta Directiva {data["year"]}'
    lead = [g for g in groups if g['id'] == 'executive']
    depts_g = [g for g in groups if g['id'] != 'executive' and not g.get('faculty')]
    fac = [g for g in groups if g.get('faculty')]
    out = ['<section class="section" id="team">\n  <div class="container">\n    <div class="reveal">\n',
           f'      <h2 class="section-title" data-en="{esc(title_en)}" data-es="{esc(title_es)}">{esc(title_en)}</h2>\n',
           '      <div class="accent-line"></div>\n',
           f'      <p class="section-sub"><span data-en="{esc(sub_en)}" data-es="{esc(sub_es)}">{esc(sub_en)}</span> '
           f'<a href="{LINKEDIN}" target="_blank" rel="noopener">LinkedIn</a>.</p>\n    </div>\n']
    out += [group(g) for g in lead]
    out.append('    <div class="team-depts">\n' + ''.join(group(g) for g in depts_g) + '    </div>\n')
    out += [group(g) for g in fac]
    out.append('  </div>\n</section>')
    return ''.join(out), students, faculty


def faces(data):
    """Homepage strip: every student board member who has a photo, in board order."""
    people = [p for g in data['groups'] if not g.get('faculty') for p in g['people'] if p.get('name') and p.get('photo')]
    imgs = ''.join(f'<img src="{esc(p["photo"])}" alt="{esc(p["name"])}" width="64" height="64" loading="lazy" decoding="async">' for p in people)
    return f'<!-- board-faces --><div class="faces">{imgs}</div><!-- /board-faces -->'


def main():
    data = json.load(open(DATA, encoding='utf8'))
    page = open(PAGE, encoding='utf8').read()
    block, students, faculty = build(data)
    new, n = re.subn(r'<section class="section" id="team">.*?</section>', lambda m: block, page, count=1, flags=re.S)
    if n != 1:
        sys.exit('about.html: team section not found')
    open(PAGE, 'w', encoding='utf8').write(new)
    home = open(HOME, encoding='utf8').read()
    home, k = re.subn(r'<!-- board-faces -->.*?<!-- /board-faces -->', lambda m: faces(data), home, count=1, flags=re.S)
    if k:
        open(HOME, 'w', encoding='utf8').write(home)
    pending = [f'{g["en"]}: {p["en"]}' for g in data['groups'] for p in g['people'] if not p.get('name')]
    print(f'about.html board: {students} students, {faculty} advisors; pending (not shown): {", ".join(pending) or "none"}')


if __name__ == '__main__':
    main()
