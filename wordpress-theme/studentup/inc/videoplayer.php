<?php
/**
 * Smart High-CPM Video & Outstream Ad Container.
 *
 * Reserves a zero-CLS responsive video slot for media and outstream units.
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Render Video / High-CPM Outstream Slot.
 *
 * @return void
 */
function studentup_video_ad_slot() {
	if ( ! is_singular( 'post' ) || ! studentup_opt( 'video_ad_enabled', '1' ) ) {
		return;
	}

	$slot_id = (string) get_option( 'studentup_adsense_slot_video', '' );
	$client  = studentup_adsense_client();

	?>
	<div class="su-video-ad-container su-ad-reserved" style="min-height:200px" data-su-height="200" aria-label="Featured Media Unit">
		<aside class="su-video-ad-box">
			<div class="su-ad-kicker">SPONSORED MEDIA</div>
			<?php if ( $client && $slot_id && studentup_consent_ok() ) : ?>
				<ins class="adsbygoogle"
					style="display:block"
					data-ad-client="<?php echo esc_attr( $client ); ?>"
					data-ad-slot="<?php echo esc_attr( $slot_id ); ?>"
					data-ad-format="auto"
					data-full-width-responsive="true"></ins>
				<script>(adsbygoogle = window.adsbygoogle || []).push({});</script>
			<?php else : ?>
				<div class="su-video-native-card">
					<span class="su-vn-play" aria-hidden="true">▶</span>
					<div class="su-vn-text">
						<strong>Video Analysis & Exam Tips</strong>
						<p>Detailed notification breakdown and syllabus preparation videos available soon.</p>
					</div>
				</div>
			<?php endif; ?>
		</aside>
	</div>
	<?php
}
