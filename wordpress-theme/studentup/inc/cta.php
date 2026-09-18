<?php
/**
 * v71: Students Internet Center + WhatsApp/Telegram join blocks.
 *
 * Why here: the homepage and every post end with a practical next step for the
 * student. Both blocks read the same theme options as the social rail, so the
 * owner changes a number once (StudentUp -> Settings) and everything follows.
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Students Internet Center — apply from home: call, WhatsApp documents, get the PDF.
 */
function studentup_cta_internet_center() {
	$soc   = studentup_social_links();
	$phone = preg_replace( '/[^0-9+]/', '', (string) studentup_opt( 'social_whatsapp', '' ) );
	$tel   = $phone ? 'tel:' . $phone : '';
	$mail  = studentup_contact_email();
	?>
	<section class="su-ic" aria-labelledby="su-ic-title">
		<div class="su-ic-head">
			<h2 id="su-ic-title">Students Internet Center</h2>
			<span class="su-ic-badge"><?php esc_html_e( 'TS & AP', 'studentup' ); ?></span>
		</div>
		<p class="su-ic-lead"><?php esc_html_e( 'Apply for any job or scholarship from home. No need to visit any centre — one call is enough.', 'studentup' ); ?></p>
		<ol class="su-ic-steps">
			<li><?php esc_html_e( 'Call us with the post you want to apply for.', 'studentup' ); ?></li>
			<li><?php esc_html_e( 'WhatsApp your documents — photo, signature, certificates, resume.', 'studentup' ); ?></li>
			<li><?php esc_html_e( 'We apply and send the PDF — your filled application reaches you at the lowest service charge.', 'studentup' ); ?></li>
		</ol>
		<p class="su-ic-te"><?php esc_html_e( 'దరఖాస్తు మొత్తం మేము చేస్తాము — PDF మీకు పంపుతాము.', 'studentup' ); ?></p>
		<div class="su-ic-actions">
			<a class="su-wa-box" href="<?php echo esc_url( $soc['whatsapp'] ); ?>" target="_blank" rel="noopener">
				<span class="su-wa-ico" aria-hidden="true">💬</span>
				<span class="su-wa-txt">
					<b><?php esc_html_e( 'WhatsApp your documents', 'studentup' ); ?></b>
					<small><?php esc_html_e( 'Tap to open our WhatsApp — we reply fast', 'studentup' ); ?></small>
				</span>
			</a>
			<?php if ( $tel ) : ?>
				<a class="su-ic-alt" href="<?php echo esc_attr( $tel ); ?>">📞 <?php esc_html_e( 'Call now', 'studentup' ); ?></a>
			<?php endif; ?>
			<?php if ( $mail ) : ?>
				<a class="su-ic-alt" href="mailto:<?php echo esc_attr( $mail ); ?>">✉️ <?php esc_html_e( 'Email', 'studentup' ); ?></a>
			<?php endif; ?>
		</div>
	</section>
	<?php
}

/**
 * Join channel block — WhatsApp + Telegram (replaces the old newsletter form).
 */
function studentup_cta_join() {
	$soc = studentup_social_links();
	?>
	<section class="su-join" aria-labelledby="su-join-title">
		<div class="su-join-copy">
			<h2 id="su-join-title"><?php esc_html_e( 'Every job, exam date and result — first on your phone', 'studentup' ); ?></h2>
			<p><?php esc_html_e( 'Free daily updates for Telangana & Andhra Pradesh students. No spam calls, leave anytime.', 'studentup' ); ?></p>
			<p class="su-join-te"><?php esc_html_e( 'ఉద్యోగాలు · నోటిఫికేషన్లు · ఫలితాలు — మా WhatsApp / Telegram లో ముందుగా.', 'studentup' ); ?></p>
		</div>
		<div class="su-join-cta">
			<a class="su-join-wa" href="<?php echo esc_url( $soc['whatsapp'] ); ?>" target="_blank" rel="noopener"><?php esc_html_e( 'WhatsApp updates', 'studentup' ); ?></a>
			<a class="su-join-tg" href="<?php echo esc_url( $soc['telegram'] ); ?>" target="_blank" rel="noopener"><?php esc_html_e( 'Telegram channel', 'studentup' ); ?></a>
			<small><?php esc_html_e( '100% free · no calls · 1–3 updates a day', 'studentup' ); ?></small>
		</div>
	</section>
	<?php
}

/**
 * Both blocks, printed right above the footer on every page.
 */
function studentup_cta_section() {
	studentup_cta_internet_center();
	studentup_cta_join();
}
