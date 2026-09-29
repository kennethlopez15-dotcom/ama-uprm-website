"""Browser regression checks; requires playwright, html5lib and installed Edge.
External services are mocked. No real emails, registrations or analytics hits.
Run: python scripts/browser_checks.py
"""
from pathlib import Path
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from threading import Thread
import json
import re
import html5lib
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args): pass
server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(ROOT)))
Thread(target=server.serve_forever, daemon=True).start()
base = f'http://127.0.0.1:{server.server_port}/'
count = 0
def passed(label):
    global count
    count += 1
    print('PASS:', label, flush=True)
def intercept(route):
    if route.request.url.startswith(base): route.continue_()
    else: route.fulfill(status=200, content_type='text/css' if 'fonts.googleapis.com' in route.request.url else 'text/html', body='')
def translate(page, lang):
    if page.locator('#burger').is_visible(): page.locator('#burger').click()
    page.locator(f'[data-lang={lang}]').click()
    if page.locator('#burger').is_visible(): page.keyboard.press('Escape')
    expect(page.locator('html')).to_have_attribute('lang', lang)

try:
    for file in ROOT.glob('*.html'):
        parser = html5lib.HTMLParser()
        parser.parse(file.read_text(encoding='utf-8'))
        assert not parser.errors, (file.name, parser.errors)
    passed('HTML5 parser: all pages')
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel='msedge', headless=True)
        context = browser.new_context(locale='es-PR', viewport={'width':1440,'height':900}, reduced_motion='reduce')
        context.route('**/*', intercept)
        page = context.new_page()
        runtime = []
        page.on('pageerror', lambda e:runtime.append(str(e)))
        page.on('console', lambda m:runtime.append(m.text) if m.type=='error' else None)
        page.clock.set_fixed_time('2026-09-29T12:00:00Z')
        page.goto(base)
        expect(page.locator('html')).to_have_attribute('lang','es')
        assert page.evaluate("localStorage.getItem('ama-lang')") is None
        expect(page.locator('#home-events .event')).to_have_count(1)
        expect(page.locator('#home-events')).to_contain_text('Feria de empleo')
        assert not page.locator('script[src*="googletagmanager"]').count()
        passed('Browser language, automatic choice not stored, current home event, GA disabled')
        translate(page,'en')
        assert page.evaluate("localStorage.getItem('ama-lang')") == 'en'
        page.goto(base+'membership.html')
        expect(page.locator('html')).to_have_attribute('lang','en')
        faq = page.locator('.faq button')
        faq.nth(0).focus(); page.keyboard.press('Enter')
        expect(faq.nth(0)).to_have_attribute('aria-expanded','true')
        expect(page.locator('#faq-answer-0')).to_be_visible()
        faq.nth(1).focus(); page.keyboard.press('Space')
        expect(page.locator('#faq-answer-0')).to_be_hidden()
        expect(page.locator('#faq-answer-1')).to_be_visible()
        page.keyboard.press('Space'); expect(page.locator('#faq-answer-1')).to_be_hidden()
        passed('Manual persistence across pages and FAQ keyboard/ARIA/visibility')
        page.goto(base+'events.html')
        expect(page.locator('.event.past')).to_have_count(7)
        page.locator('#event-status').select_option('upcoming')
        expect(page.locator('.event:visible')).to_have_count(1)
        page.locator('[data-filter=service]').click()
        expect(page.locator('#no-events')).to_be_visible()
        page.locator('[data-filter=all]').click(); page.locator('#event-status').select_option('past')
        expect(page.locator('.event:visible')).to_have_count(7)
        translate(page,'es')
        expect(page.locator('.completed-tag').first).to_have_text('Evento finalizado')
        page.clock.set_fixed_time('2026-10-03T12:00:00Z'); page.reload()
        expect(page.locator('.event.past')).to_have_count(8)
        expect(page.locator('#no-upcoming')).to_be_visible()
        passed('Dates, category/status filters, empty states and dynamic translations')
        tz = browser.new_context(locale='en-US', timezone_id='Asia/Tokyo'); tz.route('**/*', intercept)
        tp = tz.new_page(); tp.clock.set_fixed_time('2026-10-02T02:00:00Z'); tp.goto(base+'events.html')
        assert not tp.locator('#e-job-fair').evaluate("e=>e.classList.contains('past')")
        tz.close(); passed('Event day boundaries use Puerto Rico timezone')
        page.goto(base); page.locator('[role=tab]').first.focus(); page.keyboard.press('End')
        expect(page.locator('[data-aud=alumni][role=tab]')).to_have_attribute('aria-selected','true')
        expect(page.locator('[data-aud=alumni][role=tabpanel]')).to_be_visible()
        page.keyboard.press('ArrowRight')
        expect(page.locator('[data-aud=student][role=tab]')).to_be_focused()
        page.keyboard.press('End'); page.keyboard.press('Home')
        expect(page.locator('[data-aud=student][role=tab]')).to_be_focused()
        passed('Audience tab roles and arrow/Home/End navigation')
        page.set_viewport_size({'width':390,'height':844})
        burger = page.locator('#burger'); burger.click()
        expect(burger).to_have_attribute('aria-expanded','true')
        assert page.evaluate("document.body.classList.contains('menu-open')")
        expect(page.locator('#nav a').first).to_be_focused()
        page.keyboard.press('Shift+Tab'); expect(burger).to_be_focused()
        page.keyboard.press('Shift+Tab'); expect(page.locator('[data-lang=es]')).to_be_focused()
        page.keyboard.press('Escape'); expect(burger).to_be_focused()
        expect(burger).to_have_attribute('aria-expanded','false')
        expect(page.locator('body')).not_to_have_class(re.compile(r'\bmenu-open\b'))
        burger.click(); page.locator('#nav a[href="about.html#mission"]').click()
        expect(page.locator('#burger')).to_have_attribute('aria-expanded','false')
        page.locator('#burger').click(); page.locator('#nav a[href="about.html#team"]').click()
        expect(page.locator('#team')).to_be_focused()
        page.locator('#burger').click(); page.set_viewport_size({'width':1440,'height':900})
        expect(page.locator('body')).not_to_have_class(re.compile(r'\bmenu-open\b'))
        page.locator('#nav > ul > li > a[href="about.html"]').focus()
        expect(page.locator('#nav a[href="about.html#team"]')).to_be_visible()
        passed('Mobile menu focus, Escape, link navigation, resize and keyboard dropdown')
        for width in (320,390,768,1024,1440):
            page.set_viewport_size({'width':width,'height':900})
            for file in sorted(ROOT.glob('*.html')):
                page.goto(base+file.name)
                for lang in ('es','en'):
                    translate(page,lang)
                    assert not page.evaluate('document.documentElement.scrollWidth > innerWidth + 1'), (file.name,width,lang,'overflow')
                    bad = page.locator('a').evaluate_all("els=>els.filter(a=>!a.textContent.trim()&&!a.getAttribute('aria-label')&&!a.getAttribute('aria-labelledby')&&!a.querySelector('[aria-label],img[alt]')).map(a=>a.outerHTML)")
                    assert not bad, (file.name,bad)
                assert page.locator('#preloader').evaluate("e=>getComputedStyle(e).visibility==='hidden'")
        assert not runtime, runtime
        passed('110 page/width/language combinations: no overflow, unnamed links or console/runtime errors')
        page.goto(base); page.evaluate('window.scrollTo(0,500)')
        assert page.locator('.hero-content').evaluate('e=>!e.style.transform')
        assert page.locator('[data-count] .counter-value').first.inner_text() == '120+'
        expect(page.locator('[data-count] .sr-only').first).to_have_text('120+')
        passed('Reduced motion disables hero parallax and renders counters instantly')
        context.close()
        # Graceful fallback if JavaScript or observer APIs are unavailable.
        ctx=browser.new_context(java_script_enabled=False, reduced_motion='reduce', viewport={'width':390,'height':900}); ctx.route('**/*',intercept)
        pg=ctx.new_page(); pg.goto(base+'membership.html')
        expect(pg.locator('#nav a[href="membership.html"]')).to_be_visible()
        expect(pg.locator('.faq .a').first).to_be_visible()
        expect(pg.locator('#preloader')).to_be_hidden()
        pg.goto(base); expect(pg.locator('.aud-panel:visible')).to_have_count(4)
        ctx.close()
        # Intercept the mailto navigation in a lexical test adapter; no mail app opens.
        ctx=browser.new_context(locale='en-US');ctx.route('**/*',intercept)
        contact_script='(function(location){'+(ROOT/'assets/main.js').read_text(encoding='utf-8')+'})({pathname:"/about.html",set href(value){window.testMailDraft=value}});'
        ctx.route('**/assets/main.js',lambda r:r.fulfill(content_type='application/javascript',body=contact_script))
        pg=ctx.new_page();pg.goto(base+'about.html')
        pg.locator('[name=name]').fill('Test & review')
        pg.locator('[name=email]').fill('test@example.invalid')
        pg.locator('[name=message]').fill('First line\nSecond & line')
        pg.locator('.contact-form button').click()
        draft=pg.evaluate('window.testMailDraft')
        from urllib.parse import urlsplit,parse_qs
        fields=parse_qs(urlsplit(draft).query)
        assert fields['subject']==['AMA UPRM contact']
        assert 'Test & review' in fields['body'][0] and 'First line\nSecond & line' in fields['body'][0]
        ctx.close();passed('Contact creates an encoded email draft without sending or opening a mail app')
        ctx=browser.new_context(locale='en-US');ctx.route('**/*',intercept)
        ctx.add_init_script('delete window.IntersectionObserver')
        pg=ctx.new_page();pg.goto(base)
        expect(pg.locator('[data-count] .counter-value').first).to_have_text('120+')
        assert pg.locator('[data-bg]').first.evaluate('e=>Boolean(e.style.backgroundImage)')
        pg.set_viewport_size({'width':390,'height':844});pg.locator('#burger').click()
        expect(pg.locator('#nav a').first).to_be_focused()
        pg.keyboard.press('Escape');ctx.close()
        passed('No-JS reading/navigation, no-IntersectionObserver fallback and menu with normal motion')
        for locale,saved,expected in [('en-US',None,'en'),('fr-FR',None,'en'),('es-MX','invalid','es'),('es-PR','en','en')]:
            ctx = browser.new_context(locale=locale); ctx.route('**/*',intercept)
            if saved: ctx.add_init_script('localStorage.setItem("ama-lang",'+json.dumps(saved)+')')
            pg=ctx.new_page(); pg.goto(base+'programs.html'); expect(pg.locator('html')).to_have_attribute('lang',expected); ctx.close()
        ctx=browser.new_context(locale='fr-FR'); ctx.route('**/*',intercept)
        ctx.add_init_script("Object.defineProperty(navigator,'languages',{get:()=>['fr-FR','es-PR','en-US']});Object.defineProperty(window,'localStorage',{get:()=>{throw new Error('Blocked')}})")
        pg=ctx.new_page(); pg.goto(base); expect(pg.locator('html')).to_have_attribute('lang','es'); translate(pg,'en'); ctx.close()
        passed('Locale fallback, invalid/saved preferences, language order and blocked storage')
        ctx=browser.new_context(locale='en-US'); ctx.route('**/*',intercept)
        ctx.route('**/assets/config.js',lambda r:r.fulfill(content_type='application/javascript',body="window.AMA_CONFIG={analyticsId:'G-TEST12345'};"))
        pg=ctx.new_page()
        pg.goto(base+'events.html'); pg.clock.set_fixed_time('2026-09-29T12:00:00Z'); pg.reload()
        pg.evaluate("document.addEventListener('click',e=>{if(e.target.closest('a'))e.preventDefault();},true)")
        pg.locator('#e-job-fair a').click()
        assert pg.evaluate("dataLayer.filter(x=>x[1]==='event_calendar_click').length")==1
        assert pg.evaluate("dataLayer.filter(x=>x[1]==='event_rsvp_click').length")==0
        passed('Mocked calendar click tracking with analytics enabled')
        ctx.close()
        out=ROOT/'.validation'; out.mkdir(exist_ok=True)
        ctx=browser.new_context(locale='es-PR',reduced_motion='reduce'); ctx.route('**/*',intercept)
        pg=ctx.new_page(); pg.clock.set_fixed_time('2026-09-29T12:00:00Z')
        for file,width in [('index.html',1440),('index.html',390),('events.html',390),('membership.html',390)]:
            pg.set_viewport_size({'width':width,'height':900}); pg.goto(base+file)
            for y in range(0,pg.evaluate('document.body.scrollHeight'),600):
                pg.evaluate('(y)=>scrollTo(0,y)',y); pg.wait_for_timeout(20)
            pg.evaluate('scrollTo(0,0)'); pg.screenshot(path=str(out/f'{file}-{width}.png'),full_page=True)
        ctx.close(); browser.close()
finally:
    server.shutdown()
print(f'PASS: {count} groups. Screenshots in .validation/. External requests mocked; no real submissions.')
