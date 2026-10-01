<?php
/**
 * 1-Page Fresher Resume & Bio-Data Generator.
 *
 * Provides a quick 1-click professional resume generator for job applicants.
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Render Resume Maker Block.
 *
 * @return void
 */
function studentup_resume_maker_block() {
	if ( ! studentup_opt( 'resume_maker', '1' ) ) {
		return;
	}

	?>
	<section class="su-resume-wrap" id="resume-maker" aria-labelledby="su-resume-title">
		<div class="su-resume-head">
			<span class="su-resume-icon" aria-hidden="true"><?php echo studentup_ui_icon( 'doc', 26 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?></span>
			<div>
				<h3 id="su-resume-title" class="su-resume-title">Fresher Resume & Bio-Data Maker</h3>
				<p class="su-resume-desc">Enter your details and generate a clean 1-page bio-data ready for printing and job applications.</p>
			</div>
		</div>

		<div class="su-resume-form">
			<div class="su-resume-field">
				<label for="su-res-name"><?php echo studentup_ui_icon( 'person', 14 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> Full Name</label>
				<input type="text" id="su-res-name" class="su-resume-input" placeholder="e.g. John Doe">
			</div>

			<div class="su-resume-field">
				<label for="su-res-phone"><?php echo studentup_ui_icon( 'phone', 14 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> Mobile Number</label>
				<input type="tel" id="su-res-phone" class="su-resume-input" placeholder="9876543210">
			</div>

			<div class="su-resume-field">
				<label for="su-res-qual"><?php echo studentup_ui_icon( 'school', 14 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> Highest Qualification</label>
				<select id="su-res-qual" class="su-resume-select">
					<option value="B.Tech / B.E">B.Tech / B.E (Engineering)</option>
					<option value="Degree (B.Sc / B.Com / B.A)">Degree (B.Sc / B.Com / B.A)</option>
					<option value="Diploma / Polytechnic">Diploma / Polytechnic</option>
					<option value="Intermediate (10+2)">Intermediate (10+2)</option>
					<option value="10th Class (SSC)">10th Class (SSC)</option>
					<option value="Post Graduation (M.Tech/MBA/MCA/M.Sc)">Post Graduation (PG)</option>
				</select>
			</div>

			<div class="su-resume-field">
				<label for="su-res-skills"><?php echo studentup_ui_icon( 'bolt', 14 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> Skills & Computer Knowledge</label>
				<input type="text" id="su-res-skills" class="su-resume-input" placeholder="MS Office, English Typing, Computer Basics">
			</div>
		</div>

		<div class="su-resume-actions">
			<button type="button" id="su-gen-resume-btn" class="su-resume-btn-primary">
				<?php echo studentup_ui_icon( 'doc', 15 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> Preview Resume &amp; PDF
			</button>
		</div>

		<div id="su-resume-preview" class="su-resume-preview" style="display:none;" aria-live="polite">
			<div class="su-resume-paper">
				<div class="su-rp-header">
					<h2 id="su-rp-name" class="su-rp-name">Candidate Name</h2>
					<p id="su-rp-contact" class="su-rp-contact">Phone: 9876543210 | Qualification: B.Tech</p>
				</div>
				<hr class="su-rp-hr">
				<div class="su-rp-section">
					<h4 class="su-rp-sec-title">Career Objective</h4>
					<p class="su-rp-sec-p">To secure a responsible career opportunity where I can fully utilize my training and skills, while making a significant contribution to the success of the company.</p>
				</div>
				<div class="su-rp-section">
					<h4 class="su-rp-sec-title">Educational Qualifications</h4>
					<p id="su-rp-qual-text" class="su-rp-sec-p">B.Tech / Degree Graduate</p>
				</div>
				<div class="su-rp-section">
					<h4 class="su-rp-sec-title">Technical Skills</h4>
					<p id="su-rp-skills-text" class="su-rp-sec-p">Computer Basics, MS Office, Professional Typing</p>
				</div>
				<div class="su-rp-footer">
					<p>Declaration: I hereby declare that all the information furnished above is true to the best of my knowledge.</p>
				</div>
			</div>
			<div class="su-resume-print-action">
				<button type="button" class="su-resume-print-btn" onclick="window.print()"><?php echo studentup_ui_icon( 'print', 15 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> Print / Save as PDF</button>
			</div>
		</div>
	</section>
	<?php
}

/**
 * Shortcode [studentup_resume_maker].
 */
function studentup_resume_maker_shortcode( $atts ) {
	ob_start();
	studentup_resume_maker_block();
	return (string) ob_get_clean();
}
add_shortcode( 'studentup_resume_maker', 'studentup_resume_maker_shortcode' );
