<?php
/**
 * v162 — Slot lab: ad slot A/B variant assignment.
 *
 * Ye slot configuration ekkuva RPM istundo telusukovadaniki, rendu AdSense
 * ad units create chesi (udaa: "mid-A", "mid-B") rendinti ids ni ikkada
 * pedatharu. Visitor ki okate variant stable ga velthundi, and AdSense
 * report lo variant vaari RPM separate ga kanipistundi.
 *
 * Design rules (ivi deliberate):
 *  - **B slot id ivvakapothe experiment ye ledu** — eppudu A ye velthundi.
 *    Half traffic ni blank slot ki pampadam revenue loss.
 *  - Assignment **stable** — same visitor ki prati page lo, prati roju
 *    same variant. Page prati refresh ki marithe data motham garbage.
 *  - Cookie ledu, IP store ledu, personal data ledu — consent banner
 *    avasaram lekunda pani cheyyali.
 *  - Ad ni refresh cheyyadu, move cheyyadu — slot id matrame veru.
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Visitor ki stable variant ('A' leda 'B').
 *
 * Seed = daily salt + user agent + accept-language. Personal data ni store
 * cheyyam; hash matrame, request lo ne use chesi vadilesthamu.
 *
 * @return string 'A' or 'B'.
 */
function studentup_slot_variant() {
	static $variant = null;
	if ( null !== $variant ) {
		return $variant;
	}

	$ua   = isset( $_SERVER['HTTP_USER_AGENT'] ) ? sanitize_text_field( wp_unslash( $_SERVER['HTTP_USER_AGENT'] ) ) : '';
	$lang = isset( $_SERVER['HTTP_ACCEPT_LANGUAGE'] ) ? sanitize_text_field( wp_unslash( $_SERVER['HTTP_ACCEPT_LANGUAGE'] ) ) : '';
	$salt = (string) get_option( 'su_slot_lab_salt', '' );
	if ( '' === $salt ) {
		$salt = wp_generate_password( 12, false );
		update_option( 'su_slot_lab_salt', $salt, false );
	}

	$hash    = crc32( $salt . '|' . $ua . '|' . $lang );
	$variant = ( 0 === $hash % 2 ) ? 'A' : 'B';
	return $variant;
}

/**
 * Oka place ki vaadalsina AdSense slot id.
 *
 * B id set chesi, slot lab ON unte ne split; lekapothe eppudu A.
 *
 * @param string $slot_key option key suffix (udaa 'mid').
 * @return array [ slot id, variant label ] — variant '' ante experiment ledu.
 */
function studentup_slot_for( $slot_key ) {
	$slot_a = (string) get_option( 'studentup_adsense_slot_' . $slot_key, '' );
	$slot_b = (string) get_option( 'studentup_adsense_slot_' . $slot_key . '_b', '' );

	if ( '' === $slot_b || ! studentup_opt( 'slot_lab', '0' ) ) {
		return array( $slot_a, '' );
	}
	if ( 'B' === studentup_slot_variant() ) {
		return array( $slot_b, 'B' );
	}
	return array( $slot_a, 'A' );
}

/**
 * Experiment nadustunda ani owner ki chepthundi (admin bar lo).
 *
 * @param WP_Admin_Bar $bar admin bar.
 */
function studentup_slot_lab_adminbar( $bar ) {
	if ( ! current_user_can( 'manage_options' ) || ! studentup_opt( 'slot_lab', '0' ) ) {
		return;
	}
	$bar->add_node(
		array(
			'id'    => 'studentup-slot-lab',
			'title' => 'Slot lab: ' . studentup_slot_variant(),
			'meta'  => array( 'title' => __( 'Ad slot A/B test is running', 'studentup' ) ),
		)
	);
}
add_action( 'admin_bar_menu', 'studentup_slot_lab_adminbar', 90 );
