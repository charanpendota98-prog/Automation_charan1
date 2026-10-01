<?php
/**
 * Author Box (E-E-A-T) + Last-Updated Freshness Line.
 *
 * Google E-E-A-T (Experience, Expertise, Authoritativeness, Trust)
 * author profile card with verified experience and social links.
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
		'<span class="su-updated">' . studentup_ui_icon( 'refresh', 13 ) . ' Last updated: %s</span>', // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG
		esc_html( get_the_modified_date() )
	);
}

/**
 * Compact top byline.
 */
function studentup_author_meta() {
	$name = (string) studentup_opt( 'author_name', 'Charan Pendota' );
	$rev  = get_the_modified_date();
	?>
	<div class="su-author-meta" itemprop="author" itemscope itemtype="https://schema.org/Person">
		<span><?php echo studentup_ui_icon( 'person', 14 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> <strong itemprop="name"><?php echo esc_html( $name ); ?></strong></span>
		<?php if ( $rev ) : ?>
			<span>Reviewed: <time itemprop="dateModified" datetime="<?php echo esc_attr( get_the_modified_date( 'c' ) ); ?>"><?php echo esc_html( $rev ); ?></time></span>
		<?php endif; ?>
	</div>
	<?php
}

/**
 * Full Author Box (E-E-A-T) for every blog post.
 */
function studentup_author_box() {
	$name      = (string) studentup_opt( 'author_name', 'Charan Pendota' );
	$exp       = (string) studentup_opt( 'author_experience', 'Senior Education Editor · 5+ Years of Experience' );
	$bio       = (string) studentup_opt( 'author_bio', 'Charan Pendota is a senior content editor and digital career researcher with 5+ years of experience in Telugu job notifications, exam patterns, and career guidance. At StudentUp, he leads the fact-checking desk, ensuring 100% source-verified information for Telangana and Andhra Pradesh students.' );
	$avatar    = (string) studentup_opt( 'author_avatar_url', '' );
	$email     = studentup_contact_email();
	$soc       = function_exists( 'studentup_social_links' ) ? studentup_social_links() : array();
	$rev       = get_the_modified_date();
	$logo_id   = get_theme_mod( 'custom_logo' );
	$icon_url  = get_site_icon_url( 64 );

	?>
	<section class="su-author-box" itemprop="author" itemscope itemtype="https://schema.org/Person" aria-label="About the Author">
		<div class="su-ab-left">
			<div class="su-ab-avatar">
				<?php if ( $avatar && wp_http_validate_url( $avatar ) ) : ?>
					<img src="<?php echo esc_url( $avatar ); ?>" alt="<?php echo esc_attr( $name ); ?>" width="80" height="80" loading="lazy" decoding="async" class="su-ab-img">
				<?php elseif ( $logo_id || $icon_url ) : ?>
					<div class="su-ab-placeholder" aria-hidden="true">
						<span>CP</span>
					</div>
				<?php else : ?>
					<div class="su-ab-placeholder" aria-hidden="true">
						<span>CP</span>
					</div>
				<?php endif; ?>
				<span class="su-ab-verified-badge" title="E-E-A-T Verified Author" aria-label="Verified"><?php echo studentup_ui_icon( 'check', 12 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?></span>
			</div>
		</div>

		<div class="su-ab-right">
			<div class="su-ab-head">
				<div>
					<h3 class="su-ab-name" itemprop="name"><?php echo esc_html( $name ); ?></h3>
					<span class="su-ab-exp" itemprop="jobTitle"><?php echo esc_html( $exp ); ?></span>
				</div>
				<span class="su-ab-shield"><?php echo studentup_ui_icon( 'shield', 13 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> E-E-A-T Certified</span>
			</div>

			<p class="su-ab-bio" itemprop="description"><?php echo esc_html( $bio ); ?></p>

			<div class="su-ab-footer">
				<div class="su-ab-trust-pills">
					<span class="su-ab-pill"><?php echo studentup_ui_icon( 'check', 13 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> 100% Official Source Verified</span>
					<?php if ( $rev ) : ?>
						<span class="su-ab-pill"><?php echo studentup_ui_icon( 'search', 13 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> Reviewed: <?php echo esc_html( $rev ); ?></span>
					<?php endif; ?>
				</div>

				<div class="su-ab-socials">
					<?php if ( ! empty( $soc['whatsapp_channel'] ) ) : ?>
						<a href="<?php echo esc_url( $soc['whatsapp_channel'] ); ?>" target="_blank" rel="noopener" class="su-ab-soc wa" title="WhatsApp Channel">
							<?php echo studentup_social_icon( 'whatsapp', 14 ); // phpcs:ignore WordPress.Security.EscapeOutput ?> WhatsApp Channel
						</a>
					<?php elseif ( ! empty( $soc['whatsapp'] ) ) : ?>
						<a href="<?php echo esc_url( $soc['whatsapp'] ); ?>" target="_blank" rel="noopener" class="su-ab-soc wa" title="WhatsApp">
							<?php echo studentup_social_icon( 'whatsapp', 14 ); // phpcs:ignore WordPress.Security.EscapeOutput ?> WhatsApp
						</a>
					<?php endif; ?>

					<?php if ( ! empty( $soc['telegram'] ) ) : ?>
						<a href="<?php echo esc_url( $soc['telegram'] ); ?>" target="_blank" rel="noopener" class="su-ab-soc tg" title="Telegram">
							<?php echo studentup_social_icon( 'telegram', 14 ); // phpcs:ignore WordPress.Security.EscapeOutput ?> Telegram
						</a>
					<?php endif; ?>

					<?php if ( ! empty( $soc['instagram'] ) ) : ?>
						<a href="<?php echo esc_url( $soc['instagram'] ); ?>" target="_blank" rel="noopener" class="su-ab-soc ig" title="Instagram">
							<?php echo studentup_social_icon( 'instagram', 14 ); // phpcs:ignore WordPress.Security.EscapeOutput ?> Instagram
						</a>
					<?php endif; ?>

					<?php if ( ! empty( $soc['youtube'] ) ) : ?>
						<a href="<?php echo esc_url( $soc['youtube'] ); ?>" target="_blank" rel="noopener" class="su-ab-soc yt" title="YouTube">
							<?php echo studentup_social_icon( 'youtube', 14 ); // phpcs:ignore WordPress.Security.EscapeOutput ?> YouTube
						</a>
					<?php endif; ?>

					<?php if ( $email ) : ?>
						<a href="mailto:<?php echo esc_attr( $email ); ?>" class="su-ab-soc mail" title="Contact Author">
							<?php echo studentup_social_icon( 'email', 14 ); // phpcs:ignore WordPress.Security.EscapeOutput ?> Contact Email
						</a>
					<?php endif; ?>
				</div>

				<div class="su-ab-policies" style="font-size:11px;color:#94a3b8;margin-top:6px;">
					<a href="<?php echo esc_url( home_url( '/editorial-policy/' ) ); ?>" style="color:#64748b;text-decoration:underline;">Editorial policy</a> ·
					<a href="<?php echo esc_url( home_url( '/contact/' ) ); ?>" style="color:#64748b;text-decoration:underline;">Report mistakes</a>
				</div>
			</div>
		</div>

		<div itemprop="publisher" itemscope itemtype="https://schema.org/Organization" style="display:none">
			<meta itemprop="name" content="<?php echo esc_attr( get_bloginfo( 'name' ) ); ?>">
			<?php if ( $icon_url ) : ?>
				<link itemprop="logo" href="<?php echo esc_url( $icon_url ); ?>">
			<?php endif; ?>
		</div>
	</section>
	<?php
}
