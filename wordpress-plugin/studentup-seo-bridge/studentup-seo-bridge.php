<?php
/**
 * Plugin Name: StudentUp Rank Math Automation Bridge
 * Description: Authenticated REST bridge for StudentUp automation to save and verify Rank Math fields.
 * Version: 1.1.0
 * Author: StudentUp
 * Requires at least: 6.0
 * Requires PHP: 7.4
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

function studentup_seo_plugin_keys() {
	return array(
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

function studentup_seo_plugin_register_meta() {
	foreach ( array( 'post', 'page' ) as $type ) {
		foreach ( studentup_seo_plugin_keys() as $key ) {
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
add_action( 'init', 'studentup_seo_plugin_register_meta', 99 );

function studentup_seo_plugin_read( WP_REST_Request $request ) {
	$post_id = absint( $request['id'] );
	$fields  = array();
	foreach ( studentup_seo_plugin_keys() as $key ) {
		$fields[ $key ] = (string) get_post_meta( $post_id, $key, true );
	}
	$stored_score = get_post_meta( $post_id, 'rank_math_seo_score', true );
	return new WP_REST_Response(
		array(
			'ok'                => true,
			'post_id'           => $post_id,
			'fields'            => $fields,
			'rank_math_ui_score' => is_numeric( $stored_score ) ? (int) $stored_score : null,
			'score_note'        => 'Read-only Rank Math stored value; never generated or overwritten by StudentUp.',
		),
		200
	);
}

function studentup_seo_plugin_write( WP_REST_Request $request ) {
	$post_id = absint( $request['id'] );
	$body    = $request->get_json_params();
	$meta    = isset( $body['meta'] ) && is_array( $body['meta'] ) ? $body['meta'] : array();
	$saved   = array();

	foreach ( $meta as $key => $value ) {
		if ( ! in_array( $key, studentup_seo_plugin_keys(), true ) ) {
			continue;
		}
		$value = is_array( $value )
			? implode( ', ', array_map( 'sanitize_text_field', $value ) )
			: sanitize_text_field( (string) $value );
		update_post_meta( $post_id, $key, $value );
		$saved[ $key ] = (string) get_post_meta( $post_id, $key, true );
	}

	return new WP_REST_Response(
		array( 'ok' => true, 'post_id' => $post_id, 'saved' => $saved ),
		200
	);
}

add_action(
	'rest_api_init',
	function () {
		register_rest_route(
			'studentup/v1',
			'/posts/(?P<id>[\d]+)/seo',
			array(
				'methods'             => 'GET',
				'callback'            => 'studentup_seo_plugin_read',
				'permission_callback' => function ( WP_REST_Request $request ) {
					return current_user_can( 'edit_post', absint( $request['id'] ) );
				},
			)
		);
		register_rest_route(
			'studentup/v1',
			'/posts/(?P<id>[\d]+)/seo',
			array(
				'methods'             => 'POST',
				'callback'            => 'studentup_seo_plugin_write',
				'permission_callback' => function ( WP_REST_Request $request ) {
					return current_user_can( 'edit_post', absint( $request['id'] ) );
				},
			)
		);
	}
);
