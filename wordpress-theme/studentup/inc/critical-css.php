<?php
/**
 * v171: CRITICAL CSS — above-fold inline + full stylesheet async load.
 *
 * Enduku: 154 KB render-blocking CSS phone lo first paint ni 2 round-trips
 * aapestundi. Ippudu:
 *   1) Above-fold CSS (30 KB, build-time extract) → <head> lo inline
 *      → paint ki ZERO external CSS wait.
 *   2) Full CSS → media="print" + onload swap (non-blocking, low priority)
 *      → below-fold late ga kuda perfect styling.
 *   3) <noscript> fallback → JS lekapothe normal blocking load.
 *   4) critical.min.css file lekapothe (dev / manual delete) → purathana
 *      blocking path — theme eppudu break avvadu.
 *
 * Build: python3 tools/build_critical_css.py (build_wp_theme automatic ga run
 * chestundi).
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * v195: Inline CSS context — home / single / archive.
 *
 * Enduku: okate pedda "critical" file anni pages ki inline cheyyadam waste
 * (phone lo prathi pageload ~51 KB inline). Ippudu template batti chinna file
 * vastundi (home ~47 KB, archive ~47 KB), lekapote union file fallback.
 *
 * @return string
 */
function studentup_critical_context() {
	if ( is_front_page() || is_home() ) {
		return 'home';
	}
	if ( is_singular( 'post' ) ) {
		return 'single';
	}
	return 'archive';
}

/**
 * Critical CSS file path — SCRIPT_DEBUG / file lekapothe null (safe fallback).
 *
 * v195: template file (critical-home/single/archive) unte adi, lekapote
 * critical.min.css (union) — theme eppudu break avvadu.
 *
 * @return string|null
 */
function studentup_critical_css_file() {
	static $cache = array();
	if ( defined( 'SCRIPT_DEBUG' ) && SCRIPT_DEBUG ) {
		return false;
	}
	$ctx = studentup_critical_context();
	if ( array_key_exists( $ctx, $cache ) ) {
		return $cache[ $ctx ];
	}
	$dir      = get_template_directory() . '/assets/css/';
	$specific = $dir . 'critical-' . $ctx . '.min.css';
	$union    = $dir . 'critical.min.css';
	$pick     = false;
	if ( is_readable( $specific ) ) {
		$pick = $specific;
	} elseif ( is_readable( $union ) ) {
		$pick = $union;
	}
	$cache[ $ctx ] = $pick;
	return $pick;
}

/**
 * Inline critical CSS — wp_head lo first.
 */
function studentup_critical_css_inline() {
	if ( is_admin() || is_user_logged_in() ) {
		return;   // admin bar + logged-in extras ki normal path (safe).
	}
	$file = studentup_critical_css_file();
	if ( ! $file ) {
		return;
	}
	$css = file_get_contents( $file ); // phpcs:ignore WordPress.WP.AlternativeFunctions -- theme file, build-time generated.
	if ( ! $css || strlen( $css ) > 60000 ) {   // sanity cap — unexpected build output ki.
		return;
	}
	echo '<style id="su-critical">' . $css . '</style>' . "\n"; // phpcs:ignore WordPress.Security.EscapeOutput -- own build output, no user input.
}
add_action( 'wp_head', 'studentup_critical_css_inline', 1 );

/**
 * Full theme stylesheets → async (media=print + onload swap + noscript).
 *
 * @param string $tag    Link tag HTML.
 * @param string $handle Style handle.
 * @return string
 */
function studentup_async_stylesheets( $tag, $handle ) {
	if ( is_admin() || is_user_logged_in() ) {
		return $tag;
	}
	if ( ! studentup_critical_css_file() ) {
		return $tag;
	}
	if ( ! in_array( $handle, array( 'studentup', 'studentup-premium' ), true ) ) {
		return $tag;
	}
	if ( false === strpos( $tag, "media='all'" ) ) {
		return $tag;
	}
	if ( ! preg_match( '/href=[\'"]([^\'"]+)[\'"]/', $tag, $m ) ) {
		return $tag;
	}
	$swap = " media='print' onload=\"this.media='all';this.onload=null;\"";
	$tag  = str_replace( " media='all'", $swap, $tag );
	return $tag . "<noscript><link rel='stylesheet' href='" . esc_url( $m[1] ) . "'></noscript>";
}
add_filter( 'style_loader_tag', 'studentup_async_stylesheets', 10, 2 );
