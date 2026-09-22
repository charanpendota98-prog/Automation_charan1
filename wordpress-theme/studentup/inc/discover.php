<?php
/**
 * v94: DISCOVER + CORE WEB VITALS hardening (theme 1.9.5).
 *
 * Enduku (Google Discover / News + CWV):
 *   1) **Discover large-card image**: Google Discover kevalam **1200px+ wide**
 *      images unna pages ni pedda card ga chupistundi. Theme ippati varaku
 *      640×360 (`studentup-card`) mattrame register chesindi — so Discover pedda
 *      card ki eligibility ledu. Ippudu 1200×675 register avutundi (bot kuda
 *      ade size lo featured image generate chestundi — 1200×675).
 *   2) **og:image dimensions**: `og:image:width` / `og:image:height` / `og:image:alt`
 *      pampadam valla Discover + social unfurl correct ga pedda image theesukuntayi
 *      (dimension teliyakapote crawler image ni download chesi measure cheyyali —
 *      konni cases lo adi skip avutundi).
 *   3) **CLS (Core Web Vitals)**: content images ki `width`/`height` attribute
 *      pettadam valla browser mundhe space reserve chestundi → layout shift 0.
 *      (Bot side `post_gate` ide check chestundi, kaani theme uploaded images ki
 *      idi apply avvaledu — ippudu apply avutundi.)
 *   4) **INP**: scroll listeners `passive` + ad JS idle varaku aapadam (already
 *      perf.php lo) — ikkada interactive elements ki `touch-action` hint isthamu
 *      (tap delay thagginchadam → INP improve).
 *
 * Note: Rank Math unte adi OG tags output chestundi — ee file aa case lo
 * duplicate raakunda **mattrame** dimension attributes add chestundi (filter),
 * kotha og:image tag eppudu create cheyyadu.
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/** Discover/News large-card image size (Google minimum 1200px wide). */
function studentup_discover_image_size() {
	add_image_size( 'studentup-discover', 1200, 675, true );
}
add_action( 'after_setup_theme', 'studentup_discover_image_size', 11 );

/**
 * Ee attachment ki 1200px+ version unda? (lekapote `full`).
 *
 * @param int $post_id Post ID.
 * @return string size name ('' = ledu)
 */
function studentup_big_image_size( $post_id = 0 ) {
	$post_id = $post_id ? (int) $post_id : (int) get_the_ID();
	if ( ! $post_id || ! has_post_thumbnail( $post_id ) ) {
		return '';
	}
	$id = get_post_thumbnail_id( $post_id );
	foreach ( array( 'studentup-discover', 'full' ) as $size ) {
		$src = wp_get_attachment_image_src( $id, $size );
		if ( $src && isset( $src[1] ) && (int) $src[1] >= 1200 ) {
			return $size;
		}
	}
	return '';
}

/**
 * Rank Math / Yoast unte — vaati OG image ni 1200px+ version ki matrame marchutundi.
 *
 * Idempotent + safe: size dorakakapote original ni as-is return chestundi
 * (eppudu tag ni theesi, duplicate create cheyyadu).
 *
 * @param string $url  Original OG image URL.
 * @param mixed  $post Post object (plugin batti).
 * @return string
 */
function studentup_og_image_big( $url, $post = null ) {
	$post_id = 0;
	if ( is_object( $post ) && isset( $post->ID ) ) {
		$post_id = (int) $post->ID;
	} elseif ( is_numeric( $post ) ) {
		$post_id = (int) $post;
	}
	if ( ! $post_id ) {
		$post_id = (int) get_the_ID();
	}
	$size = studentup_big_image_size( $post_id );
	if ( ! $size ) {
		return $url;   // 1200px+ ledu — original ne vaduthamu (broken image vaddhu)
	}
	$src = wp_get_attachment_image_src( get_post_thumbnail_id( $post_id ), $size );
	return $src && ! empty( $src[0] ) ? $src[0] : $url;
}
add_filter( 'rank_math/opengraph/facebook/image', 'studentup_og_image_big', 10, 2 );
add_filter( 'wpseo_opengraph_image', 'studentup_og_image_big', 10, 1 );

/**
 * Discover + CWV: OG image dimensions + alt (Rank Math lekha unna vadhu —
 * duplicate raakunda `! defined('RANK_MATH_VERSION')` gate).
 */
function studentup_og_image_dims() {
	if ( is_admin() || is_feed() || ! is_singular() ) {
		return;
	}
	if ( ! has_post_thumbnail() ) {
		return;
	}
	$size = studentup_big_image_size() ? studentup_big_image_size() : 'large';
	$src  = wp_get_attachment_image_src( get_post_thumbnail_id(), $size );
	if ( ! $src ) {
		return;
	}
	echo '<meta property="og:image:width" content="' . (int) $src[1] . '">' . "\n";
	echo '<meta property="og:image:height" content="' . (int) $src[2] . '">' . "\n";
	$alt = get_post_meta( get_post_thumbnail_id(), '_wp_attachment_image_alt', true );
	$alt = $alt ? $alt : wp_strip_all_tags( get_the_title() );
	if ( $alt ) {
		echo '<meta property="og:image:alt" content="' . esc_attr( $alt ) . '">' . "\n";
	}
}
add_action( 'wp_head', 'studentup_og_image_dims', 7 );

/**
 * CLS: content images ki width/height attribute (browser space reserve chestundi).
 *
 * Idi `studentup_img_attrs` (perf.php) ki todu — akkada `decoding` undi,
 * ikkada dimensions. Rendu okate filter ki add avutayi, so conflict ledu.
 *
 * @param array $attr       Image attributes.
 * @param mixed $attachment Attachment.
 * @param mixed $size       Requested size.
 * @return array
 */
function studentup_img_dims( $attr, $attachment, $size ) {
	if ( is_admin() || ! empty( $attr['width'] ) && ! empty( $attr['height'] ) ) {
		return $attr;
	}
	$id = is_object( $attachment ) && isset( $attachment->ID ) ? (int) $attachment->ID : 0;
	if ( ! $id ) {
		$id = (int) get_the_ID();
	}
	$src = $id ? wp_get_attachment_image_src( $id, $size ) : false;
	if ( $src && isset( $src[1], $src[2] ) ) {
		$attr['width']  = (int) $src[1];
		$attr['height'] = (int) $src[2];
	}
	return $attr;
}
add_filter( 'wp_get_attachment_image_attributes', 'studentup_img_dims', 9, 3 );

/**
 * INP: interactive elements ki tap-delay thagginchadam (touch-action hint).
 *
 * Mobile INP lo `touch-action: manipulation` tap delay (~300ms double-tap zoom
 * wait) ni theesestundi — buttons/links fast ga respond avutayi. CSS lo
 * pettadam better (blocking render ledu) anduke inline style — heavy CSS
 * injection kaadu.
 */
function studentup_touch_hint_css() {
	if ( is_admin() ) {
		return;
	}
	echo '<style id="su-inp-hint">a,button,input,select,textarea,.chip,.su-save-btn{touch-action:manipulation}</style>' . "\n";
}
add_action( 'wp_head', 'studentup_touch_hint_css', 20 );
