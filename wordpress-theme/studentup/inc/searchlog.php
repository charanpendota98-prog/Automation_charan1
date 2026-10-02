<?php
/**
 * v181 — on-site search demand log.
 *
 * Enduku: students mee site lo **em search chestunnaro** telisthe adi nijamaina
 * content-demand signal (Google keyword tool kanna better). Ee module prathi
 * search ni anonymous ga count chestundi → bot (`run.py --search-demand`) aa
 * list ni teeukuni content gaps ni queue cheshtundi.
 *
 * Privacy (strict):
 *   • 'term' + 'count' + 'zero'(result leda) matrame store avutundi.
 *   • User id / IP / email / user-agent **eppudu store avvadu**.
 *   • Rate limit kosam md5(IP) ni **transient** lo 60s matrame (persist ledu).
 *   • Admin/bot searches log avvavu; 80 char cap; html/tags strip.
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

const STUDENTUP_SEARCHLOG_OPTION = 'studentup_search_log';
const STUDENTUP_SEARCHLOG_MAX    = 200;   // terms cap (option size safe)
const STUDENTUP_SEARCHLOG_WINDOW = 60;    // seconds — per-IP throttle
const STUDENTUP_SEARCHLOG_LIMIT  = 20;    // max logs per window per IP

/**
 * Term ni normalize chesi log lo count penchadam (idempotent per term).
 *
 * @param string $term    Search query.
 * @param int    $results Found posts count (0 = zero-result gap).
 * @return bool
 */
function studentup_searchlog_record( $term, $results = 0 ) {
	$term = sanitize_text_field( (string) $term );
	$term = preg_replace( '/\s+/u', ' ', trim( $term ) );
	if ( '' === $term ) {
		return false;
	}
	if ( function_exists( 'mb_substr' ) ) {
		$term = mb_substr( $term, 0, 80 );
	} else {
		$term = substr( $term, 0, 80 );
	}
	$key  = function_exists( 'mb_strtolower' ) ? mb_strtolower( $term ) : strtolower( $term );
	$zero = ( (int) $results ) < 1;

	$log = get_option( STUDENTUP_SEARCHLOG_OPTION, array() );
	if ( ! is_array( $log ) ) {
		$log = array();
	}
	$found = false;
	foreach ( $log as $i => $row ) {
		if ( isset( $row['term'] ) && $key === $row['term'] ) {
			$log[ $i ]['count'] = (int) $row['count'] + 1;
			$log[ $i ]['zero']  = ( $zero && ! empty( $row['zero'] ) ) ? 1 : ( $zero ? 1 : 0 );
			$log[ $i ]['last']  = current_time( 'Y-m-d' );
			$found              = true;
			break;
		}
	}
	if ( ! $found ) {
		$log[] = array(
			'term'  => $key,
			'count' => 1,
			'zero'  => $zero ? 1 : 0,
			'first' => current_time( 'Y-m-d' ),
			'last'  => current_time( 'Y-m-d' ),
		);
	}
	// cap: count ekkuva unna 200 terms matrame unchadam (option bloat ledu).
	if ( count( $log ) > STUDENTUP_SEARCHLOG_MAX ) {
		usort(
			$log,
			static function ( $a, $b ) {
				return (int) $b['count'] <=> (int) $a['count'];
			}
		);
		$log = array_slice( $log, 0, STUDENTUP_SEARCHLOG_MAX );
	}
	update_option( STUDENTUP_SEARCHLOG_OPTION, $log, false );
	return true;
}

/**
 * Per-IP throttle — md5(IP) ni transient lo (persist ledu, 60s lo poyedi).
 *
 * @return bool true = allowed.
 */
function studentup_searchlog_allowed() {
	$ip = isset( $_SERVER['REMOTE_ADDR'] ) ? sanitize_text_field( wp_unslash( $_SERVER['REMOTE_ADDR'] ) ) : '';
	if ( '' === $ip ) {
		return true;   // unknown IP — throttle skip (log mattrame chestam)
	}
	$key   = 'su_sl_' . md5( $ip . '|' . gmdate( 'YmdHi' ) );
	$count = (int) get_transient( $key );
	if ( $count >= STUDENTUP_SEARCHLOG_LIMIT ) {
		return false;
	}
	set_transient( $key, $count + 1, STUDENTUP_SEARCHLOG_WINDOW );
	return true;
}

/**
 * REST: POST (public log) + GET (admin-only read — bot app password tho).
 */
function studentup_searchlog_rest() {
	register_rest_route(
		'studentup/v1',
		'/search-log',
		array(
			array(
				'methods'             => 'POST',
				'callback'            => 'studentup_searchlog_post',
				'permission_callback' => '__return_true',
				'args'                => array(
					'q'       => array( 'type' => 'string', 'required' => true ),
					'results' => array( 'type' => 'integer', 'required' => false ),
				),
			),
			array(
				'methods'             => 'GET',
				'callback'            => 'studentup_searchlog_get',
				'permission_callback' => static function () {
					return current_user_can( 'edit_posts' );
				},
			),
		)
	);
}
add_action( 'rest_api_init', 'studentup_searchlog_rest' );

/**
 * POST callback — reader search ni log cheyyadam.
 *
 * @param WP_REST_Request $req Request.
 * @return WP_REST_Response
 */
function studentup_searchlog_post( $req ) {
	if ( ! studentup_searchlog_allowed() ) {
		return new WP_REST_Response( array( 'ok' => false, 'reason' => 'throttled' ), 429 );
	}
	$term    = (string) $req->get_param( 'q' );
	$results = (int) $req->get_param( 'results' );
	$ok      = studentup_searchlog_record( $term, $results );
	return new WP_REST_Response( array( 'ok' => $ok ), $ok ? 200 : 400 );
}

/**
 * GET callback — bot ki aggregated list (admin only).
 *
 * @return WP_REST_Response
 */
function studentup_searchlog_get() {
	$log = get_option( STUDENTUP_SEARCHLOG_OPTION, array() );
	if ( ! is_array( $log ) ) {
		$log = array();
	}
	usort(
		$log,
		static function ( $a, $b ) {
			return (int) $b['count'] <=> (int) $a['count'];
		}
	);
	$terms = array();
	foreach ( $log as $row ) {
		$terms[] = array(
			'term'  => (string) $row['term'],
			'count' => (int) $row['count'],
			'zero'  => ! empty( $row['zero'] ),
			'last'  => isset( $row['last'] ) ? (string) $row['last'] : '',
		);
	}
	return new WP_REST_Response(
		array(
			'total'   => array_sum( wp_list_pluck( $terms, 'count' ) ),
			'updated' => current_time( 'c' ),
			'terms'   => $terms,
		),
		200
	);
}

/**
 * REST search-knob: live-search palette /wp/v2/search hit ainappudu log.
 *
 * @param WP_REST_Response|mixed $result  Dispatch result.
 * @param WP_REST_Server         $server  Server.
 * @param WP_REST_Request        $request Request.
 * @return mixed
 */
function studentup_searchlog_rest_hook( $result, $server, $request ) {
	if ( ! $request || '/wp/v2/search' !== $request->get_route() ) {
		return $result;
	}
	if ( studentup_searchlog_is_bot() ) {
		return $result;
	}
	if ( is_user_logged_in() && current_user_can( 'edit_posts' ) ) {
		return $result;   // owner/admin searches signal ni kalupayadam ledu
	}
	$q = (string) $request->get_param( 'search' );
	if ( '' === trim( $q ) || ! studentup_searchlog_allowed() ) {
		return $result;
	}
	$count = 0;
	if ( $result instanceof WP_REST_Response && is_array( $result->get_data() ) ) {
		$count = count( $result->get_data() );
	}
	studentup_searchlog_record( $q, $count );
	return $result;
}
add_filter( 'rest_post_dispatch', 'studentup_searchlog_rest_hook', 10, 3 );

/**
 * Search results page ('?s=query') render ainappudu log (JS lekunda kuda pani).
 *
 * @param string $term    Search term.
 * @param int    $results Found posts.
 * @return void
 */
function studentup_searchlog_page( $term, $results ) {
	if ( studentup_searchlog_is_bot() ) {
		return;
	}
	if ( is_user_logged_in() && current_user_can( 'edit_posts' ) ) {
		return;
	}
	if ( studentup_searchlog_allowed() ) {
		studentup_searchlog_record( $term, $results );
	}
}

/**
 * Simple bot filter — crawler UA ni signal nunchi teesestam.
 *
 * @return bool
 */
function studentup_searchlog_is_bot() {
	$ua = isset( $_SERVER['HTTP_USER_AGENT'] )
		? strtolower( sanitize_text_field( wp_unslash( $_SERVER['HTTP_USER_AGENT'] ) ) )
		: '';
	if ( '' === $ua ) {
		return false;
	}
	foreach ( array( 'bot', 'crawl', 'spider', 'slurp', 'preview', 'monitor' ) as $needle ) {
		if ( false !== strpos( $ua, $needle ) ) {
			return true;
		}
	}
	return false;
}
