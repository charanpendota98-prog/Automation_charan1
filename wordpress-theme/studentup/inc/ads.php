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
function studentup_adsense_unit( $slot, $layout = 'auto' ) {
	$client = studentup_adsense_client();
	if ( ! $client ) {
		return;
	}
	printf(
		'<div class="adsense-slot"><ins class="adsbygoogle" style="display:block" data-ad-client="%s" data-ad-slot="%s" data-ad-format="%s" data-full-width-responsive="true"></ins><script>(adsbygoogle=window.adsbygoogle||[]).push({});</script></div>',
		esc_attr( $client ),
		esc_attr( $slot ),
		esc_attr( $layout )
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
			'cta'   => isset( $ad['cta'] ) ? wp_strip_all_tags( (string) $ad['cta'] ) : 'చూడండి →',
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
function studentup_rotate_house( $ads ) {
	$n = count( $ads );
	if ( ! $n ) {
		return null;
	}
	return $ads[ (int) gmdate( 'z' ) % $n ];
}

/**
 * Ad slot renderer — design lo unna same markup (SPONSORED label tho).
 *
 * @param string $place leaderboard|in-feed|mid|sidebar.
 */
function studentup_ad( $place = 'mid' ) {
	$house = studentup_rotate_house( studentup_house_ads() );
	$cls   = 'in-feed' === $place ? 'su-ad su-ad-feed' : ( 'leaderboard' === $place ? 'su-ad su-ad-leader' : 'su-ad' );

	if ( $house ) {
		echo '<aside class="' . esc_attr( $cls ) . '" aria-label="Sponsored content">';
		echo '<div class="su-ad-kicker">SPONSORED · భాగస్వామి</div>';
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
		echo '<div class="su-ad-disc">ప్రకటన — భాగస్వామికి నేరు లింక్. అధికారిక నోటిఫికేషన్‌లు ప్రధాన కంటెంట్‌లో మాత్రమే ఉంటాయి.</div>';
		echo '</aside>';
	}

	// AdSense slot names: option lo 'top-<slot>' style ids pettandi (ca-pub-… tarvata).
	$map = array(
		'leaderboard' => '1234567890',
		'in-feed'     => '2345678901',
		'mid'         => '3456789012',
		'sidebar'     => '4567890123',
	);
	$slot_id = (string) get_option( 'studentup_adsense_slot_' . str_replace( '-', '_', $place ), '' );
	if ( ! $slot_id && isset( $map[ $place ] ) ) {
		$slot_id = '';
	}
	if ( $slot_id ) {
		studentup_adsense_unit( $slot_id, 'in-article' === $place ? 'in-article' : 'auto' );
	}
}
