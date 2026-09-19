<?php
/**
 * v64: Author box (E-E-A-T) + last-updated line.
 *
 * Google E-E-A-T (Experience, Expertise, Authoritativeness, Trust) ki
 * "ee content evaru rasaru, eppudu verify chesaru" undali — adi idi.
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * "Last updated" line (only when published != modified).
 */
function studentup_last_updated() {
	$modified = get_the_modified_time( 'U' );
	$posted   = get_the_time( 'U' );
	if ( ! $modified || ( $modified - $posted ) < DAY_IN_SECONDS ) {
		return '';
	}
	return sprintf(
		'<span class="su-updated">♻️ Last updated: %s</span>',
		esc_html( get_the_modified_date() )
	);
}

/**
 * Editorial team box (E-E-A-T + corrections email + editorial policy).
 *
 * v79: real logo avatar (custom_logo → site icon → emoji fallback) + Person
 * schema (Google News/Discover byline) + reviewed-date + channel follow links.
 */
function studentup_author_box() {
	$name  = (string) studentup_opt( 'author_name', 'StudentUp Editorial Team' );
	$bio   = (string) studentup_opt( 'author_bio', 'Verified from official notifications and government websites, and written in simple language.' );
	$email = studentup_contact_email();
	$pol   = get_page_by_path( 'editorial-policy' );
	$logo  = function_exists( 'get_theme_mod' ) ? (int) get_theme_mod( 'custom_logo' ) : 0;
	$soc   = function_exists( 'studentup_social_links' ) ? studentup_social_links() : array();
	$rev   = get_the_modified_date();
	?>
	<div class="su-author" itemscope itemtype="https://schema.org/Organization">
		<div class="su-author-avatar" aria-hidden="true"><?php
			if ( $logo ) {
				echo wp_kses_post( wp_get_attachment_image( $logo, array( 64, 64 ), false, array( 'itemprop' => 'logo' ) ) );
			} elseif ( function_exists( 'get_site_icon_url' ) && get_site_icon_url() ) {
				echo '<img src="' . esc_url( get_site_icon_url( 64 ) ) . '" width="64" height="64" alt="" itemprop="logo">';
			} else {
				echo '📝';
			}
		?></div>
		<div>
			<span itemprop="author" itemscope itemtype="https://schema.org/Person">
				<strong itemprop="name"><?php echo esc_html( $name ); ?></strong>
				<meta itemprop="jobTitle" content="Education Editor">
			</span>
			<p itemprop="description"><?php echo esc_html( $bio ); ?></p>
			<p class="su-author-links">
				<span>✅ Verified against official sources</span>
				<?php if ( $rev ) : ?>
					<span>🔍 Reviewed: <?php echo esc_html( $rev ); ?></span>
				<?php endif; ?>
				<?php if ( ! empty( $soc['telegram'] ) ) : ?>
					<span>✈️ <a href="<?php echo esc_url( $soc['telegram'] ); ?>" target="_blank" rel="noopener">Telegram</a></span>
				<?php endif; ?>
				<?php if ( ! empty( $soc['whatsapp'] ) ) : ?>
					<span>💬 <a href="<?php echo esc_url( $soc['whatsapp'] ); ?>" target="_blank" rel="noopener">WhatsApp</a></span>
				<?php endif; ?>
				<?php if ( $email ) : ?>
					<span>✉️ Report mistakes:
						<a href="mailto:<?php echo esc_attr( $email ); ?>"><?php echo esc_html( $email ); ?></a></span>
				<?php endif; ?>
				<?php if ( $pol ) : ?>
					<span>📘 <a href="<?php echo esc_url( get_permalink( $pol ) ); ?>">Editorial policy</a></span>
				<?php endif; ?>
			</p>
		</div>
	</div>
	<?php
}
