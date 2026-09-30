<?php
/**
 * High-RPM Contextual Sponsor Hub & Verified Study Partner Box.
 *
 * Provides dedicated learning partners and preparation material recommendations.
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Render Contextual Sponsor & Study Partner Box.
 *
 * @return void
 */
function studentup_sponsor_partner_box() {
	if ( ! is_singular( 'post' ) || ! studentup_opt( 'sponsor_hub', '1' ) ) {
		return;
	}

	$post_id   = get_the_ID();
	$partner   = studentup_featured_partner_ad();
	$wa_number = studentup_wa_number( studentup_opt( 'social_whatsapp', '9182739312' ) );

	?>
	<section class="su-sponsor-box" aria-label="Verified Study Partner Opportunities">
		<div class="su-sponsor-kicker">SPONSORED · VERIFIED LEARNING PARTNERS</div>
		<div class="su-sponsor-card">
			<div class="su-sponsor-icon" aria-hidden="true"><?php echo studentup_ui_icon( 'school', 24 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?></div>
			<div class="su-sponsor-info">
				<h4 class="su-sponsor-title">Free Mock Tests & Preparation Study Kit</h4>
				<p class="su-sponsor-desc">Practice topic-wise model papers, previous exam question papers, and free online test series.</p>
			</div>
			<div class="su-sponsor-action">
				<a href="https://wa.me/<?php echo esc_attr( $wa_number ); ?>?text=<?php echo rawurlencode( 'Hello, I want free study material and mock test links.' ); ?>"
					target="_blank" rel="sponsored nofollow noopener" class="su-sponsor-btn">
					<?php echo studentup_ui_icon( 'download', 14 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> Get Free Study Kit →
				</a>
			</div>
		</div>
		<div class="su-sponsor-disc">Notice: Official notification and application links are provided separately in the article.</div>
	</section>
	<?php
}
