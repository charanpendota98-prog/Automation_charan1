<?php
/**
 * v64: StudentUp Settings — anni website options okka chota (admin page + REST).
 *
 * Enduku: ads, socials, author info, house ads — ivi WordPress
 * option ga already untunnayi kaani admin lo edit cheyyadaniki page ledu.
 * Ippudu: WP Admin → "StudentUp" menu → tabs (Ads · Socials · Content · Advanced).
 * Bot kuda idi REST tho chaduvutundi/rasutundi (/wp-json/studentup/v1/options).
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Option helper — 'studentup_' prefix tho.
 */
function studentup_opt( $key, $default = '' ) {
	return get_option( 'studentup_' . $key, $default );
}

/**
 * Editable fields (key => [label, type, default, help]).
 */
function studentup_option_fields() {
	return array(
		'ads' => array(
			'title'  => 'Ads & monetisation',
			'fields' => array(
				'ads_enabled'    => array( 'Ads ON (site) — master switch', 'check', '1', 'OFF chesthe e pages lo ads render avvavu' ),
				'adsense_client' => array( 'AdSense Client ID', 'text', '', 'ca-pub-XXXXXXXXXXXXXXXX (approve ayyaka)' ),
				'adsense_approved' => array( 'AdSense APPROVED (email vachaka ON)', 'check', '0', 'v84: OFF unte AdSense code eppudu render kaadu — house ads matrame (blank-box/policy risk zero)' ),
				'adsense_auto'   => array( 'AdSense Auto ads (head code)', 'check', '0', 'AdSense auto ads script ni head lo add chestundi' ),
				'adsense_slot_top_leaderboard' => array( 'Slot: top-leaderboard', 'text', '', 'AdSense → Ads → By ad unit → code lo data-ad-slot' ),
				'adsense_slot_sidebar'         => array( 'Slot: sidebar', 'text', '', '' ),
				'adsense_slot_anchor'          => array( 'Slot: anchor/sticky (mobile)', 'text', '', '' ),
				'adsense_slot_mid'      => array( 'Slot: mid (in-article, ₹ highest)', 'text', '', 'Article madhya lo — highest RPM slot' ),
				'adsense_slot_in_feed'  => array( 'Slot: in-feed (grid madhya)', 'text', '', 'Between the cards in the home grid' ),
				'adsense_slot_below_content' => array( 'Slot: below-content (article tarvata)', 'text', '', 'After the article — the 2nd highest RPM slot' ),
				'ads_txt'        => array( 'ads.txt content', 'textarea', '', 'Site root /ads.txt ga serve avutundi (AdSense approval tarvata publisher id line)' ),
				'in_article_ad'  => array( 'In-article ad (content 3rd para tarvata)', 'check', '1', 'Highest-CTR placement — AdSense/ house ad (density cap + lazy tho)' ),
				'max_ads'        => array( 'Page ki max ads (density cap)', 'text', '4', '4-5 safe (AdSense + UX). Ekkuva = policy risk' ),
				'lazy_ads'       => array( 'Lazy ads (below-fold) ON', 'check', '1', 'Viewability + CLS — AdSense RPM ki manchi' ),
				'ads_on_policy'  => array( 'Legal pages lo ads (privacy/about)', 'check', '0', 'Default OFF (AdSense policy safe)' ),
				'sticky_ad'      => array( 'Sticky bottom ad ON', 'check', '0', 'Mobile lo kindha fixed ad (house/AdSense anchor)' ),
				'house_ads'      => array( 'House ads (JSON)', 'textarea', '', 'Filled by the bot (ads/house.json → here). Format: [{"title":"..","text":"..","url":".."}]' ),
				'partner_ad_enabled' => array( 'Featured college partner ad ON', 'check', '0', 'ON chesthe homepage mid sponsored slot lo mee partner photo + copy + link render avutayi' ),
				'partner_ad_name'    => array( 'Partner name', 'text', '', 'College/institute/business name — image kinda small label ga kanipistundi' ),
				'partner_ad_title'   => array( 'Partner ad headline', 'text', '', 'Example: Admissions open for B.Tech, MBA & skill courses' ),
				'partner_ad_description' => array( 'Partner ad description', 'textarea', '', 'Short, factual student-useful description. Claims ni partner tho verify cheyyandi.' ),
				'partner_ad_image_url' => array( 'Partner photo URL', 'text', '', 'WordPress Media Library lo image upload chesi full https:// URL ikkada paste cheyyandi (1200×630 or similar)' ),
				'partner_ad_link'    => array( 'Partner destination URL', 'text', '', 'Full https:// admissions/course page URL. Sponsored link ga rel=sponsored nofollow tho render avutundi.' ),
				'partner_ad_cta'     => array( 'Partner button text', 'text', 'View details →', 'Example: Apply now → / View courses →' ),
			),
		),
		'socials' => array(
			'title'  => 'Social media',
			'fields' => array(
				'social_whatsapp'  => array( 'WhatsApp number', 'text', '9182739312', '10-digit mobile — +91 avasaram ledu (example: 9182739312)' ),
				'social_telegram'  => array( 'Telegram', 'text', 'studentup_in', 't.me/<idi> — channel username' ),
				'telegram_channel_url' => array( 'Telegram channel URL override (v91)', 'text', '', 'PRIVATE channel aithe full invite link (https://t.me/+AbCd…); khali unte username t.me link use avutundi' ),
				'social_instagram' => array( 'Instagram', 'text', 'studentup.in', 'instagram.com/<idi>' ),
				'social_linkedin'  => array( 'LinkedIn editorial profile', 'text', '', 'Full https://www.linkedin.com/in/... URL or profile username' ),
				'social_youtube'   => array( 'YouTube', 'text', '@studentupin', 'youtube.com/<idi>' ),
			),
		),
		'content' => array(
			'title'  => 'Content & site',
			'fields' => array(
				'contact_email' => array( 'Contact email', 'text', '', 'Errors/suggestions — falls back to the admin email if empty' ),
				'success_story_form_url' => array( 'Verified Success Story Google Form URL', 'text', '', 'Public intake link. Collect consent + evidence only; never ask for Aadhaar, PAN, bank details, OTPs or passwords.' ),
				'author_name'   => array( 'Editorial team name', 'text', 'StudentUp Editorial Team', 'Shown in the E-E-A-T box under the post' ),
				'author_bio'    => array( 'Editorial team description', 'textarea', 'We verify from official notifications and government websites, then write it in simple language. If you spot a mistake, email us — we fix it fast.', '' ),
				'breaking_json' => array( 'Breaking feed (JSON)', 'textarea', '', 'Bot nimpustundi (--push-theme-data). Format: {"items":[{"title":"..","link":"..","time":"..","tag":".."}]}' ),
				'breaking_enabled' => array( 'Breaking news section ON (v72 default OFF)', 'check', '0', 'OFF lo site lo ticker/section render avvadu (feed data intact unthundi)' ),
				'qual_filter' => array( 'Qualification filter (SSC/10th · SSC +2 · Degree · PG)', 'check', '1', 'Chips on home/archive — the tag is set automatically when a post is saved' ),
				'latest_ticker' => array( 'Legacy latest-jobs ticker (retired)', 'check', '0', 'v126: public scrolling bar removed for a calmer first viewport; retained only so old settings migrate safely' ),
				'notify_banner' => array( 'Critical alerts public banner (v90 notify)', 'check', '1', 'CRITICAL severity alerts site-wide banner ga chupistundi (readers dismiss cheste localStorage lo; admin notices ki impact ledu)' ),
				'notify_queue' => array( 'Notify alert queue (JSON)', 'textarea', '', 'v90: bot/--tg-alert nimpustundi (REST studentup/v1/notify). Format: [{"code":"..","message":"..","severity":"info|warn|critical","ts":123}] — manual ga clear cheyyadaniki edit cheyyochu' ),
				'join_cta_inline' => array( 'Mid-article join strip (WhatsApp/Telegram)', 'check', '1', '2nd para tarvata compact join box — same social options (owner number/username)' ),
				'share_inline' => array( 'In-content share bar (v98 viral reach)', 'check', '1', 'v98: modati H2 tarvata WhatsApp/Telegram share row — post chivara varaku scroll cheyyani readers ki kuda share option kanipistundi (free reach). Mobile lo native share sheet kuda vastundi.' ),
				'upnext' => array( 'Up Next block (article chivara — session depth)', 'check', '1', 'v96: ade category lo kotha posts 3 — reader tap cheste NIJAMAINA kotha pageview (ad refresh policy-safe; timer/auto-reload KAADU)' ),
				'upnext_bar' => array( 'Mobile sticky “next article” bar', 'check', '1', 'v96: scroll 60% tarvata kindha okka link bar — sticky AD tho collide avvadu (adi ON unte bar paiki jarugutundi)' ),
				'saved_enabled' => array( 'Saved / bookmarks (🔖 reader save-for-later)', 'check', '1', 'v92: readers cards/posts meeda 🔖 save cheyyagalaru (localStorage — DB/cookie ledu, privacy-safe). OFF chesthe button + panel render avvavu' ),
				'saved_max' => array( 'Saved posts limit (per browser)', 'text', '60', 'v92: localStorage cap (5–200). Limit dhatithe purani vi FIFO ga drop avutayi — browser storage bloat avvadu' ),
			),
		),
		'advanced' => array(
			'title'  => 'Advanced',
			'fields' => array(
				'progress_bar' => array( 'Reading progress bar', 'check', '1', 'Reading progress bar at the top' ),
				'toc'          => array( 'Table of contents (auto TOC)', 'check', '1', 'Automatic jump links from H2/H3' ),
				'pwa'          => array( 'PWA (mobile install + app icon)', 'check', '1', 'On phones "Add to Home screen"' ),
				'install_prompt' => array( 'Download App button (Android/iPhone)', 'check', '1', 'Install prompt on Android/Chrome, Share hint on iPhone' ),
				'schema'       => array( 'JSON-LD schema (Organization/WebSite)', 'check', '1', 'Google ki site identity' ),
				'consent_mode'    => array( 'Google Consent Mode v2', 'check', '1', 'EEA/UK/CH ki consent varaku ads hold (Google rule) — India ki impact ledu' ),
				'consent_regions' => array( 'Consent regions', 'text', 'EEA,GB,CH', 'AdSense CMP lo mee regions (default EEA+UK+Switzerland)' ),
				'consent_cmp_id'  => array( 'CMP script / snippet', 'text', '', 'AdSense → Privacy & messaging → CMP snippet ikkada paste cheyandi' ),
				'news_sitemap'    => array( 'Google News sitemap (/news-sitemap.xml)', 'check', '1', 'Discover/News ki 48h posts + images' ),
				'comments_on'  => array( 'Comments ON (engagement + freshness signal)', 'check', '1', 'OFF chesthe post lo comment form render avvadu' ),
				'security_hardening' => array( 'Security hardening (headers · XML-RPC off · enumeration block)', 'check', '1', 'Default ON — adi 100% safe (REST bot ki impact ledu)' ),
				'hsts_enforce' => array( 'HSTS enforce (HTTPS only)', 'check', '0', 'v81: SSL live confirm ayyaka matrame ON (HTTP staging lo lock risk)' ),
				'content_visibility' => array( 'content-visibility (below-fold render skip → fast)', 'check', '1', 'LCP/INP improvement — modern browsers lo mattrame' ),
				'indexnow_key' => array( 'IndexNow key (hex, 8+ chars)', 'text', '', 'Bot nimpustundi — /<key>.key file automatic ga serve avutundi (Bing/Yandex instant indexing)' ),
				'redirects_json' => array( '301 redirects (JSON)', 'textarea', '', 'v80: {"/old-url/": "/new-url/"} — slug marina old links 404 kakunda 301 (chain/loop safe, relative paths only)' ),
				'ga4_id' => array( 'GA4 Measurement ID', 'text', '', 'v80: G-XXXXXXXXXX — consent-aware analytics (EEA regions lo consent varaku hold, India lo direct)' ),
				'gsc_verify' => array( 'Search Console verification', 'text', '', 'v80: GSC → Settings → Ownership verification → HTML tag content value (meta tag auto)' ),
			),
		),
	);
}

/**
 * Register settings (sanitize type batti).
 */
function studentup_register_settings() {
	foreach ( studentup_option_fields() as $tab ) {
		foreach ( $tab['fields'] as $key => $f ) {
			$type = $f[1];
			register_setting(
				'studentup_options',
				'studentup_' . $key,
				array(
					'type'              => 'check' === $type ? 'boolean' : 'string',
					'sanitize_callback' => 'studentup_sanitize_option',
					'default'           => $f[2],
				)
			);
		}
	}
}
add_action( 'admin_init', 'studentup_register_settings' );

/**
 * Sanitize — JSON fields ki json validate, migilinavi text.
 */
function studentup_sanitize_option( $value ) {
	$value = is_string( $value ) ? trim( $value ) : $value;
	if ( is_string( $value ) && '' !== $value && ( '{' === $value[0] || '[' === $value[0] ) ) {
		$decoded = json_decode( $value, true );
		if ( null === $decoded ) {
			add_settings_error( 'studentup_options', 'studentup_json',
				'JSON tappu undi — aa field save cheyyaledu.', 'error' );
			return '';
		}
		return wp_json_encode( $decoded, JSON_UNESCAPED_UNICODE );
	}
	if ( is_string( $value ) ) {
		return wp_kses_post( $value );
	}
	return $value;
}

/**
 * Admin menu + page.
 */
function studentup_admin_menu() {
	add_menu_page(
		'StudentUp Settings', 'StudentUp', 'manage_options', 'studentup-settings',
		'studentup_settings_page', 'dashicons-megaphone', 58
	);
}
add_action( 'admin_menu', 'studentup_admin_menu' );

/**
 * Settings page — tabs (Ads / Socials / Content / Advanced).
 */
function studentup_settings_page() {
	if ( ! current_user_can( 'manage_options' ) ) {
		return;
	}
	$all  = studentup_option_fields();
	$tabs = array_keys( $all );
	$tab  = isset( $_GET['tab'] ) ? sanitize_key( wp_unslash( $_GET['tab'] ) ) : $tabs[0]; // phpcs:ignore WordPress.Security.NonceVerification
	if ( ! isset( $all[ $tab ] ) ) {
		$tab = $tabs[0];
	}
	?>
	<div class="wrap">
		<h1>🎓 StudentUp Settings</h1>
		<p>Idi mee site options panelu — bot kuda ivi REST tho chaduvutundi
			(<code>/wp-json/studentup/v1/options</code>). JSON fields ni bot nimpustundi;
			mirvu kuda edit cheyyachu.</p>
		<?php settings_errors( 'studentup_options' ); ?>
		<h2 class="nav-tab-wrapper">
			<?php foreach ( $all as $slug => $data ) : ?>
				<a class="nav-tab <?php echo esc_attr( $slug === $tab ? 'nav-tab-active' : '' ); ?>"
					href="<?php echo esc_url( admin_url( 'admin.php?page=studentup-settings&tab=' . $slug ) ); ?>">
					<?php echo esc_html( $data['title'] ); ?></a>
			<?php endforeach; ?>
		</h2>
		<form method="post" action="options.php">
			<?php settings_fields( 'studentup_options' ); ?>
			<input type="hidden" name="studentup_active_tab" value="<?php echo esc_attr( $tab ); ?>">
			<table class="form-table" role="presentation">
			<?php
			foreach ( $all[ $tab ]['fields'] as $key => $f ) :
				$name  = 'studentup_' . $key;
				$value = get_option( $name, $f[2] );
				?>
				<tr>
					<th scope="row"><label for="<?php echo esc_attr( $name ); ?>"><?php echo esc_html( $f[0] ); ?></label></th>
					<td>
						<?php if ( 'check' === $f[1] ) : ?>
							<label><input type="checkbox" id="<?php echo esc_attr( $name ); ?>"
								name="<?php echo esc_attr( $name ); ?>" value="1"
								<?php checked( '1', (string) $value ); ?>> ON</label>
						<?php elseif ( 'textarea' === $f[1] ) : ?>
							<textarea id="<?php echo esc_attr( $name ); ?>" name="<?php echo esc_attr( $name ); ?>"
								rows="6" class="large-text code"><?php echo esc_textarea( (string) $value ); ?></textarea>
						<?php else : ?>
							<input type="text" id="<?php echo esc_attr( $name ); ?>"
								name="<?php echo esc_attr( $name ); ?>" class="regular-text"
								value="<?php echo esc_attr( (string) $value ); ?>">
						<?php endif; ?>
						<?php if ( ! empty( $f[3] ) ) : ?>
							<p class="description"><?php echo esc_html( $f[3] ); ?></p>
						<?php endif; ?>
					</td>
				</tr>
			<?php endforeach; ?>
			</table>
			<?php submit_button( 'Save changes' ); ?>
		</form>
		<hr>
		<p><strong>Bot commands:</strong>
			<code>python run.py --push-theme-data</code> — JSON fields (breaking/house/deadline) ni
			ee options ki sync chestundi.</p>
	</div>
	<?php
}

/**
 * REST options bridge — bot ki (GET public-safe, POST admin mattrame).
 */
function studentup_register_options_route() {
	register_rest_route(
		'studentup/v1',
		'/options',
		array(
			array(
				'methods'             => 'GET',
				'permission_callback' => '__return_true',
				'callback'            => 'studentup_rest_get_options',
			),
			array(
				'methods'             => 'POST',
				'permission_callback' => function () {
					return current_user_can( 'manage_options' );
				},
				'callback'            => 'studentup_rest_set_options',
			),
		)
	);
}
add_action( 'rest_api_init', 'studentup_register_options_route' );

/**
 * GET — public info (secrets kaadu: house ads + socials + ads presence).
 */
function studentup_rest_get_options() {
	$house = json_decode( (string) studentup_opt( 'house_ads', '' ), true );
	return new WP_REST_Response(
		array(
			'site'        => home_url( '/' ),
			'theme'       => 'studentup',
			'version'     => defined( 'STUDENTUP_VERSION' ) ? STUDENTUP_VERSION : '',
			'socials'     => array(
				'whatsapp'  => studentup_opt( 'social_whatsapp', '9182739312' ),
				'telegram'  => studentup_opt( 'social_telegram', 'studentup_in' ),
				'instagram' => studentup_opt( 'social_instagram', 'studentup.in' ),
				'linkedin'  => studentup_opt( 'social_linkedin', '' ),
				'youtube'   => studentup_opt( 'social_youtube', '@studentupin' ),
			),
			'adsense_on'  => (bool) studentup_opt( 'adsense_client', '' ),
			'sticky_ad'   => (bool) studentup_opt( 'sticky_ad', '0' ),
			'toc'         => (bool) studentup_opt( 'toc', '1' ),
			'progress'    => (bool) studentup_opt( 'progress_bar', '1' ),
			'house_ads'   => is_array( $house ) ? count( $house ) : 0,
			'posts'       => (int) wp_count_posts()->publish,
		),
		200
	);
}

/**
 * POST — bot sync (breaking/house/deadline JSON + slots).
 */
function studentup_rest_set_options( WP_REST_Request $request ) {
	$body    = $request->get_json_params();
	$allowed = array();
	foreach ( studentup_option_fields() as $tab ) {
		foreach ( $tab['fields'] as $key => $f ) {
			$allowed[ $key ] = $f[1];
		}
	}
	$saved = array();
	foreach ( (array) $body as $key => $value ) {
		if ( ! isset( $allowed[ $key ] ) ) {
			continue;
		}
		$name = 'studentup_' . $key;
		if ( 'check' === $allowed[ $key ] ) {
			update_option( $name, $value ? '1' : '0' );
		} else {
			update_option( $name, studentup_sanitize_option( is_string( $value ) ? $value : wp_json_encode( $value, JSON_UNESCAPED_UNICODE ) ) );
		}
		$saved[] = $key;
	}
	return new WP_REST_Response( array( 'ok' => true, 'saved' => $saved ), 200 );
}

/**
 * WhatsApp number normalizer — owner 10-digit mobile ichina (9182739312),
 * +91 tho ichina (+919182739312), 0 tho ichina — anni cases lo wa.me ki
 * panikocche digits (919182739312) vastayi. International numbers ni munchamu.
 */
function studentup_wa_number( $raw = '' ) {
	$d = preg_replace( '/[^0-9]/', '', (string) $raw );
	$d = ltrim( $d, '0' );
	if ( 10 === strlen( $d ) && preg_match( '/^[6-9]/', $d ) ) {
		return '91' . $d;
	}
	if ( 12 === strlen( $d ) && 0 === strpos( $d, '91' ) ) {
		return $d;
	}
	return $d;
}

/**
 * Call/display number — user ki +91 lekunda 10-digit (9182739312).
 */
function studentup_call_number( $raw = '' ) {
	$d = preg_replace( '/[^0-9]/', '', (string) $raw );
	$d = ltrim( $d, '0' );
	if ( 12 === strlen( $d ) && 0 === strpos( $d, '91' ) ) {
		$d = substr( $d, 2 );
	}
	return $d;
}

/**
 * Social URLs — options nunchi (footer/header ki).
 */
function studentup_social_links() {
	$wa  = studentup_wa_number( studentup_opt( 'social_whatsapp', '9182739312' ) );
	$ig  = ltrim( (string) studentup_opt( 'social_instagram', 'studentup.in' ), '@' );
	$li  = trim( (string) studentup_opt( 'social_linkedin', '' ) );
	$liu = '';
	if ( $li ) {
		$liu = 0 === strpos( $li, 'http' ) ? $li : 'https://www.linkedin.com/in/' . ltrim( $li, '@/' );
	}
	$yt  = (string) studentup_opt( 'social_youtube', '@studentupin' );
	$ytu = 0 === strpos( $yt, 'http' ) ? $yt : 'https://www.youtube.com/' . ( 0 === strpos( $yt, '@' ) ? $yt : '@' . $yt );

	/*
	 * v93 FIX (nijamaina bug): ippati varaku idi `https://t.me/<username>` ne
	 * hardcode cheyyadam valla v91 lo add chesina **private channel invite
	 * override** (`telegram_channel_url`) footer rail icon · mobile panel ·
	 * footer "Telegram channel" link ki **apply avvatledu**. Private channel
	 * unte aa muggintiki link tappu (public username) velledi → join fail.
	 * Ippudu resolver okkate source (function unte adi — lekapote fallback).
	 */
	if ( function_exists( 'studentup_tg_channel_url' ) && studentup_tg_channel_url() ) {
		$tg_url = studentup_tg_channel_url();
	} else {
		$tg_user = ltrim( (string) studentup_opt( 'social_telegram', 'studentup_in' ), '@' );
		$tg_url  = 'https://t.me/' . $tg_user;
	}

	return array(
		'whatsapp'  => 'https://wa.me/' . $wa,
		'telegram'  => $tg_url,
		'instagram' => 'https://www.instagram.com/' . $ig . '/',
		'linkedin'  => $liu,
		'youtube'   => $ytu,
	);
}

/**
 * Contact email — option, lekapote admin email.
 */
function studentup_contact_email() {
	$email = (string) studentup_opt( 'contact_email', '' );
	return is_email( $email ) ? $email : (string) get_option( 'admin_email', '' );
}

/**
 * v89: brand SVG icons (CC0 / Simple Icons paths) — emoji 💬✈️📸▶️ badulu.
 * Emoji platform batti marutayi (phones lo tappu ga kanipistayi); inline SVG
 * prathi device lo same, official brand shape/color tho untundi.
 *
 * @param string $key whatsapp|telegram|instagram|youtube|x|call|email|link
 * @param int    $size px size (default 18).
 * @return string inline SVG markup
 */
function studentup_social_icon( $key, $size = 18 ) {
	$size  = max( 10, min( 64, (int) $size ) );
	$paths = array(
		'whatsapp'  => 'M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 0 1-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 0 1-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 0 1 2.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0 0 12.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 0 0 5.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 0 0-3.48-8.413Z',
		'telegram'  => 'M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z',
		'instagram' => 'M12 0C8.74 0 8.333.015 7.053.072 5.775.132 4.905.333 4.14.63c-.789.306-1.459.717-2.126 1.384S.935 3.35.63 4.14C.333 4.905.131 5.775.072 7.053.012 8.333 0 8.74 0 12s.015 3.667.072 4.947c.06 1.277.261 2.148.558 2.913.306.788.717 1.459 1.384 2.126.667.666 1.336 1.079 2.126 1.384.766.296 1.636.499 2.913.558C8.333 23.988 8.74 24 12 24s3.667-.015 4.947-.072c1.277-.06 2.148-.262 2.913-.558.788-.306 1.459-.718 2.126-1.384.666-.667 1.079-1.335 1.384-2.126.296-.765.499-1.636.558-2.913.06-1.28.072-1.687.072-4.947s-.015-3.667-.072-4.947c-.06-1.277-.262-2.149-.558-2.913-.306-.789-.718-1.459-1.384-2.126C21.319 1.347 20.651.935 19.86.63c-.765-.297-1.636-.499-2.913-.558C15.667.012 15.26 0 12 0zm0 2.16c3.203 0 3.585.016 4.85.071 1.17.055 1.805.249 2.227.415.562.217.96.477 1.382.896.419.42.679.819.896 1.381.164.422.36 1.057.413 2.227.057 1.266.07 1.646.07 4.85s-.015 3.585-.074 4.85c-.061 1.17-.256 1.805-.421 2.227-.224.562-.479.96-.899 1.382-.419.419-.824.679-1.38.896-.42.164-1.065.36-2.235.413-1.274.057-1.649.07-4.859.07-3.211 0-3.586-.015-4.859-.074-1.171-.061-1.816-.256-2.236-.421-.569-.224-.96-.479-1.379-.899-.421-.419-.69-.824-.9-1.38-.165-.42-.359-1.065-.42-2.235-.045-1.26-.061-1.649-.061-4.844 0-3.196.016-3.586.061-4.861.061-1.17.255-1.814.42-2.234.21-.57.479-.96.9-1.381.419-.419.81-.689 1.379-.898.42-.166 1.051-.361 2.221-.421 1.275-.045 1.65-.06 4.859-.06l.045.03zm0 3.678a6.162 6.162 0 1 0 0 12.324 6.162 6.162 0 1 0 0-12.324zM12 16c-2.21 0-4-1.79-4-4s1.79-4 4-4 4 1.79 4 4-1.79 4-4 4zm7.846-10.405a1.441 1.441 0 0 1-2.88 0 1.44 1.44 0 0 1 2.88 0z',
		'youtube'   => 'M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z',
		'x'         => 'M18.901 1.153h3.68l-8.04 9.19L24 22.846h-7.406l-5.8-7.584-6.638 7.584H.474l8.6-9.83L0 1.154h7.594l5.243 6.932ZM17.61 20.644h2.039L6.486 3.24H4.298Z',
		'call'      => 'M6.62 10.79c1.44 2.83 3.76 5.14 6.59 6.59l2.2-2.2c.27-.27.67-.36 1.02-.24 1.12.37 2.33.57 3.57.57.55 0 1 .45 1 1V20c0 .55-.45 1-1 1-9.39 0-17-7.61-17-17 0-.55.45-1 1-1h3.5c.55 0 1 .45 1 1 0 1.25.2 2.45.57 3.57.11.35.03.74-.25 1.02l-2.2 2.2Z',
		'email'     => 'M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2Zm0 4-8 5-8-5V6l8 5 8-5v2Z',
		'link'      => 'M3.9 12c0-1.71 1.39-3.1 3.1-3.1h4V7H7c-2.76 0-5 2.24-5 5s2.24 5 5 5h4v-1.9H7c-1.71 0-3.1-1.39-3.1-3.1zM8 13h8v-2H8v2zm9-6h-4v1.9h4c1.71 0 3.1 1.39 3.1 3.1s-1.39 3.1-3.1 3.1h-4V17h4c2.76 0 5-2.24 5-5s-2.24-5-5-5z',
	);
	$d = isset( $paths[ $key ] ) ? $paths[ $key ] : $paths['link'];
	return '<svg class="su-icn su-icn-' . esc_attr( $key ) . '" viewBox="0 0 24 24" width="' . (int) $size
		. '" height="' . (int) $size . '" fill="currentColor" aria-hidden="true" focusable="false"><path d="'
		. $d . '"/></svg>';
}
