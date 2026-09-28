<?php
/**
 * v144: reader-trust + engagement surfaces.
 *
 *  · studentup_updated_stamp() — visible "Updated on …" line when a post was
 *    genuinely edited after publishing. Freshness is one of the strongest
 *    signals for job/result pages, and readers check it before applying.
 *  · studentup_helpful_box() — "Was this helpful?" thumbs. The vote is stored
 *    in the reader's own browser only, so no counter is displayed and no
 *    engagement number is faked.
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Visible freshness stamp (only when modified noticeably after publish).
 *
 * @return void
 */
function studentup_updated_stamp() {
	if ( ! is_singular( 'post' ) || ! studentup_opt( 'updated_stamp', '1' ) ) {
		return;
	}
	$pub = (int) get_post_time( 'U', true );
	$mod = (int) get_post_modified_time( 'U', true );
	if ( $mod - $pub < HOUR_IN_SECONDS ) {
		return; // not a real update — do not dress a fresh post as "updated"
	}
	printf(
		'<p class="su-updated"><span aria-hidden="true">🔄</span> %1$s <time datetime="%2$s">%3$s</time></p>',
		esc_html__( 'Updated on', 'studentup' ),
		esc_attr( get_the_modified_date( DATE_W3C ) ),
		esc_html( get_the_modified_date( 'j M Y, g:i a' ) )
	);
}

/**
 * "Was this helpful?" box — browser-only vote, no public counter.
 *
 * @return void
 */
function studentup_helpful_box() {
	if ( ! is_singular( 'post' ) || ! studentup_opt( 'helpful_box', '1' ) ) {
		return;
	}
	$id = (int) get_the_ID();
	?>
	<section class="su-helpful" data-post="<?php echo esc_attr( $id ); ?>" aria-labelledby="su-helpful-title">
		<h2 id="su-helpful-title">Was this update helpful?</h2>
		<div class="su-helpful-btns">
			<button type="button" class="su-help-btn" data-vote="yes">👍 Yes, clear</button>
			<button type="button" class="su-help-btn" data-vote="no">👎 Something is missing</button>
		</div>
		<p class="su-helpful-note" role="status" aria-live="polite">Your answer stays in this browser. For a correction, mail
			<a href="mailto:<?php echo esc_attr( studentup_opt( 'contact_email', 'studentupinformative@gmail.com' ) ); ?>"><?php echo esc_html( studentup_opt( 'contact_email', 'studentupinformative@gmail.com' ) ); ?></a>.</p>
	</section>
	<script>
	(function(){
		var box = document.currentScript.previousElementSibling;
		if (!box) { return; }
		var key = 'su-help-' + box.getAttribute('data-post');
		var note = box.querySelector('.su-helpful-note');
		var done = null;
		try { done = localStorage.getItem(key); } catch (e) { done = null; }
		function mark(v){
			box.querySelectorAll('.su-help-btn').forEach(function(b){
				b.setAttribute('aria-pressed', String(b.getAttribute('data-vote') === v));
			});
			note.textContent = v === 'yes'
				? 'Thanks — glad it helped. Saved in this browser only.'
				: 'Thanks — tell us what is missing at the mail id on this page.';
		}
		if (done) { mark(done); }
		box.querySelectorAll('.su-help-btn').forEach(function(b){
			b.addEventListener('click', function(){
				var v = b.getAttribute('data-vote');
				try { localStorage.setItem(key, v); } catch (e) {}
				mark(v);
			});
		});
	})();
	</script>
	<?php
}

/**
 * v146: Deadline radar.
 *
 * Reads the `su_last_date` meta that the Job data box already stores and shows
 * only the applications closing inside the next 7 days, newest deadline first.
 * Nothing is invented: a post with no last date simply never appears here.
 *
 * @param int $days How far ahead to look (default 7 days).
 */
function studentup_closing_week( $days = 7 ) {
	if ( '1' !== studentup_opt( 'closing_week', '1' ) ) {
		return;
	}

	$today = current_time( 'Y-m-d' );
	$until = gmdate( 'Y-m-d', strtotime( $today . ' +' . max( 1, (int) $days ) . ' days' ) );

	$q = new WP_Query(
		array(
			'post_type'           => 'post',
			'posts_per_page'      => 6,
			'ignore_sticky_posts' => true,
			'no_found_rows'       => true,
			'meta_key'            => 'su_last_date',
			'orderby'             => 'meta_value',
			'order'               => 'ASC',
			'meta_query'          => array(
				array(
					'key'     => 'su_last_date',
					'value'   => array( $today, $until ),
					'compare' => 'BETWEEN',
					'type'    => 'DATE',
				),
			),
		)
	);

	if ( ! $q->have_posts() ) {
		wp_reset_postdata();
		return;
	}
	?>
	<section class="su-radar" aria-labelledby="su-radar-title">
		<div class="su-radar-head">
			<h2 id="su-radar-title">⏳ <?php esc_html_e( 'Closing this week', 'studentup' ); ?></h2>
			<span class="su-radar-sub"><?php esc_html_e( 'Last dates from the official notifications', 'studentup' ); ?></span>
		</div>
		<ul class="su-radar-list">
			<?php
			while ( $q->have_posts() ) :
				$q->the_post();
				$last = get_post_meta( get_the_ID(), 'su_last_date', true );
				$left = (int) floor( ( strtotime( $last ) - strtotime( $today ) ) / DAY_IN_SECONDS );
				if ( $left <= 1 ) {
					$tone = 'su-radar-red';
				} elseif ( $left <= 3 ) {
					$tone = 'su-radar-amber';
				} else {
					$tone = 'su-radar-green';
				}
				if ( 0 === $left ) {
					$label = __( 'Last day today', 'studentup' );
				} elseif ( 1 === $left ) {
					$label = __( '1 day left', 'studentup' );
				} else {
					/* translators: %d: number of days left to apply. */
					$label = sprintf( __( '%d days left', 'studentup' ), $left );
				}
				?>
				<li class="su-radar-item">
					<span class="su-radar-pill <?php echo esc_attr( $tone ); ?>"><?php echo esc_html( $label ); ?></span>
					<a href="<?php the_permalink(); ?>"><?php the_title(); ?></a>
					<time class="su-radar-date" datetime="<?php echo esc_attr( $last ); ?>">
						<?php echo esc_html( date_i18n( 'd M', strtotime( $last ) ) ); ?>
					</time>
				</li>
			<?php endwhile; ?>
		</ul>
	</section>
	<?php
	wp_reset_postdata();
}
