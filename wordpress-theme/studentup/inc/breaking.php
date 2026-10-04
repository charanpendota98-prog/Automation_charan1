<?php
/**
 * Verified TS/AP state and district news only. Job notices are deliberately
 * excluded; the homepage omits this section and its menu entries when the
 * feed has no fresh qualifying item.
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
function studentup_breaking_enabled() {
	return (bool) studentup_opt( 'breaking_enabled', '1' );
}

/**
 * A breaking-feed item qualifies only when it is explicitly scoped to TS/AP
 * local/state news, carries the corresponding local tag, and is not a job or
 * exam notice. The feed's verified flags are checked separately below.
 *
 * @param array $item Unsanitized feed row.
 * @return array|false Canonical row classification, or false.
 */
function studentup_breaking_local_kind( $item ) {
	if ( ! is_array( $item ) ) {
		return false;
	}
	$tag      = sanitize_key( isset( $item['tag'] ) ? (string) $item['tag'] : '' );
	$state_raw = sanitize_key( isset( $item['state'] ) ? (string) $item['state'] : '' );
	$state_map = array( 'ts' => 'TS', 'telangana' => 'TS', 'ap' => 'AP', 'andhra' => 'AP', 'andhra-pradesh' => 'AP' );
	$state     = isset( $state_map[ $state_raw ] ) ? $state_map[ $state_raw ] : strtoupper( $state_raw );
	$district = isset( $item['district'] ) ? trim( wp_strip_all_tags( (string) $item['district'] ) ) : '';
	$aliases  = array(
		'ts-state-news'       => array( 'state' => 'TS', 'type' => 'state' ),
		'telangana-state-news' => array( 'state' => 'TS', 'type' => 'state' ),
		'ap-state-news'       => array( 'state' => 'AP', 'type' => 'state' ),
		'andhra-state-news'    => array( 'state' => 'AP', 'type' => 'state' ),
		'ts-district-news'    => array( 'state' => 'TS', 'type' => 'district' ),
		'telangana-district-news' => array( 'state' => 'TS', 'type' => 'district' ),
		'ap-district-news'    => array( 'state' => 'AP', 'type' => 'district' ),
		'andhra-district-news' => array( 'state' => 'AP', 'type' => 'district' ),
		'state-news'          => array( 'state' => $state, 'type' => 'state' ),
		'district-news'       => array( 'state' => $state, 'type' => 'district' ),
		'local-news'          => array( 'state' => $state, 'type' => $district ? 'district' : 'state' ),
	);
	if ( ! isset( $aliases[ $tag ] ) ) {
		return false;
	}
	$scope = $aliases[ $tag ];
	if ( ! in_array( $scope['state'], array( 'TS', 'AP' ), true ) || ( $state && $state !== $scope['state'] ) ) {
		return false;
	}
	if ( 'district' === $scope['type'] && '' === $district ) {
		return false;
	}

	$title = isset( $item['title'] ) ? wp_strip_all_tags( (string) $item['title'] ) : '';
	$job_or_exam = '/(?:\bjobs?\b|\brecruit(?:ment|ing)?\b|\bvacanc(?:y|ies)\b|\bhir(?:e|ing)\b|\bcareer\b|\bemployment\b|\bwalk[ -]?in\b|\bjob mela\b|\bapply online\b|\badmit card\b|\bhall[ -]?ticket\b|\banswer key\b|\bexam(?:ination)?\b|\bresults?\b|\bmerit list\b|\bsyllabus\b|\bselection list\b|\btspsc\b|\bappsc\b|\bdsc\b|\bssc\b|\bupsc\b|\brrb\b|\bgroup [1-4]\b|\bnotification for posts\b|ఉద్యోగ|నియామక|ఖాళీ|దరఖాస్తు|హాల్.?టికెట్|పరీక్ష|ఫలితాల|ఉద్యోగమేళా|డీఎస్సీ)/iu';
	if ( preg_match( $job_or_exam, $title ) ) {
		return false;
	}

	return array(
		'state'    => $scope['state'],
		'type'     => $scope['type'],
		'district' => $district,
	);
}

/**
 * Items array (max $max) — fresh, verified TS/AP state or district news only.
 *
 * @param int $max max items.
 * @return array<int,array<string,string>>
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
	if ( isset( $data['verified_only'] ) && true !== $data['verified_only'] ) {
		return array();
	}
	$updated = isset( $data['updated'] ) ? strtotime( (string) $data['updated'] ) : false;
	if ( ! $updated || $updated > ( time() + 300 ) || ( time() - $updated ) > ( 36 * HOUR_IN_SECONDS ) ) {
		return array();
	}

	$out = array();
	foreach ( $data['items'] as $it ) {
		if ( ! is_array( $it ) || true !== ( $it['verified'] ?? false ) || true !== ( $it['source_verified'] ?? false ) ) {
			continue;
		}
		$local = studentup_breaking_local_kind( $it );
		if ( ! $local ) {
			continue;
		}
		$title = isset( $it['title'] ) ? wp_strip_all_tags( (string) $it['title'] ) : '';
		$link  = isset( $it['link'] ) ? esc_url_raw( (string) $it['link'] ) : '';
		$time  = isset( $it['time'] ) ? sanitize_text_field( (string) $it['time'] ) : '';
		$stamp = $time ? strtotime( $time ) : false;
		if ( '' === $title || '' === $link || ! preg_match( '#^https?://#i', $link ) || ! $stamp || $stamp > ( time() + 300 ) || ( time() - $stamp ) > ( 36 * HOUR_IN_SECONDS ) ) {
			continue;
		}
		$out[] = array(
			'title'    => $title,
			'link'     => $link,
			'tag'      => sanitize_key( (string) $it['tag'] ),
			'source'   => isset( $it['source'] ) ? wp_strip_all_tags( (string) $it['source'] ) : 'Verified source',
			'time'     => $time,
			'state'    => $local['state'],
			'type'     => $local['type'],
			'district' => $local['district'],
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
		'ts-state-news' => 'Telangana state',
		'telangana-state-news' => 'Telangana state',
		'ap-state-news' => 'Andhra Pradesh state',
		'andhra-state-news' => 'Andhra Pradesh state',
		'ts-district-news' => 'Telangana district',
		'telangana-district-news' => 'Telangana district',
		'ap-district-news' => 'Andhra Pradesh district',
		'andhra-district-news' => 'Andhra Pradesh district',
		'ts-jobs'      => 'Telangana',
		'ap-jobs'      => 'Andhra Pradesh',
		'central-jobs' => 'Central',
		'hallticket'   => 'Hall ticket',
		'results'      => 'Results',
		'walkin'       => 'Walk-in',
		'software'     => 'Software',
		'private'      => 'Private',
		'abroad'       => 'Abroad',
		'scholarship'  => 'Scholarship',
		'current'      => 'Current affairs',
		'success-stories' => 'Success story',
	);

	return isset( $map[ $tag ] ) ? $map[ $tag ] : 'Update';
}

/**
 * "time ago" — Telugu.
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
		return max( 1, (int) ( $diff / 60 ) ) . ' min ago';
	}
	if ( $diff < 86400 ) {
		return (int) ( $diff / 3600 ) . ' h ago';
	}
	$days = (int) ( $diff / 86400 );
	return 1 === $days ? 'yesterday' : $days . ' days ago';
}

/**
 * Ticker (renders only when there is a feed — hidden when empty).
 */
function studentup_breaking_ticker() {
	// Legacy ticker intentionally retired; the homepage uses a static, local-news
	// list only when fresh verified TS/AP state or district items exist.
	return;
}

/**
 * Breaking news section (h2 + list; honest empty message).
 */
function studentup_breaking_section() {
	if ( ! studentup_breaking_enabled() ) {
		return;
	}
	$items = studentup_breaking_items( 6 );
	if ( ! $items ) {
		return;
	}
	echo '<section class="breaking" id="breaking" aria-labelledby="breaking-title">';
	echo '<div class="brkhead"><span class="brkicon" aria-hidden="true">' . studentup_ui_icon( 'bolt', 15 ) . '</span><span class="brkdot" aria-hidden="true"></span><h2 id="breaking-title">Breaking News</h2>';
	echo '<span class="brklive">Verified TS/AP state and district news</span></div>';
	echo '<ol class="brklist">';
	foreach ( $items as $it ) {
		$place = 'TS' === $it['state'] ? 'Telangana' : 'Andhra Pradesh';
		if ( 'district' === $it['type'] && $it['district'] ) {
			$place .= ' · ' . $it['district'] . ' district';
		}
		printf(
			'<li class="brkitem"><span class="bt">%s</span><a href="%s" target="_blank" rel="noopener noreferrer">%s<span class="bwhen">%s · %s</span></a></li>',
			esc_html( $place ),
			esc_url( $it['link'] ),
			esc_html( $it['title'] ),
			esc_html( $it['source'] ),
			esc_html( studentup_ago( $it['time'] ) )
		);
	}
	echo '</ol></section>';
}

/**
 * v89: Latest Jobs scrolling ticker — SITE content nunche (feed config avasaram ledu).
 *
 * Breaking ticker (radar feed) veru — adi OFF default. Idi eppudu OWN posts
 * tho pani chestundi: latest 12 posts, prathi item click cheste aa post
 * page open avutundi (same tab — internal link). Hover lo pause; reduced-motion
 * users ki animation off (CSS). 10 min transient cache (post publish lo clear).
 *
 * @param int $max items.
 * @return array each: title/link/time
 */
function studentup_latest_ticker_items( $max = 12 ) {
	$max    = max( 1, (int) $max );
	$cached = get_transient( 'su_latest_ticker' );
	if ( is_array( $cached ) ) {
		$cached = array_values(
			array_filter(
				$cached,
				static function ( $item ) {
					$title = isset( $item['title'] ) ? wp_strip_all_tags( (string) $item['title'] ) : '';
					$link  = isset( $item['link'] ) ? (string) $item['link'] : '';
					return $link && 'guide' !== sanitize_title( $title );
				}
			)
		);
		return array_slice( $cached, 0, $max );
	}
	$q     = new WP_Query(
		array(
			'post_type'           => 'post',
			'post_status'         => 'publish',
			'posts_per_page'      => $max,
			'ignore_sticky_posts' => true,
			'no_found_rows'       => true,
		)
	);
	$items = array();
	foreach ( (array) $q->posts as $p ) {
		$link  = get_permalink( $p );
		$title = wp_strip_all_tags( (string) get_the_title( $p ) );
		$slug  = (string) get_post_field( 'post_name', $p );
		/* A generic placeholder/guide is not a useful Latest Jobs item. Keep
		 * the ticker focused on real student opportunities and avoid showing a
		 * low-value "Guide" card above the homepage on mobile. */
		if ( ! $link || 'guide' === sanitize_title( $title ) || 'guide' === $slug ) {
			continue;
		}
		$items[] = array(
			'title' => $title,
			'link'  => $link,
			'time'  => get_post_time( DATE_W3C, false, $p ),
		);
	}
	set_transient( 'su_latest_ticker', $items, 10 * MINUTE_IN_SECONDS );
	return $items;
}

/**
 * New/updated post → ticker cache clear (tappu cursor eppudu fresh latest).
 *
 * @param int $post_id post id.
 */
function studentup_latest_ticker_flush( $post_id ) {
	$post = get_post( $post_id );
	if ( $post && 'post' === $post->post_type ) {
		delete_transient( 'su_latest_ticker' );
	}
}
add_action( 'save_post', 'studentup_latest_ticker_flush', 30 );

/**
 * Render the marquee — home page mattrame (post pages lo reading ki distraction vaddu).
 */
function studentup_latest_ticker() {
	// v127: owner-enabled latest jobs strip restored — same compact, useful bar
	// as the approved reference design. It is still homepage-only and cached.
	if ( ! is_front_page() || '0' === (string) studentup_opt( 'latest_ticker', '1' ) ) {
		return;
	}
	$items = studentup_latest_ticker_items( 12 );
	if ( ! $items ) {
		return;
	}
	echo '<div class="tickerwrap su-lticker" aria-label="Latest jobs — scrolling list">';
	echo '<div class="wrap trow">';
	echo '<span class="tlabel tlabel-blue"><i aria-hidden="true"></i>' . esc_html__( 'Latest Jobs', 'studentup' ) . '</span>';
	echo '<div class="tclip"><div class="tmove">';
	foreach ( array( 0, 1 ) as $dup ) {   // duplicate set — seamless 50% loop
		foreach ( $items as $it ) {
			printf(
				'<a href="%s"%s aria-label="%s" title="Open article">%s <span class="tsrc">%s</span></a>',
				esc_url( $it['link'] ),
				$dup ? ' aria-hidden="true" tabindex="-1"' : '',
				esc_attr( 'Open article: ' . wp_strip_all_tags( (string) $it['title'] ) ),
				esc_html( $it['title'] ),
				esc_html( studentup_ago( $it['time'] ) )
			);
		}
	}
	echo '</div></div>';
	echo '<div class="su-ticker-ctrls">';
	echo '<button type="button" class="su-tbtn" id="su-t-prev" aria-label="' . esc_attr__( 'Previous headline', 'studentup' ) . '">‹</button>';
	echo '<button type="button" class="su-tbtn" id="su-t-toggle" aria-label="' . esc_attr__( 'Pause or resume ticker', 'studentup' ) . '">⏸</button>';
	echo '<button type="button" class="su-tbtn" id="su-t-next" aria-label="' . esc_attr__( 'Next headline', 'studentup' ) . '">›</button>';
	echo '</div>';
	echo '</div></div>';
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
