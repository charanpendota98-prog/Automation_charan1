<?php
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}
?>
<?php
/**
 * Footer + fixed socials (right side, vertically centered).
 *
 * @package studentup
 */

?>
<?php studentup_cta_section(); ?>

<footer class="footer">
	<div class="wrap">
		<div class="footer-grid">
			<div>
				<h4><?php bloginfo( 'name' ); ?></h4>
				<p>Jobs, scholarships, results and exam updates for students.</p>
				<p>✅ Spotted a mistake? Tell us at <a href="mailto:<?php echo esc_attr( studentup_contact_email() ); ?>"><?php echo esc_html( studentup_contact_email() ); ?></a></p>
			</div>
			<div>
				<h4>Categories</h4>
				<ul>
					<?php
					foreach ( array_slice( studentup_most_used(), 0, 5 ) as $m ) :
						$term = studentup_used_term( $m['slug'] );   // v89: alias-aware
						if ( ! $term ) {
							continue;
						}
						?>
						<li><a href="<?php echo esc_url( get_category_link( $term ) ); ?>"><?php echo esc_html( $m['label'] ); ?></a></li>
					<?php endforeach; ?>
				</ul>
			</div>
			<div>
				<h4>Other links</h4>
				<?php
				if ( has_nav_menu( 'footer' ) ) {
					wp_nav_menu( array( 'theme_location' => 'footer', 'container' => false, 'depth' => 1, 'fallback_cb' => false ) );
				}
				?>
				<ul>
					<li><a href="<?php echo esc_url( studentup_social_links()['telegram'] ); ?>" target="_blank" rel="noopener">Telegram channel</a></li>
					<li><a href="<?php echo esc_url( home_url( '/#qualsplit' ) ); ?>">Jobs by qualification</a></li>
					<?php
					/*
					 * v94: policy pages footer lo link avvali — readers + Google
					 * (AdSense reviewers kuda) prathi page nunchi reach avvali.
					 * Page publish kaakapote link render avvadu (404 ledu).
					 */
					$su_policy = array(
						'privacy'          => 'Privacy policy',
						'about'            => 'About us',
						'contact'          => 'Contact',
						'disclaimer'       => 'Disclaimer',
						'terms'            => 'Terms',
						'editorial-policy' => 'Editorial policy',
					);
					foreach ( $su_policy as $su_slug => $su_label ) :
						$su_page = get_page_by_path( $su_slug );
						if ( ! $su_page || 'publish' !== get_post_status( $su_page ) ) {
							continue;
						}
						?>
						<li><a href="<?php echo esc_url( get_permalink( $su_page ) ); ?>"><?php echo esc_html( $su_label ); ?></a></li>
					<?php endforeach; ?>
				</ul>
			</div>
		</div>
		<div class="footer-bottom">
			<span>© <?php echo esc_html( gmdate( 'Y' ) ); ?> <?php bloginfo( 'name' ); ?> — All rights reserved.</span>
			<span>Always confirm job/exam details once in the official notification.</span>
			<?php studentup_tg_join_block( 'footer' ); // v91: Telegram join chip (private channel override supported) ?>
		</div>
	</div>
</footer>

<?php $su_soc = studentup_social_links(); ?>
<!-- v71: rail auto-hides after 9s, returns every 2 minutes (see assets/js/studentup.js).
     ✕ = hide now · ‹ tab = show again instantly. -->
<nav class="su-social" id="surail" aria-label="<?php esc_attr_e( 'Social media', 'studentup' ); ?>">
	<button type="button" class="su-close" id="suclose" aria-label="<?php esc_attr_e( 'Hide social icons', 'studentup' ); ?>">✕</button>
	<a class="su-soc su-rail-wa" href="<?php echo esc_url( $su_soc['whatsapp'] ); ?>" target="_blank" rel="noopener" aria-label="WhatsApp"><?php echo studentup_social_icon( 'whatsapp', 19 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?></a>
	<a class="su-soc su-rail-tg" href="<?php echo esc_url( $su_soc['telegram'] ); ?>" target="_blank" rel="noopener" aria-label="Telegram"><?php echo studentup_social_icon( 'telegram', 19 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?></a>
	<a class="su-soc su-rail-ig" href="<?php echo esc_url( $su_soc['instagram'] ); ?>" target="_blank" rel="noopener" aria-label="Instagram"><?php echo studentup_social_icon( 'instagram', 19 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?></a>
	<a class="su-soc su-rail-yt" href="<?php echo esc_url( $su_soc['youtube'] ); ?>" target="_blank" rel="noopener" aria-label="YouTube"><?php echo studentup_social_icon( 'youtube', 19 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?></a>
</nav>
<button type="button" class="su-tab" id="sutab" aria-label="<?php esc_attr_e( 'Show social icons', 'studentup' ); ?>">‹</button>

<?php
// v64: sticky bottom ad (option: StudentUp → Ads → Sticky bottom ad ON)
if ( studentup_opt( 'sticky_ad', '0' ) ) :
	?>
	<script>document.body.classList.add('su-has-stickyad');</script>
	<div class="su-stickyad" id="su-stickyad">
		<button type="button" class="su-sticky-close" aria-label="Close">✕</button>
		<?php studentup_ad( 'anchor' ); ?>
	</div>
<?php endif; ?>

<?php
// v72.1: App DOWNLOAD — button prathi visit lo kanipistundi (mobile first).
// Click: Android/Chrome lo install prompt, iPhone/desktop lo device-wise steps.
if ( studentup_opt( 'pwa', '1' ) && studentup_opt( 'install_prompt', '1' ) ) :
	?>
	<button type="button" class="installbtn" id="installbtn" aria-controls="installhint" aria-expanded="false">⬇️ Download App <span class="ibadge">FREE</span></button>
	<div class="installsheet" id="installhint" hidden role="dialog" aria-modal="true" aria-labelledby="isheet-title">
		<h3 id="isheet-title">Install StudentUp as an app</h3>
		<p class="isub">Open it with one tap · pages you visited stay available offline.</p>
		<ol id="isteps">
			<li><b>Android (Chrome):</b> ⋮ Menu → <b>Install app</b> / <b>Add to Home screen</b></li>
			<li><b>iPhone (Safari):</b> <b>Share</b> ⬆️ → <b>Add to Home Screen</b> → Add</li>
			<li><b>Computer:</b> click the install icon in the address bar</li>
		</ol>
		<div class="irow">
			<button type="button" class="installok" id="installnow">Install now</button>
			<button type="button" class="installclose" id="installclose">Later</button>
		</div>
	</div>
<?php endif; ?>

<?php
// v92: Saved rail + drawer (reader bookmarks). localStorage mattrame — server load ledu.
studentup_saved_panel();
?>

<?php wp_footer(); ?>
</body>
</html>
