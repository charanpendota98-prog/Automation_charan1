<?php
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}
<?php
/**
 * Footer + fixed socials (right side, vertically centered).
 *
 * @package studentup
 */

?>
<footer class="footer">
	<div class="wrap">
		<div class="footer-grid">
			<div>
				<h4><?php bloginfo( 'name' ); ?></h4>
				<p><?php echo esc_html( get_bloginfo( 'description' ) ); ?></p>
				<p>✅ 100% అధికారిక మూలాలతో ధృవీకరించి ప్రచురిస్తాము. తప్పులు కనిపిస్తే <a href="mailto:<?php echo esc_attr( get_option( 'admin_email' ) ); ?>"><?php echo esc_html( get_option( 'admin_email' ) ); ?></a> కు తెలియజేయండి.</p>
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
					<li><a href="https://t.me/studentup_in" target="_blank" rel="noopener">Telegram ఛానల్</a></li>
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

<nav class="su-social" aria-label="సోషల్ మీడియా">
	<a href="https://wa.me/919999999999" target="_blank" rel="noopener" aria-label="WhatsApp">💬</a>
	<a href="https://t.me/studentup_in" target="_blank" rel="noopener" aria-label="Telegram">✈️</a>
	<a href="https://www.instagram.com/studentup.in" target="_blank" rel="noopener" aria-label="Instagram">📸</a>
	<a href="https://www.youtube.com/@studentupin" target="_blank" rel="noopener" aria-label="YouTube">▶️</a>
</nav>

<?php wp_footer(); ?>
</body>
</html>
