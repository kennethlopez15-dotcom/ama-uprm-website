"""Read-only live-font/embed review. No submissions or analytics are sent.

Run separately from browser_checks.py because network availability is external.
Uses installed Edge; saves screenshots and a factual network report in .validation.
"""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import json
import re
from playwright.sync_api import sync_playwright, expect, TimeoutError as PlaywrightTimeout

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'.validation'/'live-responsive'
OUT.mkdir(parents=True,exist_ok=True)


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self,*args): pass


server=ThreadingHTTPServer(('127.0.0.1',0),partial(QuietHandler,directory=str(ROOT)))
Thread(target=server.serve_forever,daemon=True).start()
base=f'http://127.0.0.1:{server.server_port}/'
results=[]
try:
    with sync_playwright() as pw:
        browser=pw.chromium.launch(channel='msedge',headless=True)
        ctx=browser.new_context(locale='es-PR',reduced_motion='reduce')
        ctx.route('**/assets/config.js',lambda r:r.fulfill(content_type='application/javascript',body='window.AMA_CONFIG={};'))
        for filename in ('index.html','about.html','events.html','membership.html','sponsors.html','blog-post.html','programs.html'):
            viewports=[(390,844),(1440,900)]
            if filename in ('about.html','events.html','programs.html'):
                viewports += [(320,640),(844,390)]
            for width,height in viewports:
                page=ctx.new_page()
                result={'page':filename,'width':width,'responses':[],'failed_requests':[],'errors':[]}
                page.on('response',lambda response,r=result:r['responses'].append({'url':response.url,'status':response.status}) if not response.url.startswith(base) else None)
                page.on('requestfailed',lambda request,r=result:r['failed_requests'].append({'url':request.url,'reason':request.failure}))
                page.on('pageerror',lambda error,r=result:r['errors'].append(str(error)))
                page.set_viewport_size({'width':width,'height':height})
                page.goto(base+filename,wait_until='domcontentloaded')
                try:
                    # The home page preloads its font stylesheet asynchronously:
                    # status=loaded alone can be true before any font is registered.
                    page.wait_for_function('document.fonts.size > 0 && document.fonts.status === "loaded"',timeout=15000)
                    page.evaluate('async()=>{await document.fonts.load(\'400 16px "Montserrat"\');await document.fonts.load(\'700 32px "Playfair Display"\');await document.fonts.ready}')
                    result['fonts']=page.evaluate('[...document.fonts].map(f=>({family:f.family,status:f.status}))')
                except PlaywrightTimeout:
                    result['fonts']='timeout'
                page.add_style_tag(content='html{scroll-behavior:auto!important}')
                for y in range(0,page.evaluate('document.body.scrollHeight'),650):
                    page.evaluate('(y)=>scrollTo(0,y)',y)
                    page.wait_for_timeout(30)
                if filename=='events.html':
                    page.locator('.embed-load').click()
                for frame in page.locator('iframe').all():
                    frame.scroll_into_view_if_needed()
                    try:
                        src=frame.get_attribute('src')
                        # Maps redirects its embed URL. Follow the element's frame,
                        # rather than requiring an exact final URL match.
                        child=frame.element_handle().content_frame()
                        child.wait_for_url(lambda url:url!='about:blank',wait_until='domcontentloaded',timeout=20000)
                        child.wait_for_load_state('load',timeout=20000)
                        # Use Playwright's isolated locator checks; Google's
                        # Trusted Types policy rejects main-world string eval.
                        expect(child.locator('body')).to_contain_text(re.compile(r'\S'),timeout=15000)
                        result.setdefault('embed_documents',[]).append({'url':child.url,'body_text_length':len(child.locator('body').inner_text())})
                        page.wait_for_timeout(2000)
                    except PlaywrightTimeout:
                        result['errors'].append('iframe window timeout')
                    result.setdefault('embeds',[]).append({'src':frame.get_attribute('src'),'box':frame.bounding_box()})
                    frame.screenshot(path=str(OUT/f'{Path(filename).stem}-{width}-embed.png'),animations='disabled')
                page.evaluate('scrollTo(0,0)')
                result['overflow']=page.evaluate('document.documentElement.scrollWidth>innerWidth+1')
                page.screenshot(path=str(OUT/f'{Path(filename).stem}-{width}.png'),full_page=True,animations='disabled')
                results.append(result)
                print(f'LIVE: {filename}, {width}px, overflow={result["overflow"]}, failed requests={len(result["failed_requests"])}',flush=True)
                page.close()
        ctx.close();browser.close()
finally:
    server.shutdown()
    (OUT/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
print(f'Live evidence: {OUT}')
