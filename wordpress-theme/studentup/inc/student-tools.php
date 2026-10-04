<?php
/**
 * v120: reader utility layer — compare up to three posts, deadline reminder
 * export, print action and a small local-only comparison drawer.
 *
 * No account, cookie, analytics or server-side profile is required. The
 * browser stores only the reader's selected post ids and display metadata;
 * reminder files are generated locally and are not sent to the site.
 * Missing/invalid dates never produce a fake countdown or reminder.
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

function studentup_tools_date( $post_id = 0 ) {
	$post_id = $post_id ? (int) $post_id : (int) get_the_ID();
	$values  = array(
		get_post_meta( $post_id, 'studentup_last_date', true ),
		get_post_meta( $post_id, 'su_deadline', true ),
		get_post_meta( $post_id, 'studentup_test_date', true ),
	);
	foreach ( $values as $value ) {
		$value  = trim( (string) $value );
		$parsed = preg_match( '/^20\d{2}-\d{2}-\d{2}$/', $value ) ? DateTime::createFromFormat( '!Y-m-d', $value ) : false;
		$errors = DateTime::getLastErrors();
		$valid  = $parsed && ( false === $errors || ( 0 === $errors['warning_count'] && 0 === $errors['error_count'] ) ) && $parsed->format( 'Y-m-d' ) === $value;
		if ( $valid ) {
			return $value;
		}
	}
	return '';
}

function studentup_tool_buttons( $post_id = 0, $variant = 'single' ) {
	$post_id = $post_id ? (int) $post_id : (int) get_the_ID();
	if ( ! $post_id ) {
		return '';
	}
	$title = wp_strip_all_tags( get_the_title( $post_id ) );
	$url   = get_permalink( $post_id );
	$cats  = get_the_category( $post_id );
	$cat       = $cats ? $cats[0]->name : '';
	$date      = studentup_tools_date( $post_id );
	$apply_url = trim( (string) get_post_meta( $post_id, 'studentup_apply_url', true ) );
	if ( ! wp_http_validate_url( $apply_url ) ) {
		$apply_url = '';
	}
	$class = 'su-student-tools su-tools-' . sanitize_html_class( $variant );
	$html  = '<div class="' . esc_attr( $class ) . '" data-su-tools>';
	if ( $date ) {
		$html .= '<button type="button" class="su-tool-btn" data-su-reminder data-date="' . esc_attr( $date ) . '" data-title="' . esc_attr( $title ) . '" data-url="' . esc_url( $url ) . '" aria-label="' . esc_attr__( 'Add deadline reminder', 'studentup' ) . '"><span aria-hidden="true">' . studentup_ui_icon( 'clock', 14 ) . '</span> ' . esc_html__( 'Add reminder', 'studentup' ) . '</button>';
	}
	if ( 'single' === $variant ) {
		$html .= '<button type="button" class="su-tool-btn" data-su-print aria-label="' . esc_attr__( 'Print or save this article as PDF', 'studentup' ) . '"><span aria-hidden="true">' . studentup_ui_icon( 'print', 14 ) . '</span> ' . esc_html__( 'Print / PDF', 'studentup' ) . '</button>';
	}
	$html .= '</div>';
	return $html;
}

function studentup_tools_panel() {
	// v203: comparison UI is intentionally retired from the public interface.
	return;
}

function studentup_tools_assets() {
	if ( is_admin() ) {
		return;
	}
	// v198: ee layer = reader utilities (compare · reminder · print · text size ·
	// in-article calculators). Separate file nunchi — tools-hub engine
	// (studentup-tools.js) tools page lo mattrame load avutundi.
	wp_enqueue_script(
		'studentup-reader',
		get_template_directory_uri() . '/assets/js/studentup-reader-utils.js',
		array(),
		STUDENTUP_VERSION,
		true
	);
	if ( get_query_var( 'studentup_opportunities' ) ) {
		wp_enqueue_script(
			'studentup-opportunities',
			get_template_directory_uri() . '/assets/js/studentup-opportunities.js',
			array( 'studentup-reader' ),
			STUDENTUP_VERSION,
			true
		);
	}
	wp_localize_script(
		'studentup-reader',
		'STUDENTUP_TOOLS',
		array(
			'store' => 'studentup_tools_v1',
			'home'  => esc_url_raw( home_url( '/' ) ),
			'i18n'  => array(
				'reminder' => __( 'Reminder file downloaded. Add it to your calendar.', 'studentup' ),
				'noDate'  => __( 'No confirmed date is available for this post.', 'studentup' ),
			)
		)
	);
}
add_action( 'wp_enqueue_scripts', 'studentup_tools_assets', 20 );
add_action( 'wp_footer', 'studentup_tools_panel', 18 );
