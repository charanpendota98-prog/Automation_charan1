<?php
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}
?>
<?php
/**
 * Category / tag / date search results — same card grid.
 *
 * @package studentup
 */

get_header();
?>
<main id="main">
	<div class="wrap">
		<div class="crumbs"><?php echo wp_kses_post( studentup_breadcrumbs() ); ?></div>
		<div class="sectionhead">
			<div>
				<h1><?php the_archive_title(); ?></h1>
				<p><?php echo esc_html( wp_strip_all_tags( get_the_archive_description() ) ); ?></p>
			</div>
		</div>
		<?php if ( ! have_posts() ) : ?>
			<div class="su-empty">
				<p><?php esc_html_e( 'No results — try a different word.', 'studentup' ); ?></p>
				<?php get_search_form(); ?>
				<p><a class="su-btn" href="<?php echo esc_url( home_url( '/' ) ); ?>">
					<?php esc_html_e( 'Go to home', 'studentup' ); ?></a></p>
			</div>
		<?php endif; ?>
		<div class="newsgrid">
			<?php
			$su_i = 0;
			while ( have_posts() ) :
				the_post();
				if ( 4 === $su_i ) {
					studentup_ad( 'in-feed' );
				}
				studentup_card( $su_i );
				$su_i++;
			endwhile;
			?>
		</div>
		<?php studentup_ad( 'mid' ); ?>
		<nav class="sectionhead" aria-label="Pages"><div><?php echo wp_kses_post( paginate_links() ); ?></div></nav>
	</div>
	<?php get_sidebar(); ?>
</main>
<?php
get_footer();
