"""Responsive geometry checks shared by the browser regression runner.

Mocks external services. Font enlargement tests text resizing, not native browser
zoom; a 320 CSS-pixel viewport separately tests reflow. Real touch/keyboard and
third-party embed contents still require device checks.
"""
import json
from time import monotonic
from playwright.sync_api import expect

WIDTHS = (320, 390, 559, 560, 561, 768, 899, 900, 901, 1023, 1024,
          1025, 1199, 1200, 1201, 1440, 1920)

# Measure text itself as well as boxes: document.scrollWidth can hide defects
# when body or a card clips overflow. Decorative backgrounds are not content.
GEOMETRY = """() => {
  const issues = [], viewport = innerWidth;
  const visible = el => {
    const s = getComputedStyle(el), r = el.getBoundingClientRect();
    return r.width && r.height && s.visibility !== 'hidden' &&
      !el.closest('[hidden],.sr-only,.hp') && s.display !== 'none';
  };
  const label = el => el.tagName.toLowerCase() + (el.id ? '#'+el.id : '.'+String(el.className).trim().replaceAll(' ','.'));
  if (document.documentElement.scrollWidth > viewport + 1) issues.push('document overflow');
  const nodes = document.querySelectorAll('header a,header button,main h1,main h2,main h3,main h4,main p,main li,main span,main strong,main a,main button,main label,footer p,footer a');
  for (const el of nodes) {
    if (!visible(el) || el.closest('.ph,.hero-bg,.shape')) continue;
    if (el.closest('nav') && document.querySelector('#burger').getBoundingClientRect().height && !document.querySelector('nav.open')) continue;
    for (const text of el.childNodes) {
      if (text.nodeType !== Node.TEXT_NODE || !text.textContent.trim()) continue;
      const range = document.createRange(); range.selectNodeContents(text);
      for (const r of range.getClientRects()) {
        if (r.left < -1 || r.right > viewport + 1) issues.push(label(el)+': text outside viewport');
        for (let p=el; p && p !== document.body; p=p.parentElement) {
          const s=getComputedStyle(p), b=p.getBoundingClientRect();
          if (['hidden','clip','auto','scroll'].includes(s.overflowX) && (r.left < b.left-2 || r.right > b.right+2)) issues.push(label(el)+': text clipped by '+label(p));
          if (['hidden','clip'].includes(s.overflowY) && (r.top < b.top-2 || r.bottom > b.bottom+2)) issues.push(label(el)+': text vertically clipped by '+label(p));
        }
      }
    }
  }
  for (const grid of document.querySelectorAll('.grid-2,.grid-3,.grid-4,.stats,.packages,.footer-grid,.team-grid,.steps')) {
    const boxes=[...grid.children].filter(visible).map(e=>[e,e.getBoundingClientRect()]);
    for(let i=0;i<boxes.length;i++) for(let j=i+1;j<boxes.length;j++) {
      const [a,r]=boxes[i], [b,s]=boxes[j];
      if(Math.min(r.right,s.right)-Math.max(r.left,s.left)>2 && Math.min(r.bottom,s.bottom)-Math.max(r.top,s.top)>2) issues.push(label(a)+' overlaps '+label(b));
    }
  }
  for (const el of document.querySelectorAll('button,.btn,.event-controls select,input:not([type=hidden]),textarea,select')) {
    if(!visible(el) || el.closest('.hp')) continue;
    const r=el.getBoundingClientRect();
    if(r.width<43.5 || r.height<43.5) issues.push(label(el)+': target below 44px');
    if(el.matches('input,textarea,select') && parseFloat(getComputedStyle(el).fontSize)<16) issues.push(label(el)+': field text below 16px');
  }
  return [...new Set(issues)];
}"""


def run_responsive_checks(browser, base, root, engine, quick=False):
    out = root / '.validation' / 'responsive' / engine
    out.mkdir(parents=True, exist_ok=True)
    failures, cases = [], 0

    def mock(route):
        if route.request.url.startswith(base):
            route.continue_()
        else:
            route.fulfill(status=200, content_type='text/css' if 'fonts.googleapis.com' in route.request.url else 'text/html', body='')

    def record(page, name, issues):
        if issues:
            failures.append({'case': name, 'issues': issues})
            if len(failures) <= 3:
                print('FAIL:', name, issues[:8], flush=True)
            (out/'results.json').write_text(json.dumps({'browser':engine,'cases':cases,'failures':failures},ensure_ascii=False,indent=2),encoding='utf-8')
            # Bound diagnostic screenshots, retaining every failure in JSON.
            if len(failures) <= 12:
                page.screenshot(path=str(out / (name + '.png')), full_page=True)

    for motion in ('reduce', 'no-preference'):
        ctx = browser.new_context(viewport={'width':390,'height':844}, locale='es-PR', reduced_motion=motion)
        ctx.route('**/*', mock)
        # Disable analytics and remote submissions even if public config changes.
        ctx.route('**/assets/config.js', lambda r:r.fulfill(content_type='application/javascript', body='window.AMA_CONFIG={};'))
        page = ctx.new_page()
        runtime = []
        page.on('pageerror', lambda error: runtime.append(str(error)))
        page.goto(base)
        for width in ((320, 1201, 1920) if quick else WIDTHS):
            page.set_viewport_size({'width':width,'height':900})
            for file in sorted(root.glob('*.html')):
                for lang in ('es', 'en'):
                    page.evaluate('(lang)=>localStorage.setItem("ama-lang",lang)',lang)
                    page.goto(base+file.name)
                    page.add_style_tag(content='html{scroll-behavior:auto!important}')
                    expect(page.locator('html')).to_have_attribute('lang',lang)
                    # Settle real entrance animations, including off-screen sections,
                    # without changing layout or hiding animated content from checks.
                    page.evaluate("""() => {
                      document.querySelectorAll('.reveal,.reveal-left,.reveal-right,.stagger').forEach(e=>e.classList.add('visible','settled'));
                      document.getAnimations().forEach(a=>{if(a.effect.getComputedTiming().iterations!==Infinity) a.finish()});
                    }""")
                    record(page, f'{file.stem}-{width}-{lang}-{motion}', page.evaluate(GEOMETRY))
                    cases += 1
            print(f'CHECK: {engine}, {motion}, {width}px', flush=True)

        # Short/landscape viewports and text-only enlargement are separate cases.
        for width,height,enlarged in ((844,390,False),(1024,600,False),(320,640,True),(1201,800,True)):
            page.set_viewport_size({'width':width,'height':height})
            for file in sorted(root.glob('*.html')):
                for lang in ('es','en'):
                    page.evaluate('(lang)=>localStorage.setItem("ama-lang",lang)',lang)
                    page.goto(base+file.name)
                    page.add_style_tag(content='html{scroll-behavior:auto!important}')
                    expect(page.locator('html')).to_have_attribute('lang',lang)
                    if enlarged:
                        # Double each element's original computed font size, including
                        # px/em/rem/vw-based text, without compounding descendants.
                        page.evaluate("""() => {
                          const sizes=[...document.querySelectorAll('body *')].map(e=>[e,parseFloat(getComputedStyle(e).fontSize)]);
                          sizes.forEach(([e,n])=>e.style.fontSize=(n*2)+'px');
                        }""")
                        page.evaluate('() => new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))')
                    page.evaluate("""() => {
                      document.querySelectorAll('.reveal,.reveal-left,.reveal-right,.stagger').forEach(e=>e.classList.add('visible','settled'));
                      document.getAnimations().forEach(a=>{if(a.effect.getComputedTiming().iterations!==Infinity)a.finish()});
                    }""")
                    name=f'{file.stem}-{width}x{height}-{lang}-{motion}-text{200 if enlarged else 100}'
                    record(page,name,page.evaluate(GEOMETRY))
                    if page.locator('#burger').is_visible():
                        # This pass measures the final menu geometry; actual pointer
                        # clicks and keyboard behavior are exercised by the legacy suite.
                        page.locator('#burger').evaluate('e=>e.click()')
                        expect(page.locator('#burger')).to_have_attribute('aria-expanded','true')
                        page.evaluate("document.getAnimations().forEach(a=>{if(a.effect.getComputedTiming().iterations!==Infinity)a.finish()})")
                        last=page.locator('[data-lang=es]')
                        last.scroll_into_view_if_needed()
                        bounds=last.bounding_box()
                        record(page,name+'-menu', [] if bounds and bounds['y']>=0 and bounds['y']+bounds['height']<=height+1 else ['last menu control outside viewport'])
                        record(page,name+'-menu-targets',page.locator('#nav button').evaluate_all("els=>els.filter(e=>{const r=e.getBoundingClientRect();return r.width<43.5||r.height<43.5}).map(e=>e.outerHTML)"))
                        page.keyboard.press('Escape')
                        expect(page.locator('#burger')).to_be_focused()
                        record(page,name+'-closed-menu-focus', ['closed submenu takes focus'] if page.locator('#nav .dropdown a').first.evaluate('e=>{e.focus();return document.activeElement===e}') else [])
                    # Focused fields must remain reachable above a reduced viewport.
                    for field in page.locator('.contact-form input:not(.hp),.contact-form textarea,.contact-form button').all():
                        if not field.is_visible(): continue
                        field.focus(); field.scroll_into_view_if_needed()
                        rect=field.bounding_box()
                        header=page.locator('header').bounding_box()
                        record(page,name+'-focus',[] if rect and rect['y'] >= header['height']-1 and rect['y']+rect['height']<=height+1 else ['focused form control obscured'])
                    cases+=1
            print(f'CHECK: {engine}, {motion}, {width}x{height}, text {200 if enlarged else 100}%',flush=True)
        record(page,'runtime-'+motion,runtime)
        ctx.close()

    # Native touch emulation checks the absence of stuck pointer-only effects.
    print(f'CHECK: {engine}, touch input',flush=True)
    ctx=browser.new_context(viewport={'width':390,'height':844},has_touch=True,reduced_motion='reduce')
    ctx.route('**/*',mock)
    page=ctx.new_page();page.goto(base+'index.html')
    card=page.locator('.card').first
    card.scroll_into_view_if_needed();card.tap(position={'x':10,'y':10})
    record(page,'touch-card',[] if card.evaluate("e=>getComputedStyle(e).transform==='none'") else ['hover transform sticks after touch'])
    ctx.close()

    # Fixed utility controls must not cover a third-party embed's own controls.
    print(f'CHECK: {engine}, embed controls',flush=True)
    ctx=browser.new_context(viewport={'width':320,'height':640},reduced_motion='reduce')
    ctx.route('**/*',mock)
    page=ctx.new_page()
    for file in ('about.html','events.html','programs.html'):
        page.goto(base+file)
        page.add_style_tag(content='html{scroll-behavior:auto!important}')
        page.locator('.embed').scroll_into_view_if_needed()
        expect(page.locator('#toTop')).to_have_attribute('aria-hidden','true')
        expect(page.locator('#toTop')).to_have_css('pointer-events','none')
    ctx.close()

    # Content photos must work with JavaScript disabled and choose a real asset.
    print(f'CHECK: {engine}, native photos without JavaScript',flush=True)
    ctx=browser.new_context(viewport={'width':390,'height':844},java_script_enabled=False)
    ctx.route('**/*',mock)
    page=ctx.new_page()
    loaded_photos=set()
    page.on('response',lambda response: loaded_photos.add(response.url) if response.status==200 and response.request.resource_type=='image' else None)
    for file in ('index.html','about.html','blog.html','blog-post.html','programs.html','sponsors.html'):
        loaded_photos.clear()
        page.goto(base+file)
        photos=page.locator('.photo-frame img')
        record(page,file+'-native-photos',[] if photos.count() else ['native content photo missing'])
        for photo in photos.all():
            photo.scroll_into_view_if_needed()
            if engine == 'firefox':
                # Firefox disables main-world evaluation with JS disabled. Verify
                # native selection/load through image responses instead of a JS
                # property assertion (which hangs on that engine).
                candidates=[base+c.strip().split()[0] for c in photo.get_attribute('srcset').split(',')]
                deadline=monotonic()+5
                while not any(url in loaded_photos for url in candidates) and monotonic()<deadline:
                    page.wait_for_timeout(100)
                assert any(url in loaded_photos for url in candidates), (file,'native image request missing')
                assert photo.get_attribute('sizes') and photo.bounding_box()['width']>0
            else:
                expect(photo).to_have_js_property('complete',True)
                assert photo.evaluate('e=>e.naturalWidth>0 && e.hasAttribute("srcset") && e.hasAttribute("sizes") && e.width>0'), (file,'responsive image failed')
    ctx.close()

    result={'browser':engine,'cases':cases,'external_services':'mocked','failures':failures}
    (out/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'{"FAIL" if failures else "PASS"}: {engine}: {cases} responsive cases; {len(failures)} failures. Report: {out / "results.json"}',flush=True)
    assert not failures, f'{len(failures)} responsive failures; see {out / "results.json"}'
