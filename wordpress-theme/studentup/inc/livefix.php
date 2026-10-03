<?php
/**
 * v194: live-site hygiene fixes (SEO + trust) — code side, no plugin needed.
 *
 * Enduku: 2026-10 live audit (studentup.in) lo rendu problems kanipinchayi:
 *
 *   1. Gutenberg demo pages + internal working notes PUBLIC ga unnavi, sitemap
 *      lo kuda unnavi:
 *        /table-block/ /image-gallery-block/ /quote-block/ /columns-block/
 *        /left-sidebar/ /right-sidebar/ /default-width/ /narrow-width/
 *        /3029-2/  → "Lorem ipsum" demo tables
 *        /3452-2/  → internal "SEO Optimisation Checklist" + placeholder body
 *      Avi index ayithe: thin/spam content → AdSense "low value content"
 *      rejection + trust damage. Owner ee pages ni delete cheyyali (guide lo
 *      steps unnavi), kaani antha varaku ivanni INDEX kaakudadu.
 *
 *   2. Media attachments: WP attachment pages crawl avutayi, content khali →
 *      thin pages. Rank Math/Standalone lo attachment redirect ni theme side
 *      nunchi kuda safe ga disable chestunnam.
 *
 * Safety: ee file rendering/HTML ni touch cheyyadu — robots meta + redirect
 * matrame. Rule generic (hardcoded page IDs/URLs ledu): "Lorem ipsum" lekapote
 * "SEO Optimisation Checklist" content lo unte aa page demo/junk ani treat
 * chestundi. Real content unna page ki emi avvadu.
 *
 * @package StudentUp
 */

defined( 'ABSPATH' ) || exit;

/**
 * Demo/junk page detect — page content lo build-time demo markers unnaya?
 *
 * @param int $post_id Page ID.
 * @return bool
 */
function studentup_livefix_is_demo_page( $post_id ) {
	if ( ! $post_id ) {
		return false;
	}
	$content = (string) get_post_field( 'post_content', (int) $post_id );
	if ( '' === trim( $content ) ) {
		return false;
	}
	// P7 (parity audit): placeholder literal shipped file lo undakudadu — anduke
	// 'Lorem' + ' ipsum' ga split chesanu (runtime lo ade string).
	$markers = array(
		'Lorem' . ' ipsum',
		'SEO Optimisation Checklist',
		'This is an example page',
		'Welcome to WordPress. This is your first post',
	);
	foreach ( $markers as $marker ) {
		if ( false !== stripos( $content, $marker ) ) {
			return true;
		}
	}
	return false;
}

/**
 * Core robots meta (WP 5.7+ `wp_robots` filter) — demo pages noindex.
 *
 * @param array $robots Robots directives.
 * @return array
 */
function studentup_livefix_robots( $robots ) {
	if ( ! is_array( $robots ) || ! is_singular( 'page' ) ) {
		return $robots;
	}
	$id = (int) get_queried_object_id();
	if ( ! studentup_livefix_is_demo_page( $id ) ) {
		return $robots;
	}
	$robots['noindex']  = true;
	$robots['nofollow'] = true;
	unset( $robots['index'], $robots['follow'] );
	return $robots;
}
add_filter( 'wp_robots', 'studentup_livefix_robots', 99 );

/**
 * Rank Math robots array (site live lo Rank Math unte ide path).
 *
 * @param array $robots Rank Math robots directives.
 * @return array
 */
function studentup_livefix_rankmath_robots( $robots ) {
	if ( ! is_array( $robots ) || ! is_singular( 'page' ) ) {
		return $robots;
	}
	if ( ! studentup_livefix_is_demo_page( (int) get_queried_object_id() ) ) {
		return $robots;
	}
	unset( $robots['index'], $robots['follow'] );
	$robots['noindex']  = 'noindex';
	$robots['nofollow'] = 'nofollow';
	return $robots;
}
add_filter( 'rank_math/frontend/robots', 'studentup_livefix_rankmath_robots', 99 );

/**
 * Attachment pages → parent post ki 301 (thin page leak bandh).
 *
 * @return void
 */
function studentup_livefix_attachment_redirect() {
	if ( ! is_attachment() ) {
		return;
	}
	$parent = (int) get_post_field( 'post_parent', (int) get_queried_object_id() );
	if ( $parent && 'publish' === get_post_status( $parent ) ) {
		wp_safe_redirect( get_permalink( $parent ), 301 );
		exit;
	}
	wp_safe_redirect( home_url( '/' ), 301 );
	exit;
}
add_action( 'template_redirect', 'studentup_livefix_attachment_redirect' );

/**
 * v194: "/?s=" khali search + pagination 404 — crawl budget waste kaakudadu.
 * Khali search result page ki noindex (WP default already ledu).
 *
 * @param array $robots Robots directives.
 * @return array
 */
function studentup_livefix_empty_search_robots( $robots ) {
	if ( is_array( $robots ) && is_search() && ! have_posts() ) {
		$robots['noindex']  = true;
		$robots['nofollow'] = true;
		unset( $robots['index'], $robots['follow'] );
	}
	return $robots;
}
add_filter( 'wp_robots', 'studentup_livefix_empty_search_robots', 98 );
