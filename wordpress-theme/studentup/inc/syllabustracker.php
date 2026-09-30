<?php
/**
 * Interactive Exam Syllabus & Study Progress Tracker.
 *
 * Provides an interactive checklist saving study progress to browser localStorage.
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Standard exam subjects checklist.
 *
 * @return array<int,array<string,string>>
 */
function studentup_default_syllabus_topics() {
	return array(
		array( 'id' => 'gs', 'title' => 'General Studies & Current Affairs' ),
		array( 'id' => 'history', 'title' => 'State History, Culture & Heritage' ),
		array( 'id' => 'polity', 'title' => 'Indian Constitution & Governance (Polity)' ),
		array( 'id' => 'economy', 'title' => 'Indian Economy & Planning' ),
		array( 'id' => 'science', 'title' => 'General Science & Science and Technology (S&T)' ),
		array( 'id' => 'aptitude', 'title' => 'Quantitative Aptitude & Logical Reasoning' ),
		array( 'id' => 'english', 'title' => 'General English & Comprehension' ),
	);
}

/**
 * Render Syllabus & Progress Tracker Block.
 *
 * @return void
 */
function studentup_syllabus_tracker_block() {
	if ( ! studentup_opt( 'syllabus_tracker', '1' ) ) {
		return;
	}

	$topics  = studentup_default_syllabus_topics();
	$post_id = get_the_ID();

	?>
	<section class="su-syl-wrap" id="syllabus-tracker" data-post-id="<?php echo (int) $post_id; ?>" aria-labelledby="su-syl-title">
		<div class="su-syl-head">
			<span class="su-syl-icon" aria-hidden="true">📚</span>
			<div>
				<h3 id="su-syl-title" class="su-syl-title">Exam Syllabus & Preparation Tracker</h3>
				<p class="su-syl-desc">Check off topics as you complete them. Your preparation progress saves automatically.</p>
			</div>
		</div>

		<div class="su-syl-progress-wrap">
			<div class="su-syl-pbar-bg">
				<div class="su-syl-pbar-fill" id="su-syl-bar" style="width:0%"></div>
			</div>
			<div class="su-syl-pbar-text">
				<span id="su-syl-count">0 / <?php echo (int) count( $topics ); ?> Completed</span>
				<strong id="su-syl-percent">0%</strong>
			</div>
		</div>

		<div class="su-syl-list">
			<?php foreach ( $topics as $t ) : ?>
				<label class="su-syl-item">
					<input type="checkbox" class="su-syl-chk" data-tid="<?php echo esc_attr( $t['id'] ); ?>">
					<span class="su-syl-lbl"><?php echo esc_html( $t['title'] ); ?></span>
				</label>
			<?php endforeach; ?>
		</div>

		<div class="su-syl-actions">
			<button type="button" class="su-syl-btn-print" onclick="window.print()">🖨️ Print / Save Syllabus</button>
			<button type="button" class="su-syl-btn-reset" id="su-syl-reset">Reset Progress</button>
		</div>
	</section>
	<?php
}

/**
 * Shortcode [studentup_syllabus_tracker].
 */
function studentup_syllabus_shortcode( $atts ) {
	ob_start();
	studentup_syllabus_tracker_block();
	return (string) ob_get_clean();
}
add_shortcode( 'studentup_syllabus_tracker', 'studentup_syllabus_shortcode' );
