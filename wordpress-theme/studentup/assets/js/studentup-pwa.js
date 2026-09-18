/* StudentUp PWA (v72) — app-laga install + offline.
 * Enti chestundi:
 *   1) service worker register (query URL → root scope) — repeat visits fast + offline page
 *   2) "యాప్‌గా ఇన్‌స్టాల్ చేయండి" button (Android/Chrome beforeinstallprompt,
 *      iPhone ki Share → Add to Home Screen hint)
 *   3) install ayyaka button hide (appinstalled)
 * No external library. Vanilla only.
 */
(function () {
  "use strict";
  var D = window.STUDENTUP_PWA || {};
  var btn = document.getElementById("installbtn");
  var hint = document.getElementById("installhint");
  var standalone = window.matchMedia &&
    window.matchMedia("(display-mode: standalone)").matches;
  if (window.navigator.standalone === true) standalone = true;

  /* ---------- 1) service worker ---------- */
  if (D.sw && "serviceWorker" in navigator && location.protocol === "https:") {
    try {
      navigator.serviceWorker.register(D.sw, { scope: D.scope || "/" }).catch(function () {});
    } catch (e) {}
  }

  if (standalone) {                       /* already app-laga open — button vaddu */
    if (btn) btn.hidden = true;
    if (hint) hint.hidden = true;
    return;
  }

  var deferred = null;
  window.addEventListener("beforeinstallprompt", function (e) {
    e.preventDefault();
    deferred = e;
    if (btn) btn.hidden = false;
  });

  var isIos = /iPad|iPhone|iPod/.test(navigator.userAgent || "");
  function remember(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  function recall(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }

  /* iOS lo beforeinstallprompt event undadu → chinna hint (oka sari chusi, dismiss cheyyochu) */
  if (isIos && btn && recall("su_ios_hint") !== "off") {
    btn.hidden = false;
  }

  if (btn) {
    btn.addEventListener("click", function () {
      if (deferred) {
        deferred.prompt();
        if (deferred.userChoice && deferred.userChoice.then) {
          deferred.userChoice.then(function () { deferred = null; btn.hidden = true; });
        }
        return;
      }
      if (hint) {
        hint.hidden = false;
        hint.textContent = D.iosHint || "Share → Add to Home Screen";
        setTimeout(function () { hint.hidden = true; }, 9000);
      }
      remember("su_ios_hint", "off");
    });
  }

  window.addEventListener("appinstalled", function () {
    if (btn) btn.hidden = true;
    if (hint) hint.hidden = true;
    remember("su_ios_hint", "off");
  });
})();
