<?php
/**
 * StudentUp first-party short links.
 *
 * Root links such as /ssc-cgl-2026 are stored in a small WP table and 302
 * redirect to the exact article. A 302 keeps click analytics working and lets
 * the owner change a destination later without breaking a forwarded link.
 * Only authenticated administrators can create/update links; public visitors
 * can only resolve an already-created slug.
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

function studentup_shortlinks_table() {
	global $wpdb;
	return $wpdb->prefix . 'studentup_short_links';
}

function studentup_shortlinks_install() {
	global $wpdb;
	require_once ABSPATH . 'wp-admin/includes/upgrade.php';
	$table   = studentup_shortlinks_table();
	$charset = $wpdb->get_charset_collate();
	$sql     = "CREATE TABLE {$table} (
		id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
		slug varchar(48) NOT NULL,
		original_url text NOT NULL,
		clicks bigint(20) unsigned NOT NULL DEFAULT 0,
		created_at datetime NOT NULL,
		updated_at datetime NOT NULL,
		last_clicked_at datetime NULL,
		PRIMARY KEY  (id),
		UNIQUE KEY slug (slug)
	) {$charset};";
	dbDelta( $sql );
	update_option( 'studentup_shortlinks_db_version', '1', false );
}
add_action( 'after_switch_theme', 'studentup_shortlinks_install' );

function studentup_shortlinks_reserved() {
	return array(
		'wp-admin', 'wp-json', 'wp-login', 'wp-cron', 'feed', 'category', 'tag',
		'author', 'search', 'page', 'latest-jobs', 'sitemap', 'sitemap_index',
		'robots', 'favicon', 'manifest', 'go', 'api', 'login', 'logout',
	);
}

function studentup_shortlinks_slug( $raw ) {
	$slug = sanitize_title( (string) $raw );
	$slug = trim( $slug, '-' );
	if ( strlen( $slug ) > 40 ) {
		$slug = substr( $slug, 0, 40 );
		$slug = trim( $slug, '-' );
	}
	if ( strlen( $slug ) < 2 || ! preg_match( '/^[a-z0-9][a-z0-9-]*$/', $slug ) ) {
		return '';
	}
	if ( in_array( $slug, studentup_shortlinks_reserved(), true ) ) {
		return '';
	}
	return $slug;
}

function studentup_shortlinks_url( $slug ) {
	return home_url( '/' . rawurlencode( $slug ) . '/' );
}

function studentup_shortlinks_allowed_destination( $url ) {
	$url = esc_url_raw( (string) $url );
	if ( '' === $url || ! preg_match( '#^https?://#i', $url ) ) {
		return '';
	}
	return $url;
}

function studentup_shortlinks_find( $slug ) {
	global $wpdb;
	$slug = studentup_shortlinks_slug( $slug );
	if ( '' === $slug ) {
		return null;
	}
	$table = studentup_shortlinks_table();
	return $wpdb->get_row( $wpdb->prepare( "SELECT * FROM {$table} WHERE slug = %s LIMIT 1", $slug ), ARRAY_A ); // phpcs:ignore WordPress.DB.PreparedSQL.InterpolatedNotPrepared
}

function studentup_shortlinks_resolve() {
	if ( is_admin() || wp_doing_ajax() || ( defined( 'REST_REQUEST' ) && REST_REQUEST ) ) {
		return;
	}
	// Never hijack an existing page/post/category. Unknown root paths are the
	// only candidates for a first-party short link.
	if ( is_singular() || is_category() || is_tag() || is_author() || is_search() || ! is_404() ) {
		return;
	}
	$path = isset( $_SERVER['REQUEST_URI'] ) ? wp_unslash( (string) $_SERVER['REQUEST_URI'] ) : '';
	$path = (string) wp_parse_url( $path, PHP_URL_PATH );
	$base = (string) wp_parse_url( home_url( '/' ), PHP_URL_PATH );
	if ( $base && '/' !== $base ) {
		$path = preg_replace( '#^' . preg_quote( untrailingslashit( $base ), '#' ) . '#', '', $path );
	}
	$slug = trim( $path, '/' );
	if ( '' === $slug || false !== strpos( $slug, '/' ) ) {
		return;
	}
	$row = studentup_shortlinks_find( $slug );
	if ( ! $row ) {
		return;
	}
	$destination = studentup_shortlinks_allowed_destination( $row['original_url'] );
	if ( '' === $destination ) {
		return;
	}
	global $wpdb;
	$wpdb->query( // phpcs:ignore WordPress.DB.DirectDatabaseQuery
		$wpdb->prepare(
			'UPDATE ' . studentup_shortlinks_table() . ' SET clicks = clicks + 1, last_clicked_at = %s WHERE id = %d',
			current_time( 'mysql', true ),
			(int) $row['id']
		)
	);
	nocache_headers();
	wp_redirect( $destination, 302, 'StudentUp Short Link' ); // phpcs:ignore WordPress.Security.SafeRedirect.wp_redirect_wp_redirect
	exit;
}
add_action( 'template_redirect', 'studentup_shortlinks_resolve', 1 );

function studentup_shortlinks_rest() {
	register_rest_route(
		'studentup/v1',
		'/shortlinks',
		array(
			'methods'             => WP_REST_Server::CREATABLE,
			'permission_callback' => function () {
				return current_user_can( 'manage_options' );
			},
			'callback'            => 'studentup_shortlinks_upsert',
			'args'                => array(
				'slug'         => array( 'required' => true, 'type' => 'string' ),
				'original_url' => array( 'required' => true, 'type' => 'string', 'format' => 'uri' ),
			),
		)
	);
}
add_action( 'rest_api_init', 'studentup_shortlinks_rest' );

function studentup_shortlinks_upsert( WP_REST_Request $request ) {
	global $wpdb;
	$slug        = studentup_shortlinks_slug( $request->get_param( 'slug' ) );
	$destination = studentup_shortlinks_allowed_destination( $request->get_param( 'original_url' ) );
	if ( '' === $slug || '' === $destination ) {
		return new WP_Error( 'studentup_invalid_shortlink', 'Invalid slug or destination URL.', array( 'status' => 400 ) );
	}
	$table = studentup_shortlinks_table();
	$now   = current_time( 'mysql', true );
	$old   = studentup_shortlinks_find( $slug );
	if ( $old ) {
		if ( untrailingslashit( (string) $old['original_url'] ) !== untrailingslashit( $destination ) ) {
			return new WP_Error( 'studentup_shortlink_conflict', 'Slug already points to another URL.', array( 'status' => 409 ) );
		}
		$wpdb->update( $table, array( 'updated_at' => $now ), array( 'id' => (int) $old['id'] ), array( '%s' ), array( '%d' ) ); // phpcs:ignore WordPress.DB.DirectDatabaseQuery
		$id = (int) $old['id'];
	} else {
		$ok = $wpdb->insert( $table, array( 'slug' => $slug, 'original_url' => $destination, 'created_at' => $now, 'updated_at' => $now ), array( '%s', '%s', '%s', '%s' ) ); // phpcs:ignore WordPress.DB.DirectDatabaseQuery
		if ( false === $ok ) {
			return new WP_Error( 'studentup_shortlink_create_failed', 'Could not create short link.', array( 'status' => 500 ) );
		}
		$id = (int) $wpdb->insert_id;
	}
	return new WP_REST_Response(
		array(
			'ok'            => true,
			'id'            => $id,
			'slug'          => $slug,
			'short_url'     => studentup_shortlinks_url( $slug ),
			'original_url'  => $destination,
		),
		200
	);
}
