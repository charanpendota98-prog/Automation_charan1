<?php
/**
 * v117: Verified Success Stories public intake CTA.
 *
 * The form itself lives in Google Forms so file uploads and access controls
 * stay in the owner's Google account. This theme only exposes the configured
 * form link and the editorial/privacy rules. Submissions never auto-publish.
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * [studentup_success_story_form] — use on a dedicated Share Your Story page.
 *
 * @return string
 */
function studentup_success_story_form_shortcode() {
	if ( ! function_exists( 'studentup_opt' ) ) {
		return '';
	}
	$form_url = esc_url( studentup_opt( 'success_story_form_url', '' ) );
	if ( ! $form_url ) {
		return '';
	}

	$contact = sanitize_email( studentup_opt( 'contact_email', get_option( 'admin_email' ) ) );
	$contact_link = $contact ? '<a href="mailto:' . esc_attr( $contact ) . '">Contact the editorial team</a>' : 'contact the editorial team';
	ob_start();
	?>
	<section class="su-success-intake" aria-labelledby="su-success-intake-title">
		<div class="su-kicker">VERIFIED SUCCESS STORIES · TS &amp; AP</div>
		<h2 id="su-success-intake-title">మీ Success Story పంచుకోండి</h2>
		<p>మీ exam, job, scholarship లేదా career achievement గురించి నిజమైన అనుభవాన్ని పంపండి. ప్రతి వారం గరిష్ఠంగా మూడు stories మాత్రమే evidence review తర్వాత draft చేస్తాము.</p>
		<ul>
			<li>Official result, institution, employer లేదా public proof link ఇవ్వాలి.</li>
			<li>మీ పేరు, story, quote, photo మరియు public links publish చేయడానికి స్పష్టమైన consent అవసరం.</li>
			<li>Aadhaar, PAN, bank details, OTP, password లేదా private certificates upload చేయకండి.</li>
			<li>Form పంపినంత మాత్రాన publication లేదా selection guarantee కాదు. ప్రతి submission human reviewకి వెళ్తుంది.</li>
		</ul>
		<p><a class="su-button" href="<?php echo esc_url( $form_url ); ?>" target="_blank" rel="noopener noreferrer">Google Form open చేయండి →</a></p>
		<p class="su-muted">Photo rights, identity and result details verify చేసిన తర్వాత మాత్రమే articleలో links/attribution publish చేస్తాము. Correction అవసరమైతే <?php echo wp_kses_post( $contact_link ); ?>.</p>
	</section>
	<?php
	return (string) ob_get_clean();
}
add_shortcode( 'studentup_success_story_form', 'studentup_success_story_form_shortcode' );

/**
 * Keep a configured intake CTA on the Success Stories archive without
 * injecting a form into ordinary articles.
 */
function studentup_success_story_archive_cta( $description ) {
	if ( ! is_category( 'success-stories' ) ) {
		return $description;
	}
	return $description . studentup_success_story_form_shortcode();
}
add_filter( 'the_archive_description', 'studentup_success_story_archive_cta', 20 );
