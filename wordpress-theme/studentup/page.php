<?php
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}
<?php
/**
 * Static page (About / Contact / Privacy …).
 *
 * @package studentup
 */

get_header();
?>
<main id="main">
	<div class="wrap">
		<?php
		while ( have_posts() ) :
			the_post();
			?>
			<article class="article">
				<div class="article-head"><h1><?php the_title(); ?></h1></div>
				<div class="article-content"><?php the_content(); ?></div>
				<?php studentup_trust_note(); ?>
			</article>
		<?php endwhile; ?>
	</div>
</main>
<?php
get_footer();
