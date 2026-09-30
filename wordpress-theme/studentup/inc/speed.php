<?php
/**
 * v127 INSTANT LAYER — Speculation Rules (prerender), View Transitions,
 * command palette + "For You" personalised rail bootstrapping.
 *
 * Enduku (why this is top-tier):
 *   1) **Speculation Rules API** — Chrome/Edge lo reader link meeda hover/tap
 *      cheyyadaniki mundhe next page ni prerender chestundi. Result: navigation
 *      almost 0 ms. Prefetch plugins laaga JS polling ledu — browser-native.
 *      Safety: admin, logout, comment, apply (external) links eppudu prerender
 *      kaavu; ads/analytics ki double-count raakunda prerender page activate
 *      ayite mattrame counts (browser guarantee).
 *   2) **View Transitions** — same-document kaadu, cross-document transitions
 *      (browser support unte) — app-laga smooth page change, zero JS.
 *   3) Non-support browsers ki emi marad'du (progressive enhancement).
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Speculation rules — moderate eagerness (hover/pointerdown), safe exclusions.
 */
function studentup_speculation_rules() {
	if ( is_admin() || is_user_logged_in() || ! studentup_opt( 'instant_nav', '1' ) ) {
		return;
	}
	$rules = array(
		'prerender' => array(
			array(
				'where'     => array(
					'and' => array(
						array( 'href_matches' => '/*' ),
						array( 'not' => array( 'href_matches' => '/wp-admin/*' ) ),
						array( 'not' => array( 'href_matches' => '/wp-login.php*' ) ),
						array( 'not' => array( 'href_matches' => '/*\\?*(^|&)_wpnonce=*' ) ),
						array( 'not' => array( 'selector_matches' => '.no-prerender, [rel~="nofollow"], [target="_blank"], [download]' ) ),
					),
				),
				'eagerness' => 'moderate',
			),
		),
		'prefetch'  => array(
			array(
				'where'     => array(
					'and' => array(
						array( 'href_matches' => '/*' ),
						array( 'not' => array( 'href_matches' => '/wp-admin/*' ) ),
						array( 'not' => array( 'selector_matches' => '[target="_blank"], [rel~="nofollow"]' ) ),
					),
				),
				'eagerness' => 'conservative',
			),
		),
	);
	echo '<script type="speculationrules">'
		. wp_json_encode( $rules, JSON_UNESCAPED_SLASHES )
		. '</script>' . "\n";
}
add_action( 'wp_head', 'studentup_speculation_rules', 3 );

/**
 * Cross-document view transitions (browser-native, CSS matrame).
 */
function studentup_view_transitions() {
	if ( ! studentup_opt( 'instant_nav', '1' ) ) {
		return;
	}
	echo '<meta name="view-transition" content="same-origin">' . "\n";
	echo '<style id="su-vt">@view-transition{navigation:auto}'
		. '@media(prefers-reduced-motion:reduce){@view-transition{navigation:none}}</style>' . "\n";
}
add_action( 'wp_head', 'studentup_view_transitions', 4 );

/**
 * Command palette markup (⌘K / Ctrl+K) — power-user search + quick actions.
 */
/**
 * v173: palette icon markup (trusted SVG — JS raw render).
 *
 * @param string $key icon key.
 * @return string
 */
function studentup_cmdk_icon( $key ) {
	return function_exists( 'studentup_ui_icon' ) ? studentup_ui_icon( $key, 15 ) : '';
}

function studentup_command_palette() {
	if ( ! studentup_opt( 'command_palette', '1' ) ) {
		return;
	}
	$jobs  = studentup_used_term( 'ts-jobs' );
	$schol = studentup_used_term( 'scholarships' );
	$res   = studentup_used_term( 'results' );
	$links = array();
	if ( $jobs ) {
		$links[] = array( 'i' => studentup_cmdk_icon( 'work' ), 't' => 'Latest government jobs', 'u' => get_category_link( $jobs ) );
	}
	if ( $schol ) {
		$links[] = array( 'i' => studentup_cmdk_icon( 'school' ), 't' => 'Scholarships', 'u' => get_category_link( $schol ) );
	}
	if ( $res ) {
		$links[] = array( 'i' => studentup_cmdk_icon( 'doc' ), 't' => 'Results', 'u' => get_category_link( $res ) );
	}
	$links[] = array( 'i' => studentup_cmdk_icon( 'bolt' ), 't' => 'My Workspace', 'u' => function_exists( 'studentup_workspace_url' ) ? ( studentup_workspace_url() ? studentup_workspace_url() : home_url( '/' ) ) : home_url( '/' ) );
	$links[] = array( 'i' => studentup_cmdk_icon( 'board' ), 't' => 'Active jobs board', 'u' => studentup_opportunity_board_url() );
		$links[] = array( 'i' => studentup_cmdk_icon( 'chart' ), 't' => 'Age & Eligibility Calculator', 'u' => home_url( '/#age-calculator' ) );
		$links[] = array( 'i' => studentup_cmdk_icon( 'card' ), 't' => 'Fee & Concession Calculator', 'u' => home_url( '/#fee-calculator' ) );
		$links[] = array( 'i' => studentup_cmdk_icon( 'board' ), 't' => 'Exam Negative Marks Score Calculator', 'u' => home_url( '/#score-calculator' ) );
		$links[] = array( 'i' => studentup_cmdk_icon( 'ticket' ), 't' => 'Hall Ticket Download Helper', 'u' => home_url( '/#admit-card-helper' ) );
		$links[] = array( 'i' => studentup_cmdk_icon( 'doc' ), 't' => 'Fresher Resume & Bio-Data Maker', 'u' => home_url( '/#resume-maker' ) );
		$links[] = array( 'i' => studentup_cmdk_icon( 'book' ), 't' => 'Syllabus & Study Progress Tracker', 'u' => home_url( '/#syllabus-tracker' ) );
		$links[] = array( 'i' => studentup_cmdk_icon( 'wallet' ), 't' => 'In-hand Salary Calculator', 'u' => home_url( '/#salary-calculator' ) );
		$links[] = array( 'i' => studentup_cmdk_icon( 'bolt' ), 't' => 'Daily Quiz', 'u' => home_url( '/#daily-quiz' ) );
		$links[] = array( 'i' => studentup_cmdk_icon( 'person' ), 't' => 'AI Job Match', 'u' => home_url( '/#job-match' ) );
		$links[] = array( 'i' => studentup_cmdk_icon( 'calendar' ), 't' => 'Job Calendar', 'u' => home_url( '/#job-calendar' ) );
	?>
	<div class="su-cmdk" id="su-cmdk" hidden role="dialog" aria-modal="true" aria-label="Quick search">
		<div class="su-cmdk-box">
			<div class="su-cmdk-top">
				<span aria-hidden="true">⌘</span>
				<input type="search" id="su-cmdk-input" placeholder="Search jobs, results, scholarships… (Esc to close)" autocomplete="off" spellcheck="false" aria-label="Quick search">
				<kbd>Esc</kbd>
			</div>
			<div class="su-cmdk-list" id="su-cmdk-list" role="listbox" data-su-cmdk-links='<?php echo esc_attr( wp_json_encode( $links ) ); ?>'></div>
			<div class="su-cmdk-foot"><span>↑↓ navigate · ↵ open</span><span>Ctrl/⌘ + K</span></div>
		</div>
	</div>
	<?php
}
add_action( 'wp_footer', 'studentup_command_palette', 6 );

/**
 * "For You" rail placeholder — JS reader history (localStorage) prakaram
 * nimputundi. Server side personalisation ledu (page cache safe, privacy safe).
 */
function studentup_for_you() {
	if ( ! studentup_opt( 'for_you', '1' ) ) {
		return;
	}
	?>
	<section class="su-foryou" data-su-foryou hidden aria-label="Picked for you">
		<div class="su-hot-head">
			<h2><?php echo studentup_ui_icon( 'bolt', 17 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> Picked for you</h2>
			<button type="button" class="su-foryou-clear" data-su-foryou-clear>Clear history</button>
		</div>
		<div class="su-foryou-grid" data-su-foryou-grid></div>
		<p class="su-finder-note">Mee browser lo chusina sections batti — ee list mee device lo ne untundi, server ki pampinchamu.</p>
	</section>
	<?php
}
