<?php
/**
 * 1-Click WhatsApp Status & Story Card Image Generator.
 *
 * Generates an instant high-resolution 1080x1920 (9:16) status card for sharing.
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Render WhatsApp Status Generator Box.
 *
 * @return void
 */
function studentup_status_card_generator() {
	if ( ! is_singular( 'post' ) || ! studentup_opt( 'status_card', '1' ) ) {
		return;
	}

	$post_id   = get_the_ID();
	$title     = get_the_title( $post_id );
	$vacancies = (string) get_post_meta( $post_id, 'studentup_vacancies', true );
	$last_date = (string) get_post_meta( $post_id, 'studentup_last_date', true );
	$qual      = (string) get_post_meta( $post_id, 'studentup_qual', true );

	?>
	<div class="su-status-card-box" id="su-status-box"
		data-title="<?php echo esc_attr( $title ); ?>"
		data-vacancies="<?php echo esc_attr( $vacancies ? $vacancies . ' Posts' : 'Official Notification' ); ?>"
		data-qual="<?php echo esc_attr( $qual ? $qual : 'Degree / Inter / 10th' ); ?>"
		data-last-date="<?php echo esc_attr( $last_date ? $last_date : 'Apply Immediately' ); ?>"
		data-site="studentup.in"
		aria-label="WhatsApp Status Card Generator">
		<div class="su-status-content">
			<span class="su-status-badge"><?php echo studentup_ui_icon( 'bell', 13 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> Viral Status Generator</span>
			<h4 class="su-status-title">WhatsApp Status Card (1-Click Download)</h4>
			<p class="su-status-desc">Download a high-resolution notification card formatted for WhatsApp stories and status.</p>
		</div>
		<button type="button" id="su-gen-status-btn" class="su-status-btn">
			<?php echo studentup_ui_icon( 'download', 15 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> Download Status Image
		</button>
		<canvas id="su-status-canvas" width="1080" height="1920" style="display:none;"></canvas>
	</div>
	<?php
}
