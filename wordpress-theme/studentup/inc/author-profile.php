<?php
/**
 * v195 — AUTHOR / EDITORIAL E-E-A-T PACK.
 *
 * Audit finding (LIVE_SITE_AUDIT_2026-10.md #14 + #36): live site lo byline
 * "Anand (Content Manager)" vs repo lo "Charan Pendota" — author identity
 * clash, no reviewer name, no Person schema, no real author page.
 * AdSense + Google News reviewers "ee content ni evaru verify chesaru?" ani
 * adigitaru; Google E-E-A-T ki named human + credentials kaavali.
 *
 * Ee module:
 *   1. `/editorial-team/` page → profile card (name · role · photo · bio ·
 *      expertise, since, socials) + a "how we verify" process list.
 *   2. Person schema (author posts ki) + ProfilePage schema (author archive ki)
 *      + Organization.founder reference (site identity).
 *   3. Editorial reviewer line (EDITORIAL_REVIEWER → theme option) so byline
 *      "Reviewed by X" - only when a real named person reviewed it.
 *
 * Note: illa unna content admin options nunchi vastundi (`studentup_author_card_data`),
 * so owner okkate chota update chesthe site antha correct avutundi.
 *
 * @package StudentUp
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Author card data (options → admin edits once, site-wide everywhere).
 *
 * @return array
 */
function studentup_author_card_data() {
	$name = trim( (string) studentup_opt( 'author_name', 'Charan Pendota' ) );
	return array(
		'name'      => $name ? $name : 'StudentUp Editorial Team',
		'role'      => trim( (string) studentup_opt( 'author_role', 'Founder & Content Writer' ) ),
		'bio'       => trim( (string) studentup_opt( 'author_bio', '' ) ),
		'avatar'    => trim( (string) studentup_opt( 'author_avatar_url', '' ) ),
		'expertise' => trim( (string) studentup_opt( 'author_expertise', 'Telangana & AP government jobs, exam patterns, scholarships, eligibility rules' ) ),
		'since'     => trim( (string) studentup_opt( 'author_since', '' ) ),
		'linkedin'  => trim( (string) studentup_opt( 'social_linkedin', '' ) ),
		'x'         => trim( (string) studentup_opt( 'social_x', '' ) ),
		'youtube'   => trim( (string) studentup_opt( 'social_youtube', '' ) ),
		'email'     => function_exists( 'studentup_contact_email' ) ? studentup_contact_email() : (string) get_option( 'admin_email' ),
	);
}

/**
 * Expertise string → array (comma separated).
 *
 * @return array
 */
function studentup_author_expertise_list() {
	$d   = studentup_author_card_data();
	$out = array_filter( array_map( 'trim', explode( ',', (string) $d['expertise'] ) ) );
	return $out ? $out : array( 'Government job notifications' );
}

/**
 * Author profile card HTML (also used on /editorial-team/).
 *
 * @return string
 */
function studentup_author_profile_html() {
	$d      = studentup_author_card_data();
	$avatar = $d['avatar'];
	$out    = '<div class="su-ab su-ab--page" itemscope itemtype="https://schema.org/Person">';
	if ( $avatar ) {
		$out .= '<img class="su-ab-img" src="' . esc_url( $avatar ) . '" alt="' . esc_attr( $d['name'] ) . '" width="96" height="96" loading="lazy" decoding="async">';
	}
	$out .= '<div class="su-ab-body">';
	$out .= '<h2 itemprop="name">' . esc_html( $d['name'] ) . '</h2>';
	if ( $d['role'] ) {
		$out .= '<p class="su-ab-role" itemprop="jobTitle">' . esc_html( $d['role'] ) . '</p>';
	}
	if ( $d['bio'] ) {
		$out .= '<p itemprop="description">' . esc_html( $d['bio'] ) . '</p>';
	}
	$out .= '<ul class="su-trust su-trust--expertise">';
	foreach ( studentup_author_expertise_list() as $skill ) {
		$out .= '<li>' . esc_html( $skill ) . '</li>';
	}
	$out .= '</ul>';
	$links = array();
	if ( $d['email'] ) {
		$links[] = '<a href="mailto:' . esc_attr( $d['email'] ) . '" itemprop="email">' . esc_html__( 'Email', 'studentup' ) . '</a>';
	}
	if ( $d['linkedin'] ) {
		$links[] = '<a href="' . esc_url( $d['linkedin'] ) . '" rel="me noopener" target="_blank" itemprop="sameAs">LinkedIn</a>';
	}
	if ( $d['x'] ) {
		$links[] = '<a href="' . esc_url( $d['x'] ) . '" rel="me noopener" target="_blank" itemprop="sameAs">X</a>';
	}
	if ( $d['youtube'] ) {
		$links[] = '<a href="' . esc_url( $d['youtube'] ) . '" rel="me noopener" target="_blank" itemprop="sameAs">YouTube</a>';
	}
	if ( $links ) {
		$out .= '<p class="su-ab-links">' . implode( ' · ', $links ) . '</p>';
	}
	if ( $d['since'] ) {
		$out .= '<p class="su-ab-since">' . esc_html( sprintf( 'Publishing since %s', $d['since'] ) ) . '</p>';
	}
	$out .= '</div></div>';
	return $out;
}

/**
 * [studentup_author_profile] shortcode — editorial-team page ki.
 *
 * @return string
 */
function studentup_author_profile_shortcode() {
	$verify = '<h3>' . esc_html__( 'How every update is verified', 'studentup' ) . '</h3>'
		. '<ol class="su-ab-steps">'
		. '<li>' . esc_html__( 'We start from the official notification or the department website only.', 'studentup' ) . '</li>'
		. '<li>' . esc_html__( 'Dates, fees, vacancies and eligibility go into the post exactly as published — nothing is estimated.', 'studentup' ) . '</li>'
		. '<li>' . esc_html__( 'Every post links the official source so you can check it yourself.', 'studentup' ) . '</li>'
		. '<li>' . esc_html__( 'A reader correction is published publicly with the updated date.', 'studentup' ) . '</li>'
		. '</ol>';
	return studentup_author_profile_html() . $verify;
}
add_shortcode( 'studentup_author_profile', 'studentup_author_profile_shortcode' );

/**
 * Person schema — post pages lo author (Google E-E-A-T + Discover).
 *
 * @return void
 */
function studentup_person_schema() {
	if ( is_admin() || ! studentup_opt( 'schema', '1' ) ) {
		return;
	}
	if ( ! is_singular( 'post' ) && ! is_author() && ! is_page() ) {
		return;
	}
	$d    = studentup_author_card_data();
	$home = home_url( '/' );
	$same = array_values( array_filter( array( $d['linkedin'], $d['x'], $d['youtube'] ) ) );

	$person = array(
		'@type'       => 'Person',
		'@id'         => $home . '#founder',
		'name'        => $d['name'],
		'url'         => studentup_hub_url( 'editorial-team' ) ? studentup_hub_url( 'editorial-team' ) : $home,
		'description' => $d['bio'] ? $d['bio'] : $d['role'],
		'knowsAbout'  => array_values( studentup_author_expertise_list() ),
		'worksFor'    => array( '@id' => $home . '#org' ),
	);
	if ( $d['role'] ) {
		$person['jobTitle'] = $d['role'];
	}
	if ( $d['avatar'] ) {
		$person['image'] = array( '@type' => 'ImageObject', 'url' => $d['avatar'] );
	}
	if ( $same ) {
		$person['sameAs'] = $same;
	}
	if ( $d['email'] ) {
		$person['email'] = $d['email'];
	}

	$graph = array( $person );
	if ( is_author() ) {
		$graph[] = array(
			'@type'      => 'ProfilePage',
			'@id'        => get_author_posts_url( (int) get_query_var( 'author' ) ) . '#profile',
			'name'       => $d['name'],
			'mainEntity' => array( '@id' => $home . '#founder' ),
			'isPartOf'   => array( '@id' => $home . '#website' ),
		);
	}
	echo '<script type="application/ld+json">'
		. wp_json_encode( array( '@context' => 'https://schema.org', '@graph' => $graph ), JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES )
		. '</script>' . "\n"; // phpcs:ignore WordPress.Security.EscapeOutput -- own JSON-LD.
}
add_action( 'wp_head', 'studentup_person_schema', 7 );
