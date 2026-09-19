<?php
/**
 * Ad slots — AdSense + house/sponsor ads (AdSense-compliant markup).
 *
 * Rules (code lo enforce):
 *   - prathi sponsored/house block ki SPONSORED label
 *   - links: rel="sponsored nofollow noopener"
 *   - AdSense unit: client id option 'studentup_adsense_client' (ca-pub-…)
 *   - in-feed ad .newsgrid lo render avutundi kaani filter (JS) touch cheyyadu
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * AdSense client id (option leda ADSENSE_CLIENT_ID constant leda '').
 */
function studentup_adsense_client() {
	$client = (string) get_option( 'studentup_adsense_client', '' );
	if ( ! $client && defined( 'ADSENSE_CLIENT_ID' ) ) {
		$client = (string) ADSENSE_CLIENT_ID;
	}
	return preg_match( '/^ca-pub-\d{10,20}$/', $client ) ? $client : '';
}

/**
 * AdSense unit (responsive). Approval tarvata matrame output — lekapote khali.
 *
 * @param string $slot slot name.
 * @param string $layout display layout (auto|in-article|fluid).
 */
function studentup_adsense_unit( $slot, $layout = 'auto', $lazy = false, $height = 250 ) {
	$client = studentup_adsense_client();
	if ( ! $client ) {
		return;
	}
	// v68 FIX (revenue): in-article / in-feed units ki `data-ad-layout` + `data-ad-format="fluid"`.
	// Mundu `data-ad-format="in-article"` (INVALID attribute value) velledi → Google adi
	// generic display ga treat chesi **in-article RPM miss** ayyedi (highest-RPM slot!).
	$liquid = in_array( $layout, array( 'in-article', 'in-feed' ), true );
	$attrs  = $liquid
		? ' data-ad-format="fluid" data-ad-layout="' . esc_attr( $layout ) . '"'
		: ' data-ad-format="auto"';
	printf(
		'<div class="adsense-slot su-ad-reserved%1$s" style="min-height:%2$dpx" data-su-lazy="%3$d" data-su-height="%2$d">'
		. '<ins class="adsbygoogle" style="display:block;text-align:center" data-ad-client="%4$s" '
		. 'data-ad-slot="%5$s"%6$s data-full-width-responsive="true"></ins>%7$s</div>',
		$lazy ? ' su-ad-lazy' : '',
		(int) $height,
		$lazy ? 1 : 0,
		esc_attr( $client ),
		esc_attr( $slot ),
		$attrs,
		$lazy ? '' : '<script>(adsbygoogle=window.adsbygoogle||[]).push({});</script>'
	);
}

/**
 * House ads (bot rasi: ads/house.json → WP option 'studentup_house_ads').
 * Roju okati rotate avutundi (day order) — eppudu same ad kanipinchadu.
 */
function studentup_house_ads() {
	$raw = (string) get_option( 'studentup_house_ads', '' );
	$ads = json_decode( $raw, true );
	if ( ! is_array( $ads ) ) {
		return array();
	}
	$out = array();
	foreach ( $ads as $ad ) {
		if ( ! is_array( $ad ) ) {
			continue;
		}
		$title = isset( $ad['title'] ) ? wp_strip_all_tags( (string) $ad['title'] ) : '';
		$link  = isset( $ad['link'] ) ? esc_url_raw( (string) $ad['link'] ) : '';
		if ( '' === $title || '' === $link ) {
			continue;
		}
		$out[] = array(
			'title' => $title,
			'desc'  => isset( $ad['desc'] ) ? wp_strip_all_tags( (string) $ad['desc'] ) : '',
			'link'  => $link,
			'cta'   => isset( $ad['cta'] ) ? wp_strip_all_tags( (string) $ad['cta'] ) : 'Read →',
		);
	}
	return $out;
}

/**
 * House house ads lo day-rotation (deterministic).
 *
 * @param array $ads ads list.
 * @return array|null
 */
function studentup_rotate_house( $ads, $place = '' ) {
	$n = count( $ads );
	if ( ! $n ) {
		return null;
	}
	static $shown = array();
	// v77: hour-base (rojulo 24 fresh chances — page to page kotha ad feel) +
	// slot offset (oke page lo prathi slot ki vere ad, repeat ledu).
	$base  = (int) gmdate( 'z' ) * 24 + (int) gmdate( 'G' );
	$slots = array( 'leaderboard' => 0, 'in-feed' => 1, 'mid' => 2,
		'sidebar' => 3, 'below-content' => 4, 'anchor' => 5 );
	$off   = isset( $slots[ $place ] ) ? $slots[ $place ] : 0;
	for ( $i = 0; $i < $n; $i++ ) {
		$pick = $ads[ ( $base + $off + $i ) % $n ];
		$key  = isset( $pick['title'] ) ? (string) $pick['title'] : (string) $i;
		if ( ! in_array( $key, $shown, true ) ) {
			$shown[] = $key;
			return $pick;
		}
	}
	return $ads[ ( $base + $off ) % $n ];
}

/**
 * Ad slot renderer — design lo unna same markup (SPONSORED label tho).
 *
 * @param string $place leaderboard|in-feed|mid|sidebar.
 */
function studentup_ads_allowed( $place = '' ) {
	// AdSense policy: content leni pages lo ads vaddu (404/search/attachment),
	// legal pages lo owner ishtam (default OFF), feed/admin lo eppudu vaddu.
	if ( is_admin() || is_feed() || is_404() || is_search() || is_attachment() ) {
		return false;
	}
	if ( is_page() ) {
		$slug   = (string) get_post_field( 'post_name', get_queried_object_id() );
		$policy = array( 'privacy-policy', 'about-us', 'contact-us',
			'corrections-policy', 'editorial-policy' );
		if ( in_array( $slug, $policy, true ) && ! studentup_opt( 'ads_on_policy', '0' ) ) {
			return false;
		}
	}
	return (bool) studentup_opt( 'ads_enabled', '1' );
}

/**
 * Page ki enni ads render ayyayi (density cap).
 */
function studentup_ad_count( $bump = false ) {
	static $n = 0;
	if ( $bump ) {
		$n++;
	}
	return $n;
}

/**
 * Ad slot renderer — AdSense (priority) leda house/sponsor (SPONSORED label).
 *
 * v66: page gating · density cap · reserved height (CLS 0) · lazy load
 * (below-fold → viewability + CWV) · consent mode safe.
 *
 * @param string $place leaderboard|in-feed|mid|sidebar|anchor.
 */
function studentup_ad( $place = 'mid' ) {
	if ( ! studentup_ads_allowed( $place ) ) {
		return;
	}
	$max = (int) studentup_opt( 'max_ads', '4' );
	$max = $max > 0 ? $max : 4;
	if ( studentup_ad_count() >= $max ) {
		return; // density cap — AdSense safe + UX
	}
	$client = studentup_adsense_client();
	$slot   = (string) get_option( 'studentup_adsense_slot_' . str_replace( '-', '_', $place ), '' );
	$sizes  = array( 'leaderboard' => 110, 'in-feed' => 160, 'mid' => 250,
		'sidebar' => 250, 'below-content' => 280, 'anchor' => 60 );
	$height = isset( $sizes[ $place ] ) ? $sizes[ $place ] : 250;
	$lazy   = (bool) studentup_opt( 'lazy_ads', '1' ) && ! in_array( $place, array( 'leaderboard', 'anchor' ), true );

	// 1) AdSense (publisher id + slot id unte) — highest revenue path
	if ( $client && $slot && studentup_consent_ok() ) {
		studentup_ad_count( true );
		studentup_adsense_unit(
			$slot,
			'mid' === $place ? 'in-article' : ( 'in-feed' === $place ? 'fluid' : 'auto' ),
			$lazy,
			$height
		);
		return;
	}

	// 2) House/sponsor ad (AdSense lekapote leda slot set kaakapote)
	$house = studentup_rotate_house( studentup_house_ads(), $place );
	if ( ! $house ) {
		return;
	}
	studentup_ad_count( true );
	$cls = 'in-feed' === $place ? 'su-ad su-ad-feed'
		: ( 'leaderboard' === $place ? 'su-ad su-ad-leader'
		: ( 'below-content' === $place ? 'su-ad su-ad-below'
		: ( 'sidebar' === $place ? 'su-ad su-ad-sticky' : 'su-ad' ) ) );

	echo '<div class="su-ad-reserved" style="min-height:' . (int) $height . 'px" data-su-height="' . (int) $height . '">';
	echo '<aside class="' . esc_attr( $cls ) . '" aria-label="Sponsored content">';
	echo '<div class="su-ad-kicker">SPONSORED · PARTNER</div>';
	if ( 'leaderboard' === $place ) {
		echo '<div class="su-ad-leader-body"><div>';
		echo '<div class="su-ad-title">' . esc_html( $house['title'] ) . '</div>';
		if ( $house['desc'] ) {
			echo '<p class="su-ad-desc">' . esc_html( $house['desc'] ) . '</p>';
		}
		echo '</div>';
		printf(
			'<a class="su-ad-cta" href="%s" target="_blank" rel="sponsored nofollow noopener">%s</a>',
			esc_url( $house['link'] ),
			esc_html( $house['cta'] )
		);
		echo '</div>';
	} else {
		if ( 'in-feed' === $place ) {
			echo '<div class="fthumb" aria-hidden="true">' . esc_html( $house['title'] ) . '</div>';
		}
		echo '<h3>' . esc_html( $house['title'] ) . '</h3>';
		if ( $house['desc'] ) {
			echo '<p>' . esc_html( $house['desc'] ) . '</p>';
		}
		printf(
			'<a class="su-ad-cta" href="%s" target="_blank" rel="sponsored nofollow noopener">%s</a>',
			esc_url( $house['link'] ),
			esc_html( $house['cta'] )
		);
	}
	echo '<div class="su-ad-disc">Advertisement — a direct link to our partner. Official notifications appear only in the main content.</div>';
	echo '</aside></div>';
}

/**
 * v66: in-article ad — content lo 3rd paragraph tarvata (highest-CTR placement).
 *
 * Enduku: article madhya lo unna ad ki CTR + RPM anni placements kanna ekkuva.
 * Policy-safe: paragraphs madhya lo (nav/button pakkana kaadu) · density cap ·
 * lazy load · page gating anni studentup_ad() lo ne untayi.
 *
 * @param string $content Post content HTML.
 * @return string
 */
function studentup_inject_in_article_ad( $content ) {
	if ( ! is_singular( 'post' ) || ! in_the_loop() || ! is_main_query() ) {
		return $content;
	}
	if ( '0' === (string) studentup_opt( 'in_article_ad', '1' ) ) {
		return $content;
	}
	if ( false !== strpos( $content, 'su-ad-anchor-mid' ) ) {
		return $content;   // already inject ayyindi (double render ledu)
	}
	if ( ! studentup_ads_allowed( 'mid' ) ) {
		return $content;
	}
	$max = (int) studentup_opt( 'max_ads', '4' );
	if ( studentup_ad_count() >= max( 1, $max ) ) {
		return $content;
	}
	$parts = explode( '</p>', $content, 4 );
	if ( count( $parts ) < 4 ) {
		return $content;   // 3 paragraphs kanna takkuva → ad vaddu (thin content)
	}
	ob_start();
	studentup_ad( 'mid' );
	$ad = trim( (string) ob_get_clean() );
	if ( '' === $ad ) {
		return $content;
	}
	$out = $parts[0] . '</p>' . $parts[1] . '</p>' . $parts[2] . '</p>'
		. '<!--su-ad-anchor-mid-->' . $ad . $parts[3];
	return $out;
}
add_filter( 'the_content', 'studentup_inject_in_article_ad', 20 );
