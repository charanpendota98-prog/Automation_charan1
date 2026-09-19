<?php
/**
 * v64: PWA + performance head hints.
 *
 * Mobile lo "Add to Home screen" (app laga), theme-color, preconnect
 * (AdSense/GA — first ad request fast), apple touch icon.
 * v72: service worker kuda undi (query tho serve — / lo scope header tho). Adi only
 * site pages/fonts cache chestundi; AdSense/analytics requests ni touch cheyyadu.
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * manifest.json ni query tho serve cheyyadam (rewrite rules avasaram ledu).
 */
function studentup_manifest() {
	if ( ! isset( $_GET['studentup_manifest'] ) ) { // phpcs:ignore WordPress.Security.NonceVerification
		return;
	}
	$icon = '';
	if ( has_site_icon() ) {
		$icon = get_site_icon_url( 512 );
	}
	$manifest = array(
		'name'             => get_bloginfo( 'name' ),
		'short_name'       => mb_substr( get_bloginfo( 'name' ), 0, 12 ),
		'start_url'        => home_url( '/' ),
		'scope'            => home_url( '/' ),
		'display'          => 'standalone',
		'background_color' => '#ffffff',
		'theme_color'      => '#0f2e62',
		'lang'             => 'te-IN',
		'orientation'      => 'portrait',
		'description'      => get_bloginfo( 'description' ),
		'categories'       => array( 'news', 'education', 'jobs' ),
		// v72.1: app icon long-press → nerugaa mukhyamaina sections (student-focus)
		'shortcuts'        => array(
			array(
				'name'       => 'Jobs',
				'short_name' => 'Jobs',
				'url'        => home_url( '/#jobs' ),
			),
			array(
				'name'       => 'Jobs by qualification',
				'short_name' => 'Qualification',
				'url'        => home_url( '/#qualsplit' ),
			),
			array(
				'name'       => 'Results',
				'short_name' => 'Results',
				'url'        => home_url( '/#results' ),
			),
			array(
				'name'       => 'Daily Quiz',
				'short_name' => 'Quiz',
				'url'        => home_url( '/#quiz' ),
			),
		),
	);
	if ( $icon ) {
		$manifest['icons'] = array(
			array( 'src' => $icon, 'sizes' => '512x512', 'type' => 'image/png', 'purpose' => 'any' ),
		);
	}
	nocache_headers();
	header( 'Content-Type: application/manifest+json; charset=utf-8' );
	echo wp_json_encode( $manifest, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES );
	exit;
}
add_action( 'template_redirect', 'studentup_manifest' );

/**
 * head hints: manifest link, theme-color, preconnect, apple icon.
 */
function studentup_head_hints() {
	if ( is_admin() ) {
		return;
	}
	echo '<meta name="theme-color" content="#0f2e62">' . "\n";
	echo '<link rel="preconnect" href="https://pagead2.googlesyndication.com" crossorigin>' . "\n";
	echo '<link rel="dns-prefetch" href="https://www.googletagmanager.com">' . "\n";
	if ( studentup_opt( 'pwa', '1' ) ) {
		echo '<link rel="manifest" href="' . esc_url( add_query_arg( 'studentup_manifest', '1', home_url( '/' ) ) ) . '">' . "\n";
		echo '<meta name="apple-mobile-web-app-capable" content="yes">' . "\n";
		echo '<meta name="apple-mobile-web-app-title" content="' . esc_attr( get_bloginfo( 'name' ) ) . '">' . "\n";
		if ( has_site_icon() ) {
			echo '<link rel="apple-touch-icon" href="' . esc_url( get_site_icon_url( 180 ) ) . '">' . "\n";
		}
	}
}
add_action( 'wp_head', 'studentup_head_hints', 3 );

/**
 * v72: service worker JS (query `?studentup_sw=1` tho serve — root scope header tho).
 *
 * Enti cache avutundi: site pages (network-first → fresh news), static files
 * (cache-first). Enti cache avvadu: AdSense/GA/third-party (avvi touch cheyyamu).
 *
 * @return string
 */
function studentup_sw_js() {
	$ver     = defined( 'STUDENTUP_VERSION' ) ? STUDENTUP_VERSION : '1';
	$offline = '<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
		. '<title>Offline — ' . esc_html( get_bloginfo( 'name' ) ) . '</title>'
		. '<body style="font-family:system-ui,sans-serif;margin:0;padding:28px;text-align:center;color:#0f2e62">'
		. '<h1 style="font-size:20px">You are offline</h1>'
		. '<p style="color:#5b6b85;font-size:14px;line-height:1.7">Pages you already visited stay available — new jobs, results and updates load once you are back online.</p>'
		. '<p style="font-size:14px"><a href="' . esc_url( home_url( '/' ) ) . '" style="color:#2463b7">↻ Try again</a></p>';

	return 'var VERSION=' . wp_json_encode( 'su-' . $ver ) . ';' . "\n"
		. 'var OFFLINE=' . wp_json_encode( $offline ) . ';' . "\n"
		. 'var SHELL=' . wp_json_encode( array( home_url( '/' ) ) ) . ';' . "\n"
		. <<<'JSEOF'
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
  if (url.origin !== self.location.origin) return;   /* ads/analytics untouch */
  var isHtml = req.mode === "navigate" || (req.headers.get("accept") || "").indexOf("text/html") > -1;
  if (isHtml) {
    e.respondWith(fetch(req).then(function (res) {
      var copy = res.clone();
      caches.open(VERSION).then(function (c) { c.put(req, copy); });
      return res;
    }).catch(function () {
      return caches.match(req).then(function (hit) {
        return hit || new Response(OFFLINE, { headers: { "Content-Type": "text/html; charset=utf-8" } });
      });
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
JSEOF;
}

/**
 * Service worker ni query tho serve cheyyadam (rewrite rule avasaram ledu).
 */
function studentup_service_worker() {
	if ( ! isset( $_GET['studentup_sw'] ) ) { // phpcs:ignore WordPress.Security.NonceVerification
		return;
	}
	if ( ! studentup_opt( 'pwa', '1' ) ) {
		return;
	}
	nocache_headers();
	header( 'Content-Type: application/javascript; charset=utf-8' );
	header( 'Service-Worker-Allowed: /' );
	echo studentup_sw_js(); // phpcs:ignore WordPress.Security.EscapeOutput
	exit;
}
add_action( 'template_redirect', 'studentup_service_worker' );

/**
 * Install-prompt JS ki data pass (SW url, iOS hint).
 */
function studentup_pwa_data() {
	if ( is_admin() || ! wp_script_is( 'studentup-pwa', 'enqueued' ) ) {
		return;
	}
	wp_localize_script(
		'studentup-pwa',
		'STUDENTUP_PWA',
		array(
			'sw'      => esc_url_raw( add_query_arg( 'studentup_sw', '1', home_url( '/' ) ) ),
			'scope'   => '/',
			'iosHint' => 'iPhone: tap Share → Add to Home Screen to install it like an app.',
		)
	);
}
add_action( 'wp_enqueue_scripts', 'studentup_pwa_data', 20 );

/**
 * AdSense auto ads script (option ON unte mattrame) — AdSense policy: ee code
 * unte site lo ads Google auto ga pedutundi; slots manual ga kuda undachu.
 */
function studentup_adsense_auto_head() {
	if ( is_admin() || ! studentup_opt( 'adsense_auto', '0' ) ) {
		return;
	}
	$client = (string) studentup_opt( 'adsense_client', '' );
	if ( ! preg_match( '/^ca-pub-\d{10,}$/', $client ) ) {
		return;
	}
	echo '<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client='
		. esc_attr( $client ) . '" crossorigin="anonymous"></script>' . "\n";
}
add_action( 'wp_head', 'studentup_adsense_auto_head', 6 );
