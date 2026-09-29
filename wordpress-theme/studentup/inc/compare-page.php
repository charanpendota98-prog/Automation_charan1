<?php
/**
 * v126: Compare table (page template + [studentup_compare] shortcode).
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Render the comparison table from real published posts.
 *
 * @param int $limit rows.
 */
function studentup_compare_table( $limit = 12 ) {
	$rows = studentup_smart_dataset( 60 );
	$rows = array_slice(
		array_values(
			array_filter(
				$rows,
				static function ( $r ) {
					return $r['pay'] || $r['vac'] || $r['last'] || $r['amax'];
				}
			)
		),
		0,
		(int) $limit
	);
	if ( ! $rows ) {
		echo '<p class="su-finder-empty">Comparison data inka publish avvaledu — job posts lo salary/age/last date fill ayyaka ikkada automatic ga kanipistundi.</p>';
		return;
	}
	$states = array( 'ts' => 'Telangana', 'ap' => 'Andhra Pradesh', 'central' => 'Central', 'other' => '—' );
	?>
	<section class="su-cmp" aria-label="Compare notifications">
		<div class="su-cmp-scroll">
			<table class="su-cmp-table">
				<thead>
					<tr>
						<th scope="col">Notification</th>
						<th scope="col">State</th>
						<th scope="col">Qualification</th>
						<th scope="col">Age</th>
						<th scope="col">Vacancies</th>
						<th scope="col">Salary</th>
						<th scope="col">Last date</th>
						<th scope="col">Apply</th>
					</tr>
				</thead>
				<tbody>
					<?php foreach ( $rows as $r ) : ?>
						<tr>
							<th scope="row"><a href="<?php echo esc_url( $r['link'] ); ?>"><?php echo esc_html( $r['title'] ); ?></a></th>
							<td><?php echo esc_html( isset( $states[ $r['state'] ] ) ? $states[ $r['state'] ] : '—' ); ?></td>
							<td><?php echo esc_html( $r['qual'] ? implode( ', ', $r['qual'] ) : '—' ); ?></td>
							<td><?php echo esc_html( ( $r['amin'] || $r['amax'] ) ? ( ( $r['amin'] ? $r['amin'] : '—' ) . '–' . ( $r['amax'] ? $r['amax'] : '—' ) ) : '—' ); ?></td>
							<td><?php echo esc_html( $r['vac'] ? $r['vac'] : '—' ); ?></td>
							<td><?php echo esc_html( $r['pay'] ? $r['pay'] : '—' ); ?></td>
							<td><?php echo esc_html( $r['last'] ? date_i18n( 'M j, Y', strtotime( $r['last'] ) ) : '—' ); ?></td>
							<td><a class="su-cmp-apply" href="<?php echo esc_url( $r['apply'] ? $r['apply'] : $r['link'] ); ?>"
								<?php
								if ( $r['apply'] ) {
									// External official link — new tab, nofollow (own posts ki normal link).
									echo ' target="_blank" rel="nofollow noopener"';
								}
								?>
								>Open →</a></td>
						</tr>
					<?php endforeach; ?>
				</tbody>
			</table>
		</div>
		<p class="su-finder-note">"—" ante aa detail inka official ga confirm kaledu — notification lo chudandi. Numbers manam publish chesina data nunche vastayi.</p>
	</section>
	<?php
}

/**
 * Shortcode: [studentup_compare limit="12"].
 *
 * @param array $atts attributes.
 * @return string
 */
function studentup_compare_shortcode( $atts ) {
	$atts = shortcode_atts( array( 'limit' => 12 ), $atts, 'studentup_compare' );
	ob_start();
	studentup_compare_table( (int) $atts['limit'] );
	return (string) ob_get_clean();
}
add_shortcode( 'studentup_compare', 'studentup_compare_shortcode' );
