/*
 * AIdollargame - lightweight bilingual (JA/EN) switcher for a static site.
 *
 * How it works:
 *  - Japanese is the source content written directly in the HTML.
 *  - Each translatable element carries a `data-en` attribute holding its
 *    English innerHTML (use curly quotes “ ” instead of " to avoid escaping;
 *    apostrophes are fine inside a double-quoted attribute).
 *  - <title data-en="..."> switches the browser tab title too.
 *  - Language is auto-detected from the browser (non-Japanese => English),
 *    can be overridden with the floating toggle button, and is remembered
 *    in localStorage.
 *
 * Per page you only need:
 *    <script src="i18n.js" defer></script>   (use ../i18n.js from subdirs)
 *  plus `data-en` attributes on the text you want translated.
 */
(function () {
  var STORAGE_KEY = "adg-lang";

  // Shared pub/sub so JS-driven demos (chat demos, quiz, cycle animation) can
  // react to language changes. Created defensively because inline page scripts
  // may run before this deferred file loads.
  var I = (window.ADGI18n = window.ADGI18n || { lang: null, _subs: [] });
  if (!I._subs) I._subs = [];
  if (!I.onChange) {
    I.onChange = function (fn) {
      this._subs.push(fn);
      if (this.lang) { try { fn(this.lang); } catch (e) {} }
    };
  }

  function detect() {
    try {
      var saved = localStorage.getItem(STORAGE_KEY);
      if (saved === "ja" || saved === "en") return saved;
    } catch (e) {}
    var n = (navigator.language || navigator.userLanguage || "ja").toLowerCase();
    return n.indexOf("ja") === 0 ? "ja" : "en";
  }

  function apply(lang) {
    var root = document.documentElement;
    root.setAttribute("lang", lang);
    root.setAttribute("data-lang", lang);

    var els = document.querySelectorAll("[data-en]");
    for (var i = 0; i < els.length; i++) {
      var el = els[i];
      if (el.getAttribute("data-ja") === null) {
        // remember the original Japanese once
        el.setAttribute("data-ja", el.tagName === "TITLE" ? el.textContent : el.innerHTML);
      }
      var val = lang === "en" ? el.getAttribute("data-en") : el.getAttribute("data-ja");
      if (el.tagName === "TITLE") {
        el.textContent = val;
      } else {
        el.innerHTML = val;
      }
    }

    var btn = document.getElementById("adg-lang-toggle");
    if (btn) btn.textContent = lang === "en" ? "日本語" : "EN";

    // notify JS-driven demos
    I.lang = lang;
    for (var k = 0; k < I._subs.length; k++) {
      try { I._subs[k](lang); } catch (e) {}
    }
  }

  function setLang(lang) {
    try { localStorage.setItem(STORAGE_KEY, lang); } catch (e) {}
    apply(lang);
  }

  function injectToggle() {
    if (document.getElementById("adg-lang-toggle")) return;

    var style = document.createElement("style");
    style.textContent =
      "#adg-lang-toggle{position:fixed;right:16px;bottom:16px;z-index:9999;" +
      "font:600 13px/1 -apple-system,BlinkMacSystemFont,'Helvetica Neue',Arial,sans-serif;" +
      "letter-spacing:.04em;padding:9px 14px;border-radius:999px;cursor:pointer;" +
      "color:#fff;background:rgba(10,18,56,.9);border:1px solid rgba(255,255,255,.35);" +
      "backdrop-filter:blur(6px);-webkit-backdrop-filter:blur(6px);" +
      "box-shadow:0 4px 16px rgba(0,0,0,.25);transition:transform .15s ease,opacity .15s ease}" +
      "#adg-lang-toggle:hover{transform:translateY(-2px);opacity:.92}";
    document.head.appendChild(style);

    var btn = document.createElement("button");
    btn.id = "adg-lang-toggle";
    btn.type = "button";
    btn.setAttribute("aria-label", "Switch language / 言語切替");
    btn.addEventListener("click", function () {
      var cur = document.documentElement.getAttribute("data-lang") || detect();
      setLang(cur === "en" ? "ja" : "en");
    });
    document.body.appendChild(btn);
  }

  function init() {
    injectToggle();
    apply(detect());
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
