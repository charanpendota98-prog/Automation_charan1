<?php
/**
 * v126 JOB DATA BOX — admin lo okka box lo job details enter cheyyachu.
 *
 * Enduku: v123/v124 features (hot cards, eligibility checker, calendar, compare,
 * salary chips) anni post meta meeda aadhaarapaḍatayi. Ippati varaku aa meta ni
 * bot matrame raase di — manual posts ki custom fields open cheyyalsi vachedi.
 * Ippudu editor lo clean box: last date, salary, vacancies, age, apply URL,
 * source URL + verified date.
 *
 * Rules (trust-first):
 *   · Date lu strict `YYYY-MM-DD` — invalid aithe save avvavu (fake deadline ledu).
 *   · URLs `esc_url_raw` + http(s) matrame.
 *   · Existing bot-written meta keys ne use chestundi (duplicate key ledu).
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Fields: meta key => array( label, type, ph, help ).
 *
 * @return array<string,array<int,string>>
 */
function studentup_job_fields() {
	return array(
		'studentup_last_date' => array( 'label' => 'Last date to apply', 'type' => 'date', 'ph' => '', 'help' => 'Official notification lo unna last date (YYYY-MM-DD). Confirm kaakapote khali vadalandi — theme guess cheyyadu.' ),
		'studentup_salary' => array( 'label' => 'Salary / pay scale', 'type' => 'text', 'ph' => 'e.g. ₹18,000 – ₹56,900', 'help' => 'Cards meeda chip ga kanipistundi. Notification lo unnade raayandi.' ),
		'studentup_vacancies' => array( 'label' => 'Total vacancies', 'type' => 'text', 'ph' => 'e.g. 8326', 'help' => 'Numbers matrame — "approx" lanti guesses vaddu.' ),
		'studentup_age_min' => array( 'label' => 'Minimum age', 'type' => 'number', 'ph' => '18', 'help' => 'Eligibility checker ki. Teliyakapote khali.' ),
		'studentup_age_max' => array( 'label' => 'Maximum age', 'type' => 'number', 'ph' => '33', 'help' => 'Upper age limit (relaxation notification lo chudandi).' ),
		'studentup_qual' => array( 'label' => 'Qualification tags', 'type' => 'text', 'ph' => '10th, inter, degree, pg', 'help' => 'Comma separated: 10th · inter · iti · diploma · degree · pg · btech. Khali unte auto-detect avutundi.' ),
		'studentup_apply_url' => array( 'label' => 'Official apply URL', 'type' => 'url', 'ph' => 'https://…', 'help' => 'Direct application link (rel="nofollow sponsored" kaadu — official site ga treat avutundi).' ),
		'studentup_source_url' => array( 'label' => 'Official source / notification PDF', 'type' => 'url', 'ph' => 'https://…', 'help' => 'E-E-A-T: readers + Google ki source proof.' ),
		'studentup_source_checked' => array( 'label' => 'Source last verified on', 'type' => 'date', 'ph' => '', 'help' => 'Mee team ee link ni ekkada verify chesaro aa date (YYYY-MM-DD).' ),
	);
}

/**
 * Register the box on posts.
 */
function studentup_job_box() {
	add_meta_box(
		'studentup-job-data',
		'StudentUp job data (cards · eligibility · calendar)',
		'studentup_job_box_render',
		'post',
		'normal',
		'high'
	);
}
add_action( 'add_meta_boxes', 'studentup_job_box' );

/**
 * Render.
 *
 * @param WP_Post $post post.
 */
function studentup_job_box_render( $post ) {
	wp_nonce_field( 'studentup_job_save', 'studentup_job_nonce' );
	echo '<p style="margin:0 0 12px;color:#555">Ee fields nimpithe homepage cards, AI job match, eligibility checker, job calendar and compare tool automatic ga pani chestayi. Confirm kaani information ni khali vadalandi — theme eppudu data ni guess cheyyadu.</p>';
	echo '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:14px">';
	foreach ( studentup_job_fields() as $key => $f ) {
		$val = (string) get_post_meta( $post->ID, $key, true );
		printf(
			'<label style="display:grid;gap:5px;font-weight:600"><span>%s</span>'
			. '<input type="%s" name="%s" value="%s" placeholder="%s" style="width:100%%;padding:7px 9px">'
			. '<small style="font-weight:400;color:#666">%s</small></label>',
			esc_html( $f['label'] ),
			esc_attr( $f['type'] ),
			esc_attr( $key ),
			esc_attr( $val ),
			esc_attr( $f['ph'] ),
			esc_html( $f['help'] )
		);
	}
	echo '</div>';
}

/**
 * Save — strict validation (invalid input silently drop, never store junk).
 *
 * @param int $post_id post.
 */
function studentup_job_box_save( $post_id ) {
	if ( ! isset( $_POST['studentup_job_nonce'] ) || ! wp_verify_nonce( sanitize_key( wp_unslash( $_POST['studentup_job_nonce'] ) ), 'studentup_job_save' ) ) {
		return;
	}
	if ( defined( 'DOING_AUTOSAVE' ) && DOING_AUTOSAVE ) {
		return;
	}
	if ( ! current_user_can( 'edit_post', $post_id ) ) {
		return;
	}
	foreach ( studentup_job_fields() as $key => $f ) {
		if ( ! isset( $_POST[ $key ] ) ) {
			continue;
		}
		$raw   = trim( (string) wp_unslash( $_POST[ $key ] ) ); // phpcs:ignore WordPress.Security.ValidatedSanitizedInput -- sanitised per type below.
		$clean = '';
		if ( '' !== $raw ) {
			switch ( $f['type'] ) {
				case 'date':
					$clean = preg_match( '/^20\d{2}-\d{2}-\d{2}$/', $raw ) ? $raw : '';
					break;
				case 'number':
					$clean = (string) max( 0, (int) $raw );
					$clean = '0' === $clean ? '' : $clean;
					break;
				case 'url':
					$clean = wp_http_validate_url( $raw ) ? esc_url_raw( $raw ) : '';
					break;
				default:
					$clean = sanitize_text_field( $raw );
			}
		}
		if ( '' === $clean ) {
			delete_post_meta( $post_id, $key );
		} else {
			update_post_meta( $post_id, $key, $clean );
		}
	}
	wp_cache_delete( 'studentup_smart_60', 'studentup' );
	wp_cache_delete( 'studentup_smart_10', 'studentup' );
}
add_action( 'save_post_post', 'studentup_job_box_save' );

/**
 * Admin posts list: "Job data" column — ye posts ki data missing o okka chupu lo.
 *
 * @param array $cols columns.
 * @return array
 */
function studentup_job_column( $cols ) {
	$cols['studentup_job'] = 'Job data';
	return $cols;
}
add_filter( 'manage_post_posts_columns', 'studentup_job_column' );

/**
 * Column content.
 *
 * @param string $col column key.
 * @param int    $post_id post.
 */
function studentup_job_column_row( $col, $post_id ) {
	if ( 'studentup_job' !== $col ) {
		return;
	}
	$have = 0;
	foreach ( array( 'studentup_last_date', 'studentup_salary', 'studentup_vacancies', 'studentup_apply_url' ) as $k ) {
		if ( '' !== (string) get_post_meta( $post_id, $k, true ) ) {
			$have++;
		}
	}
	$icons = array( '⚪ none', '🟠 1/4', '🟡 2/4', '🟢 3/4', '✅ full' );
	echo esc_html( $icons[ $have ] );
}
add_action( 'manage_post_posts_custom_column', 'studentup_job_column_row', 10, 2 );
