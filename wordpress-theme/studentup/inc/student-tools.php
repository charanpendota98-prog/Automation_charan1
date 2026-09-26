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
		get_post_meta( $post_id, 'studentup_exam_date', true ),
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
	$cat   = $cats ? $cats[0]->name : '';
	$date  = studentup_tools_date( $post_id );
	$class = 'su-student-tools su-tools-' . sanitize_html_class( $variant );
	$html  = '<div class="' . esc_attr( $class ) . '" data-su-tools>';
	$html .= '<button type="button" class="su-tool-btn" data-su-compare data-id="' . esc_attr( $post_id ) . '" data-title="' . esc_attr( $title ) . '" data-url="' . esc_url( $url ) . '" data-cat="' . esc_attr( $cat ) . '" aria-pressed="false" aria-label="' . esc_attr__( 'Add this post to compare', 'studentup' ) . '"><span aria-hidden="true">⚖️</span> <span data-su-compare-label>' . esc_html__( 'Compare', 'studentup' ) . '</span></button>';
	if ( 'single' === $variant && $date ) {
		$html .= '<button type="button" class="su-tool-btn" data-su-reminder data-date="' . esc_attr( $date ) . '" data-title="' . esc_attr( $title ) . '" data-url="' . esc_url( $url ) . '" aria-label="' . esc_attr__( 'Add deadline reminder', 'studentup' ) . '"><span aria-hidden="true">⏰</span> ' . esc_html__( 'Add reminder', 'studentup' ) . '</button>';
	}
	if ( 'single' === $variant ) {
		$html .= '<button type="button" class="su-tool-btn" data-su-print aria-label="' . esc_attr__( 'Print or save this article as PDF', 'studentup' ) . '"><span aria-hidden="true">🖨️</span> ' . esc_html__( 'Print / PDF', 'studentup' ) . '</button>';
	}
	$html .= '</div>';
	return $html;
}

function studentup_tools_panel() {
	?>
	<div class="su-compare-rail" id="su-compare-rail" hidden>
		<div class="su-compare-head">
			<strong><?php esc_html_e( 'Compare posts', 'studentup' ); ?></strong>
			<span data-su-compare-count aria-live="polite">0/3</span>
			<button type="button" data-su-compare-close aria-label="<?php esc_attr_e( 'Close compare panel', 'studentup' ); ?>">✕</button>
		</div>
		<div class="su-compare-items" data-su-compare-items></div>
		<div class="su-compare-actions">
			<button type="button" class="su-tool-primary" data-su-compare-open disabled><?php esc_html_e( 'Open comparison', 'studentup' ); ?></button>
			<button type="button" class="su-tool-muted" data-su-compare-clear><?php esc_html_e( 'Clear', 'studentup' ); ?></button>
		</div>
	</div>
	<?php
}

function studentup_tools_assets() {
	if ( is_admin() ) {
		return;
	}
	wp_enqueue_script(
		'studentup-tools',
		get_template_directory_uri() . '/assets/js/studentup-tools.js',
		array(),
		STUDENTUP_VERSION,
		true
	);
	if ( get_query_var( 'studentup_opportunities' ) ) {
		wp_enqueue_script(
			'studentup-opportunities',
			get_template_directory_uri() . '/assets/js/studentup-opportunities.js',
			array( 'studentup-tools' ),
			STUDENTUP_VERSION,
			true
		);
	}
	wp_localize_script(
		'studentup-tools',
		'STUDENTUP_TOOLS',
		array(
			'store' => 'studentup_tools_v1',
			'home'  => esc_url_raw( home_url( '/' ) ),
			'i18n'  => array(
				'compare' => __( 'Compare', 'studentup' ),
				'added'   => __( 'Added', 'studentup' ),
				'limit'   => __( 'Compare up to three posts.', 'studentup' ),
				'reminder' => __( 'Reminder file downloaded. Add it to your calendar.', 'studentup' ),
				'noDate'  => __( 'No confirmed date is available for this post.', 'studentup' ),
				'empty'   => __( 'Select at least two posts to compare.', 'studentup' ),
			)
		)
	);
}
add_action( 'wp_enqueue_scripts', 'studentup_tools_assets', 20 );
add_action( 'wp_footer', 'studentup_tools_panel', 18 );
