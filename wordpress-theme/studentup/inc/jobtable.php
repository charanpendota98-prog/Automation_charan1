<?php
/**
 * Compact homepage table for the same active TS/AP/Central-government rows
 * used by the cards. Qualifications and deadlines come only from post meta;
 * absent values are labelled honestly instead of being inferred.
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Rows for the homepage jobs table.
 *
 * @param int        $limit Row count.
 * @param array|null $rows  Optional already-filtered homepage rows.
 * @return array<int,array<string,mixed>>
 */
function studentup_jobtable_rows( $limit = 12, $rows = null ) {
	if ( ! is_array( $rows ) ) {
		$rows = function_exists( 'studentup_home_opportunity_rows' )
			? studentup_home_opportunity_rows()
			: array();
	}
	$rows = array_slice( $rows, 0, max( 1, (int) $limit ) );
	$out  = array();

	foreach ( $rows as $row ) {
		if ( empty( $row['id'] ) || empty( $row['title'] ) || empty( $row['link'] ) ) {
			continue;
		}
		$section = isset( $row['section'] ) ? sanitize_key( (string) $row['section'] ) : '';
		if ( ! in_array( $section, array( 'ts', 'ap', 'central' ), true ) ) {
			continue;
		}
		$qual  = isset( $row['qualification'] ) ? trim( (string) $row['qualification'] ) : '';
		$apply = isset( $row['apply_url'] ) ? trim( (string) $row['apply_url'] ) : '';
		if ( ! wp_http_validate_url( $apply ) ) {
			$apply = '';
		}
		$last = function_exists( 'studentup_opportunity_last_date' )
			? studentup_opportunity_last_date( (int) $row['id'] )
			: '';
		$out[] = array(
			'title' => (string) $row['title'],
			'link'  => (string) $row['link'],
			'cat'   => function_exists( 'studentup_opportunity_section_label' )
				? studentup_opportunity_section_label( $section )
				: ucfirst( $section ),
			'qual'  => $qual,
			'last'  => $last,
			'apply' => $apply,
		);
	}
	return $out;
}

/**
 * Render the compact jobs table when active homepage rows exist.
 *
 * @param int        $limit Row count.
 * @param array|null $rows  Optional already-filtered homepage rows.
 * @return void
 */
function studentup_jobs_table( $limit = 12, $rows = null ) {
	if ( ! studentup_opt( 'jobs_table', '1' ) ) {
		return;
	}
	$rows = studentup_jobtable_rows( $limit, $rows );
	if ( ! $rows ) {
		return;
	}
	?>
	<section class="su-jobtable" aria-labelledby="su-jobtable-title">
		<div class="su-jt-head">
			<h2 id="su-jobtable-title">Government jobs at a glance</h2>
			<p>Qualification and last-date details are shown only when available in the notice data.</p>
		</div>
		<div class="su-jt-scroll">
			<table class="su-jt">
				<thead>
					<tr>
						<th scope="col">Job / notification</th>
						<th scope="col">Qualification</th>
						<th scope="col">Last date</th>
						<th scope="col">Details</th>
					</tr>
				</thead>
				<tbody>
					<?php foreach ( $rows as $row ) : ?>
						<tr>
							<td class="su-jt-title" data-label="Job / notification">
								<a href="<?php echo esc_url( $row['link'] ); ?>"><?php echo esc_html( $row['title'] ); ?></a>
								<span class="su-jt-cat"><?php echo esc_html( $row['cat'] ); ?></span>
							</td>
							<td data-label="Qualification">
								<?php if ( $row['qual'] ) : ?>
									<?php echo esc_html( studentup_qual_pretty( $row['qual'] ) ); ?>
								<?php else : ?>
									<span class="su-jt-na">Not specified</span>
								<?php endif; ?>
							</td>
							<td data-label="Last date">
								<?php if ( $row['last'] ) : ?>
									<?php echo esc_html( wp_date( 'd M Y', strtotime( $row['last'] . ' 12:00:00' ) ) ); ?>
								<?php else : ?>
									<span class="su-jt-na">Not announced</span>
								<?php endif; ?>
							</td>
							<td data-label="Details">
								<?php if ( $row['apply'] ) : ?>
									<a class="su-jt-apply" href="<?php echo esc_url( $row['apply'] ); ?>" target="_blank" rel="noopener noreferrer">Official Apply</a>
								<?php else : ?>
									<a class="su-jt-more" href="<?php echo esc_url( $row['link'] ); ?>">Details</a>
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
