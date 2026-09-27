<?php
/**
 * Template Name: StudentUp — Compare jobs
 *
 * v126: SSC vs Railway vs TSPSC laga side-by-side comparison page (salary · age ·
 * qualification · vacancies · last date). Data anta published posts nunchi —
 * fake rows eppudu ledu.
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

get_header();
?>
<main id="main">
	<div class="wrap">
		<div class="sectionhead">
			<div>
				<h1><?php the_title(); ?></h1>
				<p>Rendu leda ekkuva notifications ni okesari compare cheyandi — salary, age limit, qualification, vacancies, last date.</p>
			</div>
		</div>
		<?php
		while ( have_posts() ) :
			the_post();
			the_content();
		endwhile;
		studentup_compare_table();
		studentup_ad( 'mid' );
		?>
	</div>
</main>
<?php
get_footer();
