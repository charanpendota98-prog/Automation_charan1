<?php
/**
 * v68: IndexNow key file — `/<key>.key`
 *
 * Enduku: IndexNow (Bing/Yandex instant indexing) ki key file site root lo undali.
 * Mundu adi cPanel/FTP lo **manual ga** pettali — marchipote bot submit fail ayyedi
 * ("key not found") → kotha post lu search lo ki fast ga vellavu (trending miss).
 * Ippudu: bot key ni theme option lo pettagane (--push-theme-data), ee route file ni
 * automatic ga serve chestundi. Manual upload ledu, marchipo yadam ledu.
 *
 * Note: file content = key mattrame (IndexNow spec). Key public ga undadam safe —
 * adi verification token, secret kaadu.
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * `/` + key + `.key` request ni serve cheyyadam (key set unte mattrame).
 */
function studentup_indexnow_key_file() {
	if ( is_admin() ) {
		return;
	}
	$key = (string) studentup_opt( 'indexnow_key', '' );
	$key = preg_replace( '/[^A-Za-z0-9-]/', '', $key );
	if ( '' === $key || strlen( $key ) < 8 ) {
		return;
	}
	$uri = isset( $_SERVER['REQUEST_URI'] )
		? (string) wp_unslash( $_SERVER['REQUEST_URI'] ) // phpcs:ignore WordPress.Security.ValidatedSanitizedInput
		: '';
	$uri = strtok( $uri, '?' );
	if ( '/' . $key . '.key' !== $uri && '/' . $key . '.txt' !== $uri ) {
		return;
	}
	header( 'Content-Type: text/plain; charset=utf-8' );
	header( 'X-Robots-Tag: noindex, nofollow' );
	echo esc_html( $key );
	exit;
}
add_action( 'template_redirect', 'studentup_indexnow_key_file', 1 );
