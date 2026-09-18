/* studentup.in service worker (v72)
 * Goal: app-like speed on mobile — shell cached, HTML network-first (fresh news),
 * offline shows the last cached page instead of the browser error.
 */
var VERSION = "su-v72-2";   // v72.1: App sheet + అర్హత sections
var SHELL = ["./", "./index.html", "./favicon.svg", "./manifest.webmanifest", "./robots.txt"];
var OFFLINE_HTML =
  "<!doctype html><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>" +
  "<title>studentup.in — offline</title>" +
  "<body style='font-family:system-ui,sans-serif;margin:0;padding:28px;text-align:center;color:#0f2e62'>" +
  "<h1 style='font-size:20px'>ఇంటర్నెట్ లేదు</h1>" +
  "<p style='color:#5b6b85;font-size:14px;line-height:1.7'>మీరు చూసిన పేజీలు మళ్లీ కనిపిస్తాయి — " +
  "కనెక్షన్ వచ్చాక కొత్త ఉద్యోగాలు, ఫలితాలు automatic ga update avutayi.</p>" +
  "<p style='font-size:14px'><a href='./index.html' style='color:#2463b7'>↻ మళ్లీ ప్రయత్నించండి</a></p>";

self.addEventListener("install", function (e) {
  e.waitUntil(caches.open(VERSION).then(function (c) { return c.addAll(SHELL).catch(function () {}); })
    .then(function () { return self.skipWaiting(); }));
});

self.addEventListener("activate", function (e) {
  e.waitUntil(caches.keys().then(function (keys) {
    return Promise.all(keys.map(function (k) { return k === VERSION ? null : caches.delete(k); }));
  }).then(function () { return self.clients.claim(); }));
});

self.addEventListener("fetch", function (e) {
  var req = e.request;
  if (req.method !== "GET") return;
  var url = new URL(req.url);
  if (url.origin !== self.location.origin) return;              /* ads/analytics untouch */
  if (req.mode === "navigate" || (req.headers.get("accept") || "").indexOf("text/html") > -1) {
    e.respondWith(fetch(req).then(function (res) {
      var copy = res.clone();
      caches.open(VERSION).then(function (c) { c.put(req, copy); });
      return res;
    }).catch(function () {
      return caches.match(req).then(function (hit) { return hit || new Response(OFFLINE_HTML, { headers: { "Content-Type": "text/html; charset=utf-8" } }); });
    }));
    return;
  }
  e.respondWith(caches.match(req).then(function (hit) {
    return hit || fetch(req).then(function (res) {
      if (res && res.status === 200 && res.type === "basic") {
        var copy = res.clone();
        caches.open(VERSION).then(function (c) { c.put(req, copy); });
      }
      return res;
    }).catch(function () { return hit; });
  }));
});
