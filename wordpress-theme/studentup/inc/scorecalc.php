<?php
/**
 * Exam Negative Marks & Cut-Off Score Calculator.
 *
 * Provides instant net score calculation factoring in negative marking penalty ratios.
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Render Exam Score Calculator Block.
 *
 * @return void
 */
function studentup_score_calculator_block() {
	if ( ! studentup_opt( 'score_calc', '1' ) ) {
		return;
	}

	?>
	<section class="su-score-calc-wrap" id="score-calculator" aria-labelledby="su-score-calc-title">
		<div class="su-score-calc-head">
			<span class="su-score-calc-icon" aria-hidden="true"><?php echo studentup_ui_icon( 'board', 26 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?></span>
			<div>
				<h3 id="su-score-calc-title" class="su-score-calc-title">Negative Marks & Cut-Off Score Calculator</h3>
				<p class="su-score-calc-desc">Enter correct and incorrect answers to calculate your exact net marks after negative marking deduction.</p>
			</div>
		</div>

		<div class="su-score-calc-form">
			<div class="su-score-field">
				<label for="su-score-correct"><?php echo studentup_ui_icon( 'check', 14 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> Correct Answers</label>
				<input type="number" id="su-score-correct" class="su-score-input" value="100" min="0">
			</div>

			<div class="su-score-field">
				<label for="su-score-wrong"><?php echo studentup_ui_icon( 'close', 14 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> Wrong Answers</label>
				<input type="number" id="su-score-wrong" class="su-score-input" value="20" min="0">
			</div>

			<div class="su-score-field">
				<label for="su-score-pos">+ Marks Per Correct Answer</label>
				<select id="su-score-pos" class="su-score-select">
					<option value="1">+1.0 Mark</option>
					<option value="2">+2.0 Marks (UPSC / SSC CGL Tier-1)</option>
					<option value="1.5">+1.5 Marks</option>
				</select>
			</div>

			<div class="su-score-field">
				<label for="su-score-neg">&minus; Negative Marking Ratio</label>
				<select id="su-score-neg" class="su-score-select">
					<option value="0.25">1/4 Deduction (-0.25 / -0.50)</option>
					<option value="0.333">1/3 Deduction (-0.33 / -0.66)</option>
					<option value="0.5">1/2 Deduction (-0.50)</option>
					<option value="0">No Negative Marking (0.00)</option>
				</select>
			</div>
		</div>

		<div class="su-score-actions">
			<button type="button" id="su-calc-score-btn" class="su-score-btn-primary">
				<?php echo studentup_ui_icon( 'bolt', 15 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> Calculate Net Score
			</button>
		</div>

		<div id="su-score-result" class="su-score-result" style="display:none;" aria-live="polite">
			<div class="su-score-grid">
				<div class="su-score-card">
					<span class="su-score-lbl">Positive Marks</span>
					<strong id="su-res-pos-marks" class="su-score-val">—</strong>
				</div>
				<div class="su-score-card">
					<span class="su-score-lbl">Negative Deduction</span>
					<strong id="su-res-neg-marks" class="su-score-val su-score-neg-val">—</strong>
				</div>
				<div class="su-score-card su-score-final-card">
					<span class="su-score-lbl">Final Net Score</span>
					<strong id="su-res-final-score" class="su-score-val su-score-highlight">—</strong>
				</div>
			</div>
			<div id="su-score-note" class="su-score-note"></div>
		</div>
	</section>
	<?php
}

/**
 * Shortcode [studentup_score_calc].
 */
function studentup_score_calc_shortcode( $atts ) {
	ob_start();
	studentup_score_calculator_block();
	return (string) ob_get_clean();
}
add_shortcode( 'studentup_score_calc', 'studentup_score_calc_shortcode' );
