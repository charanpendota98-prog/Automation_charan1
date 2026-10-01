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

/*
 * v176 REAL FIX (live-install proof): /page/2/ kuda front-page.php ne vaadutundi
 * (paged front pages aa template lo vaste — WP hierarchy gotcha). Kani grid query
 * lo 'paged' ledu + no_found_rows=true → prathi page lo SAME latest 12 posts
 * (duplicate content penalty) + "Older updates" link eppudu render cheyyaledu —
 * users ki 12 posts tarvata browse cheyadam impossible.
 *
 * Ippudu: (1) grid query paged-aware, (2) numbered pagination, (3) page 2+ lo
 * widgets ledu — lean archive (SEO duplicate content poochindi).
 */
$su_paged   = max( 1, (int) get_query_var( 'paged' ) );
$su_is_p2   = $su_paged > 1;
?>

<?php if ( ! $su_is_p2 ) : ?>
	<?php studentup_hero_premium(); // v123: premium hero (search + quick actions) ?>
<?php endif; ?>

<?php studentup_latest_ticker(); // v89: latest jobs scrolling — click cheste aa post open avutundi. ?>

<?php if ( ! $su_is_p2 ) : ?>
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
					<span class="ui" aria-hidden="true"><?php echo studentup_ui_icon( $m['icon'], 22 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?></span>
					<div><b><?php echo esc_html( $m['label'] ); ?></b><small><?php echo esc_html( $m['hint'] ); ?></small></div>
				</a>
				<?php endforeach; ?>
		</div>
	</div>
</section>
<?php endif; ?>

<?php if ( ! $su_is_p2 ) : ?>
<div class="wrap">
	<?php
	studentup_hot_jobs( 10 );      // v123: TOP 10 HOT JOBS TODAY
	studentup_personal_picks();    // v156: local-only personalised top 5
	studentup_closing_week( 7 ); // v146: closing-this-week radar (real su_last_date meta only)
	studentup_job_finder();        // v124: AI job match + eligibility checker
	studentup_ad( 'in-feed' );     // v125: high-viewability slot (cap: max_ads)
	studentup_stories( 8 );        // v129: swipeable quick story cards
	studentup_daily_quiz();        // v123: real daily quiz (colorful rotating ring)
	studentup_scholarship_strip(); // v123: scholarships spotlight
	studentup_alerts_card();       // v123: notification / WhatsApp / Telegram alerts
	studentup_for_you();           // v127: reader history rail (localStorage only)
	studentup_job_calendar();      // v124: last-date calendar (repeat visits)
	studentup_salary_calc();       // v124: in-hand salary calculator
	studentup_age_calculator_block(); // v165: age & eligibility calculator
	studentup_fee_calculator_block(); // v167: fee & concession calculator
	studentup_score_calculator_block(); // v168: score & negative marking calculator
	studentup_admit_card_block(); // v168: hall ticket & admit card helper
	studentup_resume_maker_block(); // v168: instant fresher resume & bio-data builder
	studentup_syllabus_tracker_block(); // v167: syllabus & study progress tracker
	?>
</div>
<?php endif; ?>

<?php if ( ! $su_is_p2 ) : ?>
<div class="wrap"><?php studentup_ad( 'leaderboard' ); ?></div>
<?php endif; ?>

<section class="hero hero-slim" aria-label="Page title">
	<h1 class="screen-reader-text">
		<?php
		if ( $su_is_p2 ) {
			printf(
				/* translators: %d: page number. */
				esc_html__( 'Latest student updates — page %d', 'studentup' ),
				(int) $su_paged
			);
		} else {
			esc_html_e( 'Latest student updates', 'studentup' );
		}
		?>
	</h1>
</section>

<main id="main">
	<div class="wrap">
		<?php if ( ! $su_is_p2 ) : ?>
			<?php studentup_breaking_section(); ?>
		<?php endif; ?>

		<div class="sectionhead" id="jobs">
			<div>
				<h2>
					<?php
					if ( $su_is_p2 ) {
						printf(
							/* translators: %d: page number. */
							esc_html__( 'Latest opportunities — page %d', 'studentup' ),
							(int) $su_paged
						);
					} else {
						esc_html_e( 'Latest opportunities', 'studentup' );
					}
					?>
				</h2>
				<p>Filter by qualification — Telangana · Andhra Pradesh · Central</p>
			</div>
			<?php if ( $su_is_p2 ) : ?>
				<a class="su-board-link" href="<?php echo esc_url( home_url( '/' ) ); ?>">← Newest updates</a>
			<?php else : ?>
				<a class="su-board-link" href="<?php echo esc_url( studentup_opportunity_board_url() ); ?>">All active sections →</a>
			<?php endif; ?>
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
						'paged'               => $su_paged,          // v176: /page/N/ real pagination.
						'ignore_sticky_posts' => false,
						// v176: no_found_rows=false — pagination kosam max_num_pages kavali
						// (v69 lo true pettina prati page same posts + link ye ledu).
						'no_found_rows'       => false,
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

		<?php studentup_jobs_table( 12 ); // v142: scannable latest-jobs table ?>

		<?php studentup_popular_searches(); // v140: long-tail internal links ?>

		<?php studentup_ad( 'mid' ); ?>

		<nav class="sectionhead" aria-label="Post pages">
			<div>
				<?php
				$su_total = (int) $su_q->max_num_pages;
				if ( $su_total > 1 ) {
					echo wp_kses_post(
						paginate_links(   // v176: numbered pagination (category pages laaga page-numbers markup).
							array(
								'total'     => $su_total,
								'current'   => $su_paged,
								'prev_text' => '← Newer',
								'next_text' => 'Older →',
							)
						) ?? ''
					);
				}
				?>
			</div>
		</nav>
	</div>
</main>

<?php
wp_reset_postdata();
get_footer();
