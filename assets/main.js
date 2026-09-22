/* AMA UPRM — shared behaviour */
(function () {
  'use strict';

  /* ---------- KPI tracking (Strategic Alignment & Performance) ---------- */
  function trackEvent(name, params) {
    if (typeof gtag === 'function') gtag('event', name, params || {});
  }

  /* ---------- Language toggle (EN default, ES via data-es) ---------- */
  var LANG_KEY = 'ama-lang';
  function getLang() {
    try { return localStorage.getItem(LANG_KEY) || 'en'; } catch (e) { return 'en'; }
  }
  function setLang(lang) {
    try { localStorage.setItem(LANG_KEY, lang); } catch (e) {}
    document.documentElement.lang = lang;
    document.querySelectorAll('[data-en]').forEach(function (el) {
      if (!el.dataset.en) el.dataset.en = el.innerHTML; // cache original
      var txt = lang === 'es' ? el.dataset.es : el.dataset.en;
      if (txt !== undefined) {
        if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') el.placeholder = txt;
        else el.innerHTML = txt;
      }
    });
    document.querySelectorAll('.lang button').forEach(function (b) {
      b.classList.toggle('on', b.dataset.lang === lang);
    });
  }
  document.querySelectorAll('.lang button').forEach(function (b) {
    b.addEventListener('click', function () { setLang(b.dataset.lang); });
  });
  // cache english originals before first swap
  document.querySelectorAll('[data-en]').forEach(function (el) {
    if (!el.dataset.en) el.dataset.en = (el.tagName === 'INPUT') ? el.placeholder : el.innerHTML;
  });
  setLang(getLang());

  /* ---------- Preloader ---------- */
  var pre = document.getElementById('preloader');
  if (pre) window.addEventListener('load', function () { setTimeout(function () { pre.classList.add('done'); }, 300); });

  /* ---------- Header + back to top ---------- */
  var header = document.getElementById('header'), toTop = document.getElementById('toTop');
  function onScroll() {
    var y = window.scrollY;
    if (header) header.classList.toggle('scrolled', y > 60);
    if (toTop) toTop.classList.toggle('show', y > 600);
  }
  window.addEventListener('scroll', onScroll, { passive: true }); onScroll();
  if (toTop) toTop.addEventListener('click', function () { window.scrollTo({ top: 0, behavior: 'smooth' }); });

  /* ---------- Mobile menu ---------- */
  var burger = document.getElementById('burger'), nav = document.getElementById('nav');
  if (burger && nav) {
    burger.addEventListener('click', function () { burger.classList.toggle('open'); nav.classList.toggle('open'); });
    nav.querySelectorAll('a').forEach(function (a) { a.addEventListener('click', function () { burger.classList.remove('open'); nav.classList.remove('open'); }); });
  }

  /* ---------- Active nav item ---------- */
  var here = location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('nav > ul > li').forEach(function (li) {
    var a = li.querySelector(':scope > a');
    if (a && a.getAttribute('href') === here) li.classList.add('active');
  });

  /* ---------- Scroll reveal ---------- */
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('visible'); io.unobserve(e.target); } });
    }, { threshold: 0.12 });
    document.querySelectorAll('.reveal,.reveal-left,.reveal-right,.stagger').forEach(function (el) { io.observe(el); });

    /* ---------- Counters ---------- */
    var cio = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        var el = e.target, target = +el.dataset.count, suffix = el.dataset.suffix || '', dur = 1800, start = performance.now();
        (function tick(t) {
          var p = Math.min((t - start) / dur, 1), ease = 1 - Math.pow(1 - p, 3);
          el.textContent = Math.round(target * ease) + (p === 1 ? suffix : '');
          if (p < 1) requestAnimationFrame(tick);
        })(start);
        cio.unobserve(el);
      });
    }, { threshold: 0.6 });
    document.querySelectorAll('[data-count]').forEach(function (el) { cio.observe(el); });

    /* ---------- Lazy-load placeholder photos ---------- */
    var bgIo = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        e.target.style.backgroundImage = e.target.dataset.bg;
        bgIo.unobserve(e.target);
      });
    }, { rootMargin: '300px 0px' });
    document.querySelectorAll('[data-bg]').forEach(function (el) { bgIo.observe(el); });
  } else {
    document.querySelectorAll('.reveal,.reveal-left,.reveal-right,.stagger').forEach(function (el) { el.classList.add('visible'); });
    document.querySelectorAll('[data-bg]').forEach(function (el) { el.style.backgroundImage = el.dataset.bg; });
  }

  /* ---------- Hero parallax ---------- */
  var heroC = document.querySelector('.hero-content');
  if (heroC) window.addEventListener('scroll', function () {
    var y = window.scrollY, h = window.innerHeight;
    if (y < h) { heroC.style.transform = 'translateY(' + (y * 0.25) + 'px)'; heroC.style.opacity = 1 - y / (h * 0.9); }
  }, { passive: true });

  /* ---------- FAQ accordion ---------- */
  document.querySelectorAll('.faq button').forEach(function (b) {
    b.addEventListener('click', function () {
      var item = b.parentElement, open = item.classList.contains('open');
      item.parentElement.querySelectorAll('.faq').forEach(function (f) { f.classList.remove('open'); });
      if (!open) item.classList.add('open');
    });
  });

  /* ---------- Newsletter (submits to FormSubmit.co) ---------- */
  document.querySelectorAll('form.newsletter-form').forEach(function (f) {
    f.addEventListener('submit', function (e) {
      e.preventDefault();
      var ok = f.parentElement.querySelector('.form-ok');
      var err = f.parentElement.querySelector('.form-error');
      var btn = f.querySelector('button[type="submit"]');
      if (ok) ok.style.display = 'none';
      if (err) err.style.display = 'none';
      if (btn) btn.disabled = true;
      var ajaxUrl = f.action.replace('formsubmit.co/', 'formsubmit.co/ajax/');
      fetch(ajaxUrl, { method: 'POST', headers: { Accept: 'application/json' }, body: new FormData(f) })
        .then(function (res) { if (!res.ok) throw new Error('bad status'); return res.json(); })
        .then(function () {
          if (ok) ok.style.display = 'block';
          trackEvent('newsletter_signup');
          f.reset();
        })
        .catch(function () { if (err) err.style.display = 'block'; })
        .finally(function () { if (btn) btn.disabled = false; });
    });
  });

  /* ---------- KPI click tracking: membership interest, event RSVP, sponsor packages ---------- */
  document.addEventListener('click', function (e) {
    var a = e.target.closest('a');
    if (!a) return;
    var href = a.getAttribute('href') || '';
    if (href.indexOf('membership.html#join') !== -1) {
      trackEvent('membership_interest_click', { link_text: a.textContent.trim() });
    }
    if (a.closest('.event')) {
      trackEvent('event_rsvp_click', {
        event_name: (a.closest('.event').querySelector('h3') || {}).textContent || ''
      });
    }
    if (href.indexOf('sponsors.html#packages') !== -1 || a.closest('.pkg')) {
      trackEvent('sponsor_package_click', { link_text: a.textContent.trim() });
    }
  });

  /* ---------- Simple event filter ---------- */
  var filters = document.querySelectorAll('[data-filter]');
  if (filters.length) {
    filters.forEach(function (b) {
      b.addEventListener('click', function () {
        filters.forEach(function (x) { x.classList.remove('btn-green'); x.classList.add('btn-outline-dark'); });
        b.classList.add('btn-green'); b.classList.remove('btn-outline-dark');
        var cat = b.dataset.filter;
        document.querySelectorAll('.event').forEach(function (ev) {
          ev.style.display = (cat === 'all' || ev.dataset.cat === cat) ? '' : 'none';
        });
      });
    });
  }

  /* ---------- Mark past events instead of showing them as upcoming ---------- */
  var eventList = document.getElementById('event-list');
  if (eventList) {
    var today = new Date(); today.setHours(0, 0, 0, 0);
    var anyUpcoming = false;
    eventList.querySelectorAll('.event[data-date]').forEach(function (ev) {
      var d = new Date(ev.dataset.date + 'T00:00:00');
      if (d < today) {
        ev.classList.add('past');
        var link = ev.querySelector('a.btn');
        if (link) {
          var tag = document.createElement('span');
          tag.className = 'completed-tag';
          tag.textContent = getLang() === 'es' ? 'Evento finalizado' : 'Event completed';
          link.replaceWith(tag);
        }
      } else {
        anyUpcoming = true;
      }
    });
    var notice = document.getElementById('no-upcoming');
    if (notice && !anyUpcoming) notice.style.display = 'block';
  }
})();

/* ---------- Audience switcher ---------- */
(function(){
  document.querySelectorAll('.aud').forEach(function(box){
    var tabs=box.querySelectorAll('.aud-tabs button'), panels=box.querySelectorAll('.aud-panel');
    tabs.forEach(function(t){t.addEventListener('click',function(){
      tabs.forEach(function(x){x.classList.toggle('on',x===t);});
      panels.forEach(function(p){p.hidden=p.dataset.aud!==t.dataset.aud;});
    });});
  });
})();

/* ---------- Scroll progress bar ---------- */
(function(){
  var bar=document.getElementById('progress'); if(!bar) return;
  function upd(){var d=document.documentElement;var max=d.scrollHeight-d.clientHeight;bar.style.width=(max>0?(d.scrollTop/max)*100:0)+'%';}
  window.addEventListener('scroll',upd,{passive:true}); window.addEventListener('resize',upd); upd();
})();
