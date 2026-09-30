<?php
/**
 * AI Quick Highlights & 1-Minute TL;DR Summary Box.
 *
 * Provides a concise top summary of vacancies, qualification, last date, and salary.
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Render Quick Highlights / TL;DR Box.
 *
 * @return void
 */
function studentup_quick_summary_box() {
	if ( ! is_singular( 'post' ) || ! studentup_opt( 'quick_summary', '1' ) ) {
		return;
	}

	$post_id   = get_the_ID();
	$vacancies = get_post_meta( $post_id, 'studentup_vacancies', true );
	$last_date = get_post_meta( $post_id, 'studentup_last_date', true );
	$qual      = get_post_meta( $post_id, 'studentup_qual', true );
	$salary    = get_post_meta( $post_id, 'studentup_salary', true );
	$apply_url = get_post_meta( $post_id, 'studentup_apply_url', true );

	$points = array();
	if ( $vacancies ) {
		$points[] = array( 'icon' => 'work', 'label' => 'Total Vacancies', 'val' => $vacancies . ' Posts' );
	}
	if ( $qual ) {
		$points[] = array( 'icon' => 'school', 'label' => 'Qualification', 'val' => $qual );
	}
	if ( $last_date ) {
		$points[] = array( 'icon' => 'clock', 'label' => 'Last Date to Apply', 'val' => $last_date );
	}
	if ( $salary ) {
		$points[] = array( 'icon' => 'wallet', 'label' => 'Pay Scale / Salary', 'val' => $salary );
	}

	if ( empty( $points ) ) {
		return;
	}

	?>
	<section class="su-summary-box" aria-label="1-Minute Key Highlights">
		<div class="su-summary-head">
			<span class="su-summary-badge" aria-hidden="true"><?php echo studentup_ui_icon( 'bolt', 13 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> 1-Minute Read</span>
			<h3 class="su-summary-title">Key Highlights</h3>
		</div>
		<ul class="su-summary-list">
			<?php foreach ( $points as $pt ) : ?>
				<li class="su-summary-item">
					<span class="su-summary-icon" aria-hidden="true"><?php echo studentup_ui_icon( $pt['icon'], 15 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?></span>
					<div class="su-summary-text">
						<strong><?php echo esc_html( $pt['label'] ); ?>:</strong>
						<span><?php echo esc_html( $pt['val'] ); ?></span>
					</div>
				</li>
			<?php endforeach; ?>
		</ul>
		<?php if ( $apply_url && wp_http_validate_url( $apply_url ) ) : ?>
			<div class="su-summary-cta">
				<a href="<?php echo esc_url( $apply_url ); ?>" target="_blank" rel="noopener nofollow" class="su-summary-btn">
					<?php echo studentup_ui_icon( 'external', 14 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> Official Apply Link →
				</a>
			</div>
		<?php endif; ?>
	</section>
	<?php
}
