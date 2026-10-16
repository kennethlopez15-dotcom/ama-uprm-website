"""Check mobile gesture cancellation and page wiring with synthetic events.
These checks do not reproduce native iPhone Safari pinch/rubber-band behavior.
"""
from pathlib import Path
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from threading import Thread
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args): pass
server = ThreadingHTTPServer(('127.0.0.1',0), partial(QuietHandler,directory=str(ROOT)))
Thread(target=server.serve_forever,daemon=True).start()
base = f'http://127.0.0.1:{server.server_port}/'
try:
    with sync_playwright() as pw:
        browser=pw.chromium.launch(channel='msedge',headless=True)
        context=browser.new_context(is_mobile=True,has_touch=True,viewport={'width':390,'height':844})
        context.route('**/*',lambda r:r.continue_() if r.request.url.startswith(base) else r.fulfill(status=200,body=''))
        page=context.new_page()
        errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        for file in sorted((p for p in ROOT.glob('*.html') if not p.name.startswith('google'))):
            page.goto(base+file.name,wait_until='domcontentloaded')
            results=page.evaluate('''() => {
                let scale=1;
                Object.defineProperty(visualViewport,'scale',{get:()=>scale});
                function event(type,props={}) {
                    const e=new Event(type,{bubbles:true,cancelable:true});
                    for(const [key,value] of Object.entries(props)) Object.defineProperty(e,key,{value});
                    document.body.dispatchEvent(e);return e.defaultPrevented;
                }
                const touches=d=>[{screenX:0,screenY:0},{screenX:d,screenY:0}];
                const checks=[];
                checks.push(!event('gesturestart'));
                checks.push(event('gesturechange',{scale:.8}));
                checks.push(!event('gesturechange',{scale:1.5}));
                event('gestureend');
                checks.push(!event('gesturechange',{scale:.5}));
                scale=2;event('gesturestart');
                checks.push(!event('gesturechange',{scale:.6}));
                checks.push(!event('gesturechange',{scale:.5}));
                checks.push(event('gesturechange',{scale:.4}));
                event('gestureend');
                scale=1;event('touchstart',{touches:touches(100)});
                checks.push(event('touchmove',{touches:touches(80)}));
                checks.push(!event('touchmove',{touches:touches(120)}));
                checks.push(!event('touchmove',{touches:[{screenX:0,screenY:20}]}));
                event('touchend',{touches:[]});
                checks.push(!event('touchmove',{touches:touches(40)}));
                scale=2;event('touchstart',{touches:touches(100)});
                checks.push(!event('touchmove',{touches:touches(60)}));
                checks.push(event('touchmove',{touches:touches(40)}));
                event('touchcancel');
                checks.push(!event('touchmove',{touches:touches(40)}));
                checks.push(!event('gesturechange',{scale:.1}));
                return checks;
            }''')
            assert all(results),(file.name,results)
            print('PASS:',file.name,'15 gesture checks',flush=True)
        assert not errors,errors
        # No touch handlers should interfere with browser zoom on desktop.
        desktop=browser.new_page(has_touch=False)
        desktop.route('**/*',lambda r:r.continue_() if r.request.url.startswith(base) else r.fulfill(status=200,body=''))
        desktop.goto(base,wait_until='domcontentloaded')
        assert desktop.evaluate('''()=>{
            document.dispatchEvent(new Event('gesturestart'));
            const e=new Event('gesturechange',{cancelable:true});
            Object.defineProperty(e,'scale',{value:.5});
            document.dispatchEvent(e);return !e.defaultPrevented;
        }''')
        browser.close()
        print('PASS: 195 synthetic mobile gesture checks; desktop gestures unchanged. Physical Safari verification still required.')
finally:
    server.shutdown()
