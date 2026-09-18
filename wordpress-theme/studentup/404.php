<?php
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}
?>
<?php
/**
 * 404 — Telugu friendly.
 *
 * @package studentup
 */

get_header();
?>
<main id="main">
	<div class="wrap">
		<article class="article" style="text-align:center">
			<h1 style="font-size:56px;margin:0;color:var(--orange)">404</h1>
			<h2 style="color:var(--navy)">ఈ పేజీ దొరకలేదు</h2>
			<p style="color:var(--muted)">లింక్ మారి ఉండొచ్చు — కింద వెతకండి లేదా హోమ్‌కు వెళ్లండి.</p>
			<?php get_search_form(); ?>
			<p><a class="bluebtn" href="<?php echo esc_url( home_url( '/' ) ); ?>">హోమ్‌కు వెళ్లండి →</a></p>
		</article>
	</div>
</main>
<?php
get_footer();
