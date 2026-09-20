<?php
/**
 * v90: StudentUp Notify — site-wide alert queue (theme 1.9.1).
 *
 * Enduku: bot (guardian/radar) ki site lo okka STANDARD alert channel kavali —
 * "feed stale", "drafts pending", "result released" lanti subject-owner alerts
 * WP Admin lo notices ga + critical aithe PUBLIC banner ga kanipinchali.
 * Telegram owner alerts already unnayi (autoblog/notifier.py) — idi vaatini
 * replace cheyyadu; site-side surface istundi (admin chudakapoina readers ki
 * critical info reach avutundi).
 *
 * Design rules (v89 PART-45 principle — "notify never breaks cron/page"):
 *   1) Queue = WP option `studentup_notify_queue` (array; code-wise dedupe;
 *      cap 20 — purani alerts automatic ga drop).
 *   2) Severities: info · warn · critical (whitelist — vere emi accept kaadu).
 *   3) Admin notices dismiss = per-user meta (okari dismiss inkariki apply kaadu).
 *   4) Public banner = CRITICAL matrame + option gate (`notify_banner`, default ON).
 *      Reader dismiss = localStorage (code-wise) — server round-trip ledu.
 *   5) REST `/studentup/v1/notify` — POST push / GET list / DELETE clear,
 *      anni `manage_options` permission tho (bot application password use chestundi).
 *   6) Prathi callback try/catch lopala — eppudu 500/white-screen raadu.
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/** Max alerts queue lo hold cheyyadam ( FIFO drop ). */
define( 'STUDENTUP_NOTIFY_MAX', 20 );

/**
 * Allowed severities (whitelist — icon map tho).
 *
 * @return array severity => icon
 */
function studentup_notify_severities() {
	return array(
		'info'     => 'ℹ️',
		'warn'     => '⚠️',
		'critical' => '🚨',
	);
}

/**
 * Queue read — always array (corrupt option ayina khali return).
 *
 * @return array[] [ [ 'code', 'message', 'severity', 'ts' ], ... ]
 */
function studentup_notify_all() {
	try {
		$raw = get_option( 'studentup_notify_queue', array() );
		if ( is_string( $raw ) ) {
			$raw = json_decode( $raw, true ); // settings page lo JSON string ga save ayina case
		}
		if ( ! is_array( $raw ) ) {
			return array();
		}
		$out = array();
		foreach ( $raw as $item ) {
			if ( is_array( $item ) && ! empty( $item['code'] ) && ! empty( $item['message'] ) ) {
				$out[] = $item;
			}
		}
		return $out;
	} catch ( Exception $e ) { // phpcs:ignore Generic.CodeAnalysis.EmptyStatement
		return array();
	}
}

/**
 * Push/replace an alert (same code unte update — duplicates ledu).
 *
 * @param string $code     machine id (ex: 'feed_stale') — slug chars matrame.
 * @param string $message  human text (plain — render time esc_html avutundi).
 * @param string $severity info|warn|critical.
 * @return bool saved aa leda aa
 */
function studentup_notify_push( $code, $message, $severity = 'info' ) {
	try {
		$code = sanitize_key( (string) $code );
		$message = trim( wp_strip_all_tags( (string) $message ) );
		$sevs = studentup_notify_severities();
		if ( '' === $code || '' === $message ) {
			return false;
		}
		if ( ! isset( $sevs[ $severity ] ) ) {
			$severity = 'info'; // whitelist miss → safest level.
		}
		$queue = studentup_notify_all();
		$kept  = array();
		foreach ( $queue as $item ) {
			if ( $item['code'] !== $code ) {
				$kept[] = $item;
			}
		}
		$kept[] = array(
			'code'     => $code,
			'message'  => mb_substr( $message, 0, 300 ),
			'severity' => $severity,
			'ts'       => time(),
		);
		// Cap: oldest nundi drop (critical ki priority — last push eppudu fresh).
		if ( count( $kept ) > STUDENTUP_NOTIFY_MAX ) {
			$kept = array_slice( $kept, -STUDENTUP_NOTIFY_MAX );
		}
		return update_option( 'studentup_notify_queue', wp_json_encode( $kept, JSON_UNESCAPED_UNICODE ), false );
	} catch ( Exception $e ) {
		return false;
	}
}

/**
 * Clear one alert (code tho) — leda anni (`__all__`).
 *
 * @param string $code alert code.
 * @return bool
 */
function studentup_notify_clear( $code ) {
	try {
		if ( '__all__' === $code ) {
			return delete_option( 'studentup_notify_queue' );
		}
		$code  = sanitize_key( (string) $code );
		$queue = studentup_notify_all();
		$kept  = array();
		foreach ( $queue as $item ) {
			if ( $item['code'] !== $code ) {
				$kept[] = $item;
			}
		}
		return update_option( 'studentup_notify_queue', wp_json_encode( $kept, JSON_UNESCAPED_UNICODE ), false );
	} catch ( Exception $e ) {
		return false;
	}
}

/* ------------------------------------------------------------------ ADMIN */

/**
 * Admin notices — queue lo unna anni alerts (dismiss per-user).
 */
function studentup_notify_admin_notices() {
	try {
		if ( ! current_user_can( 'manage_options' ) ) {
			return;
		}
		$dismissed = get_user_meta( get_current_user_id(), 'studentup_notify_dismissed', true );
		$dismissed = is_array( $dismissed ) ? $dismissed : array();
		$sevs      = studentup_notify_severities();
		foreach ( studentup_notify_all() as $item ) {
			if ( in_array( $item['code'], $dismissed, true ) ) {
				continue;
			}
			$sev  = isset( $sevs[ $item['severity'] ] ) ? $item['severity'] : 'info';
			$icon = $sevs[ $sev ];
			$cls  = 'critical' === $sev ? 'error' : ( 'warn' === $sev ? 'notice-warning' : 'notice-info' );
			?>
			<div class="notice <?php echo esc_attr( $cls ); ?> su-notice is-dismissible" data-su-notify="<?php echo esc_attr( $item['code'] ); ?>">
				<p><strong><?php echo esc_html( $icon ); ?> StudentUp:</strong> <?php echo esc_html( $item['message'] ); ?>
					<code style="margin-left:6px"><?php echo esc_html( $item['code'] ); ?></code></p>
			</div>
			<?php
		}
	} catch ( Exception $e ) { // phpcs:ignore Generic.CodeAnalysis.EmptyStatement
		// notify valla admin page break avvadu — silent by design.
	}
}
add_action( 'admin_notices', 'studentup_notify_admin_notices' );

/**
 * AJAX dismiss — user meta lo code add (per-user, global kaadu).
 */
function studentup_notify_ajax_dismiss() {
	try {
		if ( ! current_user_can( 'manage_options' ) || ! check_ajax_referer( 'su_notify_dismiss', 'nonce', false ) ) {
			wp_send_json_error( array( 'reason' => 'forbidden' ), 403 );
		}
		$code      = isset( $_POST['code'] ) ? sanitize_key( wp_unslash( $_POST['code'] ) ) : '';
		$dismissed = get_user_meta( get_current_user_id(), 'studentup_notify_dismissed', true );
		$dismissed = is_array( $dismissed ) ? $dismissed : array();
		if ( '' !== $code && ! in_array( $code, $dismissed, true ) ) {
			$dismissed[] = $code;
			update_user_meta( get_current_user_id(), 'studentup_notify_dismissed', array_slice( $dismissed, -50 ) );
		}
		wp_send_json_success( array( 'code' => $code ) );
	} catch ( Exception $e ) {
		wp_send_json_error( array( 'reason' => 'internal' ), 500 );
	}
}
add_action( 'wp_ajax_su_notify_dismiss', 'studentup_notify_ajax_dismiss' );

/**
 * Admin scripts — dismiss handler ki nonce/localize (admin pages matrame).
 *
 * @param string $hook current admin page hook.
 */
function studentup_notify_admin_assets( $hook ) {
	try {
		wp_localize_script(
			'jquery',
			'suNotifyAdmin',
			array( 'ajax' => admin_url( 'admin-ajax.php' ), 'nonce' => wp_create_nonce( 'su_notify_dismiss' ) )
		);
	} catch ( Exception $e ) { // phpcs:ignore Generic.CodeAnalysis.EmptyStatement
	}
}
add_action( 'admin_enqueue_scripts', 'studentup_notify_admin_assets' );

/**
 * Inline admin dismiss handler (jQuery already loaded in WP admin).
 */
function studentup_notify_admin_footer_js() {
	try {
		if ( ! current_user_can( 'manage_options' ) ) {
			return;
		}
		?>
		<script>
		jQuery( function ( $ ) {
			$( document ).on( 'click', '.su-notice .notice-dismiss', function () {
				var notice = $( this ).closest( '.su-notice' );
				var code = notice.data( 'su-notify' );
				if ( ! code || ! window.suNotifyAdmin ) { return; }
				$.post( window.suNotifyAdmin.ajax, {
					action: 'su_notify_dismiss',
					nonce: window.suNotifyAdmin.nonce,
					code: code
				} );
			} );
		} );
		</script>
		<?php
	} catch ( Exception $e ) { // phpcs:ignore Generic.CodeAnalysis.EmptyStatement
	}
}
add_action( 'admin_print_footer_scripts', 'studentup_notify_admin_footer_js' );

/* ----------------------------------------------------------------- PUBLIC */

/**
 * Public critical banner — site-wide, option gate + localStorage dismiss.
 * Header lo (`wp_body_open` tarvata) render avutundi.
 */
function studentup_notify_public_banner() {
	try {
		if ( ! studentup_opt( 'notify_banner', '1' ) ) {
			return; // owner OFF chesadu — respect.
		}
		$sevs = studentup_notify_severities();
		foreach ( studentup_notify_all() as $item ) {
			if ( 'critical' !== $item['severity'] ) {
				continue; // public ki critical matrame (info/warn = admin-only).
			}
			?>
			<div class="su-notify su-notify-critical" role="alert" data-code="<?php echo esc_attr( $item['code'] ); ?>">
				<span class="su-notify-msg"><?php echo esc_html( $sevs['critical'] ); ?> <?php echo esc_html( $item['message'] ); ?></span>
				<button type="button" class="su-notify-close" aria-label="Close">✕</button>
			</div>
			<?php
		}
	} catch ( Exception $e ) { // phpcs:ignore Generic.CodeAnalysis.EmptyStatement
		// public page lo banner fail ayina page render continue avutundi.
	}
}

/* ------------------------------------------------------------------- REST */

/**
 * REST route — bot push/list/clear (manage_options only).
 */
function studentup_notify_register_routes() {
	register_rest_route(
		'studentup/v1',
		'/notify',
		array(
			array(
				'methods'             => 'GET',
				'permission_callback' => function () {
					return current_user_can( 'manage_options' );
				},
				'callback'            => 'studentup_notify_rest_get',
			),
			array(
				'methods'             => 'POST',
				'permission_callback' => function () {
					return current_user_can( 'manage_options' );
				},
				'callback'            => 'studentup_notify_rest_push',
			),
			array(
				'methods'             => 'DELETE',
				'permission_callback' => function () {
					return current_user_can( 'manage_options' );
				},
				'callback'            => 'studentup_notify_rest_clear',
			),
		)
	);
}
add_action( 'rest_api_init', 'studentup_notify_register_routes' );

/**
 * GET — full queue (admin/bot only).
 */
function studentup_notify_rest_get() {
	return new WP_REST_Response( array( 'ok' => true, 'alerts' => studentup_notify_all() ), 200 );
}

/**
 * POST — { code, message, severity } push.
 *
 * @param WP_REST_Request $request request.
 */
function studentup_notify_rest_push( WP_REST_Request $request ) {
	$body = $request->get_json_params();
	$body = is_array( $body ) ? $body : array();
	$code = isset( $body['code'] ) ? (string) $body['code'] : '';
	$msg  = isset( $body['message'] ) ? (string) $body['message'] : '';
	$sev  = isset( $body['severity'] ) ? (string) $body['severity'] : 'info';
	if ( '' === $code || '' === $msg ) {
		return new WP_REST_Response( array( 'ok' => false, 'reason' => 'code+message required' ), 400 );
	}
	$saved = studentup_notify_push( $code, $msg, $sev );
	return new WP_REST_Response( array( 'ok' => (bool) $saved, 'code' => sanitize_key( $code ) ), $saved ? 200 : 500 );
}

/**
 * DELETE — { code } clear (`__all__` = queue motham).
 *
 * @param WP_REST_Request $request request.
 */
function studentup_notify_rest_clear( WP_REST_Request $request ) {
	$body = $request->get_json_params();
	$body = is_array( $body ) ? $body : array();
	$code = isset( $body['code'] ) ? (string) $body['code'] : '__all__';
	studentup_notify_clear( $code );
	return new WP_REST_Response( array( 'ok' => true, 'cleared' => sanitize_key( $code ) ), 200 );
}

/**
 * Localize public dismiss config (studentup.js reads suNotifyPublic).
 */
function studentup_notify_public_assets() {
	try {
		wp_localize_script( 'studentup', 'suNotifyPublic', array( 'version' => defined( 'STUDENTUP_VERSION' ) ? STUDENTUP_VERSION : '' ) );
	} catch ( Exception $e ) { // phpcs:ignore Generic.CodeAnalysis.EmptyStatement
	}
}
add_action( 'wp_enqueue_scripts', 'studentup_notify_public_assets', 20 );
