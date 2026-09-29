<?php
/**
 * v153 — static search index (instant, offline-capable search).
 *
 * The command palette used to hit the REST API on every keystroke: one HTTP
 * round trip per letter, a database query each time, and nothing at all when
 * the reader is offline. Instead the theme now publishes one small JSON index
 * of recent posts, cached in a transient and in the reader's browser, so
 * searching is instant and costs the server nothing.
 *
 * Honest limits, stated in the code so nobody is misled:
 *   - the index holds the most recent `studentup_index_limit()` posts, not the
 *     whole archive; the palette still offers a full-site search link,
 *   - it only contains data that is already public (title, link, category,
 *     last date, qualification),
 *   - it is rebuilt whenever a post is saved, deleted or restored.
 *
 * @package StudentUp
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

const STUDENTUP_INDEX_TRANSIENT = 'studentup_search_index_v1';
const STUDENTUP_INDEX_QUERYVAR  = 'su_index';

/**
 * How many recent posts go into the index.
 *
 * @return int
 */
function studentup_index_limit() {
	$n = (int) studentup_opt( 'index_limit', '300' );
	if ( $n < 20 ) {
		$n = 20;
	}
	if ( $n > 1000 ) {
		$n = 1000;
	}
	return $n;
}

/**
 * Build the index payload (cached in a transient).
 *
 * @return array
 */
function studentup_build_search_index() {
	$cached = get_transient( STUDENTUP_INDEX_TRANSIENT );
	if ( is_array( $cached ) ) {
		return $cached;
	}

	$q = new WP_Query(
		array(
			'post_type'           => 'post',
			'post_status'         => 'publish',
			'posts_per_page'      => studentup_index_limit(),
			'ignore_sticky_posts' => true,
			'no_found_rows'       => true,
			'orderby'             => 'date',
			'order'               => 'DESC',
		)
	);

	$items = array();
	while ( $q->have_posts() ) {
		$q->the_post();
		$cats = get_the_category();
		$cat  = ( is_array( $cats ) && $cats ) ? $cats[0]->name : '';
		$items[] = array(
			't' => wp_strip_all_tags( get_the_title() ),
			'u' => get_permalink(),
			'c' => $cat,
			'd' => get_the_date( 'Y-m-d' ),
			'l' => (string) get_post_meta( get_the_ID(), 'studentup_last_date', true ),
		);
	}
	wp_reset_postdata();

	$payload = array(
		'v'     => STUDENTUP_VERSION,
		'built' => gmdate( 'c' ),
		'count' => count( $items ),
		'items' => $items,
	);

	set_transient( STUDENTUP_INDEX_TRANSIENT, $payload, DAY_IN_SECONDS );
	return $payload;
}

/**
 * Drop the cache whenever content changes.
 */
function studentup_flush_search_index() {
	delete_transient( STUDENTUP_INDEX_TRANSIENT );
}
add_action( 'save_post', 'studentup_flush_search_index' );
add_action( 'deleted_post', 'studentup_flush_search_index' );
add_action( 'untrash_post', 'studentup_flush_search_index' );
add_action( 'switch_theme', 'studentup_flush_search_index' );

/**
 * Register the public query var that serves the index.
 *
 * @param array $vars Query vars.
 * @return array
 */
function studentup_index_query_var( $vars ) {
	$vars[] = STUDENTUP_INDEX_QUERYVAR;
	return $vars;
}
add_filter( 'query_vars', 'studentup_index_query_var' );

/**
 * Serve the index as JSON at `/?su_index=1`.
 */
function studentup_serve_search_index() {
	if ( '1' !== (string) get_query_var( STUDENTUP_INDEX_QUERYVAR ) ) {
		return;
	}
	if ( '1' !== studentup_opt( 'static_search', '1' ) ) {
		return;
	}
	nocache_headers();
	header( 'Content-Type: application/json; charset=utf-8' );
	header( 'X-Robots-Tag: noindex' );
	header( 'Cache-Control: public, max-age=1800' );
	echo wp_json_encode( studentup_build_search_index() );
	exit;
}
add_action( 'template_redirect', 'studentup_serve_search_index', 1 );

/**
 * Tell the front-end where the index lives and which build it is.
 */
function studentup_index_inline_config() {
	if ( '1' !== studentup_opt( 'static_search', '1' ) ) {
		return;
	}
	$url = add_query_arg( STUDENTUP_INDEX_QUERYVAR, '1', home_url( '/' ) );
	printf(
		'<script>window.STUDENTUP=window.STUDENTUP||{};STUDENTUP.indexUrl=%s;STUDENTUP.indexVer=%s;</script>',
		wp_json_encode( esc_url_raw( $url ) ),
		wp_json_encode( STUDENTUP_VERSION )
	);
}
add_action( 'wp_footer', 'studentup_index_inline_config', 4 );
