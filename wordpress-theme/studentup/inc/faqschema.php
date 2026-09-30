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

	$faqs = array();

	if ( $last_date ) {
		$faqs[] = array(
			'q' => 'What is the last date to apply for ' . esc_html( $title ) . '?',
			'a' => 'The last date to submit online application is ' . esc_html( $last_date ) . '. Candidates are advised to apply early.',
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
			'a' => 'Candidates must possess ' . esc_html( $qual ) . ' or equivalent from a recognized board or university.',
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
