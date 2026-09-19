<?php
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}
?>
<?php
/**
 * Category / tag / date archive — student card grid + ads.
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
				<h2><?php the_archive_title(); ?></h2>
				<p><?php echo esc_html( wp_strip_all_tags( get_the_archive_description() ) ); ?></p>
			</div>
		</div>
		<?php
		if ( function_exists( 'studentup_qual_bar' ) ) {
			studentup_qual_bar();          // v72: qualification filter on archives/categories too
			studentup_qual_active_note();
			studentup_hidden_note();
		}
		?>
		<div class="newsgrid" id="grid">
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
