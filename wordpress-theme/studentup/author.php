<?php
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}
?>
<?php
/**
 * Author archive — E-E-A-T friendly (bio · article count · website · verified note).
 *
 * Google ki "ee vyasam evaru rasinaru?" ane prashna ki idi jawabu: author bio,
 * published articles, external profile links, editorial policy link.
 *
 * @package studentup
 */

get_header();

$su_author = get_queried_object();
$su_id     = $su_author instanceof WP_User ? (int) $su_author->ID : (int) get_the_author_meta( 'ID' );
$su_name   = $su_author instanceof WP_User ? $su_author->display_name : get_the_author_meta( 'display_name', $su_id );
$su_bio    = $su_author instanceof WP_User ? $su_author->description : get_the_author_meta( 'description', $su_id );
$su_url    = $su_author instanceof WP_User ? $su_author->user_url : get_the_author_meta( 'user_url', $su_id );
$su_count  = $su_id ? (int) count_user_posts( $su_id, 'post', true ) : 0;
?>
<main id="main">
	<div class="wrap">
		<div class="crumbs"><?php echo wp_kses_post( studentup_breadcrumbs() ); ?></div>

		<section class="article authortop" aria-labelledby="author-title">
			<div class="authorwrap">
				<?php
				if ( $su_id ) {
					echo get_avatar( $su_id, 96, '', esc_attr( $su_name ), array( 'class' => 'author-avatar' ) );
				}
				?>
				<div class="authorbody">
					<h1 id="author-title" class="entry-title">
						<?php
						printf(
							/* translators: %s: author display name */
							esc_html__( '%s వ్యాసాలు', 'studentup' ),
							esc_html( $su_name )
						);
						?>
					</h1>
					<p class="authormeta">
						<?php
						printf(
							/* translators: %d: number of published posts */
							esc_html__( 'ప్రచురిత వ్యాసాలు: %d', 'studentup' ),
							(int) $su_count
						);
						?>
					</p>
					<?php if ( $su_bio ) : ?>
						<div class="authorbio"><?php echo wp_kses_post( wpautop( $su_bio ) ); ?></div>
					<?php else : ?>
						<p class="authorbio">
							<?php esc_html_e( 'StudentUp ఎడిటోరియల్ టీమ్ — అధికారిక మూలాల ఆధారంగా తెలంగాణ & ఆంధ్రప్రదేశ్ విద్యార్థుల కోసం నిజాయితీ వ్యాసాలు.', 'studentup' ); ?>
						</p>
					<?php endif; ?>
					<?php if ( $su_url ) : ?>
						<p class="authormeta">
							<a href="<?php echo esc_url( $su_url ); ?>" rel="me noopener" target="_blank">
								<?php esc_html_e( 'రచయిత వెబ్‌సైట్ / ప్రొఫైల్', 'studentup' ); ?>
							</a>
						</p>
					<?php endif; ?>
					<p class="authormeta">
						<a href="<?php echo esc_url( home_url( '/editorial-policy/' ) ); ?>">
							<?php esc_html_e( 'మా ఎడిటోరియల్ విధానం చదవండి', 'studentup' ); ?>
						</a>
					</p>
				</div>
			</div>
		</section>

		<div class="sectionhead">
			<div><h2><?php esc_html_e( 'ఇటీవలి వ్యాసాలు', 'studentup' ); ?></h2></div>
		</div>
		<div class="newsgrid">
			<?php
			$su_i = 0;
			while ( have_posts() ) :
				the_post();
				if ( 4 === $su_i ) {
					studentup_ad( 'in-feed' );
				}
				studentup_card( $su_i );
				$su_i++;
			endwhile;
			?>
		</div>
		<?php studentup_ad( 'mid' ); ?>
		<nav class="sectionhead" aria-label="<?php esc_attr_e( 'పేజీలు', 'studentup' ); ?>">
			<div><?php echo wp_kses_post( paginate_links() ); ?></div>
		</nav>
	</div>
	<?php get_sidebar(); ?>
</main>
<?php
get_footer();
