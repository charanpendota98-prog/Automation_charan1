<?php
/**
 * Interactive Application Fee & Concession Calculator.
 *
 * Provides real-time calculation of application and examination fee concessions by category.
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Render the Fee Calculator Block.
 *
 * @param array $args Custom base fees.
 * @return void
 */
function studentup_fee_calculator_block( $args = array() ) {
	if ( ! studentup_opt( 'fee_calc', '1' ) ) {
		return;
	}

	$post_id   = get_the_ID();
	$fee_raw   = $post_id ? (string) get_post_meta( $post_id, 'studentup_fee', true ) : '';
	$proc_fee  = 200; // Standard processing fee
	$exam_fee  = 120; // Standard exam fee

	?>
	<section class="su-fee-calc-wrap" id="fee-calculator" aria-labelledby="su-fee-calc-title">
		<div class="su-fee-calc-head">
			<span class="su-fee-calc-icon" aria-hidden="true"><?php echo studentup_ui_icon( 'card', 26 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?></span>
			<div>
				<h3 id="su-fee-calc-title" class="su-fee-calc-title">Application Fee & Concession Calculator</h3>
				<p class="su-fee-calc-desc">Select your category to determine exact examination fee concessions and total payable amount.</p>
			</div>
		</div>

		<div class="su-fee-calc-form">
			<div class="su-fee-field">
				<label for="su-fee-cat"><?php echo studentup_ui_icon( 'tag', 14 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> Reservation Category</label>
				<select id="su-fee-cat" class="su-fee-select">
					<option value="gen">OC / General / EWS (Male)</option>
					<option value="bc">BC (A/B/C/D/E) Candidates</option>
					<option value="sc_st">SC / ST Candidates (Exam Fee Exemption)</option>
					<option value="pwd">PwD / Differently Abled (100% Free)</option>
					<option value="women">Women Candidates (State Concession)</option>
					<option value="esm">Ex-Servicemen Candidates</option>
				</select>
			</div>

			<div class="su-fee-field">
				<label for="su-base-proc"><?php echo studentup_ui_icon( 'doc', 14 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> Processing Fee (₹)</label>
				<input type="number" id="su-base-proc" class="su-fee-input" value="<?php echo (int) $proc_fee; ?>" min="0">
			</div>

			<div class="su-fee-field">
				<label for="su-base-exam"><?php echo studentup_ui_icon( 'card', 14 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> Exam Fee (₹)</label>
				<input type="number" id="su-base-exam" class="su-fee-input" value="<?php echo (int) $exam_fee; ?>" min="0">
			</div>
		</div>

		<div class="su-fee-actions">
			<button type="button" id="su-calc-fee-btn" class="su-fee-btn-primary">
				<?php echo studentup_ui_icon( 'bolt', 15 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> Calculate Total Fee
			</button>
		</div>

		<div id="su-fee-result" class="su-fee-result" style="display:none;" aria-live="polite">
			<div class="su-fee-grid">
				<div class="su-fee-card">
					<span class="su-fee-lbl">Processing Fee</span>
					<strong id="su-res-proc" class="su-fee-val">₹200</strong>
				</div>
				<div class="su-fee-card">
					<span class="su-fee-lbl">Exam Fee</span>
					<strong id="su-res-exam" class="su-fee-val">₹120</strong>
				</div>
				<div class="su-fee-card su-fee-total-card">
					<span class="su-fee-lbl">Total Payable</span>
					<strong id="su-res-total" class="su-fee-val su-fee-highlight">₹320</strong>
				</div>
			</div>
			<div id="su-fee-note" class="su-fee-note"></div>
		</div>
	</section>
	<?php
}

/**
 * Shortcode [studentup_fee_calc].
 */
function studentup_fee_calc_shortcode( $atts ) {
	ob_start();
	studentup_fee_calculator_block( (array) $atts );
	return (string) ob_get_clean();
}
add_shortcode( 'studentup_fee_calc', 'studentup_fee_calc_shortcode' );
