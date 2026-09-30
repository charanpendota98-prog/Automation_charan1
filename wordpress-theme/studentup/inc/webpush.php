<?php
/**
 * v163 — Real Web Push (VAPID).
 *
 * Telegram/WhatsApp share links unnayi, kani avi reader **maname** click
 * cheyyali. Web push veru: browser closed unna, phone lo direct notification
 * velthundi. Return traffic ki top sites #1 lever idi.
 *
 * Ee file chese pani:
 *  - subscription store (sonta table, `wp_options` kaadu — vela subscriptions
 *    autoload option lo pedithe prati page load slow avutundi),
 *  - REST: subscribe / unsubscribe (public, rate-limited) + list (auth only,
 *    bot ee endpoint nunchi subscriptions teesukoni push pampistundi),
 *  - prompt UI — **immediate ga adagam**. Chrome abusive-permission
 *    penalty ki adi ne karanam. Reader 2nd pageview leda oka click taruvata
 *    ne adugutundi, "No thanks" ante 30 rojulu malli adagadu.
 *
 * Push *pampadam* bot pani (`python run.py --push-send`), endukante VAPID
 * signing ki proper crypto library kavali.
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

define( 'STUDENTUP_PUSH_TABLE', 'studentup_push_subs' );

/**
 * Subscriptions table (theme activate ayinappudu / version marinappudu).
 */
function studentup_push_install_table() {
	global $wpdb;
	$table   = $wpdb->prefix . STUDENTUP_PUSH_TABLE;
	$current = (string) get_option( 'su_push_db_version', '' );
	if ( '1' === $current ) {
		return;
	}
	require_once ABSPATH . 'wp-admin/includes/upgrade.php';
	$charset = $wpdb->get_charset_collate();
	$sql     = "CREATE TABLE {$table} (
		id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
		endpoint varchar(500) NOT NULL,
		p256dh varchar(255) NOT NULL,
		auth varchar(255) NOT NULL,
		created datetime NOT NULL,
		PRIMARY KEY  (id),
		UNIQUE KEY endpoint (endpoint(191))
	) {$charset};";
	dbDelta( $sql );
	update_option( 'su_push_db_version', '1', false );
}
add_action( 'after_switch_theme', 'studentup_push_install_table' );
add_action( 'admin_init', 'studentup_push_install_table' );

/**
 * VAPID public key (bot `--push-keys` tho generate chesi ikkada pettali).
 *
 * @return string
 */
function studentup_push_public_key() {
	return trim( (string) get_option( 'studentup_push_public_key', '' ) );
}

/**
 * Push ON aa? Key lekapothe feature motham off — half-working prompt
 * chupinchi reader permission waste cheyyadam cheddha.
 *
 * @return bool
 */
function studentup_push_enabled() {
	return (bool) studentup_opt( 'webpush', '1' ) && '' !== studentup_push_public_key();
}

/**
 * REST routes.
 */
function studentup_push_routes() {
	register_rest_route(
		'studentup/v1',
		'/push-subscribe',
		array(
			'methods'             => 'POST',
			'permission_callback' => '__return_true',
			'callback'            => 'studentup_push_subscribe',
			'args'                => array(
				'endpoint' => array( 'required' => true, 'type' => 'string' ),
				'p256dh'   => array( 'required' => true, 'type' => 'string' ),
				'auth'     => array( 'required' => true, 'type' => 'string' ),
			),
		)
	);
	register_rest_route(
		'studentup/v1',
		'/push-subscribers',
		array(
			'methods'             => 'GET',
			// Bot application-password tho login avutundi; public ki list ivvam.
			'permission_callback' => function () {
				return current_user_can( 'edit_posts' );
			},
			'callback'            => 'studentup_push_list',
		)
	);
}
add_action( 'rest_api_init', 'studentup_push_routes' );

/**
 * Subscribe (public).
 *
 * @param WP_REST_Request $req request.
 * @return WP_REST_Response|WP_Error
 */
function studentup_push_subscribe( $req ) {
	if ( ! studentup_push_enabled() ) {
		return new WP_Error( 'su_push_off', 'Push off', array( 'status' => 403 ) );
	}
	global $wpdb;

	$endpoint = esc_url_raw( (string) $req->get_param( 'endpoint' ) );
	$p256dh   = sanitize_text_field( (string) $req->get_param( 'p256dh' ) );
	$auth     = sanitize_text_field( (string) $req->get_param( 'auth' ) );

	// Only real push services. Ee check lekapothe ee endpoint ni open
	// relay la vaadukovachu.
	$host = wp_parse_url( $endpoint, PHP_URL_HOST );
	$ok   = $host && (bool) preg_match(
		'~(\.googleapis\.com|\.mozilla\.com|\.mozaws\.net|\.windows\.com|\.apple\.com)$~i',
		$host
	);
	if ( ! $ok || strlen( $endpoint ) > 500 || '' === $p256dh || '' === $auth ) {
		return new WP_Error( 'su_push_bad', 'Bad subscription', array( 'status' => 400 ) );
	}

	$table = $wpdb->prefix . STUDENTUP_PUSH_TABLE;
	// phpcs:disable WordPress.DB.DirectDatabaseQuery
	$wpdb->query(
		$wpdb->prepare(
			"INSERT INTO {$table} (endpoint, p256dh, auth, created) VALUES (%s, %s, %s, %s)
			 ON DUPLICATE KEY UPDATE p256dh = VALUES(p256dh), auth = VALUES(auth)",
			$endpoint,
			$p256dh,
			$auth,
			current_time( 'mysql' )
		)
	);
	// phpcs:enable
	return rest_ensure_response( array( 'ok' => true ) );
}

/**
 * Subscriber list (auth only) — bot ee data tho push pampistundi.
 *
 * @return WP_REST_Response
 */
function studentup_push_list() {
	global $wpdb;
	$table = $wpdb->prefix . STUDENTUP_PUSH_TABLE;
	// phpcs:disable WordPress.DB.DirectDatabaseQuery
	$rows = $wpdb->get_results( "SELECT endpoint, p256dh, auth FROM {$table} LIMIT 20000", ARRAY_A );
	// phpcs:enable
	return rest_ensure_response( array( 'count' => count( (array) $rows ), 'subs' => $rows ) );
}

/**
 * Prompt UI — engagement taruvata ne.
 */
function studentup_push_prompt() {
	if ( is_admin() || ! studentup_push_enabled() ) {
		return;
	}
	$data = array(
		'key'  => studentup_push_public_key(),
		'rest' => esc_url_raw( rest_url( 'studentup/v1/push-subscribe' ) ),
		'sw'   => esc_url_raw( add_query_arg( 'studentup_sw', '1', home_url( '/' ) ) ),
	);
	?>
	<script>
	(function () {
		var CFG = <?php echo wp_json_encode( $data ); ?>;
		if (!('serviceWorker' in navigator) || !('PushManager' in window)) { return; }
		if (Notification.permission === 'denied') { return; }

		var KEY = 'su-push-v1';
		var store = {};
		try { store = JSON.parse(localStorage.getItem(KEY) || '{}'); } catch (e) { store = {}; }
		if (store.done) { return; }
		// "No thanks" annaka 30 rojulu malli adagam.
		if (store.snoozeUntil && Date.now() < store.snoozeUntil) { return; }

		// Reader engage ayyaka ne adugutam: 2nd pageview, leda 25s + scroll.
		store.views = (store.views || 0) + 1;
		try { localStorage.setItem(KEY, JSON.stringify(store)); } catch (e) {}
		var engaged = store.views >= 2;

		function b64(base64String) {
			var pad = '='.repeat((4 - base64String.length % 4) % 4);
			var raw = atob((base64String + pad).replace(/-/g, '+').replace(/_/g, '/'));
			var out = new Uint8Array(raw.length);
			for (var i = 0; i < raw.length; i++) { out[i] = raw.charCodeAt(i); }
			return out;
		}

		function save(sub) {
			var j = sub.toJSON();
			return fetch(CFG.rest, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					endpoint: j.endpoint,
					p256dh: j.keys && j.keys.p256dh,
					auth: j.keys && j.keys.auth
				})
			});
		}

		function subscribe() {
			navigator.serviceWorker.register(CFG.sw).then(function (reg) {
				return reg.pushManager.subscribe({
					userVisibleOnly: true,
					applicationServerKey: b64(CFG.key)
				});
			}).then(save).then(function () {
				store.done = true;
				try { localStorage.setItem(KEY, JSON.stringify(store)); } catch (e) {}
				bar.remove();
			}).catch(function () { bar.remove(); });
		}

		var bar = null;
		function show() {
			if (bar || !engaged) { return; }
			bar = document.createElement('div');
			bar.className = 'su-push-bar';
			bar.innerHTML = '<span class="su-push-txt">' . studentup_ui_icon( 'bell', 15 ) . ' Kotha jobs &amp; results alerts kavala?</span>' // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG
				+ '<button type="button" class="su-push-yes">Yes, alert cheyandi</button>'
				+ '<button type="button" class="su-push-no">No thanks</button>';
			document.body.appendChild(bar);
			bar.querySelector('.su-push-yes').addEventListener('click', subscribe);
			bar.querySelector('.su-push-no').addEventListener('click', function () {
				store.snoozeUntil = Date.now() + 30 * 24 * 3600 * 1000;
				try { localStorage.setItem(KEY, JSON.stringify(store)); } catch (e) {}
				bar.remove();
			});
		}

		if (engaged) { window.setTimeout(show, 4000); }
	})();
	</script>
	<?php
}
add_action( 'wp_footer', 'studentup_push_prompt', 30 );
