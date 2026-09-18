<?php
/**
 * v64: StudentUp Settings — anni website options okka chota (admin page + REST).
 *
 * Enduku: ads, socials, exam link, author info, house ads — ivi WordPress
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
			'title'  => 'ప్రకటనలు (Ads)',
			'fields' => array(
				'ads_enabled'    => array( 'Ads ON (site) — master switch', 'check', '1', 'OFF chesthe e pages lo ads render avvavu' ),
				'adsense_client' => array( 'AdSense Client ID', 'text', '', 'ca-pub-XXXXXXXXXXXXXXXX (AdSense approve ayyaka)' ),
				'adsense_auto'   => array( 'AdSense Auto ads (head code)', 'check', '0', 'AdSense auto ads script ni head lo add chestundi' ),
				'adsense_slot_top_leaderboard' => array( 'Slot: top-leaderboard', 'text', '', 'AdSense → Ads → By ad unit → code lo data-ad-slot' ),
				'adsense_slot_sidebar'         => array( 'Slot: sidebar', 'text', '', '' ),
				'adsense_slot_anchor'          => array( 'Slot: anchor/sticky (mobile)', 'text', '', '' ),
				'adsense_slot_mid'      => array( 'Slot: mid (in-article, ₹ highest)', 'text', '', 'Article madhya lo — highest RPM slot' ),
				'adsense_slot_in_feed'  => array( 'Slot: in-feed (grid madhya)', 'text', '', 'హోమ్ grid lo cards madhya' ),
				'adsense_slot_below_content' => array( 'Slot: below-content (article tarvata)', 'text', '', 'Article chivarana — 2వ highest RPM slot' ),
				'ads_txt'        => array( 'ads.txt content', 'textarea', '', 'Site root /ads.txt ga serve avutundi (AdSense approval tarvata publisher id line)' ),
				'in_article_ad'  => array( 'In-article ad (content 3rd para tarvata)', 'check', '1', 'Highest-CTR placement — AdSense/ house ad (density cap + lazy tho)' ),
				'max_ads'        => array( 'Page ki max ads (density cap)', 'text', '4', '4-5 safe (AdSense + UX). Ekkuva = policy risk' ),
				'lazy_ads'       => array( 'Lazy ads (below-fold) ON', 'check', '1', 'Viewability + CLS — AdSense RPM ki manchi' ),
				'ads_on_policy'  => array( 'Legal pages lo ads (privacy/about)', 'check', '0', 'Default OFF (AdSense policy safe)' ),
				'sticky_ad'      => array( 'Sticky bottom ad ON', 'check', '0', 'Mobile lo kindha fixed ad (house/AdSense anchor)' ),
				'house_ads'      => array( 'House ads (JSON)', 'textarea', '', 'Bot nimpustundi (ads/house.json → ఇక్కడికి). Format: [{"title":"..","text":"..","url":".."}]' ),
			),
		),
		'socials' => array(
			'title'  => 'సోషల్ మీడియా',
			'fields' => array(
				'social_whatsapp'  => array( 'WhatsApp నంబర్', 'text', '919999999999', 'Country code tho, + లేకుండా (ఉదా: 919876543210)' ),
				'social_telegram'  => array( 'Telegram', 'text', 'studentup_in', 't.me/<idi> — channel username' ),
				'social_instagram' => array( 'Instagram', 'text', 'studentup.in', 'instagram.com/<idi>' ),
				'social_youtube'   => array( 'YouTube', 'text', '@studentupin', 'youtube.com/<idi>' ),
			),
		),
		'content' => array(
			'title'  => 'కంటెంట్ + సైట్',
			'fields' => array(
				'exam_url'      => array( 'పరీక్ష పోర్టల్ URL', 'text', '', '🎓 ప్రత్యక్ష పరీక్ష బటన్ ఎక్కడికి వెళ్లాలి' ),
				'contact_email' => array( 'సంప్రదింపు ఇమెయిల్', 'text', '', 'తప్పులు/సూచనలు — ఖాళీగా ఉంటే admin email వాడుతుంది' ),
				'author_name'   => array( 'ఎడిటోరియల్ టీమ్ పేరు', 'text', 'StudentUp ఎడిటోరియల్ టీమ్', 'పోస్ట్ కింద E-E-A-T box లో కనిపిస్తుంది' ),
				'author_bio'    => array( 'ఎడిటోరియల్ టీమ్ వివరణ', 'textarea', 'అధికారిక నోటిఫికేషన్లు, ప్రభుత్వ వెబ్‌సైట్ల నుంచి ధృవీకరించి తెలుగులో రాస్తాము. తప్పు కనిపిస్తే మెయిల్ చేయండి — వెంటనే సరిచేస్తాము.', '' ),
				'breaking_json' => array( 'బ్రేకింగ్ ఫీడ్ (JSON)', 'textarea', '', 'Bot nimpustundi (--push-theme-data). Format: {"items":[{"title":"..","link":"..","time":"..","tag":".."}]}' ),
				'breaking_enabled' => array( 'బ్రేకింగ్ న్యూస్ సెక్షన్ ON (v72 default OFF)', 'check', '0', 'OFF lo site lo ticker/section render avvadu (feed data intact unthundi)' ),
				'qual_filter' => array( 'విద్యార్హత ఫిల్టర్ (10th · 10+2 · డిగ్రీ · పీజీ)', 'check', '1', 'Home/archive lo chips — post save ayyaka tag automatic ga set avutundi' ),
				'deadline_json' => array( 'పరీక్ష కౌంట్‌డౌన్ (JSON)', 'textarea', '', '{"title":"..","date":"ISO"} — hero countdown (bot kuda nimpistundi)' ),
			),
		),
		'advanced' => array(
			'title'  => 'అడ్వాన్స్‌డ్',
			'fields' => array(
				'progress_bar' => array( 'Reading progress bar', 'check', '1', 'పోస్ట్ చదువుతుంటే పైన progress' ),
				'toc'          => array( 'విషయ సూచిక (auto TOC)', 'check', '1', 'H2/H3 నుంచి ఆటోమేటిక్ jump links' ),
				'pwa'          => array( 'PWA (mobile install + app icon)', 'check', '1', 'ఫోన్‌లో "Add to Home screen"' ),
				'install_prompt' => array( 'యాప్గా ఇన్స్టాల్ చేయండి బటన్ (Android/iPhone)', 'check', '1', 'Android/Chrome lo install prompt, iPhone lo Share hint' ),
				'schema'       => array( 'JSON-LD schema (Organization/WebSite)', 'check', '1', 'Google ki site identity' ),
				'consent_mode'    => array( 'Google Consent Mode v2', 'check', '1', 'EEA/UK/CH ki consent varaku ads hold (Google rule) — India ki impact ledu' ),
				'consent_regions' => array( 'Consent regions', 'text', 'EEA,GB,CH', 'AdSense CMP lo mee regions (default EEA+UK+Switzerland)' ),
				'consent_cmp_id'  => array( 'CMP script / snippet', 'text', '', 'AdSense → Privacy & messaging → CMP snippet ikkada paste cheyandi' ),
				'news_sitemap'    => array( 'Google News sitemap (/news-sitemap.xml)', 'check', '1', 'Discover/News ki 48h posts + images' ),
				'comments_on'  => array( 'కామెంట్లు ON (engagement + freshness signal)', 'check', '1', 'OFF chesthe post lo comment form render avvadu' ),
				'security_hardening' => array( 'Security hardening (headers · XML-RPC off · enumeration block)', 'check', '1', 'Default ON — adi 100% safe (REST bot ki impact ledu)' ),
				'content_visibility' => array( 'content-visibility (below-fold render skip → fast)', 'check', '1', 'LCP/INP improvement — modern browsers lo mattrame' ),
				'indexnow_key' => array( 'IndexNow key (hex, 8+ chars)', 'text', '', 'Bot nimpustundi — /<key>.key file automatic ga serve avutundi (Bing/Yandex instant indexing)' ),
				'api_base'     => array( 'Bot API base URL', 'text', '', 'పరీక్ష పోర్టల్/ఇతర internal API (optional)' ),
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
			<?php submit_button( 'సేవ్ చేయండి' ); ?>
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
				'whatsapp'  => studentup_opt( 'social_whatsapp', '919999999999' ),
				'telegram'  => studentup_opt( 'social_telegram', 'studentup_in' ),
				'instagram' => studentup_opt( 'social_instagram', 'studentup.in' ),
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
 * Social URLs — options nunchi (footer/header ki).
 */
function studentup_social_links() {
	$wa  = preg_replace( '/[^0-9]/', '', (string) studentup_opt( 'social_whatsapp', '919999999999' ) );
	$tg  = ltrim( (string) studentup_opt( 'social_telegram', 'studentup_in' ), '@' );
	$ig  = ltrim( (string) studentup_opt( 'social_instagram', 'studentup.in' ), '@' );
	$yt  = (string) studentup_opt( 'social_youtube', '@studentupin' );
	$ytu = 0 === strpos( $yt, 'http' ) ? $yt : 'https://www.youtube.com/' . ( 0 === strpos( $yt, '@' ) ? $yt : '@' . $yt );
	return array(
		'whatsapp'  => 'https://wa.me/' . $wa,
		'telegram'  => 'https://t.me/' . $tg,
		'instagram' => 'https://www.instagram.com/' . $ig . '/',
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
