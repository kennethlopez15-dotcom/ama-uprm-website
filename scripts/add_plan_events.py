"""Add the Chapter Plan's tentative calendar (scripts/rumi_plan.json) to events.html.

Usage (from the site folder):  python scripts/add_plan_events.py
Only future dates are added; events already on the page (same id or same date+title) are skipped,
so it is safe to run again after the plan changes. Each plan event is labelled "Tentative date".
"""
import datetime, html, json, os, re, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(ROOT, 'events.html')
PLAN = os.path.join(ROOT, 'scripts', 'rumi_plan.json')

MON_EN = 'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split()
MON_ES = 'ene feb mar abr may jun jul ago sep oct nov dic'.split()

# The flagship symposium has a month but no day yet in the plan.
EXTRA = [{
    'id': 'e-symposium-2027', 'date': '2027-02-01', 'cat': 'pro', 'tba': True,
    'en': 'AMA-UPRM Annual Marketing Symposium', 'es': 'AMA-UPRM Annual Marketing Symposium',
    'p_en': 'Our flagship half-day event: keynotes, panels and networking on personal brand, AI and strategic marketing.',
    'p_es': 'Nuestro evento insignia de medio día: conferencias, paneles y networking sobre marca personal, IA y mercadeo estratégico.',
    'meta_en': 'February 2027 · Date to be announced', 'meta_es': 'Febrero 2027 · Fecha por anunciar',
}]


def esc(s):
    return html.escape(s, quote=True)


def category(title):
    t = title.lower()
    if re.search(r'workshop|info session|networking|plant tour|debrief|study|symposium|panel', t):
        return 'pro'
    if re.search(r'school|senior home|donation|shelter', t):
        return 'service'
    return 'social'


NO_RSVP = re.compile(r'sale|raffle|announcement|car wash|fundraiser at|post cards', re.I)


def slug(s):
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')[:30]


def event_html(e):
    d = datetime.date.fromisoformat(e['date'])
    if e.get('tba'):
        box = f'<div class="date date-tba"><strong data-en="{MON_EN[d.month - 1]}" data-es="{MON_EN[d.month - 1]}">{MON_EN[d.month - 1]}</strong><span>{d.year}</span></div>'
    else:
        box = (f'<div class="date"><strong>{d.day}</strong>'
               f'<span data-en="{MON_EN[d.month - 1]}" data-es="{MON_ES[d.month - 1]}">{MON_EN[d.month - 1]}</span></div>')
    body = f'<h2 data-en="{esc(e["en"])}" data-es="{esc(e["es"])}">{esc(e["en"])}</h2>'
    if e.get('p_en'):
        body += f'<p data-en="{esc(e["p_en"])}" data-es="{esc(e["p_es"])}">{esc(e["p_en"])}</p>'
    meta_en = e.get('meta_en', 'Tentative date · Chapter Plan')
    meta_es = e.get('meta_es', 'Fecha tentativa · Chapter Plan')
    body += f'<div class="meta" data-en="{esc(meta_en)}" data-es="{esc(meta_es)}">{esc(meta_en)}</div>'
    cal = ''
    if not e.get('tba'):
        end = d + datetime.timedelta(days=1)
        url = ('https://calendar.google.com/calendar/render?action=TEMPLATE&text=' + urllib.parse.quote('AMA UPRM: ' + e['en'])
               + f'&dates={d:%Y%m%d}/{end:%Y%m%d}&ctz=America%2FPuerto_Rico')
        cal = (f'<a href="{esc(url)}" target="_blank" rel="noopener" class="btn btn-sm btn-outline-dark" '
               f'data-en="Add to calendar" data-es="Agregar al calendario">Add to calendar</a>')
    rsvp = ' data-rsvp="no"' if NO_RSVP.search(e['en']) and not re.search(r'class', e['en'], re.I) else ''
    return (f'      <div class="event" id="{e["id"]}" data-cat="{e["cat"]}" data-date="{e["date"]}"{rsvp}>'
            f'{box}<div>{body}</div>{cal}</div>\n')


def main():
    page = open(PAGE, encoding='utf8').read()
    plan = json.load(open(PLAN, encoding='utf8'))['tentative_calendar']
    today = datetime.date.today().isoformat()
    have_ids = set(re.findall(r'class="event" id="([^"]+)"', page))
    have_dates = set(re.findall(r'data-date="([^"]+)"', page))
    new = []
    for item in plan:
        if item['date'] <= today:
            continue
        eid = f'e-plan-{item["date"].replace("-", "")}-{slug(item["en"])}'
        if eid in have_ids or (item['date'] in have_dates and 'ICC' in item['en']):
            continue
        new.append(dict(item, id=eid, cat=category(item['en'])))
    for e in EXTRA:
        if e['id'] not in have_ids and e['date'] > today:
            new.append(e)
    if not new:
        print('events.html: nothing new to add'); return
    block = ''.join(event_html(e) for e in sorted(new, key=lambda e: e['date']))
    marker = '<div id="event-list">\n'
    assert page.count(marker) == 1, 'event list not found'
    page = page.replace(marker, marker + block, 1)
    open(PAGE, 'w', encoding='utf8').write(page)
    print(f'events.html: added {len(new)} events')


if __name__ == '__main__':
    main()
