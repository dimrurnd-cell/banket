/* Use the original Tilda form transport (including captcha and CRM mapping). */
window.t_onReady = window.t_onReady || function (fn) {
  if (document.readyState !== 'loading') fn();
  else document.addEventListener('DOMContentLoaded', fn);
};
window.t_onFuncLoad = window.t_onFuncLoad || function (name, fn) {
  if (typeof window[name] === 'function') return fn();
  var attempts = 0;
  var timer = setInterval(function () {
    if (typeof window[name] === 'function') { clearInterval(timer); fn(); }
    else if (++attempts > 200) clearInterval(timer);
  }, 50);
};
(function () {
  'use strict';
  // Native Tilda only accepts configured production domains. Never send demo leads.
  var local = /^(localhost|127\.0\.0\.1|\[::1\])$/.test(location.hostname);
  function previewOnly(e, form) {
    if (!local || !form) return;
    e.preventDefault(); e.stopImmediatePropagation();
    var msg = form.parentElement.querySelector('.v2-preview-message');
    if (msg) msg.textContent = 'Это локальный предпросмотр. Заявка не отправлена. На рабочем домене форма использует подключённые сервисы Tilda.';
  }
  // Tilda also starts submission from a button click, before a submit event.
  document.addEventListener('click', function (e) {
    var button = e.target.closest('.v2-native-form [type="submit"]');
    if (button) previewOnly(e, button.closest('form'));
  }, true);
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && e.target.matches('.v2-native-form input')) previewOnly(e, e.target.closest('form'));
  }, true);
  document.addEventListener('submit', function (e) {
    if (!e.target.matches('.v2-native-form')) return;
    previewOnly(e, e.target);
  }, true);
  window.t_onReady(function () {
    document.querySelectorAll('.v2-native-form').forEach(function (form) {
      var phone = form.querySelector('[data-russian-phone]');
      if (phone) {
        function maskPhone() {
          var raw = phone.value;
          var caret = phone.selectionStart || 0;
          var digitsBefore = raw.slice(0, caret).replace(/\D/g, '').length;
          var digits = raw.replace(/\D/g, '');
          if (raw.indexOf('+7') === 0 || (digits.length > 10 && /^[78]/.test(digits))) digits = digits.slice(1);
          digits = digits.slice(0, 10);
          var value = '+7';
          if (digits.length) value += ' (' + digits.slice(0, 3);
          if (digits.length >= 3) value += ') ';
          if (digits.length > 3) value += digits.slice(3, 6);
          if (digits.length > 6) value += '-' + digits.slice(6, 8);
          if (digits.length > 8) value += '-' + digits.slice(8, 10);
          phone.value = value;
          var position = value.length;
          if (caret < raw.length) {
            var count = 0;
            for (var i = 0; i < value.length; i++) {
              if (/\d/.test(value[i])) count++;
              if (count >= digitsBefore) { position = Math.max(2, i + 1); break; }
            }
          }
          phone.setSelectionRange(position, position);
        }
        phone.addEventListener('focus', function () { if (!phone.value) phone.value = '+7'; });
        phone.addEventListener('input', maskPhone);
        phone.addEventListener('paste', function (e) {
          var pasted = e.clipboardData.getData('text').replace(/\D/g, '');
          if (pasted.length >= 10) {
            e.preventDefault(); phone.value = pasted; maskPhone();
          }
        });
        phone.addEventListener('blur', function () { if (phone.value === '+7') phone.value = ''; });
      }
      var guests = form.querySelector('[name="guests"]');
      if (guests) { guests.type = 'number'; guests.min = '1'; guests.max = '2500'; guests.step = '1'; }
      var format = form.querySelector('[name="event_type"]');
      if (format && format.dataset.defaultFormat && !format.value) format.value = format.dataset.defaultFormat;
      form.addEventListener('tildaform:aftersuccess', function () {
        // No custom success claim: the native library displays success after acknowledgement.
        if (guests) guests.dispatchEvent(new Event('input', {bubbles:true}));
      });
    });
  });
})();
