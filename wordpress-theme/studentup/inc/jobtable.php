<?php
/**
 * v142: Latest jobs TABLE — the scannable row layout students already know from
 * FreeJobAlert, but with real data from post meta (qualification, last date,
 * apply link) instead of a hand-typed HTML page.
 *
 * Why a table next to the cards: cards are good for browsing, a table is better
 * for "is there anything new and when does it close". Both surfaces link to the
 * same posts, so this adds scannability and internal links without duplicating
 * content.
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Rows for the latest-jobs table.
 *
 * @param int $limit Row count.
 * @return array
 */
function studentup_jobtable_rows( $limit = 12 ) {
	$rows  = array();
	$posts = get_posts(
		array(
			'posts_per_page'      => (int) $limit,
			'ignore_sticky_posts' => true,
			'no_found_rows'       => true,
			'post_status'         => 'publish',
		)
	);
	foreach ( $posts as $p ) {
		$last  = trim( (string) get_post_meta( $p->ID, 'studentup_last_date', true ) );
		$qual  = trim( (string) get_post_meta( $p->ID, 'studentup_qual', true ) );
		$apply = trim( (string) get_post_meta( $p->ID, 'studentup_apply_url', true ) );
		$cats  = get_the_category( $p->ID );
		$rows[] = array(
			'title' => get_the_title( $p ),
			'link'  => get_permalink( $p ),
			'cat'   => $cats ? $cats[0]->name : '',
			'qual'  => $qual,
			'last'  => $last,
			'apply' => ( $apply && 0 === strpos( $apply, 'http' ) ) ? $apply : '',
			'fresh' => ( time() - (int) get_post_time( 'U', true, $p ) ) < DAY_IN_SECONDS,
		);
	}
	return $rows;
}

/**
 * Render the latest-jobs table.
 *
 * @param int $limit Row count.
 * @return void
 */
function studentup_jobs_table( $limit = 12 ) {
	if ( ! studentup_opt( 'jobs_table', '1' ) ) {
		return;
	}
	$rows = studentup_jobtable_rows( $limit );
	if ( ! $rows ) {
		return;
	}
	?>
	<section class="su-jobtable" aria-labelledby="su-jobtable-title">
		<div class="su-jt-head">
			<h2 id="su-jobtable-title">Latest updates at a glance</h2>
			<p>Last dates come from the official notification. Blank means the notice has no date yet — we leave it empty instead of guessing.</p>
		</div>
		<div class="su-jt-scroll">
			<table class="su-jt">
				<thead>
					<tr>
						<th scope="col">Post / notification</th>
						<th scope="col">Qualification</th>
						<th scope="col">Last date</th>
						<th scope="col">Link</th>
					</tr>
				</thead>
				<tbody>
					<?php foreach ( $rows as $r ) : ?>
						<tr>
							<td class="su-jt-title">
								<a href="<?php echo esc_url( $r['link'] ); ?>"><?php echo esc_html( $r['title'] ); ?></a>
								<?php if ( $r['fresh'] ) : ?><span class="su-fresh">NEW</span><?php endif; ?>
								<?php if ( $r['cat'] ) : ?><span class="su-jt-cat"><?php echo esc_html( $r['cat'] ); ?></span><?php endif; ?>
							</td>
							<td>
								<?php if ( $r['qual'] ) : ?>
									<?php echo esc_html( studentup_qual_pretty( $r['qual'] ) );   // v174: human labels ?>
								<?php else : ?>
									<span class="su-jt-na">&mdash;</span>
								<?php endif; ?>
							</td>
							<td>
								<?php if ( $r['last'] ) : ?>
									<?php echo esc_html( wp_date( 'd M Y', strtotime( $r['last'] . ' 12:00:00' ) ) );   // v174: raw ISO kaadu ?>
								<?php else : ?>
									<span class="su-jt-na">Not announced</span>
								<?php endif; ?>
							</td>
							<td>
								<?php if ( $r['apply'] ) : ?>
									<a class="su-jt-apply" href="<?php echo esc_url( $r['apply'] ); ?>" target="_blank" rel="nofollow noopener">Apply →</a>
								<?php else : ?>
									<a class="su-jt-more" href="<?php echo esc_url( $r['link'] ); ?>">Details →</a>
								<?php endif; ?>
							</td>
						</tr>
					<?php endforeach; ?>
				</tbody>
			</table>
		</div>
	</section>
	<?php
}
