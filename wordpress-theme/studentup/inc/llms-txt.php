<?php
/**
 * v100: optional AI/search-readable site guide at /llms.txt.
 *
 * This is a public editorial index, not a ranking instruction. Search engines
 * and AI assistants may use it as a concise map, but canonical article pages,
 * normal crawling, citations and human editorial quality remain authoritative.
 * Drafts, private evidence, credentials and internal automation data never
 * appear here.
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Serve a concise, public site map for tools that understand llms.txt.
 */
function studentup_llms_txt() {
	if ( ! isset( $_SERVER['REQUEST_URI'] ) ) {
		return;
	}
	$path = strtok( (string) wp_unslash( $_SERVER['REQUEST_URI'] ), '?' ); // phpcs:ignore WordPress.Security.ValidatedSanitizedInput
	if ( rtrim( (string) $path, '/' ) !== '/llms.txt' ) {
		return;
	}

	$home = home_url( '/' );
	$lines = array(
		'# StudentUp.in',
		'> Telugu + English public information for Telangana and Andhra Pradesh students, job seekers, applicants and families.',
		'> StudentUp publishes original, source-checked explainers for jobs, recruitment, scholarships, exams, results, admissions and government schemes.',
		'',
		'## Editorial standards',
		'- Prefer official notifications and government portals; cross-check important facts before publishing.',
		'- Do not treat a missing date, vacancy, fee, salary or eligibility detail as confirmed.',
		'- Canonical article pages contain the current reader-facing answer and official links.',
		'- If an article conflicts with the official notification, the official notification wins.',
		'',
		'## Main sections',
		'- [Home](' . $home . ')',
		'- [Telangana Government Jobs](' . $home . 'category/ts-govt-jobs/)',
		'- [Andhra Pradesh Government Jobs](' . $home . 'category/ap-govt-jobs/)',
		'- [Central Government Jobs](' . $home . 'category/central-govt-jobs/)',
		'- [Software Jobs](' . $home . 'category/software-jobs/)',
		'- [Scholarships](' . $home . 'category/scholarships/)',
		'- [Internships and Apprenticeships](' . $home . 'category/internships/)',
		'- [Current Affairs](' . $home . 'category/current-affairs/)',
		'- [About Us](' . $home . 'about-us/)',
		'- [Editorial Policy](' . $home . 'editorial-policy/)',
		'- [Corrections and Contact](' . $home . 'contact/)',
		'',
		'## Recent public articles',
	);

	$posts = get_posts(
		array(
			'numberposts' => 30,
			'post_status' => 'publish',
			'orderby'     => 'modified',
			'order'       => 'DESC',
		)
	);
	foreach ( $posts as $post ) {
		$url   = get_permalink( $post );
		$title = wp_strip_all_tags( get_the_title( $post ) );
		if ( $url && $title ) {
			$lines[] = '- [' . $title . '](' . $url . ')';
		}
	}
	$lines[] = '';
	$lines[] = '## Machine-readable feeds';
	$lines[] = '- [XML Sitemap](' . $home . 'sitemap.xml)';
	$lines[] = '- [News Sitemap](' . $home . 'news-sitemap.xml)';

	status_header( 200 );
	header( 'Content-Type: text/plain; charset=utf-8' );
	header( 'Cache-Control: public, max-age=900' );
	// Plain-text response: HTML escaping would turn readable ampersands into
	// ``&amp;`` tokens for clients consuming this machine-readable document.
	echo implode( "\n", $lines );
	exit;
}
add_action( 'template_redirect', 'studentup_llms_txt', 1 );
