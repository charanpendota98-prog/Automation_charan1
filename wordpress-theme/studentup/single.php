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
			<article <?php post_class( 'article' ); ?>>
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
						<?php
						if ( function_exists( 'studentup_qual_labels' ) ) {
							$su_q = studentup_qual_labels( get_the_ID(), 3 );
							if ( $su_q ) {
								echo '<span>🎯 ' . esc_html( implode( ' · ', $su_q ) ) . '</span>';
							}
							$su_badge = studentup_last_date_badge( get_the_ID() );
							if ( $su_badge ) {
								echo '<span>' . wp_kses_post( $su_badge ) . '</span>';
							}
						}
						?>
					</div>
				</div>

				<?php studentup_ad( 'mid' ); ?>

				<div class="article-content"><?php the_content(); ?></div>

				<div class="share" aria-label="Share">
					<a href="https://wa.me/?text=<?php echo rawurlencode( get_the_title() . ' — ' . get_permalink() ); ?>" target="_blank" rel="noopener">Share on WhatsApp</a>
					<a href="https://t.me/share/url?url=<?php echo rawurlencode( get_permalink() ); ?>&text=<?php echo rawurlencode( get_the_title() ); ?>" target="_blank" rel="noopener">Share on Telegram</a>
					<a href="<?php echo esc_url( 'https://twitter.com/intent/tweet?url=' . rawurlencode( get_permalink() ) ); ?>" target="_blank" rel="noopener">Share on X</a>
					<button type="button" class="su-copy" data-url="<?php echo esc_url( get_permalink() ); ?>">🔗 Copy link</button>
				</div>

				<?php studentup_trust_note(); ?>
				<?php studentup_author_box(); ?>
				<?php if ( has_tag() ) : ?>
					<div class="su-tags" aria-label="Tags">🏷 <?php the_tags( '', ' · ', '' ); ?></div>
				<?php endif; ?>
				<nav class="post-nav" aria-label="More posts">
					<span class="post-nav-prev"><?php previous_post_link( '%link', '← %title' ); ?></span>
					<span class="post-nav-next"><?php next_post_link( '%link', '%title →' ); ?></span>
				</nav>
			</article>

			<?php studentup_ad( 'below-content' ); ?>
			<?php
			if ( comments_open() || get_comments_number() ) {
				comments_template();
			}
			?>

			<?php
			$su_rel = get_the_category();
			if ( $su_rel ) {
				$su_q = new WP_Query(
					array(
						'category__in'        => wp_list_pluck( $su_rel, 'term_id' ),
						'post__not_in'        => array( get_the_ID() ),
						'posts_per_page'      => 3,
						'ignore_sticky_posts' => true,
						'no_found_rows'       => true,   // v69 perf: related posts — count query vaddu
					)
				);
				if ( $su_q->have_posts() ) {
					echo '<div class="sectionhead"><div><h2>Read this too</h2></div></div><div class="newsgrid">';
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
