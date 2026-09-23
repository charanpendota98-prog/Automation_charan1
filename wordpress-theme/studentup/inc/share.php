<?php
/**
 * v98 — VIRAL SHARE ENGINE (free reach lever)
 *
 * Kanukkunna nijamaina problems (v97 varaku):
 *   1) Share buttons **post chivara MATRAME** unnayi. Mobile lo 60–70% readers
 *      akkadi varaku scroll cheyyaru → share option vaallaki EPPUDU kanipinchadu.
 *      Share = free reach. Idi pedda miss.
 *   2) WhatsApp share text = bare "title — URL". Group lo adi boring ga
 *      kanipistundi → tap rate takkuva. Students ki **em undo** (last date,
 *      vacancies) cheppithe tap rate chala perugutundi.
 *   3) Mobile browsers lo **native share sheet** (navigator.share) vadaledu —
 *      adi vunte reader tana own apps (WhatsApp/Insta/SMS) ki 1 tap lo
 *      pampochu. Idi free ga vachhe biggest mobile lever.
 *
 * Fix (anni free, API/service avasaram ledu):
 *   · `studentup_share_bar()` — compact share row, **content lopala** (first
 *     H2 tarvata) inject avutundi → prathi reader ki kanipistundi.
 *   · Rich WhatsApp/Telegram text: title + last date (unte) + link.
 *   · Native share button — `navigator.share` support unte MATRAME kanipistundi
 *     (JS feature-detect; lekapothe hidden → broken button raadu).
 *   · Anni links `noopener` + escaped. Tracking/pixel LEDU (privacy-safe).
 *
 * Policy note: idi **organic sharing** ni sulabham chestundi. Fake/auto
 * sharing, bot clicks — EMI cheyyamu. AdSense ki idi 100% safe.
 *
 * @package StudentUp
 */

defined( 'ABSPATH' ) || exit;

/**
 * Share text lo pettadaniki deadline/hook line (unte).
 *
 * Bot `su_deadline` meta rastundi (v40+). Ledante khali string — fake
 * urgency EPPUDU create cheyyamu.
 *
 * @param int $post_id Post ID.
 * @return string Escaped-safe plain text (URL-encode caller chestadu).
 */
function studentup_share_hook( $post_id = 0 ) {
	$post_id = $post_id ? (int) $post_id : get_the_ID();
	if ( ! $post_id ) {
		return '';
	}
	$raw = get_post_meta( $post_id, 'su_deadline', true );
	if ( ! $raw ) {
		return '';
	}
	$ts = strtotime( (string) $raw );
	if ( ! $ts ) {
		return '';
	}
	// Deadline dhatipoyindi aithe urgency chupinchakudadu (misleading).
	$today = (int) current_time( 'timestamp' );
	if ( $ts < strtotime( 'today', $today ) ) {
		return '';
	}
	$days = (int) floor( ( $ts - strtotime( 'today', $today ) ) / DAY_IN_SECONDS );
	if ( 0 === $days ) {
		return 'Last date: TODAY';
	}
	if ( $days <= 7 ) {
		/* translators: %d: days left. */
		return sprintf( 'Last date in %d day(s)', $days );
	}
	return 'Last date: ' . date_i18n( 'd M Y', $ts );
}

/**
 * WhatsApp/Telegram ki rich share text (bare URL kaadu).
 *
 * @param int $post_id Post ID.
 * @return string Plain text (raw — caller rawurlencode chestadu).
 */
function studentup_share_text( $post_id = 0 ) {
	$post_id = $post_id ? (int) $post_id : get_the_ID();
	$title   = wp_strip_all_tags( get_the_title( $post_id ) );
	$hook    = studentup_share_hook( $post_id );
	$text    = $title;
	if ( $hook ) {
		$text .= ' — ' . $hook;
	}
	return $text;
}

/**
 * Share bar markup.
 *
 * @param string $place 'inline' (content lopala) leda 'bottom'.
 * @return string HTML.
 */
function studentup_share_bar( $place = 'inline' ) {
	$post_id = get_the_ID();
	if ( ! $post_id ) {
		return '';
	}
	$url   = get_permalink( $post_id );
	$text  = studentup_share_text( $post_id );
	$share = rawurlencode( $text . ' ' . $url );
	$place = ( 'bottom' === $place ) ? 'bottom' : 'inline';

	$wa = 'https://wa.me/?text=' . $share;
	$tg = 'https://t.me/share/url?url=' . rawurlencode( $url )
		. '&text=' . rawurlencode( $text );

	$out  = '<div class="su-sharebar su-sharebar-' . esc_attr( $place ) . '"'
		. ' data-su-share data-url="' . esc_url( $url ) . '"'
		. ' data-title="' . esc_attr( $text ) . '">';
	$out .= '<span class="su-sharebar-t">' . esc_html__( 'Share this with your friends', 'studentup' ) . '</span>';
	$out .= '<span class="su-sharebar-btns">';
	$out .= '<a class="su-sb su-sb-wa" href="' . esc_url( $wa ) . '" target="_blank" rel="noopener nofollow">'
		. studentup_social_icon( 'whatsapp', 15 ) . '<span>WhatsApp</span></a>';
	$out .= '<a class="su-sb su-sb-tg" href="' . esc_url( $tg ) . '" target="_blank" rel="noopener nofollow">'
		. studentup_social_icon( 'telegram', 15 ) . '<span>Telegram</span></a>';
	// Native sheet — JS feature-detect tarvata MATRAME chupistam.
	$out .= '<button type="button" class="su-sb su-sb-native" data-su-share-native hidden>'
		. studentup_social_icon( 'link', 14 ) . '<span>' . esc_html__( 'More', 'studentup' ) . '</span></button>';
	$out .= '<button type="button" class="su-sb su-sb-copy su-copy" data-url="' . esc_url( $url ) . '">'
		. studentup_social_icon( 'link', 14 ) . '<span>' . esc_html__( 'Copy link', 'studentup' ) . '</span></button>';
	$out .= '</span></div>';
	return $out;
}

/**
 * Content lopala share bar inject — modati H2 tarvata.
 *
 * Enduku modati H2 tarvata: reader intro chadivi "idi naaku kavalsinde" ani
 * decide chesina point adi. Akkada share bar pettithe tap rate ekkuva.
 * Join strip (v96) ki **collide avvakunda** — adi already unte, daani tarvata
 * vastundi (rendu vaerve blocks: join = subscribe, share = reach).
 *
 * @param string $content Post content.
 * @return string
 */
function studentup_inject_share_bar( $content ) {
	if ( ! is_singular( 'post' ) || ! in_the_loop() || ! is_main_query() ) {
		return $content;
	}
	if ( '0' === (string) studentup_opt( 'share_inline', '1' ) ) {
		return $content;
	}
	// Idempotent: already unte malli add cheyyakudadu.
	if ( false !== strpos( $content, 'su-sharebar-inline' ) ) {
		return $content;
	}
	$bar = studentup_share_bar( 'inline' );
	if ( '' === $bar ) {
		return $content;
	}
	// Modati </h2> tarvata insert (bot quick-answer card ni skip chestundi —
	// adi h2 kaadu). H2 ye lekapothe content chivara.
	$pos = stripos( $content, '</h2>' );
	if ( false === $pos ) {
		return $content . $bar;
	}
	$pos += 5;
	// Aa H2 tarvata vachhe modati paragraph tarvata pedite inka natural ga
	// untundi (heading ki venakane button block awkward).
	$after = substr( $content, $pos );
	$pp    = stripos( $after, '</p>' );
	if ( false !== $pp && $pp < 1200 ) {
		$pos += $pp + 4;
	}
	return substr( $content, 0, $pos ) . $bar . substr( $content, $pos );
}
add_filter( 'the_content', 'studentup_inject_share_bar', 14 );
