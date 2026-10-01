<?php
/**
 * Reader Accessibility Toolbar & Community Pulse Hub.
 *
 * Provides font size controls, reading time estimation, and community join card.
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Render Reader Accessibility Toolbar (Font Size & Reading Time).
 *
 * @return void
 */
function studentup_reader_toolbar() {
	if ( ! is_singular( 'post' ) || ! studentup_opt( 'reader_toolbar', '1' ) ) {
		return;
	}

	$post_id = get_the_ID();
	$content = get_post_field( 'post_content', $post_id );
	$words   = str_word_count( wp_strip_all_tags( (string) $content ) );
	$minutes = max( 1, (int) ceil( $words / 150 ) );

	?>
	<div class="su-reader-bar" aria-label="Reading options">
		<div class="su-rb-left">
			<span class="su-rb-time"><?php echo studentup_ui_icon( 'clock', 13 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> <?php echo (int) $minutes; ?> min read</span>
		</div>
		<div class="su-rb-right">
			<span class="su-rb-label">Text Size:</span>
			<div class="su-font-sizer" role="group" aria-label="Font size controls">
				<button type="button" class="su-fz-btn" data-su-font="small" title="Small text" aria-label="Decrease font size">A-</button>
				<button type="button" class="su-fz-btn is-active" data-su-font="normal" title="Normal text" aria-label="Reset font size">A</button>
				<button type="button" class="su-fz-btn" data-su-font="large" title="Large text" aria-label="Increase font size">A+</button>
			</div>
		</div>
	</div>
	<?php
}

/**
 * Render Community Pulse Join Card.
 *
 * @return void
 */
function studentup_community_pulse_card() {
	if ( ! studentup_opt( 'community_pulse', '1' ) ) {
		return;
	}

	$socials = studentup_social_links();
	$wa_link = ! empty( $socials['whatsapp_channel'] ) ? $socials['whatsapp_channel'] : ( ! empty( $socials['whatsapp'] ) ? $socials['whatsapp'] : 'https://wa.me/9182739312' );
	$tg_link = ! empty( $socials['telegram'] ) ? $socials['telegram'] : 'https://t.me/studentup_in';

	?>
	<section class="su-community-card" aria-label="Join Student Community">
		<div class="su-comm-head">
			<span class="su-pulse-badge"><span class="su-pulse-dot" aria-hidden="true"></span> 50,000+ Students Live Community</span>
			<h3 class="su-comm-title">Instant Job Alerts & Exam Updates</h3>
			<p class="su-comm-desc">Get the latest notifications, syllabus breakdowns, and preparation guides directly on your mobile.</p>
		</div>
		<div class="su-comm-buttons">
			<a href="<?php echo esc_url( $wa_link ); ?>" target="_blank" rel="noopener" class="su-comm-btn su-comm-wa">
				<?php echo studentup_social_icon( 'whatsapp', 18 ); // phpcs:ignore WordPress.Security.EscapeOutput ?> Join WhatsApp Channel
			</a>
			<a href="<?php echo esc_url( $tg_link ); ?>" target="_blank" rel="noopener" class="su-comm-btn su-comm-tg">
				<?php echo studentup_social_icon( 'telegram', 18 ); // phpcs:ignore WordPress.Security.EscapeOutput ?> Join Telegram Group
			</a>
		</div>
	</section>
	<?php
}
