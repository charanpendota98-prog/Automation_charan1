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
		array( '@type' => 'ListItem', 'position' => 1, 'name' => 'హోమ్', 'item' => home_url( '/' ) ),
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
