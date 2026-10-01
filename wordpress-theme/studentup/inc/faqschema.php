<?php
/**
 * Interactive FAQ Accordion & FAQPage JSON-LD Rich Snippet Schema.
 *
 * Provides FAQPage schema for Google search rich snippets and interactive accordion.
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Get standard FAQs for the current post.
 *
 * @param int $post_id Post ID.
 * @return array<int,array<string,string>>
 */
function studentup_get_post_faqs( $post_id = 0 ) {
	$post_id = $post_id ? $post_id : get_the_ID();
	if ( ! $post_id ) {
		return array();
	}

	$title     = get_the_title( $post_id );
	$vacancies = (string) get_post_meta( $post_id, 'studentup_vacancies', true );
	$last_date = (string) get_post_meta( $post_id, 'studentup_last_date', true );
	$qual      = (string) get_post_meta( $post_id, 'studentup_qual', true );
	$apply_url = (string) get_post_meta( $post_id, 'studentup_apply_url', true );
	$salary    = (string) get_post_meta( $post_id, 'studentup_salary', true );

	/*
	 * v175: context-aware FAQs. Puratham — hall-ticket download post meeda
	 * "last date to apply for X?" adigite wrong (apply cheyyaledu, download
	 * chestunnadu). studentup_apply_cta() kind prakaram questions maarutayi.
	 */
	$cta = function_exists( 'studentup_apply_cta' ) ? studentup_apply_cta( $post_id ) : array( 'label' => 'Apply online', 'kind' => 'job' );
	$kind = $cta['kind'];

	$faqs = array();
	$last_pretty = $last_date ? wp_date( 'd M Y', strtotime( $last_date . ' 12:00:00' ) ) : '';

	if ( 'hallticket' === $kind ) {
		if ( $last_date ) {
			$faqs[] = array(
				'q' => 'What is the last date to download the hall ticket?',
				'a' => 'The hall ticket download link is available until ' . esc_html( $last_pretty ) . '. Download early to avoid last-minute server load.',
			);
		}
		if ( $apply_url ) {
			$faqs[] = array(
				'q' => 'Where can I download my hall ticket?',
				'a' => 'Download it from the official portal only. Use the official link given in this article — never third-party sites.',
			);
		}
		$faqs[] = array(
			'q' => 'What details do I need to download the hall ticket?',
			'a' => 'Usually your registration number and date of birth (or password). Keep the application form copy ready.',
		);
		return $faqs;
	}

	if ( 'result' === $kind ) {
		if ( $apply_url ) {
			$faqs[] = array(
				'q' => 'Where can I check my result?',
				'a' => 'Check your result on the official website only. Use the official result link given in this article.',
			);
		}
		if ( $last_date ) {
			$faqs[] = array(
				'q' => 'Till when is the result link active?',
				'a' => 'The link is expected to be available until ' . esc_html( $last_pretty ) . '. Save a copy of your result for future reference.',
			);
		}
		$faqs[] = array(
			'q' => 'What should I do after checking my result?',
			'a' => 'If you qualify, check the next-stage instructions (interview/document verification) on the official website and keep your certificates ready.',
		);
		return $faqs;
	}

	if ( $last_date ) {
		$faqs[] = array(
			'q' => 'What is the last date to apply for ' . esc_html( $title ) . '?',
			'a' => 'The last date to submit online application is ' . esc_html( $last_pretty ) . '. Candidates are advised to apply early.',   // v175: human date
		);
	}

	if ( $vacancies ) {
		$faqs[] = array(
			'q' => 'How many total vacancies are available in this recruitment?',
			'a' => 'As per the official notification, a total of ' . esc_html( $vacancies ) . ' posts will be filled.',
		);
	}

	if ( $qual ) {
		$faqs[] = array(
			'q' => 'What is the minimum qualification required?',
			'a' => 'Candidates must possess ' . esc_html( studentup_qual_pretty( $qual ) ) . ' or equivalent from a recognized board or university.',   // v175: human labels
		);
	}

	if ( $salary ) {
		$faqs[] = array(
			'q' => 'What is the monthly pay scale / salary for this post?',
			'a' => 'As per government pay rules, the approximate monthly salary is ' . esc_html( $salary ) . '.',
		);
	}

	$faqs[] = array(
		'q' => 'How can I apply online for this recruitment?',
		'a' => 'Eligible candidates can fill out the online application on the official recruitment portal and upload required certificates before the deadline.',
	);

	return $faqs;
}

/**
 * Render FAQ Accordion Box in Article.
 *
 * @return void
 */
function studentup_faq_box() {
	if ( ! is_singular( 'post' ) || ! studentup_opt( 'faq_schema', '1' ) ) {
		return;
	}

	$faqs = studentup_get_post_faqs();
	if ( empty( $faqs ) ) {
		return;
	}

	?>
	<section class="su-faq-section" id="faqs" aria-labelledby="su-faq-title">
		<div class="su-faq-head">
			<span class="su-faq-badge" aria-hidden="true"><?php echo studentup_ui_icon( 'help', 13 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> FAQ</span>
			<h2 id="su-faq-title" class="su-faq-title">Frequently Asked Questions</h2>
		</div>
		<div class="su-faq-list">
			<?php foreach ( $faqs as $i => $item ) : ?>
				<?php $open_attr = ( 0 === $i ) ? ' open' : ''; ?>
				<details class="su-faq-item"<?php echo esc_attr( $open_attr ); ?>>
					<summary class="su-faq-question">
						<span><?php echo esc_html( $item['q'] ); ?></span>
						<span class="su-faq-arrow" aria-hidden="true">▾</span>
					</summary>
					<div class="su-faq-answer">
						<p><?php echo esc_html( $item['a'] ); ?></p>
					</div>
				</details>
			<?php endforeach; ?>
		</div>
	</section>
	<?php
}

/**
 * Inject Google JSON-LD FAQPage Schema in wp_head.
 *
 * @return void
 */
function studentup_faq_schema() {
	if ( ! is_singular( 'post' ) || ! studentup_opt( 'faq_schema', '1' ) ) {
		return;
	}

	$faqs = studentup_get_post_faqs();
	if ( count( $faqs ) < 2 ) {
		return;
	}

	$elements = array();
	foreach ( $faqs as $item ) {
		$elements[] = array(
			'@type'          => 'Question',
			'name'           => $item['q'],
			'acceptedAnswer' => array(
				'@type' => 'Answer',
				'text'  => $item['a'],
			),
		);
	}

	$schema = array(
		'@context'   => 'https://schema.org',
		'@type'      => 'FAQPage',
		'mainEntity' => $elements,
	);

	echo '<script type="application/ld+json">'
		. wp_json_encode( $schema, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES )
		. '</script>' . "\n";
}
add_action( 'wp_head', 'studentup_faq_schema', 12 );
