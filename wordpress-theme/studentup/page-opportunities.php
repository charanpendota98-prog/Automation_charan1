<?php
/**
 * Live active opportunities board — deadline-aware and section-wise.
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}
get_header();
$sections = studentup_opportunity_sections();
$rows     = studentup_opportunity_board_posts();
$groups   = array_fill_keys( array_keys( $sections ), array() );
foreach ( $rows as $row ) {
	if ( isset( $groups[ $row['section'] ] ) && count( $groups[ $row['section'] ] ) < 12 ) {
		$groups[ $row['section'] ][] = $row;
	}
}
$total = count( $rows );
?>
<main id="main" class="su-op-board-page" data-su-opportunities data-su-op-total="<?php echo esc_attr( $total ); ?>">
	<div class="wrap">
		<nav class="su-breadcrumbs" aria-label="Breadcrumb">
			<a href="<?php echo esc_url( home_url( '/' ) ); ?>">Home</a><span aria-hidden="true">›</span><span>Latest active opportunities</span>
		</nav>
		<section class="su-op-hero" aria-labelledby="su-op-title">
			<div>
				<p class="su-op-kicker">STUDENTUP · LIVE LIST</p>
				<h1 id="su-op-title">Latest Jobs &amp; Student Opportunities</h1>
				<p>TS, AP, Central, software, private, walk-in, job mela, scholarship, results and hall-ticket updates in one clean list.</p>
			</div>
			<div class="su-op-count"><strong><?php echo esc_html( number_format_i18n( $total ) ); ?></strong><span>active updates</span></div>
		</section>
		<div class="su-op-notice" role="note">
			✅ This list updates from published StudentUp posts. Verified last dates are shown, expired notices are hidden automatically, and an unavailable date is shown as <strong>Not announced</strong> — never guessed.
		</div>
		<section class="su-op-filters" aria-labelledby="su-op-filter-title">
			<div class="su-op-filter-heading">
				<h2 id="su-op-filter-title">Find the right opportunity</h2>
				<span data-su-op-results aria-live="polite"><?php echo esc_html( number_format_i18n( $total ) . ' active updates' ); ?></span>
			</div>
			<div class="su-op-filter-grid">
				<label><span>Search title</span><input type="search" data-su-op-search placeholder="Try SSC, software, scholarship…" autocomplete="off" /></label>
				<label><span>Category</span><select data-su-op-section-filter><option value="">All categories</option><?php foreach ( $sections as $key => $section ) : ?><option value="<?php echo esc_attr( $key ); ?>"><?php echo esc_html( $section['label'] ); ?></option><?php endforeach; ?></select></label>
				<label><span>Qualification</span><select data-su-op-qualification><option value="">Any qualification</option><option value="10th">10th</option><option value="inter">Inter / 10+2</option><option value="iti">ITI / Diploma</option><option value="degree">Degree</option><option value="pg">PG</option></select></label>
				<label><span>Deadline</span><select data-su-op-deadline><option value="">Any deadline</option><option value="7">Closing in 7 days</option><option value="30">Closing in 30 days</option><option value="unknown">Date not announced</option></select></label>
			</div>
			<p class="su-op-filter-note">Search and filters run in your browser. Open the article and confirm the official notification before applying.</p>
		</section>
		<div class="su-op-no-results" data-su-op-no-results hidden>No matching active opportunities found. Try another keyword or category.</div>
		<div class="su-op-jump" aria-label="Opportunity sections">
			<?php foreach ( $sections as $key => $section ) : ?>
				<?php if ( empty( $groups[ $key ] ) ) { continue; } ?>
				<a href="#su-<?php echo esc_attr( $key ); ?>"><?php echo esc_html( $section['icon'] . ' ' . $section['label'] ); ?></a>
			<?php endforeach; ?>
		</div>
		<?php foreach ( $sections as $key => $section ) : ?>
			<?php if ( empty( $groups[ $key ] ) ) { continue; } ?>
			<section class="su-op-section" id="su-<?php echo esc_attr( $key ); ?>" aria-labelledby="su-<?php echo esc_attr( $key ); ?>-title">
				<div class="su-op-section-head">
					<h2 id="su-<?php echo esc_attr( $key ); ?>-title"><span aria-hidden="true"><?php echo esc_html( $section['icon'] ); ?></span> <?php echo esc_html( $section['label'] ); ?></h2>
					<a href="<?php echo esc_url( home_url( '/?s=' . rawurlencode( $section['label'] ) ) ); ?>">See all →</a>
				</div>
				<div class="su-op-list">
					<?php foreach ( $groups[ $key ] as $row ) : ?>
						<?php studentup_opportunity_render_card( $row ); ?>
					<?php endforeach; ?>
				</div>
			</section>
		<?php endforeach; ?>
		<?php if ( ! $total ) : ?>
			<div class="su-op-empty">No active verified opportunities are available right now. Please check again after the next update.</div>
		<?php endif; ?>
		<p class="su-op-footnote">Last-date information is taken from the reviewed article. Always open the article and verify the official notification before applying.</p>
	</div>
</main>
<?php get_footer(); ?>
