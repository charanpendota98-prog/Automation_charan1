<?php
/**
 * v80: lightweight 301 redirect manager (P29).
 *
 * Enduku: slug marina/old URL unna prathi link link-juice pothundi + 404.
 * RankMath lekapoina redirects pani cheyyali — adi idi. Owner format
 * (StudentUp → Advanced → redirects_json):
 *   {"/old-slug/": "/new-slug/", "/jobs/old/": "/jobs/ts-jobs/"}
 *
 * Rules (master prompt P29):
 *   · exact-path match (query string ignore — tracking params safe)
 *   · self/loop target aite skip (redirect loop impossible)
 *   · target kuda map lo unte final target ki DIRECT 301 (chain ledu)
 *   · only relative paths (open-redirect impossible — external URL reject)
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Raw map (assoc array) — invalid JSON aite empty.
 *
 * @return array<string,string>
 */
function studentup_redirect_map() {
	$raw = (string) studentup_opt( 'redirects_json', '' );
	if ( '' === trim( $raw ) ) {
		return array();
	}
	$map = json_decode( $raw, true );
	if ( ! is_array( $map ) ) {
		return array();
	}
	$out = array();
	foreach ( $map as $from => $to ) {
		$from = '/' . ltrim( trim( (string) $from ), '/' );
		$to   = trim( (string) $to );
		if ( '' === $from || '' === $to || $from === $to ) {
			continue;   // self-target = loop → skip
		}
		if ( preg_match( '#^https?://#i', $to ) || strpos( $to, '//' ) === 0 ) {
			continue;   // external target = open redirect → reject
		}
		$out[ trailingslashit( $from ) ] = '/' . ltrim( $to, '/' );
	}
	return $out;
}

/**
 * Chain resolve: /a→/b→/c aite /a nunchi DIRECT /c (max 5 hops, loop-safe).
 */
function studentup_redirect_resolve( $path, $map ) {
	$seen = array();
	$cur  = trailingslashit( $path );
	for ( $i = 0; $i < 5; $i++ ) {
		if ( ! isset( $map[ $cur ] ) ) {
			return $cur;   // chain end (leda map ledu)
		}
		if ( isset( $seen[ $cur ] ) ) {
			return '';     // loop → redirect vaddu (404 normal)
		}
		$seen[ $cur ] = true;
		$cur          = trailingslashit( $map[ $cur ] );
	}
	return $cur;
}

function studentup_redirect_maybe() {
	// 404 aina pages kevalam — normal pages ni touch cheyyamu.
	if ( is_admin() || ! is_404() ) {
		return;
	}
	$map = studentup_redirect_map();
	if ( ! $map ) {
		return;
	}
	$path = (string) wp_parse_url( $_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH ); // phpcs:ignore WordPress.Security.ValidatedSanitizedInput
	if ( '' === $path ) {
		$path = '/';
	}
	$final = studentup_redirect_resolve( $path, $map );
	if ( '' === $final || trailingslashit( $path ) === $final ) {
		return;   // loop leda no-match → normal 404
	}
	wp_safe_redirect( home_url( $final ), 301 );
	exit;
}
add_action( 'template_redirect', 'studentup_redirect_maybe', 2 );
