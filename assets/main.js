/* AMA UPRM — shared behaviour */
(function () {
  'use strict';

  var config = window.AMA_CONFIG || {};
  var refreshNavigation = function () {};
  var motion = window.matchMedia('(prefers-reduced-motion: reduce)');
  var analyticsId = config.analyticsId || '';
  var analyticsEnabled = /^G-[A-Z0-9]+$/.test(analyticsId) && !/X{5,}/.test(analyticsId);
  // Keep Analytics to real visitors: never count automated browsers (our own checks) or local
  // test servers, and let the team opt a device out once with ?notrack (undo with ?track).
  (function () {
    var NOTRACK = 'ama-notrack';
    try {
      var q = new URLSearchParams(location.search);
      if (q.has('notrack')) localStorage.setItem(NOTRACK, '1');
      if (q.has('track')) localStorage.removeItem(NOTRACK);
      if (q.has('notrack') || q.has('track')) {
        q.delete('notrack'); q.delete('track');
        var rest = q.toString();
        history.replaceState(null, '', location.pathname + (rest ? '?' + rest : '') + location.hash);
      }
      if (localStorage.getItem(NOTRACK) === '1') analyticsEnabled = false;
    } catch (e) { /* storage blocked: tracking stays as configured */ }
    if (!config.analyticsInTests && (navigator.webdriver || /^(localhost|127\.0\.0\.1|\[::1\]|)$/.test(location.hostname) || /\.(localhost|test)$/.test(location.hostname))) analyticsEnabled = false;
  })();
  if (analyticsEnabled) {
    window.dataLayer = window.dataLayer || [];
    window.gtag = window.gtag || function () { window.dataLayer.push(arguments); };
    window.gtag('js', new Date());
    window.gtag('config', analyticsId);
    // gtag.js is ~176 KB and blocks the main thread while it runs, so fetch it once the
    // page has loaded and the browser is idle. Calls made earlier wait in dataLayer.
    var loadAnalytics = function () {
      var analytics = document.createElement('script');
      analytics.async = true;
      analytics.src = 'https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(analyticsId);
      document.head.appendChild(analytics);
    };
    var whenIdle = function () {
      if ('requestIdleCallback' in window) requestIdleCallback(loadAnalytics, { timeout: 3000 });
      else setTimeout(loadAnalytics, 1500);
    };
    if (document.readyState === 'complete') whenIdle();
    else window.addEventListener('load', whenIdle, { once: true });
  }

  /* ---------- KPI tracking (Strategic Alignment & Performance) ---------- */
  function trackEvent(name, params) {
    if (analyticsEnabled && typeof window.gtag === 'function') window.gtag('event', name, params || {});
  }

  /* data-bg may use image-set() for sharp screens; browsers without it get the first (1x) url. */
  function bgValue(el) {
    var v = el.dataset.bg;
    if (v.indexOf('image-set(') === 0 && !(window.CSS && CSS.supports && CSS.supports('background-image', v))) {
      v = (v.match(/url\([^)]*\)/) || [v])[0];
    }
    return v;
  }

  /* ---------- Language: saved manual choice, browser preferences, EN fallback ---------- */
  var LANG_KEY = 'ama-lang';
  function getLang() {
    try {
      var saved = localStorage.getItem(LANG_KEY);
      if (saved === 'en' || saved === 'es') return saved;
    } catch (e) { /* Storage may be blocked; manual switching still works. */ }
    var preferred = navigator.languages && navigator.languages.length ? navigator.languages : [navigator.language || 'en'];
    for (var i = 0; i < preferred.length; i++) {
      var base = preferred[i].toLowerCase().split('-')[0];
      if (base === 'es' || base === 'en') return base;
    }
    return 'en';
  }
  function setLang(lang, manual, root) {
    if (lang !== 'en' && lang !== 'es') return;
    if (manual) { try { localStorage.setItem(LANG_KEY, lang); } catch (e) {} trackEvent('language_change', { language: lang }); }
    document.documentElement.lang = lang;
    (root || document).querySelectorAll('[data-en]').forEach(function (el) {
      if (!el.dataset.en) el.dataset.en = el.innerHTML; // cache original
      var txt = lang === 'es' ? el.dataset.es : el.dataset.en;
      if (txt !== undefined) {
        if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') el.placeholder = txt;
        else el.innerHTML = txt;
      }
    });
    document.querySelectorAll('.lang button').forEach(function (b) {
      b.classList.toggle('on', b.dataset.lang === lang);
      b.setAttribute('aria-pressed', String(b.dataset.lang === lang));
    });
    (root || document).querySelectorAll('[data-aria-en]').forEach(function (el) {
      el.setAttribute('aria-label', lang === 'es' ? el.dataset.ariaEs : el.dataset.ariaEn);
    });
    refreshNavigation();
  }
  document.querySelectorAll('.lang button').forEach(function (b) {
    b.addEventListener('click', function () { setLang(b.dataset.lang, true); });
  });
  // Footer "last updated" stamp from config.siteUpdated (YYYY-MM-DD); added before the first language swap.
  var siteUpdated = window.AMA_CONFIG && window.AMA_CONFIG.siteUpdated;
  // GitHub Pages sends the publish time as Last-Modified, so the stamp never falls behind the latest
  // publish even if siteUpdated isn't bumped. Browsers report "now" when the header is missing, so a
  // value from the last two minutes is ignored.
  var published = new Date(document.lastModified);
  if (!isNaN(published) && Date.now() - published.getTime() > 120000) {
    var pr = new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Puerto_Rico', year: 'numeric', month: '2-digit', day: '2-digit' }).format(published);
    if (!siteUpdated || pr > siteUpdated) siteUpdated = pr;
  }
  var copyRow = document.querySelector('footer .copy');
  if (siteUpdated && copyRow) {
    var updatedDate = new Date(siteUpdated + 'T12:00:00');
    var stamp = document.createElement('time');
    stamp.dateTime = siteUpdated;
    stamp.dataset.en = 'Last updated ' + updatedDate.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
    stamp.dataset.es = 'Actualizado el ' + updatedDate.toLocaleDateString('es-PR', { day: 'numeric', month: 'long', year: 'numeric' });
    stamp.innerHTML = stamp.dataset.en;
    copyRow.appendChild(stamp);
  }
  // cache english originals before first swap
  document.querySelectorAll('[data-en]').forEach(function (el) {
    if (!el.dataset.en) el.dataset.en = (el.tagName === 'INPUT') ? el.placeholder : el.innerHTML;
  });
  // Pages ship in English: only rewrite the DOM when another language is needed.
  var startLang = getLang();
  if (startLang !== 'en') setLang(startLang);
  else document.querySelectorAll('.lang button').forEach(function (b) { b.classList.toggle('on', b.dataset.lang === 'en'); b.setAttribute('aria-pressed', String(b.dataset.lang === 'en')); });

  /* ---------- Preloader ---------- */
  var pre = document.getElementById('preloader');
  // Script runs after the content. Do not wait for embeds, fonts or a timer.
  if (pre) {
    pre.classList.add('done'); pre.setAttribute('aria-hidden', 'true');
    // Remove it after the fade so its looping spinner stops costing frames.
    setTimeout(function () { if (pre.parentNode) pre.parentNode.removeChild(pre); }, 800);
  }

  /* ---------- Header + back to top ---------- */
  var header = document.getElementById('header'), toTop = document.getElementById('toTop');
  // One rAF-throttled scroll handler; DOM is only touched when a state actually changes.
  var heroC = document.querySelector('.hero-content');
  var embedsInView = new Set();
  var scrolledState = null, topState = null, ticking = false, heroVisible = true;
  function onScroll() {
    ticking = false;
    var y = window.scrollY;
    var scrolled = y > 60, showTop = y > 600 && embedsInView.size === 0;
    if (header && scrolled !== scrolledState) { header.classList.toggle('scrolled', scrolled); scrolledState = scrolled; }
    if (toTop && showTop !== topState) {
      toTop.classList.toggle('show', showTop);
      toTop.tabIndex = showTop ? 0 : -1;
      toTop.setAttribute('aria-hidden', String(!showTop));
      topState = showTop;
    }
    if (heroC && heroVisible && !motion.matches) {
      var h = window.innerHeight, k = Math.min(y, h);
      heroC.style.transform = 'translate3d(0,' + (k * 0.25).toFixed(1) + 'px,0)';
      heroC.style.opacity = String(Math.max(0, 1 - k / (h * 0.9)).toFixed(3));
    }
  }
  function scheduleScrollUpdate() {
    if (!ticking) { ticking = true; requestAnimationFrame(onScroll); }
  }
  window.addEventListener('scroll', scheduleScrollUpdate, { passive: true });
  window.addEventListener('resize', scheduleScrollUpdate);
  requestAnimationFrame(onScroll);
  if ('IntersectionObserver' in window && document.querySelector('.embed')) {
    var embedObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) embedsInView.add(entry.target);
        else embedsInView.delete(entry.target);
      });
      requestAnimationFrame(onScroll);
    });
    document.querySelectorAll('.embed').forEach(function (embed) { embedObserver.observe(embed); });
  }
  if (toTop) toTop.addEventListener('click', function () {
    window.scrollTo({ top: 0, behavior: motion.matches ? 'instant' : 'smooth' });
    var main = document.getElementById('main');
    if (main) { main.tabIndex = -1; main.focus({ preventScroll: true }); }
  });

  /* ---------- Mobile menu ---------- */
  var burger = document.getElementById('burger'), nav = document.getElementById('nav');
  if (burger && nav) {
    var mobile = window.matchMedia('(max-width: 1200px)');
    function compactMenu() { return mobile.matches || header.classList.contains('compact-nav'); }
    // Text enlargement and loaded fonts can exhaust the desktop row even when
    // the viewport is wider than the normal 1200px breakpoint.
    var navSignature = '';
    function fitNavigation() {
      var container = header.querySelector('.container'), logo = header.querySelector('.logo');
      var signature = container.clientWidth + ':' + getComputedStyle(logo).fontSize + ':' + getComputedStyle(nav.querySelector('a')).fontSize + ':' + nav.textContent;
      if (signature === navSignature) return;
      navSignature = signature;
      var wasCompact = header.classList.contains('compact-nav');
      header.classList.remove('compact-nav');
      var crowded = !mobile.matches && logo.getBoundingClientRect().width + nav.scrollWidth + 20 > container.clientWidth;
      header.classList.toggle('compact-nav', crowded);
      if (wasCompact !== crowded) closeMenu(nav.contains(document.activeElement));
      nav.inert = compactMenu() && !nav.classList.contains('open');
    }
    function closeMenu(restoreFocus) {
      burger.classList.remove('open'); nav.classList.remove('open');
      burger.setAttribute('aria-expanded', 'false');
      document.body.classList.remove('menu-open');
      nav.inert = compactMenu();
      if (restoreFocus) burger.focus();
    }
    burger.addEventListener('click', function () {
      if (nav.classList.contains('open')) return closeMenu(true);
      burger.classList.add('open'); nav.classList.add('open');
      nav.inert = false;
      burger.setAttribute('aria-expanded', 'true');
      document.body.classList.add('menu-open');
      nav.querySelector('a').focus();
    });
    nav.addEventListener('click', function (e) {
      var link = e.target.closest('a');
      if (!link) return;
      closeMenu(false);
      if (link.pathname === location.pathname && link.hash) {
        var target = document.getElementById(link.hash.slice(1));
        if (target) { target.tabIndex = -1; target.focus({ preventScroll: true }); }
      }
    });
    document.addEventListener('click', function (e) {
      if (nav.classList.contains('open') && !nav.contains(e.target) && !burger.contains(e.target)) closeMenu(true);
    });
    document.addEventListener('keydown', function (e) {
      if (!compactMenu() || !nav.classList.contains('open')) return;
      if (e.key === 'Escape') { e.preventDefault(); closeMenu(true); }
      if (e.key === 'Tab') {
        var links = Array.from(nav.querySelectorAll('a,button')).filter(function (el) { return !el.disabled; });
        var first = links[0], last = links[links.length - 1];
        if (e.shiftKey && document.activeElement === first) { e.preventDefault(); burger.focus(); }
        else if (e.shiftKey && document.activeElement === burger) { e.preventDefault(); last.focus(); }
        else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); burger.focus(); }
        else if (!e.shiftKey && document.activeElement === burger) { e.preventDefault(); first.focus(); }
      }
    });
    mobile.addEventListener('change', function () { closeMenu(nav.contains(document.activeElement) && mobile.matches); });
    refreshNavigation = fitNavigation;
    fitNavigation();
    window.addEventListener('resize', fitNavigation);
    // Defer layout writes until after observer delivery (not inside its loop).
    if (window.ResizeObserver) new ResizeObserver(function () { requestAnimationFrame(fitNavigation); }).observe(header);
    if (document.fonts && document.fonts.ready) {
      var fontsChanged = function () { navSignature = ''; fitNavigation(); };
      document.fonts.ready.then(fontsChanged);
      document.fonts.addEventListener('loadingdone', fontsChanged);
    }
  }

  /* ---------- Active nav item ---------- */
  var here = location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('nav > ul > li').forEach(function (li) {
    var a = li.querySelector(':scope > a');
    var href = a && a.getAttribute('href');
    if (href === './') href = 'index.html'; // home links point at the root URL
    if (a && href === here) { li.classList.add('active'); a.setAttribute('aria-current', 'page'); }
  });

  /* ---------- Scroll reveal ---------- */
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        var el = e.target;
        el.classList.add('visible'); io.unobserve(el);
        if (el.classList.contains('stagger')) setTimeout(function () { el.classList.add('settled'); }, 1500);
      });
    }, { threshold: 0.12 });
    document.querySelectorAll('.reveal,.reveal-left,.reveal-right,.stagger').forEach(function (el) { io.observe(el); });

    /* ---------- Counters ---------- */
    var cio = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        var el = e.target, target = +el.dataset.count, suffix = el.dataset.suffix || '', dur = 1800, start = performance.now();
        var value = el.querySelector('.counter-value') || el;
        if (motion.matches) { value.textContent = target + suffix; cio.unobserve(el); return; }
        (function tick(t) {
          var p = Math.min((t - start) / dur, 1), ease = 1 - Math.pow(1 - p, 3);
          value.textContent = Math.round(target * ease) + (p === 1 ? suffix : '');
          if (motion.matches) value.textContent = target + suffix;
          else if (p < 1) requestAnimationFrame(tick);
        })(start);
        cio.unobserve(el);
      });
    }, { threshold: 0.6 });
    document.querySelectorAll('[data-count]').forEach(function (el) { cio.observe(el); });

    /* ---------- Lazy-load placeholder photos ---------- */
    var bgIo = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        e.target.style.backgroundImage = bgValue(e.target);
        bgIo.unobserve(e.target);
      });
    }, { rootMargin: '300px 0px' });
    document.querySelectorAll('[data-bg]').forEach(function (el) { bgIo.observe(el); });
  } else {
    document.querySelectorAll('.reveal,.reveal-left,.reveal-right,.stagger').forEach(function (el) { el.classList.add('visible'); });
    document.querySelectorAll('[data-bg]').forEach(function (el) { el.style.backgroundImage = bgValue(el); });
  }

  /* ---------- Pause decorative hero loops while off screen ---------- */
  var heroEl = document.querySelector('.hero,.page-hero');
  if (heroEl && 'IntersectionObserver' in window) {
    new IntersectionObserver(function (entries) {
      heroVisible = entries[0].isIntersecting;
      heroEl.classList.toggle('hero-off', !heroVisible);
      if (heroVisible) scheduleScrollUpdate();
    }).observe(heroEl);
  }
  motion.addEventListener('change', function () {
    if (motion.matches && heroC) { heroC.style.transform = ''; heroC.style.opacity = ''; }
  });

  /* ---------- Click-to-load embeds: no third-party requests or cookies until asked ---------- */
  document.querySelectorAll('.embed-facade').forEach(function (box) {
    var btn = box.querySelector('.embed-load');
    if (!btn) return;
    btn.addEventListener('click', function () {
      var frame = document.createElement('iframe');
      frame.src = box.dataset.embedSrc;
      frame.title = box.dataset.embedTitle || '';
      box.classList.add('loading');
      frame.addEventListener('load', function () { box.classList.remove('loading'); });
      box.replaceChildren(frame);
      box.classList.remove('embed-facade');
      frame.tabIndex = 0; frame.focus({ preventScroll: true });
      trackEvent('embed_load', { embed: frame.title });
    });
  });

  /* ---------- Forms: contact, membership application ----------
     With config.formEndpoint set they POST as JSON; otherwise they open a pre-filled email draft. */
  var formEndpoint = config.formEndpoint || '';
  function lang() { return document.documentElement.lang === 'es' ? 'es' : 'en'; }
  document.querySelectorAll('form[data-ama-form]').forEach(function (form) {
    var name = form.dataset.amaForm;
    var status = form.querySelector('.form-status');
    function say(kind) {
      if (!status) return;
      status.textContent = status.dataset[kind + (lang() === 'es' ? 'Es' : 'En')] || '';
      status.className = 'form-status ' + kind;
    }
    if (formEndpoint) document.querySelectorAll('.mailto-note').forEach(function (n) { n.hidden = true; });
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      if (!form.reportValidity()) return;
      var data = {};
      new FormData(form).forEach(function (v, k) { data[k] = v; });
      if (data.website) return; // honeypot: bots fill the hidden field
      delete data.website;
      function mailDraft() {
        var lines = Object.keys(data).map(function (k) { return k + ': ' + data[k]; });
        location.href = 'mailto:' + form.dataset.mailto + '?subject=' + encodeURIComponent(form.dataset.subject || name) + '&body=' + encodeURIComponent(lines.join('\n'));
        trackEvent(name + '_draft_open', { method: 'mailto' });
        var note = form.querySelector('.mailto-note'); if (note) note.hidden = false;
        say('draft');
      }
      if (formEndpoint) {
        var btn = form.querySelector('button[type=submit]'); if (btn) btn.disabled = true;
        fetch(formEndpoint, { method: 'POST', headers: { 'Accept': 'application/json', 'Content-Type': 'application/json' }, body: JSON.stringify(Object.assign({ _form: name, _page: location.pathname.split('/').pop() || 'index.html', _lang: lang() }, data)) })
          .then(function (res) {
            if (!res.ok) throw new Error('bad status');
            say('ok'); form.reset(); trackEvent(name + '_submit', { method: 'endpoint' });
          })
          .catch(mailDraft) // the backend is down: the visitor still reaches the chapter by email
          .then(function () { if (btn) btn.disabled = false; });
      } else mailDraft();
    });
  });

  /* ---------- FAQ accordion ---------- */
  document.querySelectorAll('.faq button').forEach(function (b, i) {
    var answer = b.parentElement.querySelector('.a');
    if (!answer) return;
    b.id = 'faq-question-' + i;
    answer.id = 'faq-answer-' + i;
    b.setAttribute('aria-controls', answer.id);
    b.setAttribute('aria-expanded', 'false');
    answer.setAttribute('aria-labelledby', b.id);
    answer.setAttribute('role', 'region');
    answer.hidden = true;
    var icon = b.querySelector('.ico'); if (icon) icon.setAttribute('aria-hidden', 'true');
    b.addEventListener('click', function () {
      var item = b.parentElement, open = item.classList.contains('open');
      item.parentElement.querySelectorAll('.faq').forEach(function (f) {
        f.classList.remove('open'); f.querySelector('button').setAttribute('aria-expanded', 'false'); f.querySelector('.a').hidden = true;
      });
      if (!open) { item.classList.add('open'); b.setAttribute('aria-expanded', 'true'); answer.hidden = false; }
    });
  });

  /* ---------- KPI click tracking: membership interest, event RSVP, sponsor packages ---------- */
  document.addEventListener('click', function (e) {
    var a = e.target.closest('a');
    if (!a) return;
    var href = a.getAttribute('href') || '';
    if (href.indexOf('membership.html#join') !== -1 || a.closest('#join')) {
      trackEvent('membership_interest_click', { link_text: a.textContent.trim() });
    }
    if (a.closest('.event') && (a.dataset.analytics === 'event_rsvp_click' || href.indexOf('calendar.google.com/calendar/render?action=TEMPLATE') !== -1)) {
      trackEvent(a.dataset.analytics === 'event_rsvp_click' ? 'event_rsvp_click' : 'event_calendar_click', {
        event_name: (a.closest('.event').querySelector('h2,h3') || {}).textContent || ''
      });
    }
    if (/\.pdf(\?|#|$)/i.test(href)) {
      trackEvent('resource_download', { file_name: href.split('/').pop().split(/[?#]/)[0] });
    }
    if (/^https?:/i.test(href) && href.indexOf(location.hostname) === -1 && /instagram|linkedin|youtube|spotify|facebook/i.test(href)) {
      trackEvent('social_click', { network: (href.match(/instagram|linkedin|youtube|spotify|facebook/i) || [''])[0].toLowerCase() });
    }
    if (href.indexOf('sponsors.html#packages') !== -1 || (a.closest('#packages') && href.indexOf('mailto:') !== 0)) {
      trackEvent('sponsor_package_click', { link_text: a.textContent.trim() });
    }
    /* Applications live in Google Forms: count each time a visitor opens one (the KPI's site step;
       completed applications are counted in the form's own responses). */
    if (href.indexOf('docs.google.com/forms') !== -1) {
      if (/elevate/i.test(location.pathname)) trackEvent('elevate_inquiry_click', { method: 'google_form' });
      else trackEvent('membership_form_open', { link_text: a.textContent.trim() });
    }
    /* Inquiry KPIs: mailto CTAs with a subject (sponsor partnership, ELEVATE client) */
    if (href.indexOf('mailto:') === 0) {
      var subj = decodeURIComponent((href.match(/[?&]subject=([^&]*)/i) || ['', ''])[1]);
      if (/AMPLIFY|partnership|sponsor/i.test(subj)) trackEvent('sponsor_inquiry_click', { subject: subj });
      else if (/ELEVATE/i.test(subj)) trackEvent('elevate_inquiry_click', { subject: subj });
    }
  });

  /* ---------- Simple event filter ---------- */
  var filters = document.querySelectorAll('[data-filter]');
  if (filters.length) {
    filters.forEach(function (b) {
      b.addEventListener('click', function () {
        filters.forEach(function (x) { x.classList.remove('btn-green'); x.classList.add('btn-outline-dark'); x.setAttribute('aria-pressed', 'false'); });
        b.classList.add('btn-green'); b.classList.remove('btn-outline-dark');
        b.setAttribute('aria-pressed', 'true');
        filterEvents();
      });
    });
  }

  /* ---------- Mark past events instead of showing them as upcoming ---------- */
  var eventList = document.getElementById('event-list');
  function chapterDate() {
    var parts = new Intl.DateTimeFormat('en-US', { timeZone: 'America/Puerto_Rico', year: 'numeric', month: '2-digit', day: '2-digit' }).formatToParts(new Date());
    function part(type) { return parts.find(function (p) { return p.type === type; }).value; }
    return part('year') + '-' + part('month') + '-' + part('day');
  }
  function markEvents(root) {
    var today = chapterDate();
    var anyUpcoming = false;
    root.querySelectorAll('.event[data-date]').forEach(function (ev) {
      if (ev.dataset.date < today) {
        ev.classList.add('past');
        var link = ev.querySelector('a.btn:not(.recap-link)');
        if (link) {
          var tag = document.createElement('span');
          tag.className = 'completed-tag';
          tag.dataset.en = 'Event completed'; tag.dataset.es = 'Evento finalizado';
          tag.textContent = document.documentElement.lang === 'es' ? tag.dataset.es : tag.dataset.en;
          link.replaceWith(tag);
        }
      } else {
        anyUpcoming = true;
      }
    });
    return anyUpcoming;
  }
  function filterEvents() {
    if (!eventList) return;
    var selected = document.querySelector('[data-filter][aria-pressed="true"]');
    var cat = selected ? selected.dataset.filter : 'all';
    var status = document.getElementById('event-status');
    var state = status ? status.value : 'all';
    var count = 0;
    eventList.querySelectorAll('.event').forEach(function (ev) {
      var past = ev.classList.contains('past');
      ev.hidden = !((cat === 'all' || ev.dataset.cat === cat) && (state === 'all' || (state === 'past' ? past : !past)));
      if (!ev.hidden) count++;
    });
    var empty = document.getElementById('no-events'); if (empty) empty.hidden = count > 0;
    var label = eventList.querySelector('.past-label');
    if (label) label.hidden = !eventList.querySelector('.event.past:not([hidden])');
    eventList.querySelectorAll('.month-head').forEach(function (h) {
      h.hidden = !eventList.querySelector('.event[data-date^="' + h.dataset.month + '"]:not(.past):not([hidden])');
    });
  }
  /* ---------- Event RSVP (upcoming events only) ---------- */
  function rsvpText(el, en, es) { el.dataset.en = en; el.dataset.es = es; el.textContent = lang() === 'es' ? es : en; return el; }
  function addRsvp(ev) {
    if (ev.classList.contains('past') || ev.dataset.rsvp === 'no' || ev.querySelector('.rsvp-btn')) return; // sales, raffles and announcements: calendar link only
    var interest = ev.id === 'e-icc-2027';
    var title = (ev.querySelector('h2,h3') || {}).textContent || '';
    var btn = rsvpText(document.createElement('button'), interest ? "I'm interested" : 'RSVP', interest ? 'Me interesa' : 'Confirmar asistencia');
    btn.type = 'button'; btn.className = 'btn btn-sm btn-green rsvp-btn'; btn.setAttribute('aria-expanded', 'false');
    btn.dataset.analytics = 'event_rsvp_click';
    var cal = ev.querySelector('a.btn');
    var actions = document.createElement('div'); actions.className = 'event-actions';
    if (cal) { cal.replaceWith(actions); actions.appendChild(btn); actions.appendChild(cal); } else { actions.appendChild(btn); ev.appendChild(actions); }
    btn.addEventListener('click', function () {
      var open = ev.querySelector('.rsvp-form');
      if (open) { open.remove(); btn.setAttribute('aria-expanded', 'false'); return; }
      trackEvent('event_rsvp_click', { event_name: title.trim() });
      var f = document.createElement('form'); f.className = 'rsvp-form'; f.noValidate = false;
      var uid = 'r' + Math.random().toString(36).slice(2, 7);
      f.innerHTML = '<label for="' + uid + 'n"></label><input id="' + uid + 'n" name="name" required autocomplete="name">' +
        '<label for="' + uid + 'e"></label><input id="' + uid + 'e" name="email" type="email" required autocomplete="email">' +
        '<input name="website" class="hp" tabindex="-1" autocomplete="off" aria-hidden="true">' +
        '<button class="btn btn-sm btn-primary" type="submit"></button><p class="form-status" role="status" aria-live="polite"></p>';
      rsvpText(f.querySelector('label[for$="n"]'), 'Name', 'Nombre');
      rsvpText(f.querySelector('label[for$="e"]'), 'Email', 'Correo');
      rsvpText(f.querySelector('button'), interest ? 'Count me in' : 'Confirm', interest ? 'Cuenta conmigo' : 'Confirmar');
      var st = f.querySelector('.form-status');
      f.addEventListener('submit', function (e) {
        e.preventDefault();
        if (!f.reportValidity()) return;
        var data = { _form: 'event_rsvp', _page: 'events.html', _lang: lang(), event: title.trim(), event_id: ev.id, event_date: ev.dataset.date,
          name: f.elements.name.value, email: f.elements.email.value, website: f.elements.website.value };
        if (data.website) return;
        var sub = f.querySelector('button'); sub.disabled = true;
        function done() {
          trackEvent('event_rsvp_submit', { event_name: title.trim() });
          rsvpText(st, 'You\'re on the list! See you there. 🙌', '¡Estás en la lista! Nos vemos allí. 🙌'); st.className = 'form-status ok';
          f.querySelectorAll('input,button').forEach(function (x) { x.disabled = true; });
          rsvpText(btn, 'RSVP sent ✓', 'Confirmado ✓'); btn.disabled = true;
        }
        if (!formEndpoint) { location.href = 'mailto:ama@uprm.edu?subject=' + encodeURIComponent('RSVP: ' + title.trim()) + '&body=' + encodeURIComponent(data.name + ' <' + data.email + '>'); done(); return; }
        fetch(formEndpoint, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) })
          .then(function (r) { if (!r.ok) throw new Error('rsvp'); done(); })
          .catch(function () { sub.disabled = false; rsvpText(st, 'Could not send. Please email ama@uprm.edu.', 'No se pudo enviar. Escribe a ama@uprm.edu.'); st.className = 'form-status err'; });
      });
      (ev.querySelector('.event > div:nth-child(2)') || ev).appendChild(f);
      btn.setAttribute('aria-expanded', 'true');
      f.querySelector('input').focus();
    });
  }
  if (eventList) {
    var anyUpcoming = markEvents(eventList);
    eventList.querySelectorAll('.event').forEach(addRsvp);
    var notice = document.getElementById('no-upcoming');
    if (notice && !anyUpcoming) notice.style.display = 'block';
    // Keep every historical record, with upcoming activities first.
    // Upcoming in date order; past ones follow, most recent first, under a "Recent activities" label.
    Array.from(eventList.querySelectorAll('.event[data-date]')).sort(function (a, b) {
      var pa = a.classList.contains('past'), pb = b.classList.contains('past');
      return Number(pa) - Number(pb) || (pa ? b.dataset.date.localeCompare(a.dataset.date) : a.dataset.date.localeCompare(b.dataset.date));
    }).forEach(function (ev) { eventList.appendChild(ev); });
    // Month headings for upcoming events, so a long semester reads at a glance.
    var MONTHS_EN = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
    var MONTHS_ES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'];
    var lastMonth = '';
    eventList.querySelectorAll('.event[data-date]:not(.past)').forEach(function (ev) {
      var ym = ev.dataset.date.slice(0, 7);
      if (ym === lastMonth) return;
      lastMonth = ym;
      var m = Number(ym.slice(5, 7)) - 1, y = ym.slice(0, 4);
      var h = document.createElement('h3');
      h.className = 'month-head';
      h.dataset.month = ym;
      h.dataset.en = MONTHS_EN[m] + ' ' + y;
      h.dataset.es = MONTHS_ES[m].charAt(0).toUpperCase() + MONTHS_ES[m].slice(1) + ' ' + y;
      h.textContent = lang() === 'es' ? h.dataset.es : h.dataset.en;
      eventList.insertBefore(h, ev);
    });
    var firstPast = eventList.querySelector('.event.past');
    if (firstPast) {
      var nPast = eventList.querySelectorAll('.event.past').length;
      var pastLabel = document.createElement('h3');
      pastLabel.className = 'past-label';
      pastLabel.dataset.en = 'Recent activities · ' + nPast;
      pastLabel.dataset.es = 'Actividades recientes · ' + nPast;
      pastLabel.textContent = lang() === 'es' ? pastLabel.dataset.es : pastLabel.dataset.en;
      eventList.insertBefore(pastLabel, firstPast);
    }
    filters.forEach(function (b) { b.setAttribute('aria-pressed', String(b.dataset.filter === 'all')); });
    var status = document.getElementById('event-status');
    if (status) status.addEventListener('change', filterEvents);
    filterEvents();
  }

  /* Home reads the maintained event list; its HTML fallback links to the calendar. */
  var preview = document.getElementById('home-events');
  function loadPreview() { fetch('events.html').then(function (res) {
    if (!res.ok) throw new Error('Events unavailable'); return res.text();
  }).then(function (html) {
    var source = new DOMParser().parseFromString(html, 'text/html');
    var upcoming = Array.from(source.querySelectorAll('#event-list .event[data-date]')).filter(function (ev) { return ev.dataset.date >= chapterDate(); });
    upcoming.sort(function (a, b) { return a.dataset.date.localeCompare(b.dataset.date); });
    if (!upcoming.length) return;
    preview.replaceChildren();
    upcoming.slice(0, 3).forEach(function (ev) {
      var link = ev.querySelector('a.btn');
      if (link) {
        link.href = 'events.html#' + ev.id; link.removeAttribute('target');
        link.dataset.en = 'Event details'; link.dataset.es = 'Detalles del evento';
      }
      ev.removeAttribute('id');
      var heading = ev.querySelector('h2');
      if (heading) { var h3 = document.createElement('h3'); Array.from(heading.attributes).forEach(function (a) { h3.setAttribute(a.name, a.value); }); h3.innerHTML = heading.innerHTML; heading.replaceWith(h3); }
      preview.appendChild(ev);
    });
    setLang(document.documentElement.lang, false, preview);
  }).catch(function () { /* The visible calendar link remains useful offline/on file://. */ }); }
  if (preview) {
    if ('IntersectionObserver' in window) {
      var pio = new IntersectionObserver(function (entries) {
        if (entries[0].isIntersecting) { pio.disconnect(); loadPreview(); }
      }, { rootMargin: '800px 0px' });
      pio.observe(preview);
    } else loadPreview();
  }
})();

/* ---------- Audience switcher ---------- */
(function(){
  document.querySelectorAll('.aud').forEach(function(box){
    var tabs=box.querySelectorAll('.aud-tabs button'), panels=box.querySelectorAll('.aud-panel');
    function select(t) {
      tabs.forEach(function(x){x.classList.toggle('on',x===t);x.setAttribute('aria-selected',String(x===t));x.tabIndex=x===t?0:-1;});
      panels.forEach(function(p){p.hidden=p.dataset.aud!==t.dataset.aud;});
    }
    tabs.forEach(function(t,i){
      t.id='aud-tab-'+t.dataset.aud;t.setAttribute('role','tab');t.setAttribute('aria-controls','aud-panel-'+t.dataset.aud);
      t.addEventListener('click',function(){select(t);});
      t.addEventListener('keydown',function(e){
        var next=i;
        if(e.key==='ArrowRight')next=(i+1)%tabs.length;
        else if(e.key==='ArrowLeft')next=(i+tabs.length-1)%tabs.length;
        else if(e.key==='Home')next=0;
        else if(e.key==='End')next=tabs.length-1;
        else return;
        e.preventDefault();select(tabs[next]);tabs[next].focus();
      });
    });
    panels.forEach(function(p){p.id='aud-panel-'+p.dataset.aud;p.setAttribute('role','tabpanel');p.setAttribute('aria-labelledby','aud-tab-'+p.dataset.aud);p.tabIndex=0;});
    if(tabs.length)select(tabs[0]);
  });
})();

/* ---------- Scroll progress bar ---------- */
(function(){
  var bar=document.getElementById('progress'); if(!bar) return;
  // Scale on the compositor instead of animating width, and only re-measure the page on resize/load.
  var max=0, queued=false;
  function measure(){var d=document.documentElement;max=d.scrollHeight-d.clientHeight;draw();}
  function draw(){queued=false;bar.style.transform='scaleX('+(max>0?Math.min(window.scrollY/max,1):0)+')';}
  window.addEventListener('scroll',function(){if(!queued){queued=true;requestAnimationFrame(draw);}},{passive:true});
  window.addEventListener('resize',measure); window.addEventListener('load',measure);
  if('ResizeObserver' in window) new ResizeObserver(measure).observe(document.body);
  measure();
})();

/* RUMi (chat assistant) loads once the page has finished loading and the browser is idle, so its
   124 KB script and its stylesheet never compete with the first paint on phones. */
(function () {
  window.AMA_loadRumi = function (cb) {
    if (window.RUMI) { cb(window.RUMI); return; }
    document.addEventListener('rumi:ready', function () { cb(window.RUMI); }, { once: true });
    load();
  };
  function load() {
    if (document.querySelector('script[data-rumi]')) return;
    var s = document.createElement('script');
    s.src = 'assets/rumi.js'; s.async = true; s.setAttribute('data-rumi', '');
    document.body.appendChild(s);
  }
  // First interaction (tap, scroll, mouse, key) or 4 s after load, whichever comes first: by then the
  // page's own images are in, so RUMi's download doesn't delay the largest paint.
  var EVENTS = ['pointerdown', 'pointermove', 'touchstart', 'scroll', 'keydown'];
  function go() { EVENTS.forEach(function (e) { window.removeEventListener(e, go, true); }); (window.requestIdleCallback || function (cb) { setTimeout(cb, 1); })(load, { timeout: 1500 }); }
  function arm() { EVENTS.forEach(function (e) { window.addEventListener(e, go, { capture: true, passive: true, once: true }); }); setTimeout(go, 4000); }
  if (document.readyState === 'complete') arm(); else window.addEventListener('load', arm, { once: true });
})();

/* Impact page: live totals from the Worker (counts only, never personal data). The section stays
   hidden until there is something to show, so a fresh counter never reads as "0". */
(function () {
  var box = document.getElementById('live-stats');
  var base = (window.AMA_CONFIG && window.AMA_CONFIG.rumiEndpoint) || '';
  if (!box || !base) { if (box) box.closest('section').hidden = true; return; }
  var section = box.closest('section'); section.hidden = true;
  fetch(base.replace(/\/$/, '') + '/stats').then(function (r) { return r.ok ? r.json() : null; }).then(function (d) {
    if (!d) return;
    var values = Object.assign({}, d.forms || {}, { aiAnswers: d.aiAnswers || 0 }), total = 0;
    box.querySelectorAll('[data-live]').forEach(function (el) { var n = Number(values[el.dataset.live]) || 0; total += n; el.textContent = n.toLocaleString(); });
    if (total >= 5) section.hidden = false;
  }).catch(function () {});
})();

/* ELEVATE page: "How is your website doing?" runs RUMi's website check with the visitor's link. */
(function () {
  var form = document.querySelector('.webcheck-form');
  if (!form) return;
  var input = form.querySelector('input');
  function placeholder() { input.placeholder = document.documentElement.lang === 'es' ? input.dataset.phEs : input.dataset.phEn; }
  placeholder(); new MutationObserver(placeholder).observe(document.documentElement, { attributes: true, attributeFilter: ['lang'] });
  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var url = input.value.trim();
    if (!/^[^\s]+\.[a-z]{2,}/i.test(url.replace(/^https?:\/\//, ''))) { input.setCustomValidity(document.documentElement.lang === 'es' ? 'Escribe una dirección web, por ejemplo tunegocio.com' : 'Enter a web address, for example yourbusiness.com'); input.reportValidity(); input.setCustomValidity(''); return; }
    if (!/^https?:\/\//i.test(url)) url = 'https://' + url;
    if (window.gtag) window.gtag('event', 'website_check_start', { page: 'elevate' });
    window.AMA_loadRumi(function (rumi) { rumi.ask((document.documentElement.lang === 'es' ? 'Revisa mi página web: ' : 'Check my website: ') + url); });
  });
})();

/* "Try it" buttons (How we use AI page): open RUMi with a sample question in the current language. */
document.addEventListener('click', function (e) {
  var b = e.target.closest && e.target.closest('[data-rumi-ask-en]');
  if (!b || !window.AMA_loadRumi) return;
  var q = document.documentElement.lang === 'es' ? b.dataset.rumiAskEs : b.dataset.rumiAskEn;
  if (window.gtag) window.gtag('event', 'rumi_try_click', { question: q });
  window.AMA_loadRumi(function (rumi) { rumi.ask(q); });
});
