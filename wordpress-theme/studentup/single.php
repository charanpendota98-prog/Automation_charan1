<?php
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}
?>
<?php
/**
 * Single post — article layout: meta, content, ads, share, related, trust note.
 *
 * @package studentup
 */

get_header();
?>
<div class="su-progress" aria-hidden="true"><span id="su-progress-bar"></span></div>
<main id="main">
	<div class="wrap">
		<?php
		while ( have_posts() ) :
			the_post();
			?>
			<div class="crumbs"><?php echo wp_kses_post( studentup_breadcrumbs() ); ?></div>
			<article class="article">
				<div class="article-head">
					<h1><?php the_title(); ?></h1>
					<div class="article-meta">
						<span>📅 <?php echo esc_html( get_the_date() ); ?></span>
						<span>⏱ <?php echo esc_html( studentup_reading_time() ); ?></span>
						<?php echo wp_kses_post( studentup_last_updated() ); ?>
						<?php $su_cats = get_the_category(); ?>
						<?php if ( $su_cats ) : ?>
							<span>🏷 <?php echo esc_html( $su_cats[0]->name ); ?></span>
						<?php endif; ?>
					</div>
				</div>

				<?php studentup_ad( 'mid' ); ?>

				<div class="article-content"><?php the_content(); ?></div>

				<div class="share" aria-label="షేర్ చేయండి">
					<a href="https://wa.me/?text=<?php echo rawurlencode( get_the_title() . ' — ' . get_permalink() ); ?>" target="_blank" rel="noopener">WhatsApp షేర్</a>
					<a href="https://t.me/share/url?url=<?php echo rawurlencode( get_permalink() ); ?>&text=<?php echo rawurlencode( get_the_title() ); ?>" target="_blank" rel="noopener">Telegram షేర్</a>
					<a href="<?php echo esc_url( 'https://twitter.com/intent/tweet?url=' . rawurlencode( get_permalink() ) ); ?>" target="_blank" rel="noopener">X షేర్</a>
					<button type="button" class="su-copy" data-url="<?php echo esc_url( get_permalink() ); ?>">🔗 లింక్ కాపీ</button>
				</div>

				<?php studentup_trust_note(); ?>
				<?php studentup_author_box(); ?>
			</article>

			<?php
			$su_rel = get_the_category();
			if ( $su_rel ) {
				$su_q = new WP_Query(
					array(
						'category__in'        => wp_list_pluck( $su_rel, 'term_id' ),
						'post__not_in'        => array( get_the_ID() ),
						'posts_per_page'      => 3,
						'ignore_sticky_posts' => true,
					)
				);
				if ( $su_q->have_posts() ) {
					echo '<div class="sectionhead"><div><h2>ఇది కూడా చదవండి</h2></div></div><div class="newsgrid">';
					$su_i = 0;
					while ( $su_q->have_posts() ) {
						$su_q->the_post();
						studentup_card( $su_i );
						$su_i++;
					}
					echo '</div>';
				}
				wp_reset_postdata();
			}
			?>
		<?php endwhile; ?>
	</div>
</main>
<?php
get_footer();
