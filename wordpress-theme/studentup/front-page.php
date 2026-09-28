<?php
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}
?>
<?php
/**
 * Front page — compact student-first order:
	 * latest jobs strip → "Most searched by students" → ad → verified Breaking News →
	 * accessible hidden H1 → qualification filter → latest opportunities grid → footer.
 *
 * @package studentup
 */

get_header();
?>

<?php studentup_hero_premium(); // v123: premium hero (search + quick actions) ?>

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
				// v123: "1 update / 2 updates" badge tesesamu — card lo text ki full chotu.
				$hot = ( $i < 3 ) ? ' hot' : '';             // v89: TS · AP · Central top-3 highlight
				?>
				<a class="usedcard<?php echo esc_attr( $hot ); ?>" href="<?php echo esc_url( get_category_link( $term ) ); ?>">
					<span class="ui" aria-hidden="true"><?php echo esc_html( $m['icon'] ); ?></span>
					<div><b><?php echo esc_html( $m['label'] ); ?></b><small><?php echo esc_html( $m['hint'] ); ?></small></div>
				</a>
			<?php endforeach; ?>
		</div>
	</div>
</section>

<div class="wrap">
	<?php
	studentup_hot_jobs( 10 );      // v123: TOP 10 HOT JOBS TODAY
	studentup_job_finder();        // v124: AI job match + eligibility checker
	studentup_ad( 'in-feed' );     // v125: high-viewability slot (cap: max_ads)
	studentup_stories( 8 );        // v129: swipeable quick story cards
	studentup_daily_quiz();        // v123: real daily quiz (colorful rotating ring)
	studentup_scholarship_strip(); // v123: scholarships spotlight
	studentup_alerts_card();       // v123: notification / WhatsApp / Telegram alerts
	studentup_for_you();           // v127: reader history rail (localStorage only)
	studentup_job_calendar();      // v124: last-date calendar (repeat visits)
	studentup_salary_calc();       // v124: in-hand salary calculator
	?>
</div>

<div class="wrap"><?php studentup_ad( 'leaderboard' ); ?></div>

<section class="hero hero-slim" aria-label="Page title">
	<h1 class="screen-reader-text"><?php esc_html_e( 'Latest student updates', 'studentup' ); ?></h1>
</section>

<main id="main">
	<div class="wrap">
		<?php studentup_breaking_section(); ?>

		<div class="sectionhead" id="jobs">
			<div>
				<h2>Latest opportunities</h2>
				<p>Filter by qualification — Telangana · Andhra Pradesh · Central</p>
			</div>
			<a class="su-board-link" href="<?php echo esc_url( studentup_opportunity_board_url() ); ?>">All active sections →</a>
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
					// v140: two in-feed slots (4th + 10th card). The density cap in
					// studentup_ad() still decides whether the second one renders,
					// so this raises viewable impressions without breaking policy.
					if ( 4 === $su_i || 10 === $su_i ) {
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

		<?php studentup_popular_searches(); // v140: long-tail internal links ?>

		<?php studentup_ad( 'mid' ); ?>

		<nav class="sectionhead" aria-label="Post pages">
			<div><?php next_posts_link( 'Older updates →', $su_q->max_num_pages ); ?></div>
		</nav>
	</div>
</main>

<?php
wp_reset_postdata();
get_footer();
