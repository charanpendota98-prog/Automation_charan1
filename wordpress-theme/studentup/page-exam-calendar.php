<?php
/**
 * v196 - EXAM CALENDAR page template.
 *
 * Renders inc/calendar.php (dated notifications + one-tap .ics export) inside
 * the normal theme shell, so it looks exactly like the rest of the site.
 * Template: page-exam-calendar.php (assign to the /exam-calendar/ page).
 *
 * @package StudentUp
 */

defined( 'ABSPATH' ) || exit;

get_header();
?>
<main id="main" class="wrap su-page su-cal-page">
	<?php if ( function_exists( 'studentup_breadcrumbs' ) ) { studentup_breadcrumbs(); } ?>
	<h1><?php esc_html_e( 'Exam &amp; application calendar 2026', 'studentup' ); ?></h1>
	<p><?php esc_html_e( 'Every last date we have confirmed from an official notification, in one list - sorted by month, with the closing-soon ones first.', 'studentup' ); ?></p>

	<?php
	if ( function_exists( 'studentup_calendar_page_render' ) ) {
		echo '<div class="su-cal">' . studentup_calendar_page_render() . '</div>'; // phpcs:ignore WordPress.Security.EscapeOutput -- escaped inside the renderer.
	}

	if ( have_posts() ) {
		while ( have_posts() ) {
			the_post();
			$extra = trim( (string) get_the_content() );
			if ( '' !== $extra ) {
				echo '<div class="su-cal-extra">' . wp_kses_post( apply_filters( 'the_content', $extra ) ) . '</div>';
			}
		}
	}

	if ( function_exists( 'studentup_ad' ) ) {
		studentup_ad( 'below' );   // same slot policy as every other page - no extra inventory.
	}
	?>
</main>
<?php
get_footer();
