<?php
/**
 * v172 — STUDENTUP COMMAND CENTER ("My Workspace").
 *
 * Enduku (flagship feature):
 *   Student site open chesi jobs chuse gadhapu: "naa qualification ki eligible
 *   jobs eve?", "nenu save chesina jobs lo apply chesinda?", "ee week deadline
 *   unnavi eve?" — anni prashnalaki okkate answer page.
 *
 *   1) PROFILE       — qualification · age · state (browser lo matrame; account ledu)
 *   2) ELIGIBLE JOBS — smart dataset (job meta: qual/age limits/state) ni profile
 *                      tho match chesi deadline order lo chupistundi
 *   3) PIPELINE      — Saved → Applied → Interview → Result counts (apply tracker
 *                      store tho same language — saved panel tho sync lo unta ydi)
 *   4) DEADLINE RADAR — save chesina jobs lo 3/7/14 rojlu lo mudindi vi urgent ga
 *
 * Design rules (repo conventions):
 *   · Account / cookie / server personalisation LEDU — page cache + privacy safe.
 *   · Data server-side JSON attr lo (REST round-trip ledu → instant + offline).
 *   · JS vanilla only, progressive enhancement, XSS-safe (esc/textContent).
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Feature gate (admin → StudentUp Options).
 *
 * @return bool
 */
function studentup_workspace_on() {
	return (bool) studentup_opt( 'workspace', '1' );
}

/**
 * Workspace page URL — [studentup_workspace] shortcode unna published page.
 *
 * @return string URL (lekapothe '#workspace' anchor fallback).
 */
function studentup_workspace_url() {
	static $url = null;
	if ( null !== $url ) {
		return $url;
	}
	$url = '';
	if ( studentup_workspace_on() ) {
		$cache = wp_cache_get( 'studentup_ws_url', 'studentup' );
		if ( is_string( $cache ) ) {
			$url = $cache;
		} else {
			$q = new WP_Query(
				array(
					'post_type'      => 'page',
					'post_status'    => 'publish',
					's'              => '[studentup_workspace]',
					'no_found_rows'  => true,
					'posts_per_page' => 1,
					'fields'         => 'ids',
				)
			);
			if ( $q->posts ) {
				$one = get_post( (int) $q->posts[0] );
				if ( $one && has_shortcode( (string) $one->post_content, 'studentup_workspace' ) ) {
					$url = (string) get_permalink( $one->ID );
				}
			}
			wp_cache_set( 'studentup_ws_url', $url, 'studentup', 300 );
		}
	}
	return $url;
}

/**
 * Current page lo shortcode undo (assets enqueue kosam)?
 *
 * @return bool
 */
function studentup_workspace_active() {
	if ( is_admin() || ! studentup_workspace_on() || ! is_singular() ) {
		return false;
	}
	$post = get_post();
	return $post ? has_shortcode( (string) $post->post_content, 'studentup_workspace' ) : false;
}

/**
 * Assets — workspace page lo mattrame (site-speed impact zero).
 */
function studentup_workspace_assets() {
	if ( ! studentup_workspace_active() ) {
		return;
	}
	wp_enqueue_script(
		'studentup-workspace',
		get_template_directory_uri() . '/assets/js/studentup-workspace.js',
		array(),
		STUDENTUP_VERSION,
		true
	);
	wp_localize_script(
		'studentup-workspace',
		'STUDENTUP_WS',
		array(
			'profile' => 'su_profile_v1',
			'saved'   => defined( 'STUDENTUP_SAVED_STORE' ) ? STUDENTUP_SAVED_STORE : 'studentup_saved_v1',
			'apply'   => 'studentup_apply_v1',
			'savedOn' => function_exists( 'studentup_saved_on' ) && studentup_saved_on(),
			'i18n'    => array(
				'profileHint' => __( 'Profile is stored in this browser only — no account, nothing sent to the server.', 'studentup' ),
				'anyQual'     => __( 'Any qualification', 'studentup' ),
				'stateTS'     => __( 'Telangana', 'studentup' ),
				'stateAP'     => __( 'Andhra Pradesh', 'studentup' ),
				'stateC'      => __( 'Central', 'studentup' ),
				'stateAny'    => __( 'All states', 'studentup' ),
				'eligible'    => __( 'Eligible for you', 'studentup' ),
				'partial'     => __( 'Partly eligible — check details', 'studentup' ),
				'ageElig'     => __( 'Eligible by age', 'studentup' ),
				'ageNo'       => __( 'Age limit', 'studentup' ),
				'noMatch'     => __( 'No matching posts yet — relax the filters or check back after the next update.', 'studentup' ),
				'noProfile'   => __( 'Set your qualification above — matching jobs appear here instantly.', 'studentup' ),
				'deadline'    => __( 'Deadline', 'studentup' ),
				'daysLeft'    => __( 'days left', 'studentup' ),
				'lastDay'     => __( 'Last day', 'studentup' ),
				'expired'     => __( 'Closed', 'studentup' ),
				'vac'         => __( 'Posts', 'studentup' ),
				'pay'         => __( 'Pay', 'studentup' ),
				'save'        => __( 'Save', 'studentup' ),
				'pipeSaved'   => __( 'Saved', 'studentup' ),
				'pipeApplied' => __( 'Applied', 'studentup' ),
				'pipeInter'   => __( 'Interview', 'studentup' ),
				'pipeResult'  => __( 'Result', 'studentup' ),
				'pipeEmpty'   => __( 'Save jobs from any card — your pipeline builds here automatically.', 'studentup' ),
				'radarEmpty'  => __( 'Saved jobs with deadlines will show up here, most urgent first.', 'studentup' ),
				'radarUrgent' => __( 'Closing in 3 days', 'studentup' ),
				'radarSoon'   => __( 'Closing this week', 'studentup' ),
				'radarOk'     => __( 'Closing soon', 'studentup' ),
				'openSaved'   => __( 'Open saved panel', 'studentup' ),
				'qualLabel'   => __( 'Qualification', 'studentup' ),
				'ageLabel'    => __( 'Age', 'studentup' ),
				'stateLabel'  => __( 'State', 'studentup' ),
			),
		)
	);
}
add_action( 'wp_enqueue_scripts', 'studentup_workspace_assets', 20 );

/**
 * `[studentup_workspace]` — the command center markup.
 *
 * Data (smart dataset) server-side JSON attr lo — REST wait ledu, offline kuda pani chestundi.
 *
 * @return string HTML.
 */
function studentup_workspace_shortcode() {
	if ( ! studentup_workspace_on() ) {
		return '';
	}
	$data = function_exists( 'studentup_smart_dataset' ) ? studentup_smart_dataset( 80 ) : array();
	$quals = function_exists( 'studentup_qual_terms' ) ? studentup_qual_terms() : array();
	$saved_url = function_exists( 'studentup_saved_page_url' ) ? studentup_saved_page_url() : '';
	$tools = array(
		array( 'icn' => 'person', 't' => __( 'Age & eligibility calculator', 'studentup' ), 'u' => home_url( '/#age-calculator' ) ),
		array( 'icn' => 'card', 't' => __( 'Fee & concession calculator', 'studentup' ), 'u' => home_url( '/#fee-calculator' ) ),
		array( 'icn' => 'chart', 't' => __( 'Exam score calculator', 'studentup' ), 'u' => home_url( '/#score-calculator' ) ),
		array( 'icn' => 'book', 't' => __( 'Syllabus tracker', 'studentup' ), 'u' => home_url( '/#syllabus-tracker' ) ),
		array( 'icn' => 'wallet', 't' => __( 'In-hand salary calculator', 'studentup' ), 'u' => home_url( '/#salary-calculator' ) ),
		array( 'icn' => 'board', 't' => __( 'Active jobs board', 'studentup' ), 'u' => function_exists( 'studentup_opportunity_board_url' ) ? studentup_opportunity_board_url() : home_url( '/' ) ),
	);

	ob_start();
	?>
	<section class="su-ws" id="workspace" aria-label="<?php echo esc_attr__( 'My workspace', 'studentup' ); ?>"
		data-su-ws='<?php echo esc_attr( wp_json_encode( $data ) ); ?>'>

		<div class="su-ws-head">
			<h2><?php echo esc_html__( 'My Workspace', 'studentup' ); ?></h2>
			<p><?php echo esc_html__( 'Set your profile once — eligible jobs, deadlines and your application status, all in one place.', 'studentup' ); ?></p>
		</div>

		<div class="su-ws-grid">
			<div class="su-ws-card su-ws-profile">
				<h3><?php echo esc_html__( '1 · Your profile', 'studentup' ); ?></h3>
				<form class="su-ws-form" data-su-ws-form onsubmit="return false">
					<label>
						<span><?php echo esc_html__( 'Qualification', 'studentup' ); ?></span>
						<select data-su-ws-qual>
							<option value=""><?php echo esc_html__( 'Any qualification', 'studentup' ); ?></option>
							<?php foreach ( $quals as $slug => $label ) : ?>
								<option value="<?php echo esc_attr( $slug ); ?>"><?php echo esc_html( $label ); ?></option>
							<?php endforeach; ?>
						</select>
					</label>
					<label>
						<span><?php echo esc_html__( 'Age', 'studentup' ); ?></span>
						<input type="number" inputmode="numeric" min="14" max="60" placeholder="21" data-su-ws-age>
					</label>
					<label>
						<span><?php echo esc_html__( 'State', 'studentup' ); ?></span>
						<select data-su-ws-state>
							<option value=""><?php echo esc_html__( 'All states', 'studentup' ); ?></option>
							<option value="ts"><?php echo esc_html__( 'Telangana', 'studentup' ); ?></option>
							<option value="ap"><?php echo esc_html__( 'Andhra Pradesh', 'studentup' ); ?></option>
							<option value="central"><?php echo esc_html__( 'Central', 'studentup' ); ?></option>
						</select>
					</label>
				</form>
				<p class="su-ws-note"><?php echo esc_html__( 'Profile is stored in this browser only — no account, nothing sent to the server.', 'studentup' ); ?></p>
			</div>

			<div class="su-ws-card su-ws-pipe">
				<h3><?php echo esc_html__( '2 · Application pipeline', 'studentup' ); ?></h3>
				<div class="su-ws-tiles" data-su-ws-pipe></div>
			</div>
		</div>

		<div class="su-ws-card">
			<h3 class="su-ws-mh"><?php echo esc_html__( '3 · Jobs matched for you', 'studentup' ); ?> <span class="su-ws-mcount" data-su-ws-mcount aria-live="polite"></span></h3>
			<div class="su-ws-matches" data-su-ws-matches></div>
		</div>

		<div class="su-ws-grid2">
			<div class="su-ws-card">
				<h3><?php echo esc_html__( '4 · Deadline radar', 'studentup' ); ?></h3>
				<div class="su-ws-radar" data-su-ws-radar></div>
				<?php if ( $saved_url ) : ?>
					<a class="su-ws-savedlink" href="<?php echo esc_url( $saved_url ); ?>"><?php echo studentup_ui_icon( 'bookmark', 14 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> <?php echo esc_html__( 'Open the saved page', 'studentup' ); ?></a>
				<?php endif; ?>
			</div>
			<div class="su-ws-card">
				<h3><?php echo esc_html__( 'Quick tools', 'studentup' ); ?></h3>
				<div class="su-ws-tools">
					<?php foreach ( $tools as $t ) : ?>
						<a href="<?php echo esc_url( $t['u'] ); ?>"><?php echo studentup_ui_icon( esc_html( $t['icn'] ), 15 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> <?php echo esc_html( $t['t'] ); ?></a>
					<?php endforeach; ?>
				</div>
			</div>
		</div>
	</section>
	<?php
	return (string) ob_get_clean();
}
add_shortcode( 'studentup_workspace', 'studentup_workspace_shortcode' );
