/* GA4 キーイベント計測（全ページ共通）
   contact_click          : 問い合わせ導線(メール/フォームへのリンク)のクリック
   shindan_click          : 無料AI診断への導線クリック
   contact_submit_attempt : 人の入力と判定して実際にFormspreeへ送った
   contact_submit_blocked : 自動投稿と判定して送らなかった(reasonに判定理由)
   contact_submit_recovered : 自動投稿と判定したが、本人が確認して送信を続行した
   contact_submit_error   : 送ったがFormspreeがエラーを返した
   ※ 受理された件数は thanks.html 側の contact_submit で数える。

   2026-08-06追記: 8/4-8/5は attempt 4件に対しFormspreeからのメールは1件。
   Formspreeは受理(200)を返しつつスパム判定で3件を捨てていた。
   受理件数=届いた件数ではないため、自動投稿は自前でFormspreeに渡す前に止める。

   2026-08-24追記: 8/17-8/23の週次点検で blocked 10件(5ユーザー)を観測したが、
   GA4のカスタム定義が0件で reason パラメータがディメンションとして
   登録されておらず、内訳がレポートにもデータ探索にも一切出てこなかった。
   管理画面の設定に依存しないよう、reasonをイベント名にも展開する。
   あわせて、タイミング判定で本物の人を行き止まりにしない導線を入れた。 */
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

  function setupForm(form) {
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
    ['keydown', 'input', 'paste', 'pointerdown', 'change'].forEach(function (type) {
      form.addEventListener(type, function (ev) {
        /* keydown と pointerdown は実操作のみ採用する。
           input / paste / change はパスワードマネージャや自動入力が
           isTrusted=false で発火させることがあるため信頼フラグを問わない。
           値を直接代入するbotはどのイベントも発火させないので判定は保てる。 */
        var human = (type === 'keydown' || type === 'pointerdown') ? ev.isTrusted : true;
        if (!form._firstTouch && human) form._firstTouch = Date.now();
      }, true);
    });

    form.addEventListener('submit', function (e) {
      e.preventDefault();

      /* --- 自動投稿の判定 --- */
      var gotcha = form.querySelector('[name="_gotcha"]');
      var reason = '';
      if (gotcha && gotcha.value) reason = 'honeypot_gotcha';
      else if (form.website_url && form.website_url.value) reason = 'honeypot_injected';
      else if (!form._firstTouch) reason = 'no_human_input';
      else if (Date.now() - LOADED_AT < MIN_DWELL_MS) reason = 'too_fast_page';
      else if (Date.now() - form._firstTouch < MIN_FILL_MS) reason = 'too_fast_fill';

      if (reason) {
        track('contact_submit_blocked', { reason: reason });
        /* カスタムディメンション未登録でも内訳が読めるよう、
           イベント名そのものにreasonを持たせる。 */
        track('contact_submit_blocked_' + reason, { reason: reason });

        /* ハニーポットは人には見えず触れない項目なので確実に自動投稿。ここは通さない。 */
        if (reason === 'honeypot_gotcha' || reason === 'honeypot_injected') return;

        /* タイミング系の3つは本物の人を巻き込みうる。
           行き止まりにせず、本人の意思で送り直せる逃げ道を残す。 */
        if (!window.confirm(
          '自動送信の可能性がある操作として検出されました。\n' +
          'ご本人でしたら、このまま送信できます。送信しますか？\n\n' +
          'うまくいかない場合は info@aidollargame.com までご連絡ください。'
        )) return;
        track('contact_submit_recovered', { reason: reason });
      }

      var next = form.querySelector('[name="_next"]');
      var thanksUrl = next ? next.value : '/thanks.html';
      var btn = form.querySelector('button, input[type="submit"]');
      var label = btn ? btn.innerHTML : '';
      if (btn) { btn.disabled = true; btn.innerHTML = '送信中...'; }

      track('contact_submit_attempt', {
        form_id: (form.getAttribute('action') || '').split('/').pop(),
        /* _firstTouch が無いまま本人確認で通った場合は経過秒を出せないので -1 を入れる。
           0起点で引くとエポック秒がそのまま入るため。 */
        fill_seconds: form._firstTouch ? Math.round((Date.now() - form._firstTouch) / 1000) : -1,
        blocked_reason: reason || 'none'
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

  var forms = document.querySelectorAll('form[action*="formspree"]');
  for (var i = 0; i < forms.length; i++) setupForm(forms[i]);
})();
