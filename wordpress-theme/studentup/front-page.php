<?php
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}
?>
<?php
/**
 * Front page — design (preview/index.html) same order:
	 * Ticker → "Most searched by students" → ad → slim hero →
	 * qualification filter (v72) → latest opportunities grid (chips filter) → footer.
 *
 * @package studentup
 */

get_header();
?>

<?php studentup_latest_ticker(); // v89: latest jobs scrolling — click cheste aa post open avutundi. ?>

<section class="usedwrap" aria-label="Most searched by students">
	<div class="wrap">
		<div class="usedhead">
			<b>Most searched by students</b>
			<span>One tap to the sections TS & AP students open most</span>
		</div>
		<div class="usedgrid">
			<?php
			foreach ( studentup_most_used() as $i => $m ) :
				$term = studentup_used_term( $m['slug'] );   // v89: alias-aware (live slugs differ)
				if ( ! $term ) {
					continue;
				}
				$count   = (int) $term->count;
				$hot     = ( $i < 3 ) ? ' hot' : '';         // v89: TS · AP · Central top-3 highlight
				$badge   = $count ? number_format_i18n( $count ) . ' updates' : 'Soon';
				?>
				<a class="usedcard<?php echo esc_attr( $hot ); ?>" href="<?php echo esc_url( get_category_link( $term ) ); ?>">
					<span class="ui" aria-hidden="true"><?php echo esc_html( $m['icon'] ); ?></span>
					<div><b><?php echo esc_html( $m['label'] ); ?></b><small><?php echo esc_html( $m['hint'] ); ?></small></div>
					<em class="ucount"><?php echo esc_html( $badge ); ?></em>
				</a>
			<?php endforeach; ?>
		</div>
	</div>
</section>

<div class="wrap"><?php studentup_ad( 'leaderboard' ); ?></div>

<h1 class="screen-reader-text"><?php esc_html_e( 'Latest student updates', 'studentup' ); ?></h1>

<main id="main">
	<div class="wrap">
		<?php studentup_breaking_section(); ?>

		<div class="sectionhead" id="jobs">
			<div>
				<h2>Latest opportunities</h2>
				<p>Filter by qualification — Telangana · Andhra Pradesh · Central</p>
			</div>
		</div>

		<?php
		studentup_qual_bar();
		studentup_qual_active_note();
		studentup_hidden_note();
		?>

		<div class="chips" id="chips" role="tablist" aria-label="Category filters">
			<button type="button" class="chip active" data-cat="all" role="tab" aria-selected="true">All</button>
			<?php foreach ( studentup_most_used() as $m ) : ?>
				<button type="button" class="chip" data-cat="<?php echo esc_attr( sanitize_html_class( $m['slug'] ) ); ?>" role="tab" aria-selected="false"><?php echo esc_html( $m['label'] ); ?></button>
			<?php endforeach; ?>
		</div>

		<div class="newsgrid" id="grid">
			<?php
			$su_q = new WP_Query(
				studentup_qual_query_args(   // v72: ?qual=degree → server-side filter
					array(
						'post_type'           => 'post',
						'posts_per_page'      => 12,
						'ignore_sticky_posts' => false,
						'no_found_rows'       => true,   // v69 perf: pagination ledu → extra SQL query vaddu
					)
				)
			);
			$su_i = 0;
			if ( $su_q->have_posts() ) :
				while ( $su_q->have_posts() ) :
					$su_q->the_post();
					if ( 4 === $su_i ) {
						studentup_ad( 'in-feed' );
					}
					studentup_card( $su_i );
					$su_i++;
				endwhile;
			else :
				?>
			<p class="nores" style="display:block">No posts yet — the bot will publish the first update soon.</p>
			<?php endif; ?>
		</div>
		<p class="nores" id="nores">Nothing for this filter — open the "All" tab and try again.</p>

		<?php studentup_ad( 'mid' ); ?>

		<nav class="sectionhead" aria-label="Post pages">
			<div><?php next_posts_link( 'Older updates →', $su_q->max_num_pages ); ?></div>
		</nav>
	</div>
</main>

<?php
wp_reset_postdata();
get_footer();
