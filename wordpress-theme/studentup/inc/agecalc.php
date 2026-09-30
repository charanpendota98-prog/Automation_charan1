<?php
/**
 * Interactive Job Age & Eligibility Calculator.
 *
 * Provides instant age calculation (Years, Months, Days) and category relaxation check.
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Render the Age & Eligibility Calculator widget.
 *
 * @param array $args Optional custom cutoff and age limits.
 * @return void
 */
function studentup_age_calculator_block( $args = array() ) {
	if ( ! studentup_opt( 'age_calc', '1' ) ) {
		return;
	}

	$post_id  = get_the_ID();
	$min_age  = $post_id ? (int) get_post_meta( $post_id, 'studentup_age_min', true ) : 18;
	$max_age  = $post_id ? (int) get_post_meta( $post_id, 'studentup_age_max', true ) : 44;
	$min_age  = $min_age > 0 ? $min_age : 18;
	$max_age  = $max_age > 0 ? $max_age : 44;
	$cutoff   = '2026-07-01';

	?>
	<section class="su-age-calc-wrap" id="age-calculator" aria-labelledby="su-age-calc-title">
		<div class="su-age-calc-head">
			<span class="su-age-calc-icon" aria-hidden="true">🧮</span>
			<div>
				<h3 id="su-age-calc-title" class="su-age-calc-title">Age & Eligibility Calculator</h3>
				<p class="su-age-calc-desc">Enter your date of birth and category to check upper age limit relaxation instantly.</p>
			</div>
		</div>

		<div class="su-age-calc-form">
			<div class="su-age-field">
				<label for="su-dob">🎂 Date of Birth (DOB)</label>
				<input type="date" id="su-dob" class="su-age-input" value="2000-01-01" max="<?php echo esc_attr( date_i18n( 'Y-m-d' ) ); ?>">
			</div>

			<div class="su-age-field">
				<label for="su-cutoff">📅 Cutoff Date</label>
				<input type="date" id="su-cutoff" class="su-age-input" value="<?php echo esc_attr( $cutoff ); ?>">
			</div>

			<div class="su-age-field">
				<label for="su-cat">🏷️ Category</label>
				<select id="su-cat" class="su-age-select">
					<option value="0">OC / General (No Relaxation)</option>
					<option value="5">BC-A / BC-B / BC-C / BC-D / BC-E (+5 Years)</option>
					<option value="5">SC / ST (+5 Years)</option>
					<option value="10">PwD / Differently Abled (+10 Years)</option>
					<option value="3">Ex-Servicemen (+3 Years + Service)</option>
					<option value="5">State Government Employee (+5 Years)</option>
				</select>
			</div>
		</div>

		<div class="su-age-actions">
			<button type="button" id="su-calc-age-btn" class="su-calc-btn-primary" data-min="<?php echo (int) $min_age; ?>" data-max="<?php echo (int) $max_age; ?>">
				⚡ Calculate Age & Eligibility
			</button>
		</div>

		<div id="su-age-result" class="su-age-result" style="display:none;" aria-live="polite">
			<div class="su-age-grid">
				<div class="su-age-card">
					<span class="su-age-lbl">Exact Age</span>
					<strong id="su-exact-age" class="su-age-val">—</strong>
				</div>
				<div class="su-age-card">
					<span class="su-age-lbl">Max Age Allowed (with relaxation)</span>
					<strong id="su-max-allowed" class="su-age-val">—</strong>
				</div>
				<div class="su-age-card su-age-status-card">
					<span class="su-age-lbl">Eligibility Status</span>
					<strong id="su-elig-status" class="su-age-status">—</strong>
				</div>
			</div>
			<div id="su-elig-note" class="su-age-note"></div>
		</div>
	</section>
	<?php
}

/**
 * Shortcode [studentup_age_calc].
 */
function studentup_age_calc_shortcode( $atts ) {
	ob_start();
	studentup_age_calculator_block( (array) $atts );
	return (string) ob_get_clean();
}
add_shortcode( 'studentup_age_calc', 'studentup_age_calc_shortcode' );
