<?php
/**
 * v196 - STUDENTS INTERNET CENTER page (transparent pricing, audit blocker #12).
 *
 * Why: the live site advertised "very low service charge" everywhere and never
 * published a price, and the paid offline service was mixed with publisher
 * content. A hidden price looks like a trap to both readers and reviewers.
 * This page puts the whole offer on one page: exact price list, what is
 * included, what is never included, government fee separation, turnaround and
 * the cancellation rule - and it stays out of the editorial flow.
 *
 * Template: page-internet-center.php (assign to the /internet-center/ page).
 *
 * @package StudentUp
 */

defined( 'ABSPATH' ) || exit;

get_header();

$soc   = function_exists( 'studentup_social_links' ) ? studentup_social_links() : array();
$phone = function_exists( 'studentup_call_number' ) ? studentup_call_number( studentup_opt( 'social_whatsapp', '' ) ) : '';
$mail  = function_exists( 'studentup_contact_email' ) ? studentup_contact_email() : '';
$wa    = isset( $soc['whatsapp'] ) ? $soc['whatsapp'] : '';

$p1 = (int) studentup_opt( 'ic_price_basic', '50' );
$p2 = (int) studentup_opt( 'ic_price_form', '100' );
$p3 = (int) studentup_opt( 'ic_price_combo', '150' );
?>
<main id="main" class="wrap su-page su-ic-page">
	<?php if ( function_exists( 'studentup_breadcrumbs' ) ) { studentup_breadcrumbs(); } ?>
	<h1><?php esc_html_e( 'Students Internet Center', 'studentup' ); ?></h1>
	<p class="su-ic-page-sub"><?php esc_html_e( 'Separate offline service · Telangana & Andhra Pradesh · run by the same team that publishes this website', 'studentup' ); ?></p>

	<div class="su-ic-note">
		<strong><?php esc_html_e( 'This is optional.', 'studentup' ); ?></strong>
		<?php esc_html_e( 'Reading this website, getting job alerts and using every tool here is free. You never need this service to use StudentUp.', 'studentup' ); ?>
	</div>

	<h2><?php esc_html_e( 'Price list (2026)', 'studentup' ); ?></h2>
	<table class="su-ic-price">
		<thead>
			<tr>
				<th scope="col"><?php esc_html_e( 'Service', 'studentup' ); ?></th>
				<th scope="col"><?php esc_html_e( 'What you get', 'studentup' ); ?></th>
				<th scope="col"><?php esc_html_e( 'Our service charge', 'studentup' ); ?></th>
			</tr>
		</thead>
		<tbody>
			<tr>
				<td><?php esc_html_e( 'Single application form', 'studentup' ); ?></td>
				<td><?php esc_html_e( 'One online form filled, checked and returned as a PDF', 'studentup' ); ?></td>
				<td><b><?php echo esc_html( '₹' . $p1 ); ?></b></td>
			</tr>
			<tr>
				<td><?php esc_html_e( 'Form + photo &amp; signature formatting', 'studentup' ); ?></td>
				<td><?php esc_html_e( 'Form filling plus resizing/renaming of your photo and signature to the official size', 'studentup' ); ?></td>
				<td><b><?php echo esc_html( '₹' . $p2 ); ?></b></td>
			</tr>
			<tr>
				<td><?php esc_html_e( 'Application + document pack', 'studentup' ); ?></td>
				<td><?php esc_html_e( 'Form, photo/signature work and a single PDF pack of the documents the notification asks for', 'studentup' ); ?></td>
				<td><b><?php echo esc_html( '₹' . $p3 ); ?></b></td>
			</tr>
		</tbody>
	</table>
	<p class="su-ic-price-note">
		<?php esc_html_e( 'Government application fee, exam fee or any official payment is separate and is never collected by us - you pay the department directly on the official portal.', 'studentup' ); ?>
		<?php esc_html_e( 'Prices are shown here permanently and do not change based on who calls.', 'studentup' ); ?>
	</p>

	<h2><?php esc_html_e( 'What we never do', 'studentup' ); ?></h2>
	<ul>
		<li><?php esc_html_e( 'We never promise a job, a rank, a seat or a selection - no one can.', 'studentup' ); ?></li>
		<li><?php esc_html_e( 'We never ask for Aadhaar, PAN, bank details, OTPs or passwords.', 'studentup' ); ?></li>
		<li><?php esc_html_e( 'We never fill a form with guessed details. If a document is missing, we tell you instead of inventing it.', 'studentup' ); ?></li>
	</ul>

	<h2><?php esc_html_e( 'How it works', 'studentup' ); ?></h2>
	<ol class="su-ab-steps">
		<li><?php esc_html_e( 'Send the job or scholarship name on WhatsApp, and ask for the price before paying.', 'studentup' ); ?></li>
		<li><?php esc_html_e( 'Send only the documents the notification asks for.', 'studentup' ); ?></li>
		<li><?php esc_html_e( 'We fill the form, share a draft PDF with you, and submit only after you approve it.', 'studentup' ); ?></li>
		<li><?php esc_html_e( 'Turnaround: typically the same day, at most 24 hours on working days.', 'studentup' ); ?></li>
	</ol>

	<h2><?php esc_html_e( 'Cancellation and refund', 'studentup' ); ?></h2>
	<p><?php esc_html_e( 'If we cannot submit your application, the service charge is returned in full. If you cancel before we start filling, nothing is charged. Government fees paid on the official portal are between you and the department.', 'studentup' ); ?></p>

	<h2><?php esc_html_e( 'Contact the center', 'studentup' ); ?></h2>
	<p class="su-ic-page-actions">
		<?php if ( $wa ) : ?>
			<a class="su-cta" href="<?php echo esc_url( $wa ); ?>" rel="nofollow noopener" target="_blank"><?php esc_html_e( 'WhatsApp the center', 'studentup' ); ?></a>
		<?php endif; ?>
		<?php if ( $phone ) : ?>
			<a class="su-ic-alt" href="<?php echo esc_attr( 'tel:+91' . $phone ); ?>"><?php esc_html_e( 'Call', 'studentup' ); ?> +91 <?php echo esc_html( $phone ); ?></a>
		<?php endif; ?>
		<?php if ( $mail ) : ?>
			<a class="su-ic-alt" href="<?php echo esc_attr( 'mailto:' . $mail ); ?>"><?php echo esc_html( $mail ); ?></a>
		<?php endif; ?>
	</p>
	<p class="su-ic-page-legal">
		<?php esc_html_e( 'This service is a private offline service. It is not connected to any government department, and paying us gives you no advantage in any selection process.', 'studentup' ); ?>
	</p>
</main>
<?php
get_footer();
