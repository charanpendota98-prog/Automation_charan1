<?php
/**
 * v63: SEO bridge — allow Rank Math meta to be written through the REST API.
 *
 * Enduku idi (nijamaina problem):
 *   WordPress default ga custom post meta ni REST lo accept cheyyadu. Bot
 *   (Application Password tho) `rank_math_focus_keyword`, `rank_math_title`,
 *   `rank_math_description`, `rank_math_robots` pampiste WordPress 400 isthundi
 *   → appudu bot meta lekunda post pedutundi → **SEO fields khali ga migilipothayi**
 *   (Rank Math lo score takkuva, Google ki signals thakkuva).
 *
 * Ee file aa meta keys ni REST ki register chestundi (edit_posts unna user matrame).
 * Rank Math plugin unna/lekapoyina harmless — keys register avutayi.
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Rank Math meta keys — bot (autoblog/seo.py rankmath_meta) pampichevi.
 *
 * @return string[]
 */
function studentup_rankmath_keys() {
	return array(
		'rank_math_seo_score',   // bot compute chesina score (admin column)
		'rank_math_title',
		'rank_math_description',
		'rank_math_focus_keyword',
		'rank_math_robots',
		'rank_math_facebook_title',
		'rank_math_facebook_description',
		'rank_math_twitter_title',
		'rank_math_twitter_description',
		'rank_math_twitter_use_open_graph',
		'rank_math_canonical_url',
	);
}

/**
 * REST lo write allow — prathi post type ki (post/page).
 */
function studentup_register_seo_meta() {
	$types = apply_filters( 'studentup_seo_meta_post_types', array( 'post', 'page' ) );
	foreach ( studentup_rankmath_keys() as $key ) {
		foreach ( $types as $type ) {
			register_post_meta(
				$type,
				$key,
				array(
					'show_in_rest'  => true,
					'single'        => true,
					'type'          => 'string',
					'auth_callback' => function ( $allowed, $meta_key, $post_id ) {
						return current_user_can( 'edit_post', $post_id );
					},
				)
			);
		}
	}
}
add_action( 'init', 'studentup_register_seo_meta' );

/**
 * rank_math_robots array ga vasthundi (bot: ["index, follow, max-image-preview:large"]).
 * REST schema string aduguthundi → string ki convert chesi store chestundi.
 */
add_filter(
	'rest_pre_insert_value',
	function ( $value, $request, $key ) {
		if ( in_array( $key, studentup_rankmath_keys(), true ) && is_array( $value ) ) {
			$value = implode( ', ', array_map( 'sanitize_text_field', $value ) );
		}
		return $value;
	},
	10,
	3
);

/**
 * v80 (P5): on-page fallback — Rank Math ACTIVE lekapothe mattrame.
 * Rank Math unte adi title/meta/canonical/OG anni output chestundi (duplicate vaddu).
 * Lekapothe: WP core title + canonical untayi; description + OG maname isthamu
 * (bot rasina rank_math_description/focus meta nunchi — kotha invent ledu).
 */
function studentup_seo_fallback_head() {
	if ( is_admin() || is_feed() ) {
		return;
	}
	if ( defined( 'RANK_MATH_VERSION' ) || class_exists( 'RankMath' ) ) {
		return;   // Rank Math handles everything
	}
	// v84: Yoast/AIOSEO unna double-meta vaddu (owner vere plugin vesthe).
	if ( defined( 'WPSEO_VERSION' ) || defined( 'AIOSEO_VERSION' ) ) {
		return;
	}
	$desc = '';
	if ( is_singular() ) {
		$desc = (string) get_post_meta( get_the_ID(), 'rank_math_description', true );
		if ( '' === $desc ) {
			$desc = get_the_excerpt();
		}
		$img = get_the_post_thumbnail_url( get_the_ID(), 'large' );
	} else {
		$desc = get_bloginfo( 'description' );
		$img  = '';
	}
	$desc = trim( wp_strip_all_tags( (string) $desc ) );
	if ( '' !== $desc ) {
		echo '<meta name="description" content="' . esc_attr( mb_substr( $desc, 0, 160 ) ) . '">' . "\n";
		echo '<meta property="og:description" content="' . esc_attr( mb_substr( $desc, 0, 200 ) ) . '">' . "\n";
	}
	if ( is_singular() ) {
		echo '<meta property="og:title" content="' . esc_attr( wp_strip_all_tags( get_the_title() ) ) . '">' . "\n";
		echo '<meta property="og:url" content="' . esc_url( get_permalink() ) . '">' . "\n";
		echo '<meta property="og:type" content="article">' . "\n";
		if ( $img ) {
			echo '<meta property="og:image" content="' . esc_url( $img ) . '">' . "\n";
		}
		echo '<meta name="twitter:card" content="summary_large_image">' . "\n";
	}
	echo '<meta property="og:site_name" content="' . esc_attr( get_bloginfo( 'name' ) ) . '">' . "\n";
}
add_action( 'wp_head', 'studentup_seo_fallback_head', 5 );

/**
 * Ee site ki SEO bridge active ani bot ki cheppadam (verification kosam).
 *   GET /wp-json/studentup/v1/theme-info
 */
add_action(
	'rest_api_init',
	function () {
		register_rest_route(
			'studentup/v1',
			'/theme-info',
			array(
				'methods'             => 'GET',
				'permission_callback' => '__return_true',
				'callback'            => function () {
					return new WP_REST_Response(
						array(
							'theme'      => 'studentup',
							'version'    => defined( 'STUDENTUP_VERSION' ) ? STUDENTUP_VERSION : '',
							'seo_bridge' => true,
							'rankmath'   => defined( 'RANK_MATH_VERSION' ) || class_exists( 'RankMath' ),
							'adsense'    => (bool) get_option( 'studentup_adsense_client', '' ),
							'posts'      => (int) wp_count_posts()->publish,
						),
						200
					);
				},
			)
		);
	}
);
