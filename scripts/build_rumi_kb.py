"""Build RUMi's knowledge base from the site's own pages: python scripts/build_rumi_kb.py

Writes assets/rumi/kb.json. RUMi (the chat assistant) answers only from this file,
so re-run it after editing page content and commit the result.
"""
from html import escape, unescape
from html.parser import HTMLParser
from pathlib import Path
import datetime
import json
import re

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets' / 'rumi' / 'kb.json'
PAGES = ['index.html', 'about.html', 'elevate.html', 'programs.html', 'events.html',
         'membership.html', 'sponsors.html', 'blog.html', 'blog-post.html',
         'case-ppm.html', 'case-cancer-relief.html']
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'source', 'track', 'wbr'}
SKIP = {'script', 'style', 'noscript', 'svg', 'header', 'nav', 'footer', 'form', 'title', 'head'}
BLOCK = {'h1', 'h2', 'h3', 'h4', 'p', 'li', 'dt', 'dd', 'blockquote', 'td', 'button'}


class Localize(HTMLParser):
    """Rewrites a page in one language: an element's data-en/data-es replaces its content,
    the same swap main.js does in the browser."""

    def __init__(self, lang):
        super().__init__(convert_charrefs=False)
        self.lang, self.out, self.hide = lang, [], 0

    def handle_starttag(self, tag, attrs):
        if self.hide:
            if tag not in VOID:
                self.hide += 1
            return
        a = dict(attrs)
        self.out.append('<' + tag + ''.join(f' {k}="{escape(v or "", True)}"' for k, v in attrs) + '>')
        value = a.get('data-' + self.lang) or a.get('data-en')
        if value is not None and tag not in VOID:
            self.out.append(value)
            self.hide = 1
            self.tag = tag

    def handle_startendtag(self, tag, attrs):
        if not self.hide:
            self.out.append(self.get_starttag_text())

    def handle_endtag(self, tag):
        if self.hide:
            self.hide -= 1
            if self.hide:
                return
        self.out.append(f'</{tag}>')

    def handle_data(self, data):
        if not self.hide:
            self.out.append(data)

    def handle_entityref(self, name):
        self.handle_data(f'&{name};')

    def handle_charref(self, name):
        self.handle_data(f'&#{name};')


class Extract(HTMLParser):
    """Collects page sections (h1/h2 headings with their text blocks) and event cards."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip, self.depth = 0, 0
        self.block = None
        self.sections = [{'title': '', 'text': []}]
        self.events, self.event = [], None

    def handle_starttag(self, tag, attrs):
        if tag in VOID:
            return
        self.depth += 1
        a = dict(attrs)
        if tag in SKIP:
            self.skip += 1
        if self.skip:
            return
        classes = (a.get('class') or '').split()
        if tag == 'div' and 'event' in classes and a.get('data-date'):
            self.event = {'id': a.get('id', ''), 'date': a['data-date'], 'cat': a.get('data-cat', ''),
                          'title': '', 'desc': '', 'meta': '', '_depth': self.depth}
        if self.block is None and (tag in BLOCK or (tag == 'div' and 'meta' in classes)):
            self.block = [tag if tag in BLOCK else 'meta', self.depth, []]

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if tag in SKIP:
            self.skip -= 1
        if self.block and self.block[1] == self.depth:
            kind, _, parts = self.block
            self.block = None
            self.store(kind, clean(''.join(parts)).rstrip(' +'))
        if self.event and self.event['_depth'] == self.depth:
            self.event.pop('_depth')
            self.events.append(self.event)
            self.event = None
        self.depth -= 1

    def store(self, kind, text):
        if not re.search(r'\w', text or ''):
            return
        if self.event:
            key = {'h2': 'title', 'h3': 'title', 'p': 'desc', 'meta': 'meta'}.get(kind)
            if key and not self.event[key]:
                self.event[key] = text
            return
        if kind in ('h1', 'h2'):
            self.sections.append({'title': text, 'text': []})
        elif text not in self.sections[-1]['text']:
            self.sections[-1]['text'].append(text)

    def handle_data(self, data):
        if not self.skip and self.block:
            self.block[2].append(data)


def clean(s):
    return re.sub(r'\s+', ' ', unescape(re.sub(r'<[^>]+>', ' ', s or ''))).strip()


def localize(text, lang):
    p = Localize(lang)
    p.feed(text)
    p.close()
    return ''.join(p.out)


def extract(html):
    p = Extract()
    p.feed(html)
    p.close()
    return [s for s in p.sections if s['text']], p.events


def board(html):
    """Executive board: name, role and email from about.html's team cards."""
    people = []
    for card in re.findall(r'<div class="member">(.*?)</div>(?=<div class="member">|</div>)', html, re.S):
        name = re.search(r'<h4[^>]*>(.*?)</h4>', card, re.S)
        role = re.search(r'</h4>\s*<span[^>]*>(.*?)</span>', card, re.S)
        mail = re.search(r'href="mailto:([^"?]+)', card)
        photo = re.search(r'data-bg="url\((assets/img/[^)]+)\)"', card)
        if name:
            people.append({'name': clean(name.group(1)), 'role': clean(role.group(1)) if role else '',
                           'email': mail.group(1) if mail else 'ama@uprm.edu',
                           'photo': photo.group(1) if photo else ''})
    return people


def main():
    kb = {'generated': datetime.date.today().isoformat(), 'site': 'https://amauprm.org/',
          'contact': {'email': 'ama@uprm.edu', 'phone': '787-832-4040 ext. 3800',
                      'office': 'College of Business Administration (ADEM), UPR Mayagüez',
                      'instagram': 'https://www.instagram.com/amauprm/',
                      'linkedin': 'https://www.linkedin.com/in/ama-uprm-36a961203/',
                      'podcast_spotify': 'https://open.spotify.com/show/1tSlBHLMHbvfkaXzMGXZKU',
                      'youtube': 'https://www.youtube.com/@ama-uprm',
                      'calendar': 'https://calendar.google.com/calendar/render?cid=c_8a9abc0be7be501449cb1983c1c28db632aae9ac62fe2d7c57bed1a1c3b64962%40group.calendar.google.com',
                      'donate': 'https://www.uprm.edu/donaciones/cba/'},
          'pages': [], 'events': [], 'board': {}}
    for name in PAGES:
        path = ROOT / name
        if not path.exists():
            continue
        raw = path.read_text(encoding='utf-8')
        title = clean(re.search(r'<title>(.*?)</title>', raw, re.S).group(1))
        page = {'url': name, 'title': title}
        events = {}
        for lang in ('en', 'es'):
            html = localize(raw, lang)
            page[lang], events[lang] = extract(html)
            if name == 'about.html':
                kb['board'][lang] = board(html)
        kb['pages'].append(page)
        if name == 'events.html':
            for en, es in zip(events['en'], events['es']):
                kb['events'].append({'id': en['id'], 'date': en['date'], 'cat': en['cat'],
                                     'en': {k: en[k] for k in ('title', 'desc', 'meta')},
                                     'es': {k: es[k] for k in ('title', 'desc', 'meta')}})
            kb['events'].sort(key=lambda e: e['date'])
    # Chapter Plan facts and its tentative calendar, maintained by hand in scripts/rumi_plan.json.
    plan = ROOT / 'scripts' / 'rumi_plan.json'
    if plan.exists():
        kb['plan'] = {k: v for k, v in json.loads(plan.read_text(encoding='utf-8')).items() if not k.startswith('_')}
    # Curated FAQ (AMA national, campus terms, chapter vocabulary), maintained in scripts/rumi_faq.json.
    faq = ROOT / 'scripts' / 'rumi_faq.json'
    if faq.exists():
        kb['faq'] = json.loads(faq.read_text(encoding='utf-8'))['faq']
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(kb, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    words = sum(len(' '.join(s['text']).split()) for pg in kb['pages'] for s in pg['en'])
    print(f"wrote {OUT.relative_to(ROOT).as_posix()}: {len(kb['pages'])} pages, {len(kb['events'])} events, "
          f"{len(kb['board'].get('en', []))} board members, {len(kb.get('faq', []))} FAQ entries, ~{words} English words, "
          f"{OUT.stat().st_size // 1024} KB")


if __name__ == '__main__':
    main()
