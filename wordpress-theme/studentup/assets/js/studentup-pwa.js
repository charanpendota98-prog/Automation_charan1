/* StudentUp PWA / App download (v72.1)
 * Enti chestundi:
 *   1) service worker register (query URL → root scope) — repeat visits fast + offline page
 *   2) "⬇️ Download App" button — prathi visit lo kanipistundi (standalone lo hide)
 *      · Android/Chrome: beforeinstallprompt prompt
 *      · iPhone/desktop: device-wise steps sheet (Share → Add to Home Screen)
 *   3) install ayyaka button hide
 * No external library. Vanilla only.
 */
(function () {
  "use strict";
  var D = window.STUDENTUP_PWA || {};
  var btn = document.getElementById("installbtn");
  var sheet = document.getElementById("installhint");
  var nowBtn = document.getElementById("installnow");
  var closeBtn = document.getElementById("installclose");
  var steps = document.getElementById("isteps");
  var deferred = null;
  var standalone = (window.matchMedia &&
    window.matchMedia("(display-mode: standalone)").matches) ||
    window.navigator.standalone === true;

  /* ---------- 1) service worker ---------- */
  if (D.sw && "serviceWorker" in navigator && location.protocol === "https:") {
    try {
      navigator.serviceWorker.register(D.sw, { scope: D.scope || "/" }).catch(function () {});
    } catch (e) {}
  }

  if (standalone) {                       /* already app-laga open — button vaddu */
    if (btn) btn.hidden = true;
    if (sheet) sheet.hidden = true;
    return;
  }

  var ua = navigator.userAgent || "";
  var isIos = /iPad|iPhone|iPod/.test(ua);
  var isAndroid = /Android/i.test(ua);

  function moved(list, want) {            /* device ki taggattu steps order */
    if (!list || !list.length) return;
    var order = isIos ? [1, 0, 2] : (isAndroid ? [0, 2, 1] : [2, 0, 1]);
    var items = order.map(function (i) { return list[i]; }).filter(Boolean);
    while (steps.firstChild) steps.removeChild(steps.firstChild);
    items.forEach(function (li) { steps.appendChild(li); });
  }

  function openSheet() {
    if (!sheet) return;
    if (steps) moved(Array.prototype.slice.call(steps.children));
    sheet.hidden = false;
    if (btn) btn.setAttribute("aria-expanded", "true");
    if (closeBtn) closeBtn.focus();
  }
  function closeSheet() {
    if (sheet) sheet.hidden = true;
    if (btn) btn.setAttribute("aria-expanded", "false");
  }

  window.addEventListener("beforeinstallprompt", function (e) {
    e.preventDefault();
    deferred = e;
  });

  function installNow() {
    if (!deferred) return false;
    deferred.prompt();
    if (deferred.userChoice && deferred.userChoice.then) {
      deferred.userChoice.then(function () { deferred = null; });
    }
    closeSheet();
    return true;
  }

  if (btn) {
    btn.addEventListener("click", function () {
      if (!installNow()) openSheet();
    });
  }
  if (nowBtn) nowBtn.addEventListener("click", function () { if (!installNow()) openSheet(); });
  if (closeBtn) closeBtn.addEventListener("click", closeSheet);
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") closeSheet();
  });

  window.addEventListener("appinstalled", function () {
    if (btn) btn.hidden = true;
    closeSheet();
  });
})();
