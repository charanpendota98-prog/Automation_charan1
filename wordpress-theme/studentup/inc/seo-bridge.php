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
