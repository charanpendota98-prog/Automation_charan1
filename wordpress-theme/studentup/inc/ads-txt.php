<?php
/**
 * v66: ads.txt — WP nunchi serve (shared hosting friendly).
 *
 * Enduku: `ads.txt` **site root** lo undali (`https://studentup.in/ads.txt`).
 * MilesWeb lo file manager tho upload cheyyachu, kaani ee module WP nunchi
 * serve chestundi (option lo edit cheyyachu — bot kuda nimpistundi).
 *
 * Format (IAB): <domain>, <publisher-id>, DIRECT, <cert-authority>
 * AdSense example: google.com, pub-0000000000000000, DIRECT, f08c47fec0942fa0
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * /ads.txt ni WP nunchi serve + /ads.txt default content (option).
 */
function studentup_ads_txt_serve() {
	if ( ! isset( $_SERVER['REQUEST_URI'] ) ) {
		return;
	}
	$path = strtok( (string) wp_unslash( $_SERVER['REQUEST_URI'] ), '?' ); // phpcs:ignore WordPress.Security.ValidatedSanitizedInput
	if ( '/ads.txt' !== rtrim( (string) $path, '/' ) ) {
		return;
	}
	$body = (string) studentup_opt( 'ads_txt', '' );
	if ( '' === trim( $body ) ) {
		$client = studentup_adsense_client();
		if ( $client ) {
			$pub_id = str_replace( 'ca-', '', $client );        // ca-pub-xxx → pub-xxx
			$body   = "# StudentUp (auto) — AdSense DIRECT\n"
				. "google.com, {$pub_id}, DIRECT, f08c47fec0942fa0\n";
		} else {
			$body = "# ads.txt — AdSense approval tarvata publisher id ikkadiki vastundi\n"
				. "# (StudentUp → Ads → ads.txt lo edit cheyachu; bot kuda nimpistundi)\n";
		}
	}
	header( 'Content-Type: text/plain; charset=utf-8' );
	header( 'X-Robots-Tag: noindex' );
	nocache_headers();
	echo esc_html( $body );
	exit;
}
add_action( 'template_redirect', 'studentup_ads_txt_serve', 1 );
