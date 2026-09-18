<?php
/**
 * v64: PWA + performance head hints.
 *
 * Mobile lo "Add to Home screen" (app laga), theme-color, preconnect
 * (AdSense/GA — first ad request fast), apple touch icon.
 * Service worker ledu — shared hosting lo stale cache risk vaddu (honest).
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
		'description'      => get_bloginfo( 'description' ),
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
