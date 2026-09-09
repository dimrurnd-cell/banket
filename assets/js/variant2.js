/* Second homepage: guest recommendation, navigation and gallery focus.
   Existing site.js continues to own forms, gallery and anchor scrolling. */
(function () {
  'use strict';

  var root = document.querySelector('.bn2');
  if (!root) return;

  var number = root.querySelector('#v2-guests');
  var range = root.querySelector('#v2-range');
  var status = root.querySelector('#v2-recommendation');
  var cards = Array.prototype.slice.call(root.querySelectorAll('[data-v2-hall]'));
  var presets = Array.prototype.slice.call(root.querySelectorAll('[data-v2-guests]'));
  var minimum = 20;
  var maximum = 2500;
  var current = 120;
  var chosen = false;
  var numberDirty = false;
  var syncingForm = false;
  var hallNames = {
    bankethall: 'Банкетный зал',
    ametist: 'зал «Аметист»',
    vystavochny: 'Выставочный зал'
  };

  function bounded(value) {
    return Math.max(minimum, Math.min(maximum, Math.round(value)));
  }

  function guestLabel(value) {
    var lastTwo = value % 100;
    var last = value % 10;
    if (lastTwo >= 11 && lastTwo <= 14) return value + ' гостей';
    if (last === 1) return value + ' гость';
    if (last >= 2 && last <= 4) return value + ' гостя';
    return value + ' гостей';
  }

  function findGuestField() {
    var field = document.getElementById('f-guests');
    if (field) return field;
    var names = ['guests', 'Выберите количество гостей', 'Выберите число гостей'];
    for (var i = 0; i < names.length; i++) {
      field = document.querySelector('[name="' + names[i] + '"]');
      if (field) return field;
    }
    return null;
  }

  function syncForm() {
    if (!chosen) return;
    var field = findGuestField();
    if (!field || field.value === String(current)) return;
    field.value = String(current);
    syncingForm = true;
    try {
      field.dispatchEvent(new Event('input', { bubbles: true }));
      field.dispatchEvent(new Event('change', { bubbles: true }));
    } finally {
      syncingForm = false;
    }
  }

  function render(updateNumber) {
    var hall = current <= 150 ? 'bankethall' : current <= 500 ? 'ametist' : 'vystavochny';
    if (updateNumber) number.value = String(current);
    range.value = String(current);
    range.setAttribute('aria-valuetext', guestLabel(current));
    range.style.setProperty('--v2-range-progress', ((current - minimum) / (maximum - minimum) * 100) + '%');

    cards.forEach(function (card) {
      var recommended = card.getAttribute('data-v2-hall') === hall;
      card.classList.toggle('is-recommended', recommended);
      Array.prototype.forEach.call(card.querySelectorAll('[data-v2-badge]'), function (badge) {
        badge.hidden = !recommended;
        badge.textContent = current < 50 ? 'Уточним рассадку' : 'Подходит вам';
      });
    });
    presets.forEach(function (preset) {
      preset.setAttribute('aria-pressed', String(Number(preset.getAttribute('data-v2-guests')) === current));
    });
    if (status) {
      status.textContent = current < 50 ?
        'Для небольшого мероприятия уточним рассадку с менеджером. Можно выбрать зал просторнее.' :
        'Гостей: ' + current + '. Рекомендуем ' + hallNames[hall] + '. Можно выбрать зал просторнее.';
    }
  }

  function choose(value, updateNumber) {
    current = bounded(value);
    chosen = true;
    render(updateNumber);
    syncForm();
  }

  if (number && range) {
    number.min = range.min = String(minimum);
    number.max = range.max = String(maximum);
    number.step = '1';
    /* A range with step=10 silently rounds exact entries such as 123. */
    range.step = '1';
    var initial = number.value.trim() === '' ? NaN : Number(number.value);
    current = Number.isFinite(initial) ? bounded(initial) : current;
    if (status) {
      status.setAttribute('aria-live', 'polite');
      status.setAttribute('aria-atomic', 'true');
    }
    render(true);

    /* A later edit in the request form is the newest choice. Delegation
       also handles native Tilda fields inserted after this script runs. */
    function guestFieldChanged(event) {
      if (syncingForm || event.target === number || event.target === range || event.target !== findGuestField()) return;
      var text = String(event.target.value).trim();
      var value = text === '' ? NaN : Number(text);
      numberDirty = false;
      if (!Number.isFinite(value) || !Number.isInteger(value) || value < minimum || value > maximum) {
        chosen = false;
        return;
      }
      current = value;
      chosen = true;
      render(true);
    }
    document.addEventListener('input', guestFieldChanged);
    document.addEventListener('change', guestFieldChanged);

    range.addEventListener('input', function () {
      choose(Number(range.value), true);
    });
    number.addEventListener('input', function () {
      /* Do not clamp intermediate input: typing 250 must allow 2, then 25. */
      numberDirty = true;
      if (number.value.trim() === '') return;
      var value = Number(number.value);
      if (Number.isFinite(value) && Number.isInteger(value) && value >= minimum && value <= maximum) {
        choose(value, false);
      }
    });
    function finishNumber() {
      if (!numberDirty) return;
      numberDirty = false;
      var value = number.value.trim() === '' ? NaN : Number(number.value);
      if (Number.isFinite(value)) choose(value, true);
      else render(true);
    }
    number.addEventListener('change', finishNumber);
    number.addEventListener('blur', finishNumber);

    presets.forEach(function (preset) {
      preset.addEventListener('click', function () {
        var value = Number(preset.getAttribute('data-v2-guests'));
        if (Number.isFinite(value)) choose(value, true);
      });
    });
    root.addEventListener('click', function (event) {
      if (event.target.closest('a[href="#zayavka"]')) syncForm();
    });
  }

  var toggle = root.querySelector('#v2-menu-toggle');
  var nav = root.querySelector('#v2-nav');
  if (toggle && nav) {
    function setOpen(open, returnFocus) {
      toggle.setAttribute('aria-expanded', String(open));
      nav.classList.toggle('is-open', open);
      if (returnFocus) toggle.focus();
    }
    setOpen(false, false);
    toggle.addEventListener('click', function () {
      setOpen(toggle.getAttribute('aria-expanded') !== 'true', false);
    });
    nav.addEventListener('click', function (event) {
      if (event.target.closest('a')) setOpen(false, false);
    });
    document.addEventListener('click', function (event) {
      if (!nav.contains(event.target) && !toggle.contains(event.target)) setOpen(false, false);
    });
    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') {
        event.preventDefault();
        setOpen(false, true);
      }
    });
  }

  /* site.js opens and closes its shared lightbox. Capture the initiating
     button before that handler runs; query the lightbox at event time so
     this enhancement also works when Tilda loads site.js afterwards. */
  var galleryTrigger = null;

  function restoreGalleryFocus() {
    var trigger = galleryTrigger;
    if (!trigger) return;
    window.setTimeout(function () {
      var lightbox = document.querySelector('.lightbox');
      if (galleryTrigger !== trigger || (lightbox && lightbox.classList.contains('is-open'))) return;
      galleryTrigger = null;
      if (document.documentElement.contains(trigger)) trigger.focus({ preventScroll: true });
    }, 0);
  }

  document.addEventListener('click', function (event) {
    var shot = event.target.closest('.v2-gallery-shot');
    if (shot && root.contains(shot)) {
      galleryTrigger = shot;
      return;
    }
    var lightbox = document.querySelector('.lightbox.is-open');
    if (!galleryTrigger || !lightbox) return;
    if (event.target === lightbox || event.target.closest('.lightbox__close')) restoreGalleryFocus();
  }, true);

  document.addEventListener('keydown', function (event) {
    var lightbox = document.querySelector('.lightbox.is-open');
    if (!galleryTrigger || !lightbox) return;
    if (event.key === 'Escape') {
      restoreGalleryFocus();
      return;
    }
    if (event.key !== 'Tab') return;

    var controls = Array.prototype.slice.call(lightbox.querySelectorAll(
      '.lightbox__close, .lightbox__nav--prev, .lightbox__nav--next'
    )).filter(function (control) {
      return !control.disabled && control.tabIndex >= 0 && !control.hidden &&
        control.getClientRects().length > 0 && window.getComputedStyle(control).visibility !== 'hidden';
    });
    if (!controls.length) return;
    event.preventDefault();
    var index = controls.indexOf(document.activeElement);
    var next = index < 0 ? (event.shiftKey ? controls.length - 1 : 0) :
      (index + (event.shiftKey ? -1 : 1) + controls.length) % controls.length;
    controls[next].focus();
  }, true);
})();
