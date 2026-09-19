<?php
/**
 * v81 (§65): Admin SEO-health dashboard widget.
 *
 * Enduku: expired/expiring jobs + drafts + redirects anni okate chota —
 * owner roju open chesi chudali. Queries anni light (counts only,
 * no_found_rows) — admin slow avvadu.
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * studentup_last_date meta batti expiring/expired counts.
 *
 * @return array{expiring:int,expired:int}
 */
function studentup_health_deadlines() {
	$today    = current_time( 'Y-m-d' ); // phpcs:ignore WordPress.DateTime.CurrentTimeTimestamp
	$expiring = new WP_Query(
		array(
			'post_type'      => 'post',
			'post_status'    => 'publish',
			'posts_per_page' => 100,
			'no_found_rows'  => true,
			'fields'         => 'ids',
			'meta_query'     => array( // phpcs:ignore WordPress.DB.SlowDBQuery
				array(
					'key'     => 'studentup_last_date',
					'value'   => array( $today, gmdate( 'Y-m-d', strtotime( '+7 days' ) ) ),
					'compare' => 'BETWEEN',
					'type'    => 'DATE',
				),
			),
		)
	);
	$expired = new WP_Query(
		array(
			'post_type'      => 'post',
			'post_status'    => 'publish',
			'posts_per_page' => 100,
			'no_found_rows'  => true,
			'fields'         => 'ids',
			'meta_query'     => array( // phpcs:ignore WordPress.DB.SlowDBQuery
				array(
					'key'     => 'studentup_last_date',
					'value'   => $today,
					'compare' => '<',
					'type'    => 'DATE',
				),
			),
		)
	);
	return array(
		'expiring' => count( (array) $expiring->posts ),
		'expired'  => count( (array) $expired->posts ),
	);
}

function studentup_health_widget_render() {
	$counts   = wp_count_posts( 'post' );
	$dl       = studentup_health_deadlines();
	$redirect = 0;
	if ( function_exists( 'studentup_redirect_map' ) ) {
		$redirect = count( studentup_redirect_map() );
	}
	?>
	<ul class="su-health">
		<li>📰 Published: <strong><?php echo (int) $counts->publish; ?></strong></li>
		<li>📝 Drafts: <strong><?php echo (int) $counts->draft; ?></strong></li>
		<li>⏳ Expiring (7 days): <strong><?php echo (int) $dl['expiring']; ?></strong></li>
		<li>⏰ Expired (update/refresh): <strong><?php echo (int) $dl['expired']; ?></strong></li>
		<li>🔀 301 redirects: <strong><?php echo (int) $redirect; ?></strong></li>
	</ul>
	<p><a href="<?php echo esc_url( admin_url( 'themes.php?page=studentup-settings' ) ); ?>">StudentUp Settings →</a></p>
	<?php
}

function studentup_health_widget_register() {
	wp_add_dashboard_widget(
		'studentup_health',
		'StudentUp Health (SEO)',
		'studentup_health_widget_render'
	);
}
add_action( 'wp_dashboard_setup', 'studentup_health_widget_register' );
