<?php
/**
 * v196 - CORRECTIONS LOG (audit finding #41).
 *
 * Why: the editorial policy promises that a mistake is corrected publicly with
 * the updated date. That promise needs a page readers can check - it is one of
 * the strongest E-E-A-T / "people-first" signals a jobs site can show, and
 * AdSense/News reviewers look for it.
 *
 * Data source: `studentup_correction_note` post meta (admin/bot writes it).
 * Template: page-corrections.php (assign to the /corrections/ page).
 *
 * @package StudentUp
 */

defined( 'ABSPATH' ) || exit;

get_header();

$q = new WP_Query(
	array(
		'post_type'           => 'post',
		'post_status'         => 'publish',
		'posts_per_page'      => 50,
		'meta_key'            => 'studentup_correction_note', // phpcs:ignore WordPress.DB.SlowDBQuery.slow_db_query_meta_key -- small site, indexed by WP.
		'orderby'             => 'modified',
		'order'               => 'DESC',
		'ignore_sticky_posts' => true,
		'no_found_rows'       => true,
	)
);
?>
<main id="main" class="wrap su-page su-corrections">
	<?php if ( function_exists( 'studentup_breadcrumbs' ) ) { studentup_breadcrumbs(); } ?>
	<h1><?php esc_html_e( 'Corrections &amp; updates', 'studentup' ); ?></h1>
	<p><?php esc_html_e( 'Every correction we make is listed here with what changed and when. If you find a mistake, write to us with the page link and we will publish the fix on this page as well.', 'studentup' ); ?></p>

	<?php if ( $q->have_posts() ) : ?>
		<ul class="su-corr-list">
			<?php
			while ( $q->have_posts() ) :
				$q->the_post();
				$note = (string) get_post_meta( get_the_ID(), 'studentup_correction_note', true );
				?>
				<li class="su-corr-item">
					<a class="su-corr-title" href="<?php the_permalink(); ?>"><?php the_title(); ?></a>
					<span class="su-corr-meta">
						<?php esc_html_e( 'Updated:', 'studentup' ); ?>
						<time datetime="<?php echo esc_attr( get_the_modified_date( 'c' ) ); ?>"><?php echo esc_html( get_the_modified_date() ); ?></time>
					</span>
					<?php if ( '' !== trim( $note ) ) : ?>
						<p class="su-corr-note"><?php echo esc_html( $note ); ?></p>
					<?php endif; ?>
				</li>
			<?php endwhile; ?>
		</ul>
	<?php else : ?>
		<p class="su-corr-empty"><?php esc_html_e( 'No corrections have been needed so far. When one happens, it will be listed here with the date - we do not silently edit published facts.', 'studentup' ); ?></p>
	<?php endif; ?>
	<?php wp_reset_postdata(); ?>

	<h2><?php esc_html_e( 'How to report a mistake', 'studentup' ); ?></h2>
	<ol class="su-ab-steps">
		<li><?php esc_html_e( 'Copy the page link (or the headline) that looks wrong.', 'studentup' ); ?></li>
		<li><?php esc_html_e( 'Tell us what the official notification says instead - a screenshot or the official link helps most.', 'studentup' ); ?></li>
		<li><?php
			$mail = function_exists( 'studentup_contact_email' ) ? studentup_contact_email() : '';
			if ( $mail ) {
				echo wp_kses_post( sprintf(
					/* translators: %s: contact email link. */
					esc_html__( 'Send it to %s. Verified corrections are published within 48 hours.', 'studentup' ),
					'<a href="mailto:' . esc_attr( $mail ) . '">' . esc_html( $mail ) . '</a>'
				) );
			} else {
				esc_html_e( 'Send it to us on WhatsApp or Telegram. Verified corrections are published within 48 hours.', 'studentup' );
			}
		?></li>
	</ol>
</main>
<?php
get_footer();
