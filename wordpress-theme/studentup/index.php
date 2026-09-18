<?php
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}
<?php
/**
 * Fallback template — blog list (design cards same).
 *
 * @package studentup
 */

get_header();
?>
<main id="main">
	<div class="wrap">
		<div class="sectionhead">
			<div>
				<h2>
					<?php
					if ( is_home() && ! is_front_page() ) {
						single_post_title();
					} elseif ( is_search() ) {
						printf( 'వెతుకుడు: %s', esc_html( get_search_query() ) );
					} else {
						esc_html_e( 'తాజా అప్డేట్‌లు', 'studentup' );
					}
					?>
				</h2>
				<p>అధికారిక మూలాలతో ధృవీకరించిన మార్గదర్శకాలు</p>
			</div>
		</div>

		<?php get_search_form(); ?>

		<div class="newsgrid">
			<?php
			$su_i = 0;
			if ( have_posts() ) :
				while ( have_posts() ) :
					the_post();
					studentup_card( $su_i );
					$su_i++;
				endwhile;
			else :
				?>
				<p class="nores" style="display:block">ఏమీ దొరకలేదు — వేరే పదంతో వెతకండి.</p>
			<?php endif; ?>
		</div>

		<nav class="sectionhead" aria-label="పేజీలు">
			<div><?php echo wp_kses_post( paginate_links() ); ?></div>
		</nav>
	</div>
</main>
<?php
get_footer();
