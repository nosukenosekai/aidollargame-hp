/* GA4 キーイベント計測（全ページ共通）
   contact_click          : 問い合わせ導線(メール/フォームへのリンク)のクリック
   shindan_click          : 無料AI診断への導線クリック
   contact_submit_attempt : 人の入力と判定して実際にFormspreeへ送った
   contact_submit_blocked : 自動投稿と判定して送らなかった(reasonに判定理由)
   contact_submit_error   : 送ったがFormspreeがエラーを返した
   ※ 受理された件数は thanks.html 側の contact_submit で数える。

   2026-08-06追記: 8/4-8/5は attempt 4件に対しFormspreeからのメールは1件。
   Formspreeは受理(200)を返しつつスパム判定で3件を捨てていた。
   受理件数=届いた件数ではないため、自動投稿は自前でFormspreeに渡す前に止める。 */
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
  var LOADED_AT = Date.now();
  var MIN_DWELL_MS = 5000;      /* ページを開いてから送信までの最短時間 */
  var MIN_FILL_MS = 2000;       /* 最初の入力から送信までの最短時間 */

  var forms = document.querySelectorAll('form[action*="formspree"]');
  for (var i = 0; i < forms.length; i++) {
    var form = forms[i];

    /* 2つめのハニーポット。HTMLに書かずJSで差し込むので、
       静的にHTMLを読むタイプの収集botの目に触れない。
       全項目を機械的に埋めるbotだけがここに値を入れる。 */
    var trap = document.createElement('input');
    trap.type = 'text';
    trap.name = 'website_url';
    trap.tabIndex = -1;
    trap.autocomplete = 'off';
    trap.setAttribute('aria-hidden', 'true');
    trap.style.cssText = 'position:absolute;left:-9999px;width:1px;height:1px;opacity:0;';
    form.appendChild(trap);

    /* 人が触った証拠を記録する。プログラムから value を代入しただけでは
       input も keydown も発生しないため、機械的な投稿と区別できる。 */
    form._firstTouch = 0;
    ['keydown', 'input', 'paste', 'pointerdown'].forEach(function (type) {
      form.addEventListener(type, function (ev) {
        if (!form._firstTouch && ev.isTrusted) form._firstTouch = Date.now();
      }, true);
    });

    form.addEventListener('submit', function (e) {
      var form = e.target;
      e.preventDefault();

      /* --- 自動投稿の判定。ここを通さないものは送信もGA4計上もしない --- */
      var gotcha = form.querySelector('[name="_gotcha"]');
      var reason = '';
      if (gotcha && gotcha.value) reason = 'honeypot_gotcha';
      else if (form.website_url && form.website_url.value) reason = 'honeypot_injected';
      else if (!form._firstTouch) reason = 'no_human_input';
      else if (Date.now() - LOADED_AT < MIN_DWELL_MS) reason = 'too_fast_page';
      else if (Date.now() - form._firstTouch < MIN_FILL_MS) reason = 'too_fast_fill';

      if (reason) {
        track('contact_submit_blocked', { reason: reason });
        /* 万一これが本物の人だった場合の逃げ道を必ず出す */
        if (reason !== 'honeypot_gotcha' && reason !== 'honeypot_injected') {
          alert('送信を確認できませんでした。お手数ですが info@aidollargame.com までご連絡ください。');
        }
        return;
      }

      var next = form.querySelector('[name="_next"]');
      var thanksUrl = next ? next.value : '/thanks.html';
      var btn = form.querySelector('button, input[type="submit"]');
      var label = btn ? btn.innerHTML : '';
      if (btn) { btn.disabled = true; btn.innerHTML = '送信中...'; }

      track('contact_submit_attempt', {
        form_id: (form.getAttribute('action') || '').split('/').pop(),
        fill_seconds: Math.round((Date.now() - form._firstTouch) / 1000)
      });

      var payload = new FormData(form);
      payload.delete('website_url');  /* 罠フィールドはメール本文に出さない */

      fetch(form.action, {
        method: 'POST',
        body: payload,
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
