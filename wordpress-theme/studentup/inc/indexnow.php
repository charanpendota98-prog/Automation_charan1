<?php
/**
 * v68: IndexNow key-file serving — instant indexing (Bing/Yandex) ki kavalsina key file.
 *
 * Enduku: bot `autoblog/indexnow.py` publish tarvata URL submit chestundi, kaani
 * IndexNow ki **key file site root lo** undali (`/<key>.key`). Mundu adi manual ga
 * cPanel lo pettali — appudu bot nunchi submit fail ayyedi ("key verification failed").
 * Ippudu theme ne serve chestundi → admin lo key pettithe chalu, end-to-end automatic.
 *
 * Security: file lo **key mattrame** (random hex, public ga undadam safe — idi protocol).
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * `/<key>.key` ni serve cheyyadam (key option lo unte mattrame).
 */
function studentup_indexnow_key_file() {
	$key = preg_replace( '/[^a-f0-9]/i', '', (string) studentup_opt( 'indexnow_key', '' ) );
	if ( '' === $key || strlen( $key ) < 8 ) {
		return;   // key set kaaledu → ee route ledu
	}
	$path = isset( $_SERVER['REQUEST_URI'] ) ? (string) wp_unslash( $_SERVER['REQUEST_URI'] ) : '';
	$path = strtok( $path, '?' );
	if ( '/' . $key . '.key' !== $path ) {
		return;
	}
	header( 'Content-Type: text/plain; charset=utf-8' );
	header( 'X-Robots-Tag: noindex' );
	echo esc_html( $key );
	exit;
}
add_action( 'template_redirect', 'studentup_indexnow_key_file', 1 );
