<?php
/**
 * Breaking News navigation. It uses only fresh, verified TS/AP state or
 * district items from the radar feed; there is no latest-post fallback.
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Breaking nav items — verified local-news feed only.
 *
 * @param int $limit max items.
 * @return array<int,array<string,string>>
 */
function studentup_breaking_nav_items( $limit = 5 ) {
	$limit = max( 1, min( 8, (int) $limit ) );
	if ( ! function_exists( 'studentup_breaking_items' ) ) {
		return array();
	}
	$out = array();
	foreach ( studentup_breaking_items( $limit ) as $it ) {
		$place = 'TS' === $it['state'] ? 'Telangana' : 'Andhra Pradesh';
		if ( 'district' === $it['type'] && $it['district'] ) {
			$place .= ' · ' . $it['district'];
		}
		$ago = function_exists( 'studentup_ago' ) ? studentup_ago( (string) $it['time'] ) : '';
		$out[] = array(
			'title' => (string) $it['title'],
			'url'   => (string) $it['link'],
			'meta'  => trim( implode( ' · ', array_filter( array( $place, $ago ) ) ) ),
			'kind'  => 'verified-local-news',
		);
	}
	return $out;
}

/**
 * "Breaking News" nav panel URL — verified homepage section only.
 *
 * @return string
 */
function studentup_breaking_nav_url() {
	return home_url( '/#breaking' );
}

/**
 * Desktop nav item (li + sub-menu) — '' when there is nothing real to show.
 *
 * @return string
 */
function studentup_breaking_nav_li() {
	if ( ! function_exists( 'studentup_opt' ) || ! studentup_opt( 'breaking_nav', '1' ) ) {
		return '';
	}
	$items = studentup_breaking_nav_items( 5 );
	if ( ! $items ) {
		return '';
	}
	$url   = studentup_breaking_nav_url();

	$h  = '<li class="menu-item menu-item-has-children su-navbrk">';
	$h .= '<a href="' . esc_url( $url ) . '" aria-haspopup="true" aria-expanded="false" aria-controls="su-brkdd">'
		. '<span class="su-brkdot" aria-hidden="true"></span><span class="su-mega-lb">'
		. esc_html__( 'Breaking News', 'studentup' ) . '</span></a>';
	$h .= '<ul class="sub-menu su-brkdd" id="su-brkdd" aria-label="' . esc_attr__( 'Breaking News', 'studentup' ) . '">';
	$h .= '<li class="menu-item su-brkdd-head" role="none"><span>'
		. esc_html__( 'Verified TS/AP local news', 'studentup' )
		. '</span><em>' . esc_html__( 'Fresh', 'studentup' ) . '</em></li>';

	foreach ( $items as $it ) {
		$h .= '<li class="menu-item" role="none"><a role="menuitem" href="' . esc_url( $it['url'] ) . '">'
			. '<span class="su-mega-ic">' . studentup_ui_icon( 'bolt', 16 ) . '</span>'
			. '<span class="su-mega-t">' . esc_html( $it['title'] )
			. '<small>' . esc_html( $it['meta'] ) . '</small></span></a></li>';
	}
	$h .= '<li class="menu-item su-brkdd-foot" role="none"><a class="su-brkdd-cta" href="' . esc_url( $url ) . '">'
		. esc_html__( 'All local updates', 'studentup' )
		. ' ' . studentup_ui_icon( 'arrow', 13 ) . '</a></li>';
	$h .= '</ul></li>';
	return $h;
}

/**
 * Mobile panel block (`.mpanel` top) — '' when there is nothing real.
 *
 * @return string
 */
function studentup_breaking_mobile_block() {
	if ( ! function_exists( 'studentup_opt' ) || ! studentup_opt( 'breaking_nav', '1' ) ) {
		return '';
	}
	$items = studentup_breaking_nav_items( 4 );
	if ( ! $items ) {
		return '';
	}
	$url = studentup_breaking_nav_url();
	$h   = '<div class="mlabel mlabel-brk"><span class="su-brkdot" aria-hidden="true"></span>'
		. esc_html__( 'Breaking News · TS/AP state and district updates', 'studentup' ) . '</div>';
	foreach ( $items as $it ) {
		$h .= '<a class="su-mbrk" href="' . esc_url( $it['url'] ) . '">'
			. studentup_ui_icon( 'bolt', 16 )
			. '<span class="su-mbrk-t">' . esc_html( $it['title'] )
			. '<small>' . esc_html( $it['meta'] ) . '</small></span></a>';
	}
	$h .= '<a class="su-mbrk-all" href="' . esc_url( $url ) . '">'
		. esc_html__( 'All local updates', 'studentup' ) . ' ' . studentup_ui_icon( 'arrow', 13 ) . '</a>';
	return $h;
}

/**
 * First **top-level** item ayyipoyina taruvata byte offset.
 *
 * Enduku depth lekka: WP menu HTML lo modati `</li>` nested sub-item di kuda
 * avvachu (modati item ki children unte, udaharanaki `Jobs ▾` modatlo unte).
 * Appudu naiva `strpos( $items, '</li>' )` item ni **sub-menu lopala** pettestundi.
 * Ee helper `<li` / `</li>` depth ni lekka chesi, depth 0 ki tirigi vachina
 * modati position ni istundi.
 *
 * @param string $items Menu items HTML.
 * @return int|false Byte offset (first item tarvata) leda false.
 */
function studentup_breaking_first_item_end( $items ) {
	$len   = strlen( $items );
	$depth = 0;
	$off   = 0;
	while ( $off < $len ) {
		if ( ! preg_match( '/<(li|\/li)\b[^>]*>/i', $items, $m, PREG_OFFSET_CAPTURE, $off ) ) {
			return false;
		}
		$tag = strtolower( $m[1][0] );
		$end = $m[0][1] + strlen( $m[0][0] );
		if ( 'li' === $tag ) {
			$depth++;
		} else {
			$depth--;
			if ( $depth <= 0 ) {
				return $end; // first top-level item complete.
			}
		}
		$off = $end;
	}
	return false;
}

/**
 * Inject into a user-built WP menu (primary location) — right after Home.
 *
 * @param string   $items Menu items HTML.
 * @param stdClass $args  wp_nav_menu args.
 * @return string
 */
function studentup_breaking_menu_filter( $items, $args ) {
	$loc = isset( $args->theme_location ) ? (string) $args->theme_location : '';
	if ( 'primary' !== $loc ) {
		return $items;
	}
	if ( false !== strpos( (string) $items, 'su-navbrk' ) ) {
		return $items; // already there (custom menu item).
	}
	if ( false !== stripos( (string) $items, 'breaking news' ) ) {
		return $items; // admin already added own Breaking News item.
	}
	$li = studentup_breaking_nav_li();
	if ( '' === $li ) {
		return $items;
	}
	$pos = studentup_breaking_first_item_end( (string) $items );
	if ( false === $pos ) {
		return $li . $items; // odd markup — item ni mundu pettadam safe.
	}
	return substr( $items, 0, $pos ) . $li . substr( $items, $pos );
}
// Intentionally not registered: the current header owns one Home/TS/AP/Central/More menu.
