<?php
/**
 * v64: Auto Table of Contents (Table of contents) — H2/H3 nunchi jump links.
 *
 * Bot rase posts lo TOC already untundi (autoblog/rm100.py). Idi manual ga
 * rayabadina posts ki + bot content lo TOC lekapote. Rank Math readability
 * ki, Google jump-to-section snippet ki, reader UX ki useful.
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Content lo H2/H3 ki ids + TOC ni prepend cheyyadam (single post mattrame).
 */
function studentup_content_toc( $content ) {
	if ( is_admin() || is_feed() || ! is_singular( 'post' ) ) {
		return $content;
	}
	if ( ! studentup_opt( 'toc', '1' ) ) {
		return $content;
	}
	if ( false !== strpos( $content, 'su-toc' ) || false !== strpos( $content, 'studentup-disable-toc' ) ) {
		return $content;
	}
	if ( ! preg_match_all( '/<h([23])([^>]*)>(.*?)<\/h\1>/s', $content, $m, PREG_SET_ORDER ) ) {
		return $content;
	}
	if ( count( $m ) < 3 ) {
		return $content;
	}
	$used  = array();
	$items = array();
	foreach ( $m as $h ) {
		$inner = trim( wp_strip_all_tags( $h[3] ) );
		if ( '' === $inner ) {
			continue;
		}
		if ( preg_match( '/id=["\']([^"\']+)["\']/', $h[2], $idm ) ) {
			$id = $idm[1];
		} else {
			$id = sanitize_title( $inner );
			if ( '' === $id ) {
				$id = 'sec-' . ( count( $items ) + 1 );
			}
			$base = $id;
			$i    = 2;
			while ( in_array( $id, $used, true ) ) {
				$id = $base . '-' . $i;
				$i++;
			}
			$content = str_replace( $h[0], '<h' . $h[1] . $h[2] . ' id="' . esc_attr( $id ) . '">' . $h[3] . '</h' . $h[1] . '>', $content );
		}
		$used[]  = $id;
		$items[] = '<li><a href="#' . esc_attr( $id ) . '">' . esc_html( $inner ) . '</a></li>';
	}
	if ( count( $items ) < 3 ) {
		return $content;
	}
	$toc = '<div class="su-toc" role="navigation" aria-label="Table of contents">'
		. '<div class="su-toc-title">Table of contents</div><ol>'
		. implode( '', array_slice( $items, 0, 12 ) )
		. '</ol></div>';
	// first paragraph tarvata pettali (ledu ante modatlo)
	if ( preg_match( '/<p[^>]*>.*?<\/p>/s', $content, $pm ) ) {
		return str_replace( $pm[0], $pm[0] . "\n" . $toc, $content );
	}
	return $toc . $content;
}
add_filter( 'the_content', 'studentup_content_toc', 12 );
