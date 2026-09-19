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
			<?php
			// v80 (P28): popular categories + latest posts — 404 nunchi recovery.
			$su_pop = get_categories(
				array(
					'orderby'    => 'count',
					'order'      => 'DESC',
					'number'     => 6,
					'hide_empty' => true,
				)
			);
			if ( $su_pop ) {
				echo '<nav class="su-subcats su-404cats" aria-label="Popular categories">';
				foreach ( $su_pop as $su_c ) {
					printf(
						'<a href="%s">%s</a>',
						esc_url( get_category_link( $su_c ) ),
						esc_html( $su_c->name )
					);
				}
				echo '</nav>';
			}
			$su_new = new WP_Query(
				array(
					'posts_per_page'      => 5,
					'post_status'         => 'publish',
					'ignore_sticky_posts' => true,
					'no_found_rows'       => true,
				)
			);
			if ( $su_new->have_posts() ) {
				echo '<ul class="su-404latest">';
				while ( $su_new->have_posts() ) {
					$su_new->the_post();
					printf(
						'<li><a href="%s">%s</a></li>',
						esc_url( get_permalink() ),
						esc_html( get_the_title() )
					);
				}
				echo '</ul>';
				wp_reset_postdata();
			}
			?>
		</article>
	</div>
</main>
<?php
get_footer();
