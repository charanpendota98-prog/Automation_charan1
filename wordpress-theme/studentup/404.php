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
			<h2 style="color:var(--navy)">Page not found</h2>
			<p style="color:var(--muted)">The link may have changed — search below or go to the home page.</p>
			<?php get_search_form(); ?>
			<p><a class="bluebtn" href="<?php echo esc_url( home_url( '/' ) ); ?>">Go to home →</a></p>
		</article>
	</div>
</main>
<?php
get_footer();
