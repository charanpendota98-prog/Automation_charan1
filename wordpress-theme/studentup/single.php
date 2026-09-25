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
						<?php echo wp_kses_post( studentup_last_updated() ); ?>
						<?php // studentup_reading_time() intentionally not shown on article pages. ?>
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
					<?php // Byline is intentionally omitted from the article header; schema retains publisher/author data. ?>
				</div>

				<?php if ( has_post_thumbnail() ) : ?>
					<figure class="su-featured-hero">
						<?php the_post_thumbnail( 'studentup-discover', array(
							'loading'       => 'eager',
							'fetchpriority' => 'high',
							'decoding'      => 'async',
							'alt'           => esc_attr( get_the_title() ),
						) ); ?>
					</figure>
				<?php endif; ?>

				<?php echo wp_kses_post( studentup_save_button( 0, 'su-save-single' ) ); // v92: 🔖 save-for-later ?>

				<?php echo function_exists( 'studentup_expired_notice' ) ? wp_kses_post( studentup_expired_notice() ) : ''; ?>

				<?php studentup_ad( 'mid' ); ?>

				<div class="article-content"><?php the_content(); ?></div>

				<div class="share" aria-label="Share">
					<a class="su-share-btn su-share-wa" href="https://wa.me/?text=<?php echo rawurlencode( get_the_title() . ' — ' . get_permalink() ); ?>" target="_blank" rel="noopener"><?php echo studentup_social_icon( 'whatsapp', 15 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> Share on WhatsApp</a>
					<a class="su-share-btn su-share-tg" href="https://t.me/share/url?url=<?php echo rawurlencode( get_permalink() ); ?>&text=<?php echo rawurlencode( get_the_title() ); ?>" target="_blank" rel="noopener"><?php echo studentup_social_icon( 'telegram', 15 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> Share on Telegram</a>
					<a class="su-share-btn su-share-x" href="<?php echo esc_url( 'https://twitter.com/intent/tweet?url=' . rawurlencode( get_permalink() ) ); ?>" target="_blank" rel="noopener"><?php echo studentup_social_icon( 'x', 14 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> Share on X</a>
					<button type="button" class="su-copy su-share-copy" data-url="<?php echo esc_url( get_permalink() ); ?>"><?php echo studentup_social_icon( 'link', 14 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> Copy link</button>
				</div>

				<?php
				// These helpers remain available for policy pages, not every post.
				if ( false ) {
					studentup_trust_note();
					studentup_author_box();
				}
				?>
				<?php if ( has_tag() ) : ?>
					<div class="su-tags" aria-label="Tags">🏷 <?php the_tags( '', ' · ', '' ); ?></div>
				<?php endif; ?>
				<nav class="post-nav" aria-label="More posts">
					<span class="post-nav-prev"><?php previous_post_link( '%link', '← %title' ); ?></span>
					<span class="post-nav-next"><?php next_post_link( '%link', '%title →' ); ?></span>
				</nav>
			</article>

			<?php
			// v96: Up Next — reader tap = NIJAMAINA kotha pageview (policy-safe
			// ad refresh). Ad ki MUNDU pedatunnam: content link modata, ad tarvata.
			if ( function_exists( 'studentup_upnext_block' ) ) {
				studentup_upnext_block();
			}
			?>
			<?php studentup_ad( 'below-content' ); ?>
			<?php
			if ( comments_open() || get_comments_number() ) {
				comments_template();
			}
			?>

			<?php
			$su_rel = get_the_category();
			$su_tags = wp_get_post_tags( get_the_ID(), array( 'fields' => 'ids' ) );
			if ( $su_rel && $su_tags ) {
				// Topic tags are generated from the focus/secondary keywords. Use
				// them first; category-only matching was showing unrelated posts.
				$su_q = new WP_Query(
					array(
						'category__in'        => wp_list_pluck( $su_rel, 'term_id' ),
						'tag__in'             => $su_tags,
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
