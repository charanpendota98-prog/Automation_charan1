<?php
/**
 * Interactive Hall Ticket & Admit Card Direct Download Helper.
 *
 * Provides official examination hall ticket links and login guidance.
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Standard exam hall ticket portals mapping.
 *
 * @return array<int,array<string,string>>
 */
function studentup_admit_card_portals() {
	return array(
		array( 'name' => 'TSPSC (Telangana Public Service Commission)', 'url' => 'https://websitenew.tspsc.gov.in/', 'req' => 'TSPSC ID & Date of Birth (DOB)' ),
		array( 'name' => 'APPSC (Andhra Pradesh PSC)', 'url' => 'https://psc.ap.gov.in/', 'req' => 'OTPR ID & Password' ),
		array( 'name' => 'TS / AP Police Recruitment (TGLPRB / SLPRB)', 'url' => 'https://www.tslprb.in/', 'req' => 'Mobile No & Password' ),
		array( 'name' => 'SSC (Staff Selection Commission - SR)', 'url' => 'https://www.sscsr.gov.in/', 'req' => 'Online Registration ID & DOB' ),
		array( 'name' => 'Railway Recruitment Board (RRB Secunderabad)', 'url' => 'https://rrbsecunderabad.gov.in/', 'req' => 'Registration No & User Password' ),
		array( 'name' => 'IBPS Banking Exams (PO / Clerk / RRB)', 'url' => 'https://www.ibps.in/', 'req' => 'Registration / Roll No & Password / DOB' ),
	);
}

/**
 * Render Admit Card Helper Block.
 *
 * @return void
 */
function studentup_admit_card_block() {
	if ( ! studentup_opt( 'admit_card_helper', '1' ) ) {
		return;
	}

	$portals = studentup_admit_card_portals();
	?>
	<section class="su-admit-wrap" id="admit-card-helper" aria-labelledby="su-admit-title">
		<div class="su-admit-head">
			<span class="su-admit-icon" aria-hidden="true">🎫</span>
			<div>
				<h3 id="su-admit-title" class="su-admit-title">Hall Ticket & Admit Card Download Helper</h3>
				<p class="su-admit-desc">Select your recruitment board to access the official admit card download portal directly.</p>
			</div>
		</div>

		<div class="su-admit-select-wrap">
			<label for="su-admit-select">📋 Select Recruitment Board / Exam:</label>
			<select id="su-admit-select" class="su-admit-select">
				<?php foreach ( $portals as $i => $p ) : ?>
					<option value="<?php echo (int) $i; ?>" data-url="<?php echo esc_url( $p['url'] ); ?>" data-req="<?php echo esc_attr( $p['req'] ); ?>">
						<?php echo esc_html( $p['name'] ); ?>
					</option>
				<?php endforeach; ?>
			</select>
		</div>

		<div class="su-admit-info-box" id="su-admit-info">
			<div class="su-admit-req">
				<strong>🔑 Credentials Required:</strong>
				<span id="su-admit-req-text"><?php echo esc_html( $portals[0]['req'] ); ?></span>
			</div>
			<div class="su-admit-action">
				<a href="<?php echo esc_url( $portals[0]['url'] ); ?>" id="su-admit-link" target="_blank" rel="noopener noreferrer" class="su-admit-btn">
					🚀 Open Official Hall Ticket Portal →
				</a>
			</div>
		</div>

		<div class="su-admit-tips">
			<strong>⚠️ Exam Hall Guidelines:</strong>
			<span>Carry a printed copy of the hall ticket along with original Photo ID proof (Aadhaar / Voter ID) and 2 passport photos.</span>
		</div>
	</section>
	<?php
}

/**
 * Shortcode [studentup_admit_card].
 */
function studentup_admit_card_shortcode( $atts ) {
	ob_start();
	studentup_admit_card_block();
	return (string) ob_get_clean();
}
add_shortcode( 'studentup_admit_card', 'studentup_admit_card_shortcode' );
