<?php
/**
 * v201: “Latest Notifications” sliding track — PREVIEW ↔ LIVE PARITY.
 *
 * Enduku ee file: `preview/worldclass/index.html` (owner ki live preview lo
 * kanipinche demo) lo hero kinda oka “Latest Notifications” card slider undi.
 * Aa CSS (`worldclass.css` lo `.su-slider-*` / `.su-scard*`) theme ki ship
 * ayyindi, kaani **aa markup ni output chese PHP eppudu raledu** — anduke
 * zip upload chesina taruvata live lo aa section kanipinchaledu.
 * Ippudu idi nijamaina posts nunchi ade markup generate chestundi:
 *
 *   ticker → hero → Latest Notifications slider → most searched → …
 *
 * Data ippudu fake kaadu (demo lo hardcoded cards unnayi): prathi card =
 * okka published post — category · exam label, vacancies, qualification,
 * last date, apply link, WhatsApp share. Deadline ≤14 rojulu unte pill,
 * published inside 48 hours → "New" pill.
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Exam shorthand for the card head (“SSC CHSL 2026 Notification …” → “SSC CHSL”).
 *
 * @param string $title Post title.
 * @return string Short label ('' when nothing sensible).
 */
function studentup_slider_exam( $title ) {
	$title = trim( wp_strip_all_tags( (string) $title ) );
	if ( '' === $title ) {
		return '';
	}
	// "SSC CHSL 2026 …" / "TSPSC Group 2 2026 …" → year ki mundu unna 1–2 words.
	if ( preg_match( '/^([A-Z][A-Za-z&.\-]{1,12}(?:\s+[A-Za-z][A-Za-z&.\-]{1,12})?)\s+20\d\d/u', $title, $m ) ) {
		return trim( $m[1] );
	}
	if ( preg_match( '/^([A-Z][A-Za-z&.\-]{1,12})/u', $title, $m ) ) {
		return trim( $m[1] );
	}
	return '';
}

/**
 * Card head label — “Central Govt Jobs · SSC” (category · exam).
 *
 * @param int $post_id Post ID.
 * @return string
 */
function studentup_slider_label( $post_id ) {
	$cats  = get_the_category( $post_id );
	$label = $cats ? $cats[0]->name : __( 'Latest update', 'studentup' );
	$exam  = studentup_slider_exam( get_the_title( $post_id ) );
	if ( '' === $exam || false !== stripos( $label, $exam ) ) {
		return $label;
	}
	return $label . ' · ' . $exam;
}

/**
 * Card pill — deadline pill (≤14 days) / “New” (<48h) / '' (nothing).
 *
 * @param int $post_id Post ID.
 * @return string Escaped HTML.
 */
function studentup_slider_pill( $post_id ) {
	$last = function_exists( 'studentup_opportunity_last_date' ) ? studentup_opportunity_last_date( $post_id ) : '';
	$left = ( '' !== $last && function_exists( 'studentup_opportunity_days_left' ) ) ? studentup_opportunity_days_left( $last ) : null;

	if ( null !== $left && $left >= 0 && $left <= 14 ) {
		$text = ( 0 === $left )
			? __( 'Last day today', 'studentup' )
			/* translators: %s: number of days left. */
			: sprintf( __( '%s Days Left', 'studentup' ), number_format_i18n( $left ) );
		return '<span class="su-scard-urgent">⏳ ' . esc_html( $text ) . '</span>';
	}

	$published = (int) get_post_time( 'U', true, $post_id );
	$hours     = (int) floor( ( (int) current_time( 'timestamp' ) - $published ) / HOUR_IN_SECONDS ); // phpcs:ignore WordPress.DateTime.CurrentTimeTimestamp
	if ( $hours >= 0 && $hours < 48 ) {
		return '<span class="su-scard-hot">🔥 ' . esc_html__( 'New', 'studentup' ) . '</span>';
	}
	return '';
}

/**
 * Card meta row — vacancies · qualification · last date (only real meta).
 *
 * @param int $post_id Post ID.
 * @return string Escaped HTML ('' when no data).
 */
function studentup_slider_meta( $post_id ) {
	$out = '';

	$vac = trim( (string) get_post_meta( $post_id, 'studentup_vacancies', true ) );
	if ( '' !== $vac && preg_match( '/\d/', $vac ) ) {
		if ( ! preg_match( '/post|vacanc/i', $vac ) ) {
			/* translators: %s: vacancy number. */
			$vac = sprintf( __( '%s Posts', 'studentup' ), $vac );
		}
		$out .= '<span class="su-scard-vac">' . esc_html( $vac ) . '</span>';
	}

	if ( function_exists( 'studentup_qual_labels' ) ) {
		$quals = studentup_qual_labels( $post_id, 1 );
		if ( $quals ) {
			$out .= '<span>' . esc_html( (string) reset( $quals ) ) . '</span>';
		}
	}

	$last = function_exists( 'studentup_opportunity_last_date' ) ? studentup_opportunity_last_date( $post_id ) : '';
	if ( '' !== $last ) {
		$stamp = strtotime( $last . ' 12:00:00' );
		if ( $stamp ) {
			$out .= '<span class="su-scard-date">' . studentup_ui_icon( 'clock', 12 )
				. ' ' . esc_html( date_i18n( 'd M', $stamp ) ) . '</span>';
		}
	}

	return ( '' === $out ) ? '' : '<div class="su-scard-meta">' . $out . '</div>';
}

/**
 * The sliding track — phone lo horizontal scroll + auto-slide, laptop lo same.
 *
 * Front page lo mattrame (demo page kuda home ne). Posts lekapote emanu
 * render cheyyadu — empty section ledu.
 *
 * @param array $args limit (default 10) · heading.
 */
function studentup_latest_notifications( $args = array() ) {
	if ( ! is_front_page() || is_paged() ) {
		return;
	}

	$args  = wp_parse_args( $args, array( 'limit' => 10, 'heading' => __( 'Latest Notifications', 'studentup' ) ) );
	$limit = max( 1, min( 20, (int) $args['limit'] ) );

	$posts = get_posts(
		array(
			'post_type'           => 'post',
			'post_status'         => 'publish',
			'posts_per_page'      => $limit,
			'no_found_rows'       => true,
			'ignore_sticky_posts' => true,
		)
	);
	if ( ! $posts ) {
		return;
	}
	?>
	<div class="wrap">
		<section class="su-slider-sec" aria-label="<?php esc_attr_e( 'Latest Jobs Sliding Track', 'studentup' ); ?>">
			<div class="su-slider-head">
				<div class="su-slider-title-wrap">
					<span class="su-slider-badge"><i aria-hidden="true"></i> <?php esc_html_e( 'LIVE', 'studentup' ); ?></span>
					<h2><?php echo esc_html( $args['heading'] ); ?></h2>
				</div>
				<div class="su-slider-ctrls">
					<button type="button" class="su-sbtn" id="su-track-prev" aria-label="<?php esc_attr_e( 'Slide Left', 'studentup' ); ?>">‹</button>
					<button type="button" class="su-sbtn" id="su-track-pause" aria-label="<?php esc_attr_e( 'Pause or play sliding track', 'studentup' ); ?>">⏸</button>
					<button type="button" class="su-sbtn" id="su-track-next" aria-label="<?php esc_attr_e( 'Slide Right', 'studentup' ); ?>">›</button>
				</div>
			</div>

			<div class="su-slider-viewport" id="su-jobs-track-wrap" tabindex="0" role="region"
				aria-label="<?php esc_attr_e( 'Scrolling latest jobs carousel', 'studentup' ); ?>">
				<div class="su-slider-track" id="su-jobs-track">
					<?php
					foreach ( $posts as $post ) :
						$link  = get_permalink( $post );
						$title = get_the_title( $post );
						$label = studentup_slider_label( $post->ID );
						$share = $title . ' — ' . $link;
						?>
						<div class="su-scard" data-cat="<?php echo esc_attr( studentup_card_accent( $label ) ); ?>">
							<div class="su-scard-head">
								<span class="su-scard-tag"><?php echo esc_html( $label ); ?></span>
								<?php echo studentup_slider_pill( $post->ID ); // phpcs:ignore WordPress.Security.EscapeOutput -- escaped inside. ?>
							</div>
							<h3><a href="<?php echo esc_url( $link ); ?>"><?php echo esc_html( $title ); ?></a></h3>
							<?php echo studentup_slider_meta( $post->ID ); // phpcs:ignore WordPress.Security.EscapeOutput -- escaped inside. ?>
							<div class="su-scard-acts-row">
								<a class="su-scard-act" href="<?php echo esc_url( $link ); ?>">
									<span><?php esc_html_e( 'Full details & Apply', 'studentup' ); ?></span>
									<span aria-hidden="true">→</span>
								</a>
								<a class="su-card-wa" href="<?php echo esc_url( 'https://wa.me/?text=' . rawurlencode( $share ) ); ?>"
									target="_blank" rel="noopener" title="<?php esc_attr_e( 'Share on WhatsApp', 'studentup' ); ?>">
									<?php echo studentup_social_icon( 'whatsapp', 12 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG. ?>
									<?php esc_html_e( 'Share', 'studentup' ); ?>
								</a>
							</div>
						</div>
					<?php endforeach; ?>
				</div>
			</div>
		</section>
	</div>
	<?php
}
