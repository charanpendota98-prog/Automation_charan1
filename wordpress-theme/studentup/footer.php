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
				<p><?php echo esc_html( get_bloginfo( 'description' ) ); ?></p>
				<p>✅ 100% అధికారిక మూలాలతో ధృవీకరించి ప్రచురిస్తాము. తప్పులు కనిపిస్తే <a href="mailto:<?php echo esc_attr( studentup_contact_email() ); ?>"><?php echo esc_html( studentup_contact_email() ); ?></a> కు తెలియజేయండి.</p>
			</div>
			<div>
				<h4>విభాగాలు</h4>
				<ul>
					<?php
					foreach ( array_slice( studentup_most_used(), 0, 5 ) as $m ) :
						$term = get_category_by_slug( $m['slug'] );
						if ( ! $term ) {
							continue;
						}
						?>
						<li><a href="<?php echo esc_url( get_category_link( $term ) ); ?>"><?php echo esc_html( $m['label'] ); ?></a></li>
					<?php endforeach; ?>
				</ul>
			</div>
			<div>
				<h4>ఇతర లింకులు</h4>
				<?php
				if ( has_nav_menu( 'footer' ) ) {
					wp_nav_menu( array( 'theme_location' => 'footer', 'container' => false, 'depth' => 1, 'fallback_cb' => false ) );
				}
				?>
				<ul>
					<li><a href="<?php echo esc_url( studentup_social_links()['telegram'] ); ?>" target="_blank" rel="noopener">Telegram ఛానల్</a></li>
					<li><a href="<?php echo esc_url( home_url( '/#breaking' ) ); ?>">బ్రేకింగ్ న్యూస్</a></li>
				</ul>
			</div>
		</div>
		<div class="footer-bottom">
			<span>© <?php echo esc_html( gmdate( 'Y' ) ); ?> <?php bloginfo( 'name' ); ?> — అన్ని హక్కులు కలవు.</span>
			<span>కరెక్ట్నెస్ కోసం మాత్రమే: ఉద్యోగ/పరీక్ష సమాచారం అధికారిక నోటిఫికేషన్‌తో నిర్ధారించుకోండి.</span>
		</div>
	</div>
</footer>

<?php $su_soc = studentup_social_links(); ?>
<!-- v71: rail auto-hides after 9s, returns every 2 minutes (see assets/js/studentup.js).
     ✕ = hide now · ‹ tab = show again instantly. -->
<nav class="su-social" id="surail" aria-label="<?php esc_attr_e( 'సోషల్ మీడియా', 'studentup' ); ?>">
	<button type="button" class="su-close" id="suclose" aria-label="<?php esc_attr_e( 'Hide social icons', 'studentup' ); ?>">✕</button>
	<a href="<?php echo esc_url( $su_soc['whatsapp'] ); ?>" target="_blank" rel="noopener" aria-label="WhatsApp">💬</a>
	<a href="<?php echo esc_url( $su_soc['telegram'] ); ?>" target="_blank" rel="noopener" aria-label="Telegram">✈️</a>
	<a href="<?php echo esc_url( $su_soc['instagram'] ); ?>" target="_blank" rel="noopener" aria-label="Instagram">📸</a>
	<a href="<?php echo esc_url( $su_soc['youtube'] ); ?>" target="_blank" rel="noopener" aria-label="YouTube">▶️</a>
</nav>
<button type="button" class="su-tab" id="sutab" aria-label="<?php esc_attr_e( 'Show social icons', 'studentup' ); ?>">‹</button>

<?php
// v64: sticky bottom ad (option: StudentUp → Ads → Sticky bottom ad ON)
if ( studentup_opt( 'sticky_ad', '0' ) ) :
	?>
	<div class="su-stickyad" id="su-stickyad">
		<button type="button" class="su-sticky-close" aria-label="మూసివేయండి">✕</button>
		<?php studentup_ad( 'anchor' ); ?>
	</div>
<?php endif; ?>

<?php
// v72.1: App DOWNLOAD — button prathi visit lo kanipistundi (mobile first).
// Click: Android/Chrome lo install prompt, iPhone/desktop lo device-wise steps.
if ( studentup_opt( 'pwa', '1' ) && studentup_opt( 'install_prompt', '1' ) ) :
	?>
	<button type="button" class="installbtn" id="installbtn">⬇️ App డౌన్‌లోడ్ <span class="ibadge">FREE</span></button>
	<div class="installsheet" id="installhint" hidden role="dialog" aria-labelledby="isheet-title">
		<h3 id="isheet-title">StudentUp ను యాప్‌లా ఇన్‌స్టాల్ చేసుకోండి</h3>
		<p class="isub">ఒక్క ట్యాప్‌తో తెరవండి · ఇంటర్నెట్ లేకపోయినా చూసిన పేజీలు కనిపిస్తాయి.</p>
		<ol id="isteps">
			<li><b>Android (Chrome):</b> ⋮ మెనూ → <b>Install app</b> / <b>Add to Home screen</b></li>
			<li><b>iPhone (Safari):</b> <b>Share</b> ⬆️ → <b>Add to Home Screen</b> → Add</li>
			<li><b>Computer:</b> address bar లో install ఐకాన్ నొక్కండి</li>
		</ol>
		<div class="irow">
			<button type="button" class="installok" id="installnow">ఇప్పుడే ఇన్‌స్టాల్ చేయండి</button>
			<button type="button" class="installclose" id="installclose">తర్వాత</button>
		</div>
	</div>
<?php endif; ?>

<?php wp_footer(); ?>
</body>
</html>
