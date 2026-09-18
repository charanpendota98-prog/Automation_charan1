<?php
/**
 * బ్రేకింగ్ న్యూస్ — radar feed (bot rasi preview/data/breaking.json) WordPress lo.
 *
 * Data path (okka chota, honest):
 *   1) WP option 'studentup_breaking_json' (bot REST/CLI tho push cheyyochu) — fastest
 *   2) site root lo /data/breaking.json (bot radar rasi file) — 10 min transient cache
 *   3) khali → section "కొత్త verified అప్డేట్‌లు లేవు" ani chupistundi (fake news ledu)
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Items array (max $max) — sanitized.
 *
 * @param int $max max items.
 * @return array
 */
function studentup_breaking_items( $max = 6 ) {
	$max = max( 1, (int) $max );

	$raw = get_option( 'studentup_breaking_json', '' );
	if ( ! is_string( $raw ) || '' === trim( $raw ) ) {
		$cache = get_transient( 'studentup_breaking_feed' );
		if ( false === $cache ) {
			$cache = '';
			$url   = home_url( '/data/breaking.json' );
			$res   = wp_remote_get( $url, array( 'timeout' => 6 ) );
			if ( ! is_wp_error( $res ) && 200 === (int) wp_remote_retrieve_response_code( $res ) ) {
				$cache = (string) wp_remote_retrieve_body( $res );
			}
			set_transient( 'studentup_breaking_feed', $cache, 10 * MINUTE_IN_SECONDS );
		}
		$raw = $cache;
	}

	$data = json_decode( (string) $raw, true );
	if ( ! is_array( $data ) || empty( $data['items'] ) || ! is_array( $data['items'] ) ) {
		return array();
	}

	$out = array();
	foreach ( $data['items'] as $it ) {
		if ( ! is_array( $it ) ) {
			continue;
		}
		$title = isset( $it['title'] ) ? wp_strip_all_tags( (string) $it['title'] ) : '';
		$link  = isset( $it['link'] ) ? esc_url_raw( (string) $it['link'] ) : '';
		if ( '' === $title || '' === $link || ! preg_match( '#^https?://#i', $link ) ) {
			continue;
		}
		$out[] = array(
			'title'  => $title,
			'link'   => $link,
			'tag'    => isset( $it['tag'] ) ? sanitize_key( (string) $it['tag'] ) : 'current',
			'source' => isset( $it['source'] ) ? wp_strip_all_tags( (string) $it['source'] ) : 'రాడార్',
			'time'   => isset( $it['time'] ) ? sanitize_text_field( (string) $it['time'] ) : '',
		);
		if ( count( $out ) >= $max ) {
			break;
		}
	}
	return $out;
}

/**
 * Tag → Telugu label (site ticker/section ki).
 *
 * @param string $tag tag key.
 * @return string
 */
function studentup_tag_label( $tag ) {
	$map = array(
		'ts-jobs'      => 'తెలంగాణ',
		'ap-jobs'      => 'ఆంధ్రప్రదేశ్',
		'central-jobs' => 'కేంద్రం',
		'hallticket'   => 'హాల్ టికెట్',
		'results'      => 'ఫలితాలు',
		'walkin'       => 'వాక్-ఇన్',
		'software'     => 'సాఫ్ట్‌వేర్',
		'private'      => 'ప్రైవేట్',
		'abroad'       => 'విదేశీ',
		'scholarship'  => 'స్కాలర్‌షిప్',
		'current'      => 'కరెంట్',
	);
	return isset( $map[ $tag ] ) ? $map[ $tag ] : 'అప్డేట్';
}

/**
 * "ఎంత సేపటి క్రితం" — Telugu.
 *
 * @param string $iso ISO time.
 * @return string
 */
function studentup_ago( $iso ) {
	$t = strtotime( (string) $iso );
	if ( ! $t ) {
		return '';
	}
	$diff = time() - $t;
	if ( $diff < 3600 ) {
		return max( 1, (int) ( $diff / 60 ) ) . ' నిమిషాల క్రితం';
	}
	if ( $diff < 86400 ) {
		return (int) ( $diff / 3600 ) . ' గంటల క్రితం';
	}
	$days = (int) ( $diff / 86400 );
	return 1 === $days ? 'నిన్న' : $days . ' రోజుల క్రితం';
}

/**
 * టికర్ (feed unte matrame render — khali aithe hide).
 */
function studentup_breaking_ticker() {
	$items = studentup_breaking_items( 5 );
	if ( ! $items ) {
		return;
	}
	echo '<div class="tickerwrap"><div class="wrap trow">';
	echo '<span class="tlabel"><i aria-hidden="true"></i>బ్రేకింగ్</span><div class="tclip"><div class="tmove">';
	foreach ( $items as $it ) {
		printf(
			'<a href="%s" target="_blank" rel="noopener">%s <span class="tsrc">%s</span></a>',
			esc_url( $it['link'] ),
			esc_html( $it['title'] ),
			esc_html( studentup_ago( $it['time'] ) )
		);
	}
	foreach ( $items as $it ) { // duplicate — CSS animation seamless loop ki.
		printf(
			'<a href="%s" target="_blank" rel="noopener" aria-hidden="true" tabindex="-1">%s <span class="tsrc">%s</span></a>',
			esc_url( $it['link'] ),
			esc_html( $it['title'] ),
			esc_html( studentup_ago( $it['time'] ) )
		);
	}
	echo '</div></div><a class="tall" href="#breaking">అన్నీ →</a></div></div>';
}

/**
 * బ్రేకింగ్ న్యూస్ section (h2 + list; honest empty message).
 */
function studentup_breaking_section() {
	$items = studentup_breaking_items( 6 );
	echo '<section class="breaking" id="breaking" aria-label="బ్రేకింగ్ న్యూస్">';
	echo '<div class="brkhead"><span class="brkdot" aria-hidden="true"></span><h2>బ్రేకింగ్ న్యూస్</h2>';
	echo '<span class="brklive">రాడార్ · Google News తెలుగు + అధికారిక మూలాలు · 6 గంటలకు ఒకసారి</span></div>';
	if ( ! $items ) {
		echo '<p class="brkempty">ప్రస్తుతం కొత్త verified బ్రేకింగ్ అప్డేట్‌లు లేవు — రాడార్ ప్రతి 6 గంటలకు చెక్ చేస్తుంది.</p>';
	} else {
		echo '<ol class="brklist">';
		foreach ( $items as $it ) {
			printf(
				'<li class="brkitem"><span class="bt">%s</span><a href="%s" target="_blank" rel="noopener">%s<span class="bwhen">%s · %s</span></a></li>',
				esc_html( studentup_tag_label( $it['tag'] ) ),
				esc_url( $it['link'] ),
				esc_html( $it['title'] ),
				esc_html( $it['source'] ),
				esc_html( studentup_ago( $it['time'] ) )
			);
		}
		echo '</ol>';
	}
	echo '</section>';
}

/**
 * Bot/manual update ki: option set → transient clear.
 */
function studentup_set_breaking_json( $json ) {
	update_option( 'studentup_breaking_json', (string) $json, false );
	delete_transient( 'studentup_breaking_feed' );
}

/**
 * REST endpoint — bot (website nunchi) breaking/deadline/house-ads ni
 * WordPress ki push cheyyadaniki. Auth: Application Password + edit_posts.
 *
 *   POST /wp-json/studentup/v1/theme-data
 *   body: { "breaking": [...], "deadline": {...}, "house_ads": [...] }
 */
function studentup_register_rest() {
	register_rest_route(
		'studentup/v1',
		'/theme-data',
		array(
			'methods'             => 'POST',
			'permission_callback' => function () {
				return current_user_can( 'edit_posts' );
			},
			'callback'            => function ( WP_REST_Request $req ) {
				$done = array();
				$breaking = $req->get_param( 'breaking' );
				if ( is_array( $breaking ) ) {
					studentup_set_breaking_json( wp_json_encode( array( 'items' => $breaking ) ) );
					$done[] = 'breaking';
				}
				$deadline = $req->get_param( 'deadline' );
				if ( is_array( $deadline ) && ! empty( $deadline['date'] ) ) {
					studentup_set_deadline(
						isset( $deadline['title'] ) ? $deadline['title'] : '',
						$deadline['date']
					);
					$done[] = 'deadline';
				}
				$house = $req->get_param( 'house_ads' );
				if ( is_array( $house ) ) {
					update_option( 'studentup_house_ads', wp_json_encode( $house ), false );
					$done[] = 'house_ads';
				}
				// v64: website options (socials · adsense · flags) — same allowlist tho
				$opts = $req->get_param( 'options' );
				if ( is_array( $opts ) && function_exists( 'studentup_option_fields' ) ) {
					$allowed = array();
					foreach ( studentup_option_fields() as $tab ) {
						foreach ( $tab['fields'] as $okey => $of ) {
							$allowed[ $okey ] = $of[1];
						}
					}
					$saved = array();
					foreach ( $opts as $okey => $oval ) {
						if ( ! isset( $allowed[ $okey ] ) ) {
							continue;
						}
						if ( 'check' === $allowed[ $okey ] ) {
							update_option( 'studentup_' . $okey, $oval ? '1' : '0', false );
						} else {
							update_option( 'studentup_' . $okey,
								studentup_sanitize_option( is_string( $oval ) ? $oval : wp_json_encode( $oval, JSON_UNESCAPED_UNICODE ) ), false );
						}
						$saved[] = $okey;
					}
					if ( $saved ) {
						$done[] = 'options:' . implode( ',', $saved );
					}
				}
				return new WP_REST_Response( array( 'ok' => true, 'updated' => $done ), 200 );
			},
		)
	);
}
add_action( 'rest_api_init', 'studentup_register_rest' );
