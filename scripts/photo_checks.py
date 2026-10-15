"""Check the three chapter photos at phone/desktop sizes, including without JS."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from time import monotonic

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(ROOT)))
Thread(target=server.serve_forever, daemon=True).start()
base = f'http://127.0.0.1:{server.server_port}/'
try:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel='msedge', headless=True)
        for width, scale in [(320, 2), (390, 3), (768, 2), (1440, 1)]:
            for js in [True, False]:
                context = browser.new_context(viewport={'width': width, 'height': 844},
                                              device_scale_factor=scale, java_script_enabled=js,
                                              reduced_motion='reduce')
                context.route('**/*', lambda r: r.continue_() if r.request.url.startswith(base)
                              else r.fulfill(status=200, body=''))
                page = context.new_page()
                for name in ['events', 'membership', 'programs']:
                    page.goto(base + name + '.html')
                    photo = page.locator('.photo-band img')
                    photo.evaluate('(img) => img.scrollIntoView({behavior: "instant", block: "center"})')
                    deadline = monotonic() + 10
                    while not photo.evaluate('(img) => img.complete && img.naturalWidth > 0') and monotonic() < deadline:
                        page.wait_for_timeout(100)
                    assert photo.evaluate('(img) => img.complete && img.naturalWidth > 0 && img.naturalHeight > 0')
                    box = photo.bounding_box()
                    assert box and box['height'] > 100 and box['width'] <= width
                    assert photo.is_visible()
                    assert box['x'] >= 0 and box['x'] + box['width'] <= width
                context.close()
                print(f'PASS: three photos, {width}px, {scale}x, JS={js}', flush=True)
        browser.close()
finally:
    server.shutdown()
