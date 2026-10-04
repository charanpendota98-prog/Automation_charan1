<?php
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Compact government-jobs homepage.
 *
 * The homepage is deliberately limited to current Telangana, Andhra Pradesh
 * and Central government opportunities. `studentup_home_opportunity_rows()`
 * uses the active-board expiry/staleness/deduplication rules, then orders by
 * publication date so the newest eligible notices appear first.
 *
 * @package studentup
 */

get_header();

$su_paged       = max( 1, (int) get_query_var( 'paged' ), (int) get_query_var( 'page' ) );
$su_per_page    = 8;
$su_home_rows   = studentup_home_opportunity_rows();
$su_row_count   = count( $su_home_rows );
$su_total_pages = max( 1, (int) ceil( $su_row_count / $su_per_page ) );
$su_paged       = min( $su_paged, $su_total_pages );
$su_page_rows   = array_slice( $su_home_rows, ( $su_paged - 1 ) * $su_per_page, $su_per_page );
$su_card_rows   = array_slice( $su_page_rows, 0, 4 );
?>

<section class="su-home-intro" aria-labelledby="su-home-title">
	<div class="wrap su-home-intro-inner">
		<div class="su-home-copy">
			<h1 id="su-home-title">
				<?php
				if ( 1 < $su_paged ) {
					esc_html_e( 'Latest Government Jobs', 'studentup' );
				} else {
					esc_html_e( 'Government Jobs', 'studentup' );
				}
				?>
			</h1>
			<p>Telangana <span aria-hidden="true">·</span> Andhra Pradesh <span aria-hidden="true">·</span> Central Government</p>
		</div>
	</div>
</section>

<main id="main" class="su-home-main">
	<div class="wrap">
		<?php studentup_breaking_section(); // Renders only fresh, verified TS/AP state or district news. ?>

		<section class="su-home-jobs" id="jobs" aria-labelledby="su-home-jobs-title">
			<div class="su-home-section-head">
				<div>
					<h2 id="su-home-jobs-title">
						<?php
						if ( 1 < $su_paged ) {
							printf(
								/* translators: %d: page number. */
								esc_html__( 'Latest active government jobs — page %d', 'studentup' ),
								(int) $su_paged
							);
						} else {
							esc_html_e( 'Latest job notices', 'studentup' );
						}
						?>
					</h2>
					<p>Telangana · Andhra Pradesh · Central Government</p>
				</div>
				<?php if ( 1 < $su_paged ) : ?>
					<a class="su-home-newest" href="<?php echo esc_url( get_pagenum_link( 1 ) ); ?>">Newest jobs</a>
				<?php endif; ?>
			</div>

			<div class="chips su-home-chips" id="home-job-filters" role="tablist" aria-label="Filter government jobs by region">
				<button type="button" class="chip active" data-cat="all" role="tab" aria-selected="true">All</button>
				<button type="button" class="chip" data-cat="ts-jobs" role="tab" aria-selected="false">Telangana</button>
				<button type="button" class="chip" data-cat="ap-jobs" role="tab" aria-selected="false">Andhra Pradesh</button>
				<button type="button" class="chip" data-cat="central-jobs" role="tab" aria-selected="false">Central Govt</button>
			</div>

			<?php if ( $su_page_rows ) : ?>
				<div class="newsgrid su-home-job-grid" id="grid">
					<?php foreach ( $su_card_rows as $su_row ) : ?>
						<?php studentup_home_opportunity_render_card( $su_row ); ?>
					<?php endforeach; ?>
				</div>
				<p class="nores" id="nores">No active listings in this region. Choose another filter to browse the other government-job sections.</p>
			<?php else : ?>
				<div class="su-home-empty" role="status">
					<strong>No current government-job listings are available.</strong>
					<span>When active Telangana, Andhra Pradesh or Central notices are published, their available qualification and deadline details will appear here.</span>
				</div>
			<?php endif; ?>

			<?php if ( 1 < $su_total_pages ) : ?>
				<nav class="su-home-pagination" aria-label="Government job pages">
					<?php if ( 1 < $su_paged ) : ?>
						<a href="<?php echo esc_url( get_pagenum_link( $su_paged - 1 ) ); ?>">← Newer</a>
					<?php endif; ?>
					<span>Page <?php echo esc_html( (string) $su_paged ); ?> of <?php echo esc_html( (string) $su_total_pages ); ?></span>
					<?php if ( $su_paged < $su_total_pages ) : ?>
						<a href="<?php echo esc_url( get_pagenum_link( $su_paged + 1 ) ); ?>">Older →</a>
					<?php endif; ?>
				</nav>
			<?php endif; ?>
		</section>

		<?php if ( $su_page_rows ) : ?>
			<?php studentup_jobs_table( 8, $su_page_rows ); ?>
		<?php endif; ?>
	</div>
</main>

<?php get_footer(); ?>
