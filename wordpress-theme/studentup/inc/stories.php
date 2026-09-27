<?php
/**
 * v129 QUICK STORIES — Web-Stories laga full-screen swipe cards (pure CSS
 * scroll-snap, JS avasaram ledu). Mobile readers ki 10 seconds lo "today lo
 * emi kotha" — Discover/engagement surface.
 *
 * Data: real published posts + job meta. Image lekapote auto social card
 * (v129 generator) leda brand gradient.
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Render the story viewer.
 *
 * @param int $limit cards.
 */
function studentup_stories( $limit = 8 ) {
	if ( ! studentup_opt( 'stories', '1' ) ) {
		return;
	}
	$rows = array_slice( studentup_smart_dataset( 20 ), 0, (int) $limit );
	if ( ! $rows ) {
		return;
	}
	$total = count( $rows );
	?>
	<section class="su-stories" aria-label="Quick story cards">
		<div class="su-stories-rail">
			<?php foreach ( $rows as $i => $r ) : ?>
				<?php
				$img = $r['img'];
				if ( ! $img && function_exists( 'studentup_og_url' ) ) {
					$img = studentup_og_url( $r['id'] );
				}
				?>
				<article class="su-story" id="su-story-<?php echo (int) ( $i + 1 ); ?>">
					<?php if ( $img ) : ?>
						<img class="su-story-bg" src="<?php echo esc_url( $img ); ?>" alt="" loading="lazy" decoding="async" width="1200" height="630">
					<?php endif; ?>
					<div class="su-story-bars" aria-hidden="true">
						<?php for ( $b = 0; $b < $total; $b++ ) : ?>
							<i class="<?php echo esc_attr( $b === $i ? 'on' : '' ); ?>"></i>
						<?php endfor; ?>
					</div>
					<div class="su-story-in">
						<span class="su-story-kick"><?php echo esc_html( sprintf( '%d / %d', $i + 1, $total ) ); ?></span>
						<h3><?php echo esc_html( $r['title'] ); ?></h3>
						<div class="su-story-meta">
							<?php if ( $r['last'] ) : ?>
								<span>📅 <?php echo esc_html( date_i18n( 'M j', strtotime( $r['last'] ) ) ); ?></span>
							<?php endif; ?>
							<?php if ( $r['pay'] ) : ?>
								<span>💰 <?php echo esc_html( $r['pay'] ); ?></span>
							<?php endif; ?>
							<?php if ( $r['vac'] ) : ?>
								<span>🧾 <?php echo esc_html( $r['vac'] ); ?> posts</span>
							<?php endif; ?>
						</div>
						<a class="su-story-cta" href="<?php echo esc_url( $r['link'] ); ?>">Full details →</a>
					</div>
					<?php if ( $i + 1 < $total ) : ?>
						<a class="su-story-next" href="#su-story-<?php echo (int) ( $i + 2 ); ?>" aria-label="Next card">›</a>
					<?php endif; ?>
					<?php if ( $i > 0 ) : ?>
						<a class="su-story-prev" href="#su-story-<?php echo (int) $i; ?>" aria-label="Previous card">‹</a>
					<?php endif; ?>
				</article>
			<?php endforeach; ?>
		</div>
	</section>
	<?php
}

/**
 * Shortcode: [studentup_stories limit="8"].
 *
 * @param array $atts atts.
 * @return string
 */
function studentup_stories_shortcode( $atts ) {
	$atts = shortcode_atts( array( 'limit' => 8 ), $atts, 'studentup_stories' );
	ob_start();
	studentup_stories( (int) $atts['limit'] );
	return (string) ob_get_clean();
}
add_shortcode( 'studentup_stories', 'studentup_stories_shortcode' );
