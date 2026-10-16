"""Verify real Edge tab zoom (50–400%), not CSS zoom or device emulation.
Requires Python Playwright and installed Edge. The temporary local extension only
sets browser tab zoom; all external requests are mocked.
"""
from pathlib import Path
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from threading import Thread
from tempfile import TemporaryDirectory
import json
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args): pass

def same_composition(actual, expected):
    # Browser zoom introduces subpixel rounding in track allocation.
    if isinstance(actual, list) and isinstance(expected, list):
        return len(actual) == len(expected) and all(same_composition(a,b) for a,b in zip(actual,expected))
    if isinstance(actual, (int,float)) and isinstance(expected, (int,float)):
        return abs(actual-expected) <= 1
    return actual == expected

server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(ROOT)))
Thread(target=server.serve_forever, daemon=True).start()
base = f'http://127.0.0.1:{server.server_port}/'
out = ROOT / '.validation'
out.mkdir(exist_ok=True)
try:
    with TemporaryDirectory(prefix='browser-zoom-', dir=out) as temp, sync_playwright() as pw:
        extension = Path(temp) / 'extension'
        extension.mkdir()
        (extension/'manifest.json').write_text(json.dumps({
            'manifest_version': 3, 'name': 'Local zoom verification', 'version': '1.0',
            'permissions': ['tabs'], 'background': {'service_worker': 'background.js'}
        }), encoding='utf-8')
        (extension/'background.js').write_text('chrome.runtime.onInstalled.addListener(() => {});', encoding='utf-8')
        context = pw.chromium.launch_persistent_context(
            str(Path(temp)/'profile'), channel='msedge', headless=True,
            args=[f'--disable-extensions-except={extension}', f'--load-extension={extension}'],
            viewport={'width':1440,'height':900}, locale='es-PR', reduced_motion='reduce')
        try:
            context.route('**/*', lambda r: r.continue_() if r.request.url.startswith(base) else r.fulfill(status=200, body=''))
            worker = context.service_workers[0] if context.service_workers else context.wait_for_event('serviceworker')
            page = context.pages[0]
            errors = []
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.goto(base)
            baseline = {}
            count = 0
            for lang in ['es','en']:
                page.evaluate('(lang)=>localStorage.setItem("ama-lang",lang)', lang)
                for zoom in [1,.8,.67,.5,1.25,1.5,2,3,4]:
                    actual = worker.evaluate('''async z => {
                        const [tab] = await chrome.tabs.query({active:true});
                        await chrome.tabs.setZoom(tab.id,z);
                        return await chrome.tabs.getZoom(tab.id);
                    }''', zoom)
                    assert abs(actual-zoom) < .001, (zoom, actual)
                    for file in sorted(ROOT.glob('*.html')):
                        label = (lang, zoom, file.name)
                        page.goto(base+file.name, wait_until='domcontentloaded')
                        page.evaluate('document.fonts.ready')
                        assert abs(page.evaluate('innerWidth')-1440/zoom) <= 2, label
                        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1'), (label,'page overflow')
                        clipped = page.evaluate('''() => [...document.querySelectorAll('main h1,main h2,main h3,main p,main button,main .btn,footer p,footer a')]
                            .filter(e=>e.clientWidth>0 && e.scrollWidth>e.clientWidth+2 && !e.matches('.sr-only'))
                            .map(e=>e.tagName+'.'+e.className)''')
                        assert not clipped, (label,'clipped content',clipped)
                        if page.locator('#burger').count():
                            if page.locator('#burger').is_visible():
                                page.locator('#burger').click()
                                assert page.locator('nav').evaluate('n=>{const r=n.getBoundingClientRect();return r.left>=-1&&r.right<=innerWidth+1&&n.scrollWidth<=n.clientWidth+2}'), (label,'menu overflow')
                                page.keyboard.press('Escape')
                            else:
                                assert page.locator('nav').evaluate('n=>n.getBoundingClientRect().left>=document.querySelector("header .logo").getBoundingClientRect().right'), (label,'header overlap')
                        # At zoom-out levels, content widths, typography and grid tracks stay stable.
                        fingerprint = page.evaluate('''() => [...document.querySelectorAll('main .container,main h1,main .grid-2,main .grid-3,main .steps,main .stats')].map(e=>{
                            const s=getComputedStyle(e);return [Math.round(e.getBoundingClientRect().width),Math.round(parseFloat(s.fontSize)),s.gridTemplateColumns.split(" ").map(v=>v.endsWith("px")?Math.round(parseFloat(v)):v)]
                        })''')
                        if zoom == 1: baseline[(lang,file.name)] = fingerprint
                        elif zoom < 1:
                            assert same_composition(fingerprint, baseline[(lang,file.name)]), (label,'zoom-out changed composition', [(a,b) for a,b in zip(fingerprint,baseline[(lang,file.name)]) if a!=b])
                        if file.name == 'programs.html':
                            assert page.locator('.steps-single').evaluate('e=>getComputedStyle(e).gridTemplateColumns.split(" ").length===1'), (label,'single-column program sequence')
                        if file.name == 'index.html':
                            assert page.locator('.hero').evaluate('h=>h.clientHeight>=h.querySelector(".hero-content").offsetHeight'), (label,'clipped hero')
                            if zoom <= 1:
                                assert page.locator('.hero').evaluate('h=>h.clientHeight<=900'), (label,'unbounded hero')
                            if lang == 'es' and zoom in [1,.5,2,4]:
                                page.screenshot(path=str(out/f'real-zoom-{round(zoom*100)}.png'))
                        count += 1
                    print(f'PASS: {lang}, actual browser zoom {zoom*100:g}%, all {len(list(ROOT.glob("*.html")))} pages', flush=True)
            assert not errors, errors
            print(f'PASS: {count} real browser zoom/page/language combinations; stable zoom-out composition, readable content, menus and no runtime errors.', flush=True)
        finally:
            context.close()
finally:
    server.shutdown()
