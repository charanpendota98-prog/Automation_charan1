<?php
/**
 * v158 — Key-facts strip + HowTo schema (AEO).
 *
 * Rendu kuda **meta unte ne** vastayi. Data lekapote block ye raadu —
 * empty "—" cells or guessed numbers Google ki thin content signal,
 * readers ki kuda cheddha experience.
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Post lo unna real meta values matrame collect chestundi.
 *
 * @param int $post_id post id.
 * @return array label => value (only non-empty).
 */
function studentup_keyfacts_data( $post_id = 0 ) {
	$post_id = $post_id ? (int) $post_id : get_the_ID();
	$map     = array(
		'studentup_vacancies' => array( __( 'Vacancies', 'studentup' ), '📋' ),
		'studentup_qual'      => array( __( 'Qualification', 'studentup' ), '🎓' ),
		'studentup_salary'    => array( __( 'Salary', 'studentup' ), '💰' ),
		'studentup_last_date' => array( __( 'Last date', 'studentup' ), '🗓️' ),
	);

	$out = array();
	foreach ( $map as $key => $meta ) {
		$val = trim( (string) get_post_meta( $post_id, $key, true ) );
		if ( '' === $val ) {
			continue;
		}
		if ( 'studentup_last_date' === $key ) {
			$ts = strtotime( $val );
			if ( $ts ) {
				$val = date_i18n( 'd M Y', $ts );
			}
		}
		$out[] = array(
			'label' => $meta[0],
			'icon'  => $meta[1],
			'value' => $val,
		);
	}
	return $out;
}

/**
 * Key numbers strip — snippet-friendly plain text (spans, no tables).
 */
function studentup_keyfacts_box() {
	if ( ! is_singular( 'post' ) || ! studentup_opt( 'keyfacts', '1' ) ) {
		return;
	}
	$facts = studentup_keyfacts_data();
	if ( count( $facts ) < 2 ) {
		return; // okate fact unte strip ki value ledu.
	}
	?>
	<div class="su-keyfacts" aria-label="<?php esc_attr_e( 'Key details', 'studentup' ); ?>">
		<?php foreach ( $facts as $f ) : ?>
			<div class="su-kf">
				<span class="su-kf-i" aria-hidden="true"><?php echo esc_html( $f['icon'] ); ?></span>
				<span class="su-kf-l"><?php echo esc_html( $f['label'] ); ?></span>
				<strong class="su-kf-v"><?php echo esc_html( $f['value'] ); ?></strong>
			</div>
		<?php endforeach; ?>
	</div>
	<?php
}

/**
 * Content lo "How to apply" heading kinda unna <ol> nunchi steps teestundi.
 *
 * @param string $content post content.
 * @return array steps (plain text). 3 kanna thakkuva unte empty.
 */
function studentup_howto_steps( $content = '' ) {
	if ( '' === $content ) {
		$content = get_post_field( 'post_content', get_the_ID() );
	}
	/**
	 * Apply-section heading patterns. Theme PHP lo Telugu literals undakudadu
	 * (v73 rule) — extra languages ee filter dwara add cheyyandi.
	 *
	 * @param string $pattern regex alternation body.
	 */
	$su_apply = apply_filters( 'studentup_apply_heading_pattern', 'how\s+to\s+apply|apply\s+online|application\s+process' );

	if ( ! $content || ! preg_match( '~(' . $su_apply . ')~i', $content ) ) {
		return array();
	}

	// Apply heading taruvata unna first <ol> matrame.
	if ( ! preg_match(
		'~<h[2-4][^>]*>[^<]*(?:' . $su_apply . ')[^<]*</h[2-4]>(.*?)(?:<h[2-4]|$)~is',
		$content,
		$block
	) ) {
		return array();
	}
	if ( ! preg_match( '~<ol[^>]*>(.*?)</ol>~is', $block[1], $ol ) ) {
		return array();
	}
	if ( ! preg_match_all( '~<li[^>]*>(.*?)</li>~is', $ol[1], $items ) ) {
		return array();
	}

	$steps = array();
	foreach ( $items[1] as $raw ) {
		$text = trim( wp_strip_all_tags( $raw ) );
		if ( strlen( $text ) >= 8 ) {
			$steps[] = $text;
		}
	}
	return count( $steps ) >= 3 ? array_slice( $steps, 0, 12 ) : array();
}

/**
 * HowTo JSON-LD — nijamaina steps unte ne. Fake schema = manual action risk.
 */
function studentup_howto_schema() {
	if ( is_admin() || is_feed() || ! is_singular( 'post' ) || ! studentup_opt( 'keyfacts', '1' ) ) {
		return;
	}
	$steps = studentup_howto_steps();
	if ( count( $steps ) < 3 ) {
		return;
	}

	$list = array();
	$i    = 0;
	foreach ( $steps as $step ) {
		$i++;
		$list[] = array(
			'@type'    => 'HowToStep',
			'position' => $i,
			'text'     => wp_html_excerpt( $step, 300, '' ),
		);
	}

	$node = array(
		'@context' => 'https://schema.org',
		'@type'    => 'HowTo',
		'@id'      => get_permalink() . '#howto',
		'name'     => wp_html_excerpt( get_the_title(), 110, '' ),
		'step'     => $list,
	);

	echo "\n<script type=\"application/ld+json\">" .
		wp_json_encode( $node, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE ) .
		"</script>\n"; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- wp_json_encode output.
}
add_action( 'wp_head', 'studentup_howto_schema', 22 );
