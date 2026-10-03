<?php
/**
 * v195 — HUB PAGES (topic clusters that concentrate authority + pageviews).
 *
 * Enduku (audit finding #11 in LIVE_SITE_AUDIT_2026-10.md): reader okka job
 * card chusi vellipoyadu → pages/session takkuva → AdSense RPM takkuva.
 * Hub page = "TS Jobs" / "Results" lanti okka URL, andulo aa category lo
 * latest posts + sub-topic links. Google ki topical authority, reader ki next
 * click, revenue ki extra pageview.
 *
 * Design rules (pin-to-pin with the theme):
 *   - Cards inkaa `news` classes ne — same CSS, same look, no new design.
 *   - Server-side render (SEO + CWV) - no JavaScript needed.
 *   - 15 min transient cache → DB load ledu.
 *   - ItemList schema (Google ki list identity).
 *   - Ads: hub page lo normal slot rules ne (`studentup_ad()`), extra slot ledu.
 *
 * Usage (page content lo shortcode):
 *   [studentup_hub cats="ts-jobs,ap-jobs,central-jobs" title="All Government Jobs"]
 *
 * @package StudentUp
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Hub page slugs the setup creates (slug => array( title, cats, intro )).
 *
 * @return array
 */
function studentup_hub_plan() {
	return array(
		'ts-jobs-hub'         => array(
			'Telangana Government Jobs 2026',
			array( 'ts-jobs', 'results', 'hall-ticket' ),
			'TSPSC, TS Police, DSC, Gurukulam and every Telangana state notification — latest first, official source link tho.',
		),
		'ap-jobs-hub'         => array(
			'Andhra Pradesh Government Jobs 2026',
			array( 'ap-jobs', 'results', 'hall-ticket' ),
			'APPSC, AP Police, AP DSC and AP state government notifications — apply dates, eligibility, official links.',
		),
		'central-jobs-hub'    => array(
			'Central Government Jobs 2026',
			array( 'central-jobs', 'results', 'hall-ticket' ),
			'SSC, UPSC, Railway, Bank, Defence and central government job notifications for Telugu students.',
		),
		'results-hub'         => array(
			'Exam Results & Hall Tickets 2026',
			array( 'results', 'hall-ticket', 'admissions' ),
			'Every result and hall ticket link — TS, AP and central exams, updated as soon as the official site publishes.',
		),
		'scholarships-hub'    => array(
			'Scholarships 2026 — Telangana, AP & Central',
			array( 'scholarships', 'admissions', 'internships' ),
			'NSP, ePASS, AICTE and private scholarships with amounts, eligibility and last dates.',
		),
	);
}

/**
 * Hub page URL by slug (footer/menu links ki).
 *
 * @param string $slug Hub slug.
 * @return string
 */
function studentup_hub_url( $slug ) {
	$page = get_page_by_path( $slug );
	return ( $page instanceof WP_Post ) ? get_permalink( $page ) : '';
}

/**
 * Latest posts of a category (cached 15 min).
 *
 * @param string $slug  Category slug.
 * @param int    $limit Count.
 * @return WP_Post[]
 */
function studentup_hub_posts( $slug, $limit = 6 ) {
	$key    = 'su_hub_' . md5( $slug . '|' . (int) $limit );
	$cached = get_transient( $key );
	if ( is_array( $cached ) ) {
		return array_map( 'get_post', $cached );
	}
	$q = new WP_Query(
		array(
			'category_name'       => sanitize_title( $slug ),
			'posts_per_page'      => max( 1, min( 12, (int) $limit ) ),
			'post_status'         => 'publish',
			'ignore_sticky_posts' => true,
			'no_found_rows'       => true,
		)
	);
	$ids = wp_list_pluck( $q->posts, 'ID' );
	set_transient( $key, $ids, 15 * MINUTE_IN_SECONDS );
	return $q->posts;
}

/**
 * Render one hub section (cards reuse the theme card markup classes).
 *
 * @param string $slug  Category slug.
 * @param string $label Heading.
 * @param int    $limit Count.
 * @return string
 */
function studentup_hub_section( $slug, $label, $limit = 6 ) {
	$posts = studentup_hub_posts( $slug, $limit );
	if ( ! $posts ) {
		return '';
	}
	$cat_url = '';
	$term    = get_term_by( 'slug', $slug, 'category' );
	if ( $term && ! is_wp_error( $term ) ) {
		$cat_url = get_term_link( $term );
	}
	$out = '<h2 class="su-hub-h">' . esc_html( $label ) . '</h2><div class="newsgrid">';
	foreach ( $posts as $p ) {
		$out .= studentup_hub_card( $p );
	}
	$out .= '</div>';
	if ( $cat_url && ! is_wp_error( $cat_url ) ) {
		$out .= '<p class="su-hub-more"><a class="su-viewall" href="' . esc_url( $cat_url ) . '">'
			. esc_html( 'See all ' . $label ) . ' ' . studentup_ui_icon( 'arrow-right', 13 ) . '</a></p>';
	}
	return $out;
}

/**
 * One card (same classes as archive cards — pin-to-pin).
 *
 * @param WP_Post $p Post.
 * @return string
 */
function studentup_hub_card( $p ) {
	$id    = (int) $p->ID;
	$title = get_the_title( $id );
	$date  = get_the_date( '', $id );
	$link  = get_permalink( $id );
	$img   = get_the_post_thumbnail( $id, 'studentup-card', array(
		'alt'      => esc_attr( $title ),
		'loading'  => 'lazy',
		'decoding' => 'async',
	) );
	$thumb = $img
		? '<a class="thumb" href="' . esc_url( $link ) . '" aria-hidden="true" tabindex="-1">' . $img . '</a>'
		: '<a class="thumb thumb--auto" href="' . esc_url( $link ) . '" aria-hidden="true" tabindex="-1"><span class="su-cov"><span class="su-cov-brand">StudentUp</span></span></a>';
	return '<article class="news su-hub-card">' . $thumb
		. '<div class="newsbody"><h3><a href="' . esc_url( $link ) . '">' . esc_html( $title ) . '</a></h3>'
		. '<div class="newsfoot"><span class="su-date">' . esc_html( $date ) . '</span>'
		. '<a class="su-readmore" href="' . esc_url( $link ) . '">' . esc_html__( 'View details', 'studentup' ) . ' →</a></div>'
		. '</div></article>';
}

/**
 * [studentup_hub cats="ts-jobs,results" title="…"] shortcode.
 *
 * @param array $atts Attributes.
 * @return string
 */
function studentup_hub_shortcode( $atts ) {
	$atts = shortcode_atts(
		array(
			'cats'  => 'ts-jobs,ap-jobs,central-jobs',
			'title' => '',
			'limit' => 6,
		),
		$atts,
		'studentup_hub'
	);
	$slugs = array_filter( array_map( 'sanitize_title', explode( ',', (string) $atts['cats'] ) ) );
	if ( ! $slugs ) {
		return '';
	}
	$out = '';
	if ( '' !== trim( (string) $atts['title'] ) ) {
		$out .= '<h2 class="sectionhead"><span>' . esc_html( (string) $atts['title'] ) . '</span></h2>';
	}
	foreach ( $slugs as $slug ) {
		$term  = get_term_by( 'slug', $slug, 'category' );
		$label = ( $term && ! is_wp_error( $term ) ) ? $term->name : ucwords( str_replace( '-', ' ', $slug ) );
		$out  .= studentup_hub_section( $slug, $label, (int) $atts['limit'] );
	}
	if ( '' === trim( wp_strip_all_tags( $out ) ) ) {
		// Hub empty (posts levu) → reader ki dead-end vaddu: home + category links.
		$out = '<p>' . esc_html__( 'New notifications are added every day. Meanwhile:', 'studentup' ) . ' '
			. '<a href="' . esc_url( home_url( '/' ) ) . '">' . esc_html__( 'latest updates on the home page', 'studentup' ) . '</a>.</p>';
	}
	return '<div class="su-hub">' . $out . '</div>';
}
add_shortcode( 'studentup_hub', 'studentup_hub_shortcode' );

/**
 * Hub lo unna posts ni ItemList schema ga (Google list identity).
 *
 * @return void
 */
function studentup_hub_schema() {
	if ( is_admin() || ! is_page() ) {
		return;
	}
	$id      = (int) get_queried_object_id();
	$content = (string) get_post_field( 'post_content', $id );
	if ( '' === $content || false === strpos( $content, '[studentup_hub' ) ) {
		return;
	}
	$items = array();
	$pos   = 1;
	foreach ( studentup_hub_posts( 'ts-jobs', 6 ) as $p ) {
		$items[] = array(
			'@type'    => 'ListItem',
			'position' => $pos++,
			'url'      => get_permalink( $p ),
			'name'     => wp_strip_all_tags( get_the_title( $p ) ),
		);
	}
	if ( ! $items ) {
		return;
	}
	$graph = array(
		array(
			'@type'           => 'CollectionPage',
			'@id'             => get_permalink( $id ) . '#hub',
			'name'            => wp_strip_all_tags( get_the_title( $id ) ),
			'url'             => get_permalink( $id ),
			'inLanguage'      => 'te-IN',
			'isPartOf'        => array( '@id' => home_url( '/' ) . '#website' ),
			'mainEntity'      => array(
				'@type'           => 'ItemList',
				'numberOfItems'   => count( $items ),
				'itemListElement' => $items,
			),
		),
	);
	echo '<script type="application/ld+json">'
		. wp_json_encode( array( '@context' => 'https://schema.org', '@graph' => $graph ), JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES )
		. '</script>' . "\n"; // phpcs:ignore WordPress.Security.EscapeOutput -- own JSON-LD.
}
add_action( 'wp_head', 'studentup_hub_schema', 6 );

/**
 * v195: internal-link engine ki hub pages kuda "target" ga — so old posts
 * kotha hub pages ki link istayi (orphan pages fix).
 *
 * @param array $map phrase => url.
 * @return array
 */
function studentup_hub_autolink_targets( $map ) {
	if ( ! is_array( $map ) ) {
		return $map;
	}
	foreach ( studentup_hub_plan() as $slug => $info ) {
		$url = studentup_hub_url( $slug );
		if ( '' === $url ) {
			continue;
		}
		$map[ $info[0] ] = $url;   // pedda phrase (>=14 chars) → pass avutundi.
	}
	return $map;
}
add_filter( 'studentup_autolink_map', 'studentup_hub_autolink_targets', 10, 1 );
