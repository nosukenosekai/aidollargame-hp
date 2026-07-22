/* GA4 キーイベント計測（全ページ共通）
   contact_click  : 問い合わせ導線(メール/フォームへのリンク)のクリック
   shindan_click  : 無料AI診断への導線クリック
   contact_submit : 問い合わせフォーム送信 */
(function () {
  function track(name, params) {
    if (typeof gtag === 'function') {
      params = params || {};
      params.page_path = location.pathname;
      gtag('event', name, params);
    }
  }

  document.addEventListener('click', function (e) {
    var a = e.target.closest ? e.target.closest('a') : null;
    if (!a) return;
    var href = a.getAttribute('href') || '';
    if (href.indexOf('mailto:') === 0) {
      track('contact_click', { method: 'mail', link_url: href });
    } else if (href.indexOf('#contact') !== -1) {
      track('contact_click', { method: 'form_link' });
    } else if (href.indexOf('shindan') !== -1) {
      track('shindan_click', { link_text: (a.textContent || '').trim().slice(0, 50) });
    }
  });

  var forms = document.querySelectorAll('form[action*="formspree"]');
  for (var i = 0; i < forms.length; i++) {
    forms[i].addEventListener('submit', function () {
      track('contact_submit', {});
    });
  }
})();
