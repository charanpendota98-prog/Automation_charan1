<?php
/**
 * v202 BREAKING NEWS NAV — header lo "Breaking News" item (desktop panel +
 * mobile block), exactly like the other mega items.
 *
 * Owner (2026-10-04): *"Breaking News kuda same like Central Jobs alaga undali —
 * akkada click chethe open avvali."*
 *
 * Rules (same honesty contract as the rest of the theme):
 *   · Data = **real** verified radar items (studentup_breaking_items()) unte avi;
 *     lekapote **mee latest published posts** ("Latest update" ani label) —
 *     0 posts unte ee nav item inject avvadu (khali panel chupinchamu).
 *   · Prathi link real: verified item link leda post permalink leda category,
 *     fallback `/#breaking` (404 eppudu ledu).
 *   · Desktop = `li.menu-item-has-children` + `ul.sub-menu` — theme JS (click /
 *     Enter / ArrowDown / Escape) mariyu v93 hover CSS rendu automatic ga
 *     apply avutayi (Central Jobs laage).
 *   · Mobile = `.mpanel` lopala top block (icon + title + time).
 *   · Telugu ledu (v73 invariant) — labels English.
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Breaking nav items — verified feed first, else latest published posts.
 *
 * @param int $limit max items.
 * @return array<int,array<string,string>> [ title, url, meta, kind ]
 */
function studentup_breaking_nav_items( $limit = 5 ) {
	$limit = max( 1, min( 8, (int) $limit ) );
	$out   = array();

	// 1) Verified radar feed (bot push) — best source.
	if ( function_exists( 'studentup_breaking_items' ) ) {
		foreach ( studentup_breaking_items( $limit ) as $it ) {
			$ago  = function_exists( 'studentup_ago' ) ? studentup_ago( (string) $it['time'] ) : '';
			$tag  = function_exists( 'studentup_tag_label' ) ? studentup_tag_label( (string) $it['tag'] ) : '';
			$meta = trim( implode( ' · ', array_filter( array( $ago, $tag ) ) ) );
			$out[] = array(
				'title' => (string) $it['title'],
				'url'   => (string) $it['link'],
				'meta'  => $meta ? $meta : 'Verified',
				'kind'  => 'verified',
			);
		}
	}
	if ( $out ) {
		return $out;
	}

	// 2) Latest published posts — real content, honest label.
	$posts = get_posts(
		array(
			'post_type'           => 'post',
			'post_status'         => 'publish',
			'posts_per_page'      => $limit,
			'no_found_rows'       => true,
			'ignore_sticky_posts' => true,
		)
	);
	foreach ( $posts as $p ) {
		$when = human_time_diff( (int) get_post_time( 'U', true, $p ), time() );
		$cats = get_the_category( $p->ID );
		$cat  = ! empty( $cats ) ? $cats[0]->name : '';
		$out[] = array(
			'title' => wp_trim_words( get_the_title( $p ), 12, '…' ),
			'url'   => (string) get_permalink( $p ),
			'meta'  => trim( implode( ' · ', array_filter( array( $when . ' ago', $cat ) ) ) ),
			'kind'  => 'latest',
		);
	}
	return $out;
}

/**
 * "Breaking News" nav panel URL — real category, else the front-page surface.
 *
 * @return string
 */
function studentup_breaking_nav_url() {
	foreach ( array( 'breaking-news', 'breaking', 'current-affairs' ) as $slug ) {
		$term = function_exists( 'studentup_used_term' ) ? studentup_used_term( $slug ) : null;
		if ( $term ) {
			return (string) get_category_link( $term );
		}
	}
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
	$has_f = ( 'verified' === $items[0]['kind'] );

	$h  = '<li class="menu-item menu-item-has-children su-navbrk">';
	$h .= '<a href="' . esc_url( $url ) . '" aria-haspopup="true" aria-expanded="false" aria-controls="su-brkdd">'
		. '<span class="su-brkdot" aria-hidden="true"></span><span class="su-mega-lb">'
		. esc_html__( 'Breaking News', 'studentup' ) . '</span></a>';
	$h .= '<ul class="sub-menu su-brkdd" id="su-brkdd" aria-label="' . esc_attr__( 'Breaking News', 'studentup' ) . '">';
	$h .= '<li class="menu-item su-brkdd-head" role="none"><span>'
		. esc_html__( 'Latest verified updates', 'studentup' )
		. '</span><em>' . esc_html__( 'Live', 'studentup' ) . '</em></li>';

	foreach ( $items as $it ) {
		$h .= '<li class="menu-item" role="none"><a role="menuitem" href="' . esc_url( $it['url'] ) . '">'
			. '<span class="su-mega-ic">' . studentup_ui_icon( 'bolt', 16 ) . '</span>'
			. '<span class="su-mega-t">' . esc_html( $it['title'] )
			. '<small>' . esc_html( $it['meta'] ) . '</small></span></a></li>';
	}
	$h .= '<li class="menu-item su-brkdd-foot" role="none"><a class="su-brkdd-cta" href="' . esc_url( $url ) . '">'
		. esc_html( $has_f ? __( 'All updates', 'studentup' ) : __( 'All latest', 'studentup' ) )
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
		. esc_html__( 'Breaking News', 'studentup' ) . '</div>';
	foreach ( $items as $it ) {
		$h .= '<a class="su-mbrk" href="' . esc_url( $it['url'] ) . '">'
			. studentup_ui_icon( 'bolt', 16 )
			. '<span class="su-mbrk-t">' . esc_html( $it['title'] )
			. '<small>' . esc_html( $it['meta'] ) . '</small></span></a>';
	}
	$h .= '<a class="su-mbrk-all" href="' . esc_url( $url ) . '">'
		. esc_html__( 'All updates', 'studentup' ) . ' ' . studentup_ui_icon( 'arrow', 13 ) . '</a>';
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
add_filter( 'wp_nav_menu_items', 'studentup_breaking_menu_filter', 10, 2 );
