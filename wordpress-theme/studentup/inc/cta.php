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
	$phone = studentup_call_number( studentup_opt( 'social_whatsapp', '' ) );
	$tel   = $phone ? 'tel:+91' . $phone : '';
	$mail  = studentup_contact_email();
	?>
	<section class="su-ic" aria-labelledby="su-ic-title">
		<div class="su-ic-head">
			<h2 id="su-ic-title"><?php esc_html_e( 'విద్యార్థుల ఇంటర్నెట్ సెంటర్', 'studentup' ); ?></h2>
			<span class="su-ic-badge"><?php esc_html_e( 'TS & AP', 'studentup' ); ?></span>
		</div>
		<p class="su-ic-sub"><?php esc_html_e( 'Students Internet Center · Telangana & Andhra Pradesh', 'studentup' ); ?></p>
		<p class="su-ic-lead su-ic-te"><?php esc_html_e( 'మీరు jobs apply చేయటం కోసం ఎక్కడికీ వెళ్లవలసిన అవసరం లేదు — కేవలం మా Center కి call చేసి, సంబంధించిన documents మా WhatsApp కి పంపిస్తే చాలు. అతి తక్కువ ధరలో apply చేసి, మీ filled application PDF మీకు పంపిస్తాం.', 'studentup' ); ?></p>
		<ol class="su-ic-steps">
			<li><?php esc_html_e( 'మీకు apply చేయాలనుకున్న job / scholarship పేరు మాకు call లేదా WhatsApp లో చెప్పండి.', 'studentup' ); ?></li>
			<li><?php esc_html_e( 'మీ documents — photo, signature, certificates, resume — మా WhatsApp కి పంపండి.', 'studentup' ); ?></li>
			<li><?php esc_html_e( 'మేము మొత్తం application fill చేసి, PDF మీకు పంపిస్తాం — అతి తక్కువ service charge లోనే.', 'studentup' ); ?></li>
		</ol>
		<p class="su-ic-perks">
			<span><?php esc_html_e( 'Application PDF', 'studentup' ); ?></span>
			<span><?php esc_html_e( 'పూర్తి Guidance', 'studentup' ); ?></span>
			<span><?php esc_html_e( 'Preparation Group', 'studentup' ); ?></span>
		</p>
		<div class="su-ic-actions">
			<a class="su-wa-box" href="<?php echo esc_url( $soc['whatsapp'] ); ?>" target="_blank" rel="noopener">
				<span class="su-wa-ico" aria-hidden="true"><?php echo studentup_social_icon( 'whatsapp', 20 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?></span>
				<span class="su-wa-txt">
					<b><?php esc_html_e( 'WhatsApp లో documents పంపండి', 'studentup' ); ?></b>
					<small><?php esc_html_e( 'Tap చేస్తే మా WhatsApp open అవుతుంది — వెంటనే reply', 'studentup' ); ?></small>
				</span>
			</a>
			<?php if ( $tel ) : ?>
				<a class="su-ic-alt" href="<?php echo esc_attr( $tel ); ?>"><?php echo studentup_social_icon( 'call', 15 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> <?php esc_html_e( 'Call now', 'studentup' ); ?></a>
			<?php endif; ?>
			<?php if ( $mail ) : ?>
				<a class="su-ic-alt" href="mailto:<?php echo esc_attr( $mail ); ?>"><?php echo studentup_social_icon( 'email', 15 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> <?php esc_html_e( 'Email', 'studentup' ); ?></a>
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
			<p class="su-join-te"><?php esc_html_e( 'Jobs · notifications · results — first on our WhatsApp / Telegram.', 'studentup' ); ?></p>
		</div>
		<div class="su-join-cta">
			<a class="su-join-wa" href="<?php echo esc_url( $soc['whatsapp'] ); ?>" target="_blank" rel="noopener"><?php echo studentup_social_icon( 'whatsapp', 16 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> <?php esc_html_e( 'WhatsApp updates', 'studentup' ); ?></a>
			<a class="su-join-tg" href="<?php echo esc_url( $soc['telegram'] ); ?>" target="_blank" rel="noopener"><?php echo studentup_social_icon( 'telegram', 16 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> <?php esc_html_e( 'Telegram channel', 'studentup' ); ?></a>
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

/**
 * v79: compact mid-article join strip (Telegram + WhatsApp).
 *
 * DELIBERATE markup rules: div/span/strong/a ONLY — no <p> (ad injector
 * counts </p> for position) and no <h2> (TOC scans headings). Same social
 * options as rail/footer — owner changes once, everywhere follows.
 */
function studentup_cta_join_inline() {
	$soc = studentup_social_links();
	?>
	<div class="su-join-inline" role="complementary" aria-label="<?php esc_attr_e( 'Join our channels', 'studentup' ); ?>">
		<span class="su-join-inline-txt"><strong>📲 <?php esc_html_e( 'Free job alerts on your phone', 'studentup' ); ?></strong>
			<span><?php esc_html_e( 'Jobs · results · hall tickets — first on WhatsApp / Telegram.', 'studentup' ); ?></span></span>
		<span class="su-join-inline-btns">
			<a class="su-join-wa" href="<?php echo esc_url( $soc['whatsapp'] ); ?>" target="_blank" rel="noopener"><?php echo studentup_social_icon( 'whatsapp', 15 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> <?php esc_html_e( 'Join WhatsApp', 'studentup' ); ?></a>
			<a class="su-join-tg" href="<?php echo esc_url( $soc['telegram'] ); ?>" target="_blank" rel="noopener"><?php echo studentup_social_icon( 'telegram', 15 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> <?php esc_html_e( 'Join Telegram', 'studentup' ); ?></a>
		</span>
	</div>
	<?php
}

/**
 * v79: inject the strip after the 2nd paragraph of single posts.
 * Priority 12 = before the in-article ad (20); the strip has no </p>
 * so the ad still lands after the 3rd ORIGINAL paragraph.
 */
function studentup_inject_join_cta( $content ) {
	if ( ! is_singular( 'post' ) || ! in_the_loop() || ! is_main_query() || is_feed() ) {
		return $content;
	}
	if ( '0' === (string) studentup_opt( 'join_cta_inline', '1' ) ) {
		return $content;
	}
	if ( false !== strpos( $content, 'su-join-inline' ) ) {
		return $content;   // already inject ayyindi (double render ledu)
	}
	/*
	 * v96 DEDUPE: bot (autoblog `monetize.insert_join_strip`) kuda article
	 * madhyalo `.su-join-strip` ni HTML lopala pedutundi — adi content lo
	 * unte theme inkoka strip render cheyyakudadu (okate page lo rendu join
	 * boxes = spammy look + AdSense "value" review lo minus).
	 */
	if ( false !== strpos( $content, 'su-join-strip' ) ) {
		return $content;
	}
	$parts = explode( '</p>', $content, 3 );
	if ( count( $parts ) < 3 ) {
		return $content;   // 2 paragraphs kanna takkuva → strip vaddu
	}
	ob_start();
	studentup_cta_join_inline();
	$strip = trim( (string) ob_get_clean() );
	if ( '' === $strip ) {
		return $content;
	}
	return $parts[0] . '</p>' . $parts[1] . '</p>'
		. '<!--su-join-inline-->' . $strip . $parts[2];
}
add_filter( 'the_content', 'studentup_inject_join_cta', 12 );
