/* БанкетХолл — site behaviour
   No dependencies. Every feature degrades to working HTML without JS. */
(function () {
  'use strict';

  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var $  = function (s, c) { return (c || document).querySelector(s); };
  var $$ = function (s, c) { return Array.prototype.slice.call((c || document).querySelectorAll(s)); };

  /* ---------- header ---------------------------------------------------- */
  var header = $('.header');
  if (header) {
    var onScroll = function () {
      header.classList.toggle('is-stuck', window.scrollY > 24);
    };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  /* ---------- mobile nav ------------------------------------------------ */
  var burger = $('.burger');
  var mnav = $('.mnav');
  if (burger && mnav) {
    burger.addEventListener('click', function () {
      var open = burger.getAttribute('aria-expanded') === 'true';
      burger.setAttribute('aria-expanded', String(!open));
      mnav.classList.toggle('is-open', !open);
      document.body.style.overflow = !open ? 'hidden' : '';
    });
    mnav.addEventListener('click', function (e) {
      if (e.target.closest('a')) {
        burger.setAttribute('aria-expanded', 'false');
        mnav.classList.remove('is-open');
        document.body.style.overflow = '';
      }
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && mnav.classList.contains('is-open')) burger.click();
    });
  }

  /* ---------- scroll reveals -------------------------------------------- */
  var revealables = $$('.reveal');
  if (revealables.length) {
    if (reduced || !('IntersectionObserver' in window)) {
      revealables.forEach(function (el) { el.classList.add('is-in'); });
    } else {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
          if (en.isIntersecting) {
            en.target.classList.add('is-in');
            io.unobserve(en.target);
          }
        });
      }, { rootMargin: '0px 0px -12% 0px', threshold: 0.06 });
      revealables.forEach(function (el) { io.observe(el); });
    }
  }

  /* ---------- count-up stats -------------------------------------------- */
  var counters = $$('[data-count]');
  if (counters.length && !reduced && 'IntersectionObserver' in window) {
    var cio = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        cio.unobserve(en.target);
        var el = en.target;
        var target = parseFloat(el.getAttribute('data-count'));
        var t0 = null;
        var step = function (ts) {
          if (!t0) t0 = ts;
          var p = Math.min((ts - t0) / 1400, 1);
          var eased = 1 - Math.pow(1 - p, 3);
          el.textContent = fmt(Math.round(target * eased));
          if (p < 1) requestAnimationFrame(step);
        };
        requestAnimationFrame(step);
      });
    }, { threshold: 0.4 });
    counters.forEach(function (el) { cio.observe(el); });
  }

  function fmt(n) { return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ' '); }

  /* Поле ищем по id нашей формы, а если её нет — по имени переменной.
     Имён несколько: рекомендованное для новой формы Tilda и те, что
     использовались раньше, — чтобы подстановка работала при любом варианте. */
  function findField(id, names) {
    var el = document.getElementById(id);
    if (el) return el;
    for (var i = 0; i < names.length; i++) {
      el = document.querySelector('[name="' + names[i] + '"]');
      if (el) return el;
    }
    return null;
  }

  var FIELD_GUESTS = ['guests', 'Выберите количество гостей', 'Выберите число гостей'];
  var FIELD_FORMAT = ['event_type', 'мероприятие', 'Формат мероприятия'];

  function setField(el, value) {
    if (!el) return;
    el.value = value;
    /* Tilda вешает на свои поля собственные обработчики — уведомляем их,
       иначе плавающая подпись и валидация не заметят подставленное значение. */
    el.dispatchEvent(new Event('input', { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
  }

  /* ---------- capacity picker (signature) -------------------------------- */
  /* A logarithmic guest scale: 20 → 2500. Position on the scale selects the
     hall, and the chosen number is carried into the request form. */
  var picker = $('[data-picker]');
  if (picker) {
    var slider  = $('[data-picker-range]', picker);
    var readout = $('[data-picker-count]', picker);
    var panels  = $$('[data-hall-panel]', picker);
    var info    = $('[data-picker-info]', picker);
    var halls   = JSON.parse(picker.getAttribute('data-picker'));

    var LO = Math.log(20), HI = Math.log(2500);
    var toGuests = function (pct) {
      var g = Math.exp(LO + (HI - LO) * (pct / 100));
      var round = g < 100 ? 5 : g < 600 ? 10 : 50;
      return Math.max(20, Math.round(g / round) * round);
    };

    var current = -1;
    var apply = function (pct) {
      var guests = toGuests(pct);
      readout.textContent = fmt(guests);

      var idx = 0;
      for (var i = 0; i < halls.length; i++) { if (guests <= halls[i].to) { idx = i; break; } idx = i; }
      if (idx === current) return;
      current = idx;

      panels.forEach(function (p, i) { p.classList.toggle('is-active', i === idx); });
      var h = halls[idx];
      info.innerHTML =
        '<h3>' + h.name + '</h3><p>' + h.note + '</p>' +
        '<div class="picker__meta">' + h.meta.map(function (m) { return '<span>' + m + '</span>'; }).join('') + '</div>' +
        '<div class="picker__actions btn-row">' +
          '<a class="btn" href="' + h.url + '">Смотреть зал<span class="btn__arrow">→</span></a>' +
          '<a class="btn btn--ghost" href="#zayavka" data-prefill-guests>Проверить дату<span class="btn__arrow">→</span></a>' +
        '</div>';
    };

    slider.addEventListener('input', function () { apply(+slider.value); });
    apply(+slider.value);

    /* выбранное число гостей уезжает в форму */
    document.addEventListener('click', function (e) {
      if (!e.target.closest('[data-prefill-guests]')) return;
      setField(findField('f-guests', FIELD_GUESTS),
               readout.textContent.replace(/\s/g, ''));
    });
  }

  /* ---------- gallery filter -------------------------------------------- */
  var filters = $('[data-filters]');
  if (filters) {
    var shots = $$('[data-tags]');
    filters.addEventListener('click', function (e) {
      var btn = e.target.closest('button');
      if (!btn) return;
      var tag = btn.getAttribute('data-tag');
      $$('button', filters).forEach(function (b) {
        b.setAttribute('aria-pressed', String(b === btn));
      });
      shots.forEach(function (s) {
        s.hidden = !(tag === 'all' || s.getAttribute('data-tags').split(' ').indexOf(tag) > -1);
      });
    });
  }

  /* ---------- lightbox --------------------------------------------------- */
  var lb = $('.lightbox');
  if (lb) {
    var lbFig = $('.lightbox__fig', lb);
    var visible = function () { return $$('.shot').filter(function (s) { return !s.hidden; }); };
    var at = 0;
    var show = function (i) {
      var list = visible();
      if (!list.length) return;
      at = (i + list.length) % list.length;
      var shot = list[at];
      var thumb = $('img', shot);
      // Крупная версия в самом лёгком формате, который поймёт браузер.
      var pic = document.createElement('picture');
      ['avif', 'webp'].forEach(function (fmt) {
        var url = shot.getAttribute('data-full-' + fmt);
        if (!url) return;
        var src = document.createElement('source');
        src.type = 'image/' + fmt;
        src.srcset = url;
        pic.appendChild(src);
      });
      var im = document.createElement('img');
      im.src = shot.getAttribute('data-full') || (thumb && thumb.currentSrc) || thumb.src;
      im.alt = (thumb && thumb.alt) || '';
      pic.appendChild(im);
      while (lbFig.firstChild) lbFig.removeChild(lbFig.firstChild);
      lbFig.appendChild(pic);
    };
    document.addEventListener('click', function (e) {
      var shot = e.target.closest('.shot');
      if (shot) {
        show(visible().indexOf(shot));
        lb.classList.add('is-open');
        document.body.style.overflow = 'hidden';
        $('.lightbox__close', lb).focus();
        return;
      }
      if (e.target.closest('.lightbox__close') || e.target === lb) close();
      if (e.target.closest('.lightbox__nav--prev')) show(at - 1);
      if (e.target.closest('.lightbox__nav--next')) show(at + 1);
    });
    var close = function () {
      lb.classList.remove('is-open');
      document.body.style.overflow = '';
    };
    document.addEventListener('keydown', function (e) {
      if (!lb.classList.contains('is-open')) return;
      if (e.key === 'Escape') close();
      if (e.key === 'ArrowLeft') show(at - 1);
      if (e.key === 'ArrowRight') show(at + 1);
    });
  }

  /* ---------- request form ---------------------------------------------- */
  /* Posts to the venue's existing form endpoint so leads keep landing in the
     same inbox the team already works from. */
  var form = $('#request-form');
  if (form) {
    var status = $('.form-status', form);
    var submit = $('[type=submit]', form);


    form.addEventListener('submit', function (e) {
      e.preventDefault();
      if (submit.disabled) return;

      var root = $('#allrecords');
      var data = new FormData(form);

      /* <input type=date> отдаёт ГГГГ-ММ-ДД, а прежняя форма сайта слала
         ДД-ММ-ГГГГ. Приводим к привычному виду, чтобы менеджер видел дату
         в том же формате, что и раньше. */
      var dateField = $('#f-date', form);
      if (dateField && /^\d{4}-\d{2}-\d{2}$/.test(dateField.value)) {
        var p = dateField.value.split('-');
        data.set(dateField.name, p[2] + '-' + p[1] + '-' + p[0]);
      }
      data.append('tildaspec-formid', 'request-form');
      data.append('tildaspec-formskey', form.getAttribute('data-formskey') || '');
      data.append('tildaspec-pageid', root ? root.getAttribute('data-tilda-page-id') : '');
      data.append('tildaspec-projectid', root ? root.getAttribute('data-tilda-project-id') : '');
      data.append('tildaspec-referer', window.location.href);
      data.append('form-spec-comments', '');

      var body = new URLSearchParams();
      data.forEach(function (v, k) { body.append(k, v); });

      submit.disabled = true;
      var label = submit.textContent;
      submit.textContent = 'Отправляем…';
      say('', '');

      fetch('https://forms.tildacdn.com/procces/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8' },
        body: body.toString()
      })
        .then(function (r) { return r.json(); })
        .then(function (res) {
          if (res && res.error) throw new Error(res.error);
          form.reset();
          say('ok', 'Заявка ушла менеджеру. Перезвоним в течение 15 минут в рабочее время, пн–сб с 9:00 до 18:00.');
        })
        .catch(function () {
          say('err', 'Не удалось отправить форму. Позвоните нам: +7 (863) 256-35-30 — или напишите на banket@donexpocentre.ru.');
        })
        .then(function () {
          submit.disabled = false;
          submit.textContent = label;
        });
    });

    function say(kind, text) {
      if (!status) return;
      status.className = 'form-status' + (kind ? ' is-visible form-status--' + kind : '');
      status.textContent = text;
    }
  }

  /* ---------- формат мероприятия из кнопки страницы ---------------------- */
  /* Живёт отдельно от нашей формы: в Tilda форму даёт штатный блок,
     а подставить формат всё равно нужно. */
  document.addEventListener('click', function (e) {
    var t = e.target.closest('[data-format]');
    if (!t) return;
    var sel = findField('f-format', FIELD_FORMAT);
    if (!sel) return;
    var want = t.getAttribute('data-format');
    if ($$('option', sel).some(function (o) { return o.value === want; })) setField(sel, want);
  });

  /* ---------- anchor scrolling ------------------------------------------- */
  /* Отступ под фиксированную шапку задаётся в css через scroll-margin-top,
     поэтому здесь достаточно scrollIntoView. Ленивые картинки догружаются
     уже во время прокрутки и сдвигают вёрстку вниз, из-за чего плавный
     скролл недоезжает — после остановки доводим цель на место. */
  function scrollToTarget(el) {
    el.scrollIntoView({ behavior: reduced ? 'auto' : 'smooth', block: 'start' });
    el.setAttribute('tabindex', '-1');
    el.focus({ preventScroll: true });
    if (reduced) return;

    var tries = 0;
    var settle = function () {
      var drift = el.getBoundingClientRect().top - 84;
      var canScroll = window.scrollY + window.innerHeight < document.body.scrollHeight - 4;
      if (Math.abs(drift) > 24 && canScroll && tries < 3) {
        tries++;
        el.scrollIntoView({ behavior: 'auto', block: 'start' });
        setTimeout(settle, 220);
      }
    };
    setTimeout(settle, 700);
  }

  document.addEventListener('click', function (e) {
    var a = e.target.closest('a[href^="#"]');
    if (!a) return;
    var id = a.getAttribute('href');
    if (id.length < 2) return;
    /* Tilda отдаёт якорь блока то как id, то как <a name>. Поддерживаем оба,
       иначе теряется отступ под шапку и плавная прокрутка. */
    var key = id.slice(1);
    var target = document.getElementById(key) ||
                 document.querySelector('a[name="' + key + '"]');
    if (!target) return;
    e.preventDefault();
    scrollToTarget(target);
  });
})();
