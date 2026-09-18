<?php
/**
 * v67: SECURITY HARDENING — top-theme level hardening (shared hosting safe).
 *
 * Enti chestundi:
 *  · Security headers (clickjacking · MIME sniffing · referrer · permissions)
 *  · WordPress version geneator meta theeseyadam (fingerprinting)
 *  · XML-RPC / pingback off (bot REST API vaadutundi — XML-RPC avasaram ledu)
 *  · ?author=N enumeration block (user names leak avvavu)
 *  · Emoji scripts theeseyadam (perf: 2 requests + inline CSS)
 *  · Attachment pages → parent post ki redirect (thin page index avvavu)
 *  · Comment flood guard (link count limit — spam)
 *
 * CSP add cheyyaledu: AdSense/analytics inline scripts tho conflict avutundi — adi
 * hosting/WAF level lo cheyyali (docs lo chusandi). Option: StudentUp → Advanced →
 * Security hardening OFF (emergency lo mattrame).
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Hardening ON aa? (default ON — emergency lo admin nunchi OFF cheyyochu)
 *
 * @return bool
 */
function studentup_security_on() {
	return '0' !== (string) studentup_opt( 'security_hardening', '1' );
}

/**
 * Security headers (front-end + admin, cheap — hosting lo mod_headers lekapoyina pani chestundi).
 */
function studentup_security_headers() {
	if ( is_admin() || ! studentup_security_on() ) {
		return;
	}
	if ( headers_sent() ) {
		return;
	}
	header( 'X-Content-Type-Options: nosniff' );
	header( 'X-Frame-Options: SAMEORIGIN' );
	header( 'Referrer-Policy: strict-origin-when-cross-origin' );
	header( 'Permissions-Policy: geolocation=(), microphone=(), camera=()' );
	header( 'Cross-Origin-Opener-Policy: same-origin-allow-popups' );
}
add_action( 'send_headers', 'studentup_security_headers' );

/**
 * WP version meta + emoji scripts theeseyadam (fingerprint + perf).
 */
function studentup_clean_head() {
	if ( ! studentup_security_on() ) {
		return;
	}
	remove_action( 'wp_head', 'wp_generator' );
	remove_action( 'wp_head', 'wp_shortlink_wp_head' );
	remove_action( 'wp_head', 'print_emoji_detection_script', 7 );
	remove_action( 'wp_print_styles', 'print_emoji_styles' );
	remove_action( 'admin_print_scripts', 'print_emoji_detection_script' );
	remove_action( 'admin_print_styles', 'print_emoji_styles' );
}
add_action( 'init', 'studentup_clean_head' );

/**
 * XML-RPC off (REST API tho bot pani chestundi — XML-RPC attack surface thagginchadam).
 *
 * @param bool $enabled XML-RPC enabled.
 * @return bool
 */
function studentup_disable_xmlrpc( $enabled ) {
	return studentup_security_on() ? false : $enabled;
}
add_filter( 'xmlrpc_enabled', 'studentup_disable_xmlrpc' );

/**
 * ?author=N enumeration block — usernames leak avvakunda home ki pampadam.
 */
function studentup_block_author_enum() {
	if ( ! studentup_security_on() || is_admin() || is_user_logged_in() ) {
		return;
	}
	if ( isset( $_GET['author'] ) && ! is_author() ) { // phpcs:ignore WordPress.Security.NonceVerification
		wp_safe_redirect( home_url( '/' ), 301 );
		exit;
	}
	if ( isset( $_GET['author'] ) && preg_match( '/^\d+$/', (string) wp_unslash( $_GET['author'] ) ) ) { // phpcs:ignore WordPress.Security.NonceVerification
		wp_safe_redirect( home_url( '/' ), 301 );
		exit;
	}
}
add_action( 'template_redirect', 'studentup_block_author_enum' );

/**
 * Attachment pages → parent post (thin content index avvakunda, AdSense quality safe).
 */
function studentup_attachment_redirect() {
	if ( ! studentup_security_on() || ! is_attachment() ) {
		return;
	}
	$parent = get_post_parent();
	if ( $parent ) {
		wp_safe_redirect( get_permalink( $parent ), 301 );
		exit;
	}
	wp_safe_redirect( home_url( '/' ), 301 );
	exit;
}
add_action( 'template_redirect', 'studentup_attachment_redirect' );

/**
 * Comment link-flood guard (spam comment moderation load thagginchadam).
 *
 * @param array $comment_data Comment data.
 * @return array
 */
function studentup_comment_flood_guard( $comment_data ) {
	if ( isset( $comment_data['comment_content'] ) ) {
		$links = preg_match_all( '#https?://#i', (string) $comment_data['comment_content'] );
		if ( $links > 3 ) {
			wp_die( esc_html__( 'ఒక కామెంట్‌లో 3 కంటే ఎక్కువ లింక్‌లు అనుమతి లేదు.', 'studentup' ),
				esc_html__( 'కామెంట్ నిరాకరించబడింది', 'studentup' ), 403 );
		}
	}
	return $comment_data;
}
add_filter( 'preprocess_comment', 'studentup_comment_flood_guard' );

/**
 * Admin: file editor off (hosting lo accidental code edits prevent) — option tho.
 */
function studentup_maybe_disable_file_edit() {
	if ( ! studentup_security_on() ) {
		return;
	}
	if ( ! defined( 'DISALLOW_FILE_EDIT' ) ) {
		define( 'DISALLOW_FILE_EDIT', true );
	}
}
add_action( 'admin_init', 'studentup_maybe_disable_file_edit' );
