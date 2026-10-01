<?php
/**
 * Scroll-Depth High-RPM Smart Recirculation & Multiplex Unit.
 *
 * Provides high-intent related job recommendations to boost pages per session.
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Render Smart Recirculation Unit.
 *
 * @return void
 */
function studentup_smart_recirculation_box() {
	if ( ! is_singular( 'post' ) || ! studentup_opt( 'smart_recirc', '1' ) ) {
		return;
	}

	$cats    = get_the_category();
	$cat_ids = $cats ? array( (int) $cats[0]->term_id ) : array();

	$q = new WP_Query(
		array(
			'post_type'           => 'post',
			'posts_per_page'      => 4,
			'category__in'        => $cat_ids,
			'post__not_in'        => array( get_the_ID() ),
			'ignore_sticky_posts' => true,
			'no_found_rows'       => true,
		)
	);
	if ( ! $q->have_posts() ) {
		return;
	}

	?>
	<section class="su-recirc-wrap" aria-label="Trending and High-Intent Recommendations">
		<div class="su-recirc-head">
			<span class="su-recirc-icon" aria-hidden="true"><?php echo studentup_ui_icon( 'bolt', 15 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?></span>
			<h3 class="su-recirc-title">Trending & Related Notifications</h3>
		</div>
		<div class="su-recirc-grid">
			<?php
			$idx = 1;
			while ( $q->have_posts() ) :
				$q->the_post();
				?>
				<a href="<?php the_permalink(); ?>" class="su-recirc-card">
					<span class="su-recirc-rank">#<?php echo (int) $idx; ?></span>
					<div class="su-recirc-body">
						<h4 class="su-recirc-post-title"><?php the_title(); ?></h4>
						<span class="su-recirc-date"><?php echo studentup_ui_icon( 'calendar', 12 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> <?php echo esc_html( get_the_date() ); ?> · Read details →</span>
					</div>
				</a>
				<?php
				$idx++;
			endwhile;
			wp_reset_postdata();
			?>
		</div>
	</section>
	<?php
}
