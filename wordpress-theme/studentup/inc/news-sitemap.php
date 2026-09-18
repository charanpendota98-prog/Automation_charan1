<?php
/**
 * v66: GOOGLE NEWS / DISCOVER sitemap — /news-sitemap.xml
 *
 * Enduku: Google News + Discover ki 48 gantala lopu publish ayyina posts
 * (image tho) chupiyali. Idi lekapote Discover/News eligibility thakkuva.
 * Robots lo kuda reference add avutundi (option ON unte).
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * /news-sitemap.xml → WP posts (48h) + title + publication date + image.
 */
function studentup_news_sitemap() {
	if ( ! isset( $_SERVER['REQUEST_URI'] ) ) {
		return;
	}
	$path = strtok( (string) wp_unslash( $_SERVER['REQUEST_URI'] ), '?' ); // phpcs:ignore WordPress.Security.ValidatedSanitizedInput
	if ( ! in_array( rtrim( (string) $path, '/' ), array( '/news-sitemap.xml', '/news-sitemap' ), true ) ) {
		return;
	}
	if ( ! studentup_opt( 'news_sitemap', '1' ) ) {
		wp_die( 'news sitemap off', '', array( 'response' => 404 ) );
	}
	$posts = get_posts(
		array(
			'numberposts' => 1000,
			'post_status' => 'publish',
			'date_query'  => array( array( 'after' => '48 hours ago' ) ),
		)
	);
	header( 'Content-Type: application/xml; charset=utf-8' );
	$home = home_url( '/' );
	echo '<?xml version="1.0" encoding="UTF-8"?>' . "\n";
	echo '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" ' .
		'xmlns:news="http://www.google.com/schemas/sitemap-news/0.9" ' .
		'xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">' . "\n";
	foreach ( $posts as $p ) {
		$title = wp_strip_all_tags( get_the_title( $p ) );
		echo "\t<url>\n";
		echo "\t\t<loc>" . esc_url( get_permalink( $p ) ) . "</loc>\n";
		echo "\t\t<news:news>\n\t\t\t<news:publication>\n\t\t\t\t<news:name>" .
			esc_html( get_bloginfo( 'name' ) ) . "</news:name>\n" .
			"\t\t\t\t<news:language>te</news:language>\n\t\t\t</news:publication>\n";
		echo "\t\t\t<news:publication_date>" .
			esc_html( get_gmt_from_date( get_post_time( 'Y-m-d H:i:s', false, $p ) ) ) .
			"</news:publication_date>\n";
		echo "\t\t\t<news:title>" . esc_html( $title ) . "</news:title>\n\t\t</news:news>\n";
		if ( has_post_thumbnail( $p ) ) {
			$img = wp_get_attachment_image_src( get_post_thumbnail_id( $p ), 'full' );
			if ( $img ) {
				echo "\t\t<image:image>\n\t\t\t<image:loc>" . esc_url( $img[0] ) .
					"</image:loc>\n\t\t\t<image:title>" . esc_html( $title ) .
					"</image:title>\n\t\t</image:image>\n";
			}
		}
		echo "\t</url>\n";
	}
	echo '</urlset>';
	exit;
}
add_action( 'template_redirect', 'studentup_news_sitemap', 1 );

/**
 * robots.txt lo news sitemap line (Rank Math unte adi kuda chestundi).
 */
function studentup_robots_add_news( $output, $public ) { // phpcs:ignore
	if ( ! $public || ! studentup_opt( 'news_sitemap', '1' ) ) {
		return $output;
	}
	if ( false === strpos( $output, 'news-sitemap.xml' ) ) {
		$output .= "\nSitemap: " . home_url( '/news-sitemap.xml' ) . "\n";
	}
	return $output;
}
add_filter( 'robots_txt', 'studentup_robots_add_news', 20, 2 );
