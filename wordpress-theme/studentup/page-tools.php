<?php
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}
?>
<?php
/**
 * Template Name: StudentUp Tools
 *
 * v191.2: calculator / utility wall HOME nunchi ikkadaki vachindi.
 *
 * Enduku: home lo 8 calculator blocks unte adi "widget wall" ayyeedi — reader
 * first job card chudadaniki 3-4 screens scroll cheyyalsi vachedi (bounce ↑,
 * ad viewability ↓). Ippudu ivi ee dedicated page lo mattrame; home page
 * clean content + ad layout ga untundi (AdSense policy ki kuda best).
 *
 * Usage: Pages → Add New → title "Tools" → Template: "StudentUp Tools" → Publish.
 *
 * @package studentup
 */

get_header();
?>
<main id="main">
	<div class="wrap">
		<div class="hero hero-slim" aria-label="Page title">
			<h1>
				<?php
				if ( have_posts() ) {
					while ( have_posts() ) {
						the_post();
						the_title();
					}
					rewind_posts();
				} else {
					esc_html_e( 'Free tools for students', 'studentup' );
				}
				?>
			</h1>
			<p class="lede"><?php esc_html_e( 'Salaries, age limits, fees, scores, admit cards, resumes and syllabus — official rules batti calculate cheyandi.', 'studentup' ); ?></p>
		</div>

		<div class="su-railed" style="margin:14px 0">
			<?php
			if ( function_exists( 'studentup_tools_tabs' ) ) {
				studentup_tools_tabs();
			}
			?>
		</div>

		<?php studentup_ad( 'mid' ); ?>

		<div class="article-content" style="max-width:760px">
			<?php
			if ( have_posts() ) {
				while ( have_posts() ) {
					the_post();
					the_content();
				}
			} else {
				echo '<p>' . esc_html__( 'Ee page ki content add cheyyandi (WP Admin → Pages → Tools). Tools anni kinda unnayi.', 'studentup' ) . '</p>';
			}
			?>
		</div>

		<?php studentup_popular_searches(); ?>
	</div>
</main>
<?php
get_footer();
