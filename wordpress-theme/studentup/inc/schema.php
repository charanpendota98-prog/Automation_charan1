<?php
/**
 * v64: JSON-LD schema — Organization + WebSite (SearchAction) + BreadcrumbList.
 *
 * Post-level Article/JobPosting/FAQ schema bot nunchi vasthundi (autoblog/seo.py);
 * site identity schema (ee file) WordPress nunchi — Google ki "ee site evaru" ani.
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * wp_head lo schema (admin/feed lo vaddu).
 */
function studentup_schema_head() {
	if ( is_admin() || is_feed() || ! studentup_opt( 'schema', '1' ) ) {
		return;
	}
	$home  = home_url( '/' );
	$name  = get_bloginfo( 'name' );
	$desc  = get_bloginfo( 'description' );
	$logo  = has_custom_logo() ? wp_get_attachment_image_url( get_theme_mod( 'custom_logo' ), 'full' ) : '';
	$socials = array_values( studentup_social_links() );

	$org = array(
		'@type' => 'Organization',
		'@id'   => $home . '#org',
		'name'  => $name,
		'url'   => $home,
	);
	if ( $logo ) {
		$org['logo'] = array( '@type' => 'ImageObject', 'url' => $logo );
	}
	if ( $socials ) {
		$org['sameAs'] = $socials;
	}
	if ( $desc ) {
		$org['description'] = $desc;
	}
	$site = array(
		'@type'           => 'WebSite',
		'@id'             => $home . '#website',
		'url'             => $home,
		'name'            => $name,
		'publisher'       => array( '@id' => $home . '#org' ),
		'inLanguage'      => 'te-IN',
		'potentialAction' => array(
			'@type'       => 'SearchAction',
			'target'      => array(
				'@type'       => 'EntryPoint',
				'urlTemplate' => $home . '?s={search_term_string}',
			),
			'query-input' => 'required name=search_term_string',
		),
	);
	$graph = array( $org, $site );

	if ( is_singular() ) {
		$graph[] = array(
			'@type'           => 'BreadcrumbList',
			'@id'             => get_permalink() . '#breadcrumb',
			'itemListElement' => studentup_breadcrumb_items(),
		);
	}
	echo '<script type="application/ld+json">'
		. wp_json_encode( array( '@context' => 'https://schema.org', '@graph' => $graph ), JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES )
		. '</script>' . "\n";
}
add_action( 'wp_head', 'studentup_schema_head', 5 );

/**
 * Breadcrumb items (Rank Math breadcrumb unte adi vadhu — duplicate avvali).
 */
function studentup_breadcrumb_items() {
	$items = array(
		array( '@type' => 'ListItem', 'position' => 1, 'name' => 'Home', 'item' => home_url( '/' ) ),
	);
	if ( is_singular( 'post' ) ) {
		$cats = get_the_category();
		if ( $cats ) {
			$items[] = array(
				'@type'    => 'ListItem',
				'position' => 2,
				'name'     => $cats[0]->name,
				'item'     => get_category_link( $cats[0] ),
			);
		}
		$items[] = array(
			'@type'    => 'ListItem',
			'position' => count( $items ) + 1,
			'name'     => get_the_title(),
			'item'     => get_permalink(),
		);
	}
	return $items;
}

/**
 * NewsArticle schema for single posts (Google News / Discover eligibility).
 *
 * v141: only emitted when nothing else already describes the article — if Rank
 * Math (or another SEO plugin) is active it owns the Article graph and a second
 * one would be a duplicate. The bot's in-content Article/FAQ schema is also
 * detected, so a post never carries two competing article nodes.
 *
 * @return void
 */
function studentup_newsarticle_schema() {
	if ( is_admin() || is_feed() || ! is_singular( 'post' ) ) {
		return;
	}
	if ( ! studentup_opt( 'news_schema', '1' ) ) {
		return;
	}
	if ( class_exists( 'RankMath' ) || defined( 'WPSEO_VERSION' ) || defined( 'SEOPRESS_VERSION' ) ) {
		return; // SEO plugin already emits the article graph.
	}
	$post_id = get_the_ID();
	$content = (string) get_post_field( 'post_content', $post_id );
	if ( false !== strpos( $content, '"@type": "Article"' ) || false !== strpos( $content, '"@type":"Article"' ) ) {
		return; // bot already shipped the Article node inside the content
	}
	$image = get_the_post_thumbnail_url( $post_id, 'full' );
	$data  = array(
		'@context'         => 'https://schema.org',
		'@type'            => 'NewsArticle',
		'@id'              => get_permalink( $post_id ) . '#newsarticle',
		'headline'         => wp_trim_words( get_the_title( $post_id ), 20, '' ),
		'description'      => wp_strip_all_tags( get_the_excerpt( $post_id ) ),
		'datePublished'    => get_the_date( DATE_W3C, $post_id ),
		'dateModified'     => get_the_modified_date( DATE_W3C, $post_id ),
		'inLanguage'       => get_bloginfo( 'language' ),
		'mainEntityOfPage' => get_permalink( $post_id ),
		'author'           => array(
			'@type' => 'Person',
			'name'  => get_the_author_meta( 'display_name', (int) get_post_field( 'post_author', $post_id ) ),
			'url'   => get_author_posts_url( (int) get_post_field( 'post_author', $post_id ) ),
		),
		'publisher'        => array( '@id' => home_url( '/' ) . '#org' ),
	);
	if ( $image ) {
		$data['image'] = array( $image );
	}
	echo '<script type="application/ld+json">'
		. wp_json_encode( $data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES )
		. '</script>' . "\n";
}
add_action( 'wp_head', 'studentup_newsarticle_schema', 7 );
