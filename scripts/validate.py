"""Validate this static site with Python's standard library: python scripts/validate.py."""
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
import json
import re
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = 'https://www.amauprm.org'
errors = []

def check(ok, message):
    if not ok:
        errors.append(message)

class Page(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.tags = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))
        keys = [k for k, _ in attrs]
        check(len(set(keys)) == len(keys), f'Duplicate attributes: {tag} {keys}')

    handle_startendtag = handle_starttag

    def select(self, tag, **attrs):
        return [a for t, a in self.tags if t == tag and all(a.get(k) == v for k, v in attrs.items())]

texts = {p.name: p.read_text(encoding='utf-8') for p in ROOT.glob('*.html')}
pages = {name: Page(text) for name, text in texts.items()}
references = 0
schemas = 0
for name, page in pages.items():
    text = texts[name]
    ids = [a['id'] for _, a in page.tags if 'id' in a]
    check(len(ids) == len(set(ids)), f'{name}: duplicate IDs')
    check(len(page.select('h1')) == 1, f'{name}: expected one h1')
    check(len(page.select('main')) == 1, f'{name}: expected one main')
    for kind, key, value in [('link', 'rel', 'canonical'), ('meta', 'name', 'description'), ('meta', 'property', 'og:title'), ('meta', 'property', 'og:description'), ('meta', 'property', 'og:image'), ('meta', 'property', 'og:url'), ('meta', 'name', 'twitter:card'), ('meta', 'name', 'twitter:image')]:
        check(len(page.select(kind, **{key:value})) == 1, f'{name}: missing/duplicate {value}')
    expected = ORIGIN + ('/' if name == 'index.html' else '/' + name)
    check(page.select('link', rel='canonical')[0].get('href') == expected, f'{name}: canonical mismatch')
    check(page.select('meta', property='og:url')[0].get('content') == expected, f'{name}: OG URL mismatch')
    check('G-XXXXXXXXXX' not in text, f'{name}: live placeholder GA ID')
    check('images.unsplash.com' not in text, f'{name}: stock photo still presented as chapter content')
    for tag, attrs in page.tags:
        check('data-en' not in attrs or 'data-es' in attrs, f'{name}: missing ES text on {tag}')
        if tag == 'img': check('alt' in attrs, f'{name}: image without alt')
        if tag == 'iframe': check(bool(attrs.get('title')), f'{name}: iframe without title')
        if tag == 'a' and attrs.get('target') == '_blank':
            check('noopener' in attrs.get('rel', ''), f'{name}: unsafe new tab')
        refs = [attrs[k] for k in ('href', 'src') if attrs.get(k)]
        for key in ('data-bg', 'style'):
            refs += re.findall(r'url\([\'\"]?([^\)\'\"]+)', attrs.get(key,''))
        if tag == 'meta' and attrs.get('property', attrs.get('name','')) in ('og:image','twitter:image'):
            refs.append(attrs['content'])
        # Translated rich text is parsed separately so broken hrefs cannot hide in attributes.
        for key in ('data-en','data-es'):
            if attrs.get(key):
                nested = Page(attrs[key])
                refs += [a['href'] for t,a in nested.tags if t == 'a' and a.get('href')]
        for ref in refs:
            url = urlsplit(ref)
            if url.scheme and not ref.startswith(ORIGIN + '/'):
                continue
            if url.netloc and url.netloc != 'www.amauprm.org': continue
            target = unquote(url.path).lstrip('/') or name
            if ref == ORIGIN + '/': target = 'index.html'
            if target.endswith('/'): target += 'index.html'
            check((ROOT/target).is_file(), f'{name}: missing local target {ref}')
            if url.fragment and target in pages:
                target_ids = {a.get('id') for _,a in pages[target].tags}
                check(unquote(url.fragment) in target_ids, f'{name}: missing anchor {ref}')
            references += 1
    for raw in re.findall(r'<script type="application/ld\+json">(.*?)</script>',text,re.S):
        try:
            data = json.loads(raw)
            items = data if isinstance(data,list) else [data]
            schemas += len(items)
            for item in items:
                check('@type' in item and '@context' in item, f'{name}: incomplete JSON-LD')
                if item.get('@type') == 'Organization':
                    check(item['logo'].endswith('/assets/img/logo-full.png'), f'{name}: wrong organization logo')
        except (ValueError, KeyError) as e: errors.append(f'{name}: invalid JSON-LD: {e}')

navs = {re.search(r'<nav\b.*?</nav>',s,re.S)[0] for s in texts.values()}
footers = {re.sub(r'h[23]', 'h2', re.search(r'<footer>.*?</footer>',s,re.S)[0]) for s in texts.values()}
check(len(navs) == 1, 'Navigation has drifted between pages')
check(len(footers) == 1, 'Footer has drifted between pages')
manifest = json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))
check((ROOT/manifest['start_url']).is_file(), 'Invalid manifest start_url')
for icon in manifest['icons']: check((ROOT/icon['src']).is_file(), f'Missing icon: {icon}')
check(manifest['display'] == 'browser', 'Manifest promises an app experience without offline support')
sitemap = ET.parse(ROOT/'sitemap.xml')
urls = [e.text for e in sitemap.findall('.//{*}loc')]
expected = {ORIGIN+('/' if name=='index.html' else '/'+name) for name in texts if name!='404.html'}
check(set(urls) == expected and len(urls)==len(expected), 'Sitemap mismatch')
robots=(ROOT/'robots.txt').read_text(encoding='utf-8')
check('Disallow: /' not in robots and ORIGIN+'/sitemap.xml' in robots, 'robots.txt blocks site or has wrong sitemap')
check(len(pages['events.html'].select('div', **{'class':'event'})) == 8, 'The eight existing official events must remain')
check(not list(ROOT.glob('assets/*.pdf')), 'Unexpected PDF: verify it is not a restored placeholder')

if errors:
    print('\n'.join(errors))
    sys.exit(1)
print(f'PASS: {len(pages)} pages, {references} local references, {schemas} schema objects, EN/ES links, shared navigation/footer, manifest, sitemap and robots.')
