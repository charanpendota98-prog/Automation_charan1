<?php
/**
 * v64: Author box (E-E-A-T) + last-updated line.
 *
 * Google E-E-A-T (Experience, Expertise, Authoritativeness, Trust) ki
 * "ee content evaru rasaru, eppudu verify chesaru" undali — adi idi.
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * "చివరిగా అప్డేట్" line (published != modified unte mattrame).
 */
function studentup_last_updated() {
	$modified = get_the_modified_time( 'U' );
	$posted   = get_the_time( 'U' );
	if ( ! $modified || ( $modified - $posted ) < DAY_IN_SECONDS ) {
		return '';
	}
	return sprintf(
		'<span class="su-updated">♻️ చివరిగా అప్డేట్: %s</span>',
		esc_html( get_the_modified_date() )
	);
}

/**
 * Editorial team box (E-E-A-T + corrections email + editorial policy).
 */
function studentup_author_box() {
	$name  = (string) studentup_opt( 'author_name', 'StudentUp ఎడిటోరియల్ టీమ్' );
	$bio   = (string) studentup_opt( 'author_bio', 'అధికారిక నోటిఫికేషన్లు, ప్రభుత్వ వెబ్‌సైట్ల నుంచి ధృవీకరించి తెలుగులో రాస్తాము.' );
	$email = studentup_contact_email();
	$pol   = get_page_by_path( 'editorial-policy' );
	?>
	<div class="su-author" itemscope itemtype="https://schema.org/Organization">
		<div class="su-author-avatar" aria-hidden="true">📝</div>
		<div>
			<strong itemprop="name"><?php echo esc_html( $name ); ?></strong>
			<p itemprop="description"><?php echo esc_html( $bio ); ?></p>
			<p class="su-author-links">
				<span>✅ అధికారిక మూలాలతో ధృవీకరణ</span>
				<?php if ( $email ) : ?>
					<span>✉️ తప్పులు తెలియజేయండి:
						<a href="mailto:<?php echo esc_attr( $email ); ?>"><?php echo esc_html( $email ); ?></a></span>
				<?php endif; ?>
				<?php if ( $pol ) : ?>
					<span>📘 <a href="<?php echo esc_url( get_permalink( $pol ) ); ?>">ఎడిటోరియల్ పాలసీ</a></span>
				<?php endif; ?>
			</p>
		</div>
	</div>
	<?php
}
