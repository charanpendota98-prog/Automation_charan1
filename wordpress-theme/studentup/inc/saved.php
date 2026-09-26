<?php
/**
 * v92: SAVED — reader bookmark layer (theme 1.9.3).
 *
 * Enduku (retention + engagement):
 *   StudentUp readers job notification chusi "tarvata apply cheddam" anukuntaru —
 *   kaani ippati varaku aa post ni **save cheyyadaniki daari ledu**. Browser
 *   bookmark vaadadam kastam (phone lo), anduku reader tirigi ravatam thaggutundi.
 *   Idi oka reader-facing retention feature: post ni save chesi, tarvata
 *   "Saved" panel lo chusi tirigi vastaru.
 *
 * Design rules (v89 PART-45 principle — "feature never breaks page"):
 *   1) Backend ledu, DB ledu, cookie ledu — antha **localStorage** lo (privacy-safe,
 *      AdSense/privacy-policy ki clean, server load zero). Server round-trip ledu.
 *   2) Save button = real button element (keyboard + screen-reader OK) with
 *      `aria-pressed`; JS lekapoyina page baaguntundi (progress-enhancement only).
 *   3) Panel markup server-side render (a11y/SEO clean) — list ni JS nimpustundi.
 *      JS off / localStorage blocked (private mode) aithe panel "empty" note
 *      chupistundi, error ledu.
 *   4) Option gate `saved_enabled` (default ON) — OFF chesthe button/panel render
 *      avvavu, ee file eppudu fatal avvadu.
 *   5) Prathi callback ABSPATH-guarded + escaped (XSS zero).
 *
 * Shortcode: `[studentup_saved]` — /saved/ page create chesi idi paste cheyandi
 * (home menu lo link pettachu). Page template avasaram ledu.
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/** localStorage keys — JS tho share avutayi (single source of truth). */
define( 'STUDENTUP_SAVED_STORE', 'studentup_saved_v1' );
define( 'STUDENTUP_SAVED_RECENT', 'studentup_recent_v1' );

/**
 * Feature ON aa? (default ON — admin → StudentUp → Content lo OFF cheyyochu)
 *
 * @return bool
 */
function studentup_saved_on() {
	return '0' !== (string) studentup_opt( 'saved_enabled', '1' );
}

/**
 * localStorage lo max enta store cheyyali (pagination ledu — cap tho FIFO).
 *
 * @return int
 */
function studentup_saved_max() {
	$max = (int) studentup_opt( 'saved_max', '60' );
	if ( $max < 5 ) {
		$max = 5;
	}
	if ( $max > 200 ) {
		$max = 200;
	}
	return $max;
}

/**
 * Save/un-save button — card lo + single lo vadutunnamu.
 *
 * Markup ni JS chaduvutundi (`data-su-save`) and localStorage nunchi state
 * restore chestundi. Ee function eppudu HTML ni query cheyyadu (N+1 ledu) —
 * kevalam static markup + data attributes.
 *
 * @param int    $post_id Post ID (0 = current post in the loop).
 * @param string $class   Extra CSS class (card lo compact variant).
 * @return string HTML (escaped) — empty string if feature OFF.
 */
function studentup_saved_sync_item( $raw ) {
	if ( ! is_array( $raw ) ) {
		return null;
	}
	$id    = isset( $raw['id'] ) ? absint( $raw['id'] ) : 0;
	$url   = isset( $raw['url'] ) ? esc_url_raw( $raw['url'] ) : '';
	$host  = wp_parse_url( home_url( '/' ), PHP_URL_HOST );
	$u_host = wp_parse_url( $url, PHP_URL_HOST );
	$date  = isset( $raw['date'] ) ? sanitize_text_field( (string) $raw['date'] ) : '';
	if ( ! $id || ! $url || ! $u_host || strtolower( (string) $u_host ) !== strtolower( (string) $host ) ) {
		return null;
	}
	if ( $date && ! preg_match( '/^20\d{2}-\d{2}-\d{2}$/', $date ) ) {
		$date = '';
	}
	return array(
		'id'    => $id,
		'title' => substr( sanitize_text_field( (string) ( $raw['title'] ?? '' ) ), 0, 180 ),
		'url'   => $url,
		'cat'   => substr( sanitize_text_field( (string) ( $raw['cat'] ?? '' ) ), 0, 80 ),
		'date'  => $date,
		'ts'    => isset( $raw['ts'] ) ? absint( $raw['ts'] ) : time(),
	);
}

function studentup_saved_sync_user_items( $items ) {
	$out  = array();
	$seen = array();
	foreach ( (array) $items as $raw ) {
		$item = studentup_saved_sync_item( $raw );
		if ( ! $item || isset( $seen[ $item['id'] ] ) ) {
			continue;
		}
		$seen[ $item['id'] ] = true;
		$out[] = $item;
		if ( count( $out ) >= studentup_saved_max() ) {
			break;
		}
	}
	return $out;
}

function studentup_saved_sync_permission() {
	return is_user_logged_in() ? true : new WP_Error( 'studentup_login_required', 'Sign in to sync saved posts.', array( 'status' => 401 ) );
}

function studentup_saved_sync_get() {
	return new WP_REST_Response( array(
		'ok'    => true,
		'items' => studentup_saved_sync_user_items( get_user_meta( get_current_user_id(), 'studentup_saved_items', true ) ),
	), 200 );
}

function studentup_saved_sync_put( WP_REST_Request $request ) {
	$items = studentup_saved_sync_user_items( $request->get_param( 'items' ) );
	update_user_meta( get_current_user_id(), 'studentup_saved_items', $items );
	return new WP_REST_Response( array( 'ok' => true, 'items' => $items ), 200 );
}

function studentup_saved_sync_routes() {
	register_rest_route(
		'studentup/v1',
		'/saved',
		array(
			array(
				'methods'             => WP_REST_Server::READABLE,
				'callback'            => 'studentup_saved_sync_get',
				'permission_callback' => 'studentup_saved_sync_permission',
			),
			array(
				'methods'             => WP_REST_Server::CREATABLE,
				'callback'            => 'studentup_saved_sync_put',
				'permission_callback' => 'studentup_saved_sync_permission',
			),
		)
	);
}
add_action( 'rest_api_init', 'studentup_saved_sync_routes' );

function studentup_save_button( $post_id = 0, $class = '' ) {
	if ( ! studentup_saved_on() ) {
		return '';
	}
	$post_id = $post_id ? (int) $post_id : (int) get_the_ID();
	if ( ! $post_id ) {
		return '';
	}
	$title = wp_strip_all_tags( get_the_title( $post_id ) );
	$cats  = get_the_category( $post_id );
	$cat   = $cats ? $cats[0]->name : '';
	$date  = function_exists( 'studentup_tools_date' ) ? studentup_tools_date( $post_id ) : '';

	$classes = 'su-save-btn';
	if ( $class ) {
		$classes .= ' ' . sanitize_html_class( $class );
	}

	return sprintf(
		'<button type="button" class="%1$s" data-su-save data-id="%2$d" data-title="%3$s" data-url="%4$s" data-cat="%5$s" data-date="%6$s" aria-pressed="false" aria-label="%7$s"><span class="su-save-ico" aria-hidden="true">🔖</span><span class="su-save-txt">%8$s</span></button>',
		esc_attr( $classes ),
		$post_id,
		esc_attr( $title ),
		esc_url( get_permalink( $post_id ) ),
		esc_attr( $cat ),
		esc_attr( $date ),
		esc_attr__( 'Save this post for later', 'studentup' ),
		esc_html__( 'Save', 'studentup' )
	);
}

/**
 * Saved panel — footer lo okkasari render (slide-out drawer, mobile + desktop).
 *
 * List ni JS nimpustundi (localStorage). Server-side empty-state chupistundi —
 * anduke JS lekunda kuda page meeda "no saved posts" note kanipistundi, error kaadu.
 */
function studentup_saved_page_url() {
	$page = get_page_by_path( 'saved' );
	return ( $page && 'publish' === get_post_status( $page ) ) ? get_permalink( $page ) : '';
}

function studentup_saved_panel() {
	if ( ! studentup_saved_on() ) {
		return;
	}
	$su_saved_url = studentup_saved_page_url();
	?>
	<div class="su-saved-rail" id="su-saved-rail">
		<button type="button" class="su-saved-tab" id="su-saved-tab" data-su-saved-open aria-expanded="false" aria-controls="su-saved-panel" aria-label="<?php echo esc_attr__( 'Saved posts', 'studentup' ); ?>">
			<span class="su-saved-ico" aria-hidden="true">🔖</span>
			<span class="su-saved-count" data-su-saved-count hidden>0</span>
		</button>
		<div class="su-saved-panel" id="su-saved-panel" role="dialog" aria-label="<?php echo esc_attr__( 'Saved posts', 'studentup' ); ?>" hidden>
			<div class="su-saved-head">
				<strong><?php echo esc_html__( 'Saved', 'studentup' ); ?></strong>
				<span class="su-saved-n" data-su-saved-count aria-live="polite">0</span>
				<button type="button" class="su-saved-close" id="su-saved-close" aria-label="<?php echo esc_attr__( 'Close', 'studentup' ); ?>">✕</button>
			</div>
			<div class="su-saved-body" id="su-saved-body" data-su-saved-body>
				<p class="su-saved-empty"><?php echo esc_html__( 'No saved posts yet. Tap 🔖 on any card to save it for later.', 'studentup' ); ?></p>
			</div>
			<div class="su-saved-foot">
				<?php if ( $su_saved_url ) : ?>
					<a class="su-saved-all" href="<?php echo esc_url( $su_saved_url ); ?>"><?php echo esc_html__( 'Open the saved page', 'studentup' ); ?></a>
				<?php else : ?>
					<button type="button" class="su-saved-all su-saved-page-fallback" data-su-saved-open><?php echo esc_html__( 'View saved here', 'studentup' ); ?></button>
				<?php endif; ?>
				<button type="button" class="su-saved-clear" id="su-saved-clear"><?php echo esc_html__( 'Clear all', 'studentup' ); ?></button>
			</div>
		</div>
	</div>
	<?php
}

/**
 * `[studentup_saved]` — /saved/ page content (grid + empty-state).
 *
 * Idi JS render target (`#su-saved-page`). LocalStorage empty aithe JS
 * empty-state chupistundi; server-side fallback note kuda undi.
 *
 * @return string HTML.
 */
function studentup_saved_shortcode() {
	if ( ! studentup_saved_on() ) {
		return '';
	}
	return '<div class="su-saved-page" id="su-saved-page" data-su-saved-page>'
		. '<p class="su-saved-empty" data-su-saved-page-empty>'
		. esc_html__( 'No saved posts yet. Open any post and tap 🔖 Save.', 'studentup' )
		. '</p></div>';
}
add_shortcode( 'studentup_saved', 'studentup_saved_shortcode' );

/**
 * Body class — CSS hooks (feature ON unte mattrame).
 *
 * @param array $classes Body classes.
 * @return array
 */
function studentup_saved_body_class( $classes ) {
	if ( studentup_saved_on() ) {
		$classes[] = 'su-has-saved';
	}
	return $classes;
}
add_filter( 'body_class', 'studentup_saved_body_class' );

/**
 * JS asset — defer (site speed; feature progressive enhancement).
 *
 * `STUDENTUP_SAVED` localize: storage keys + limits + i18n strings.
 * JS lo strings hardcode cheyyaledu (i18n + test parity).
 */
function studentup_saved_assets() {
	if ( is_admin() || ! studentup_saved_on() ) {
		return;
	}
	wp_enqueue_script(
		'studentup-saved',
		get_template_directory_uri() . '/assets/js/studentup-saved.js',
		array(),
		STUDENTUP_VERSION,
		true
	);
	wp_localize_script(
		'studentup-saved',
		'STUDENTUP_SAVED',
		array(
		'store'  => STUDENTUP_SAVED_STORE,
		'recent' => STUDENTUP_SAVED_RECENT,
		'max'    => studentup_saved_max(),
		'sync'   => array(
			'enabled'  => is_user_logged_in(),
			'endpoint' => is_user_logged_in() ? esc_url_raw( rest_url( 'studentup/v1/saved' ) ) : '',
			'nonce'    => is_user_logged_in() ? wp_create_nonce( 'wp_rest' ) : '',
		),
		'i18n'   => array(
				'save'    => __( 'Save', 'studentup' ),
				'saved'   => __( 'Saved', 'studentup' ),
				'saveLabel' => __( 'Save this post for later', 'studentup' ),
				'savedLabel' => __( 'Remove this post from saved', 'studentup' ),
				'removed' => __( 'Removed from saved', 'studentup' ),
				'savedmsg' => __( 'Post saved — open 🔖 any time to read it later.', 'studentup' ),
				'nomore'  => __( 'Storage is not available in this browser (private mode?) — saving is off.', 'studentup' ),
				'empty'   => __( 'No saved posts yet. Open any post and tap 🔖 Save.', 'studentup' ),
				'confirm' => __( 'Remove all saved posts?', 'studentup' ),
				'cleared' => __( 'All saved posts removed.', 'studentup' ),
				'recent'  => __( 'Recently read', 'studentup' ),
			),
		)
	);
}
add_action( 'wp_enqueue_scripts', 'studentup_saved_assets' );
