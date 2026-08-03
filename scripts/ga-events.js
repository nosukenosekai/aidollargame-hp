/* GA4 キーイベント計測（全ページ共通）
   contact_click          : 問い合わせ導線(メール/フォームへのリンク)のクリック
   shindan_click          : 無料AI診断への導線クリック
   contact_submit_attempt : 問い合わせフォームの送信ボタンを押した(成功したとは限らない)
   ※ 実際に送信が通った件数は thanks.html 側の contact_submit で数える。
      submit イベントは Formspree に受理されなくても発火するため、ここでは成功を測れない。 */
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

  /* Formspreeフォームは自前でAJAX送信する。
     理由: _next(送信後の遷移先)が効かずFormspree既定の完了画面に飛ぶため、
     サンクスページに到達せず成功件数を数えられない(2026-08-03に実送信で確認)。
     AJAXなら受理/失敗が戻り値で分かり、遷移も自分で制御できる。 */
  var forms = document.querySelectorAll('form[action*="formspree"]');
  for (var i = 0; i < forms.length; i++) {
    forms[i].addEventListener('submit', function (e) {
      var form = e.target;
      e.preventDefault();

      /* ハニーポットが埋まっている＝自動投稿。送信もGA4計上もしない。 */
      var gotcha = form.querySelector('[name="_gotcha"]');
      if (gotcha && gotcha.value) return;

      var next = form.querySelector('[name="_next"]');
      var thanksUrl = next ? next.value : '/thanks.html';
      var btn = form.querySelector('button, input[type="submit"]');
      var label = btn ? btn.innerHTML : '';
      if (btn) { btn.disabled = true; btn.innerHTML = '送信中...'; }

      track('contact_submit_attempt', { form_id: (form.getAttribute('action') || '').split('/').pop() });

      fetch(form.action, {
        method: 'POST',
        body: new FormData(form),
        headers: { Accept: 'application/json' }
      }).then(function (res) {
        if (res.ok) {
          location.href = thanksUrl;
          return;
        }
        throw new Error('status ' + res.status);
      }).catch(function (err) {
        track('contact_submit_error', { reason: String(err && err.message || err).slice(0, 100) });
        if (btn) { btn.disabled = false; btn.innerHTML = label; }
        alert('送信に失敗しました。お手数ですが info@aidollargame.com までご連絡ください。');
      });
    });
  }
})();
