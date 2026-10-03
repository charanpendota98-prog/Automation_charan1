<?php
/**
 * v196 - EXAM CALENDAR (deadline intelligence, the sticky feature).
 *
 * Why (audit LIVE_SITE_AUDIT_2026-10.md): every card said "Last date: Not
 * announced" and there was no reason to come back tomorrow. This module turns
 * the whole site into one dated calendar:
 *
 *   - every post's last date (studentup_last_date) is grouped by month,
 *   - "closing soon" ordering so the urgent ones come first,
 *   - ONE TAP adds every deadline to the reader's phone calendar as a single
 *     .ics file (server-side, works even with JavaScript disabled),
 *   - ItemList + Event JSON-LD so Google understands the dates,
 *   - honest empty state when no dates are known (never invents a date).
 *
 * Privacy: the .ics is generated from public data only. No reader data is
 * stored or logged.
 *
 * @package StudentUp
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Calendar items: published posts that have a real last date today or later.
 *
 * @param int $limit Max items.
 * @return array List of ['id','title','date','url','cat','days'].
 */
function studentup_calendar_items( $limit = 60 ) {
	$today = current_time( 'Y-m-d' );
	$q     = new WP_Query(
		array(
			'post_type'           => 'post',
			'post_status'         => 'publish',
			'posts_per_page'      => max( 1, min( 120, (int) $limit ) ),
			'meta_key'            => 'studentup_last_date',
			'orderby'             => 'meta_value',
			'order'               => 'ASC',
			'ignore_sticky_posts' => true,
			'no_found_rows'       => true,
			'meta_query'          => array(
				array(
					'key'     => 'studentup_last_date',
					'value'   => $today,
					'compare' => '>=',
					'type'    => 'DATE',
				),
			),
		)
	);
	$out = array();
	foreach ( $q->posts as $p ) {
		$raw = (string) get_post_meta( $p->ID, 'studentup_last_date', true );
		if ( ! preg_match( '/^\d{4}-\d{2}-\d{2}$/', $raw ) ) {
			continue;   // bad data → skip (never guess).
		}
		$diff   = (int) floor( ( strtotime( $raw . ' 23:59:59' ) - strtotime( $today . ' 00:00:00' ) ) / DAY_IN_SECONDS );
		$terms  = get_the_category( $p->ID );
		$out[]  = array(
			'id'    => (int) $p->ID,
			'title' => $p->post_title,
			'date'  => $raw,
			'url'   => get_permalink( $p ),
			'cat'   => ( $terms && isset( $terms[0] ) ) ? $terms[0]->name : '',
			'days'  => max( 0, $diff ),
		);
	}
	return $out;
}

/**
 * Month label for a Y-m-d date (site locale aware).
 *
 * @param string $ymd Date.
 * @return string
 */
function studentup_calendar_month_label( $ymd ) {
	$ts = strtotime( $ymd . ' 12:00:00' );
	return $ts ? date_i18n( 'F Y', $ts ) : $ymd;
}

/**
 * The calendar page body (also used by [studentup_calendar] shortcode).
 *
 * @return string
 */
function studentup_calendar_page_render() {
	$items = studentup_calendar_items( 60 );
	$total = count( $items );
	$ics   = add_query_arg( 'su_ics', '1', get_permalink() );

	$head = '<div class="su-cal-head">'
		. '<p class="su-cal-count" role="status">' . esc_html( sprintf(
			/* translators: %d: number of dated notifications. */
			_n( '%d dated notification is open right now.', '%d dated notifications are open right now.', $total, 'studentup' ),
			$total
		) ) . '</p>'
		. ( $total
			? '<a class="su-cta" href="' . esc_url( $ics ) . '" rel="nofollow">'
				. studentup_ui_icon( 'calendar', 16 ) . ' '
				. esc_html__( 'Add all dates to my calendar (.ics)', 'studentup' ) . '</a>'
				. '<p class="su-cal-hint">' . esc_html__( 'Opens in Google Calendar, Apple Calendar or any phone calendar. One alarm one day before each last date.', 'studentup' ) . '</p>'
			: '' )
		. '</div>';

	if ( ! $total ) {
		return $head . '<p>' . esc_html__( 'No last dates are confirmed yet. Dates appear here only after the official notification is published - we never estimate a deadline.', 'studentup' ) . '</p>';
	}

	$by_month = array();
	foreach ( $items as $it ) {
		$by_month[ studentup_calendar_month_label( $it['date'] ) ][] = $it;
	}

	$out = '';
	foreach ( $by_month as $month => $rows ) {
		$out .= '<section class="su-cal-month"><h2 class="su-hub-h">' . esc_html( $month ) . '</h2><ul class="su-cal-list">';
		foreach ( $rows as $it ) {
			$urgent = ( $it['days'] <= 3 ) ? ' su-cal-urgent' : '';
			$badge  = ( $it['days'] <= 0 )
				? esc_html__( 'Last date today', 'studentup' )
				: esc_html( sprintf(
					/* translators: %d: days left. */
					_n( '%d day left', '%d days left', $it['days'], 'studentup' ),
					$it['days']
				) );
			$due = date_i18n( 'd M Y', strtotime( $it['date'] . ' 12:00:00' ) );
			$out .= '<li class="su-cal-item' . esc_attr( $urgent ) . '">'
				. '<span class="su-cal-date" aria-hidden="true">' . esc_html( $due ) . '</span>'
				. '<span class="su-cal-body"><a class="su-cal-title" href="' . esc_url( $it['url'] ) . '">' . esc_html( $it['title'] ) . '</a>'
				. '<span class="su-cal-meta">' . esc_html( $it['cat'] ) . ' · ' . esc_html__( 'Last date:', 'studentup' ) . ' ' . esc_html( $due ) . '</span></span>'
				. '<span class="su-cal-badge' . esc_attr( $urgent ) . '">' . $badge . '</span>'
				. '</li>';
		}
		$out .= '</ul></section>';
	}
	return $head . $out;
}

/**
 * [studentup_calendar] shortcode.
 *
 * @return string
 */
function studentup_calendar_shortcode() {
	return '<div class="su-cal">' . studentup_calendar_page_render() . '</div>';
}
add_shortcode( 'studentup_calendar', 'studentup_calendar_shortcode' );

/**
 * .ics export: /exam-calendar/?su_ics=1 -> one VCALENDAR with all deadlines.
 *
 * @return void
 */
function studentup_calendar_ics_export() {
	if ( ! isset( $_GET['su_ics'] ) || '1' !== (string) wp_unslash( $_GET['su_ics'] ) ) { // phpcs:ignore WordPress.Security.NonceVerification -- public read-only export.
		return;
	}
	$items = studentup_calendar_items( 60 );
	if ( ! $items ) {
		wp_safe_redirect( home_url( '/' ) );
		exit;
	}
	$lines = array(
		'BEGIN:VCALENDAR',
		'VERSION:2.0',
		'PRODID:-//StudentUp//Exam Calendar//EN',
		'CALSCALE:GREGORIAN',
		'METHOD:PUBLISH',
		'X-WR-CALNAME:' . studentup_ics_escape( get_bloginfo( 'name' ) . ' - ' . __( 'Government job & exam last dates', 'studentup' ) ),
	);
	foreach ( $items as $it ) {
		$ymd   = str_replace( '-', '', $it['date'] );
		$end   = date( 'Ymd', strtotime( $it['date'] . ' +1 day' ) );
		$lines = array_merge(
			$lines,
			array(
				'BEGIN:VEVENT',
				'UID:studentup-' . $ymd . '-' . (int) $it['id'] . '@' . wp_parse_url( home_url(), PHP_URL_HOST ),
				'DTSTAMP:' . gmdate( 'Ymd\THis\Z' ),
				'DTSTART;VALUE=DATE:' . $ymd,
				'DTEND;VALUE=DATE:' . $end,
				'SUMMARY:' . studentup_ics_escape( sprintf( '%s - %s', __( 'Last date', 'studentup' ), wp_strip_all_tags( $it['title'] ) ) ),
				'DESCRIPTION:' . studentup_ics_escape( sprintf( '%s: %s', __( 'Full details and official apply link', 'studentup' ), $it['url'] ) ),
				'URL:' . $it['url'],
				'BEGIN:VALARM',
				'TRIGGER:-P1D',
				'ACTION:DISPLAY',
				'DESCRIPTION:' . studentup_ics_escape( __( 'Apply today - last date tomorrow', 'studentup' ) ),
				'END:VALARM',
				'END:VEVENT',
			)
		);
	}
	$lines[] = 'END:VCALENDAR';
	$body    = studentup_ics_output( $lines );

	nocache_headers();
	header( 'Content-Type: text/calendar; charset=utf-8' );
	header( 'Content-Disposition: attachment; filename="studentup-exam-calendar.ics"' );
	header( 'Content-Length: ' . strlen( $body ) );
	// ICS body: prathi line studentup_ics_escape() tho already escaped (RFC 5545).
	// esc_html() ikka vadakoodadu — HTML entities calendar file ni corrupt chestayi.
	echo studentup_ics_output( $lines ); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- trusted builder
	exit;
}
add_action( 'template_redirect', 'studentup_calendar_ics_export', 5 );

/**
 * Build the final ICS document from escaped lines (trusted output builder).
 *
 * @param array $lines ICS lines.
 * @return string
 */
function studentup_ics_output( $lines ) {
	$out = array();
	foreach ( (array) $lines as $line ) {
		$line = (string) $line;
		// VALUES (SUMMARY/DESCRIPTION/X-WR-CALNAME) already escaped by the caller;
		// structural keywords stay untouched (no HTML entities in a calendar file).
		$out[] = preg_replace( '/[\x00-\x08\x0B\x0C\x0E-\x1F]/', '', $line );
	}
	return implode( "\r\n", $out ) . "\r\n";
}

/**
 * RFC 5545 text escaping.
 *
 * @param string $text Raw text.
 * @return string
 */
function studentup_ics_escape( $text ) {
	$text = (string) $text;
	$text = str_replace( array( '\\', ';', ',', "\r\n", "\n", "\r" ), array( '\\\\', '\\;', '\\,', '\\n', '\\n', '\\n' ), $text );
	return trim( preg_replace( '/[\x00-\x08\x0B\x0C\x0E-\x1F]/', '', $text ) );
}

/**
 * ItemList + Event schema for the calendar page (only dated items).
 *
 * @return void
 */
function studentup_calendar_schema() {
	if ( is_admin() || ! is_page() ) {
		return;
	}
	$id = (int) get_queried_object_id();
	$content = (string) get_post_field( 'post_content', $id );
	$slug    = (string) get_post_field( 'post_name', $id );
	$is_cal  = ( false !== strpos( $content, '[studentup_calendar' ) ) || 'exam-calendar' === $slug;
	if ( ! $is_cal ) {
		return;
	}
	$items = studentup_calendar_items( 40 );
	if ( ! $items ) {
		return;
	}
	$list = array();
	$pos  = 1;
	foreach ( $items as $it ) {
		$list[] = array(
			'@type'    => 'ListItem',
			'position' => $pos++,
			'item'     => array(
				'@type'     => 'Event',
				'name'      => wp_strip_all_tags( $it['title'] ),
				'startDate' => $it['date'],
				'url'       => $it['url'],
				'eventStatus' => 'https://schema.org/EventScheduled',
				'eventAttendanceMode' => 'https://schema.org/OnlineEventAttendanceMode',
				'location'  => array( '@type' => 'VirtualLocation', 'url' => $it['url'] ),
				'organizer' => array( '@id' => home_url( '/' ) . '#org' ),
			),
		);
	}
	$graph = array(
		array(
			'@type'           => 'ItemList',
			'@id'             => get_permalink( $id ) . '#calendar',
			'name'            => wp_strip_all_tags( get_the_title( $id ) ),
			'numberOfItems'   => count( $list ),
			'itemListElement' => $list,
		),
	);
	echo '<script type="application/ld+json">'
		. wp_json_encode( array( '@context' => 'https://schema.org', '@graph' => $graph ), JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES )
		. '</script>' . "\n"; // phpcs:ignore WordPress.Security.EscapeOutput -- own JSON-LD.
}
add_action( 'wp_head', 'studentup_calendar_schema', 8 );
