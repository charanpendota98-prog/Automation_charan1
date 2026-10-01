<?php
/**
 * v128 GO-LIVE SCORE — admin page that scores the live site the way Google,
 * AdSense reviewers and readers actually see it.
 *
 * Enduku: theme perfect ga unna, site data (policy pages, featured images,
 * job meta, social links, AdSense ids) missing aithe approval + CTR debba
 * tinipistundi. Ee page okka chupu lo "inka em chesthe 100/100" ani cheptundi.
 *
 * Anni checks live site data meeda — hardcoded "ok" eppudu ledu.
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Posts missing a featured image (Discover + CTR blocker).
 *
 * @return int
 */
function studentup_score_missing_images() {
	$q = new WP_Query(
		array(
			'post_type'      => 'post',
			'post_status'    => 'publish',
			'posts_per_page' => 100,
			'fields'         => 'ids',
			'no_found_rows'  => true,
			'meta_query'     => array( // phpcs:ignore WordPress.DB.SlowDBQuery
				array(
					'key'     => '_thumbnail_id',
					'compare' => 'NOT EXISTS',
				),
			),
		)
	);
	return count( (array) $q->posts );
}

/**
 * Posts missing job data (last date / apply url).
 *
 * @return int
 */
function studentup_score_missing_jobdata() {
	$q = new WP_Query(
		array(
			'post_type'      => 'post',
			'post_status'    => 'publish',
			'posts_per_page' => 100,
			'fields'         => 'ids',
			'no_found_rows'  => true,
			'meta_query'     => array( // phpcs:ignore WordPress.DB.SlowDBQuery
				array(
					'key'     => 'studentup_last_date',
					'compare' => 'NOT EXISTS',
				),
			),
		)
	);
	return count( (array) $q->posts );
}

/**
 * All checks: label, pass, weight, fix hint.
 *
 * @return array<int,array<string,mixed>>
 */
function studentup_score_checks() {
	$published = (int) wp_count_posts( 'post' )->publish;
	$policy    = array( 'privacy', 'about', 'contact', 'disclaimer', 'terms', 'editorial-policy' );
	$have      = 0;
	foreach ( $policy as $slug ) {
		$page = get_page_by_path( $slug );
		if ( $page && 'publish' === get_post_status( $page ) ) {
			$have++;
		}
	}
	$soc      = studentup_social_links();
	$no_img   = studentup_score_missing_images();
	$no_job   = studentup_score_missing_jobdata();
	$menu_ok  = has_nav_menu( 'primary' );
	$logo_ok  = has_custom_logo();
	$icon_ok  = (bool) get_site_icon_url();
	$ssl_ok   = is_ssl() || 0 === strpos( home_url( '/' ), 'https://' );
	$perma_ok = (bool) get_option( 'permalink_structure' );
	$index_ok = '1' === (string) get_option( 'blog_public', '1' );
	$ads_id   = trim( (string) studentup_opt( 'adsense_client', '' ) );
	$ads_ok   = (bool) preg_match( '/^ca-pub-\d{10,20}$/', $ads_id );
	$gsc_ok   = '' !== trim( (string) studentup_opt( 'gsc_verify', '' ) );
	$ga_ok    = '' !== trim( (string) studentup_opt( 'ga4_id', '' ) );

	return array(
		array(
			'label'  => 'HTTPS live (SSL)',
			'pass'   => $ssl_ok,
			'weight' => 10,
			'fix'    => 'MilesWeb cPanel → SSL/TLS Status → AutoSSL run cheyandi, tarvata WordPress Address + Site Address ni https:// ki marchandi.',
		),
		array(
			'label'  => 'Search engines can index the site',
			'pass'   => $index_ok,
			'weight' => 10,
			'fix'    => 'Settings → Reading → "Discourage search engines" UNCHECK cheyandi.',
		),
		array(
			'label'  => 'Pretty permalinks (/%postname%/)',
			'pass'   => $perma_ok,
			'weight' => 6,
			'fix'    => 'Settings → Permalinks → Post name → Save.',
		),
		array(
			'label'  => 'At least 25 published posts (AdSense reviewers ki content depth)',
			'pass'   => $published >= 25,
			'weight' => 10,
			/* translators: %d: published post count. */
			'fix'    => sprintf( 'Ippudu %d posts unnayi — original, source-linked updates publish cheyandi.', $published ),
		),
		array(
			'label'  => 'All six policy pages published (privacy · about · contact · disclaimer · terms · editorial)',
			'pass'   => 6 === $have,
			'weight' => 12,
			/* translators: %d: policy pages present. */
			'fix'    => sprintf( '%d/6 unnayi. Missing vaatini Pages lo publish cheyandi — footer lo automatic ga link avutayi (AdSense approval ki must).', $have ),
		),
		array(
			'label'  => 'Custom logo + site icon set',
			'pass'   => $logo_ok && $icon_ok,
			'weight' => 5,
			'fix'    => 'Appearance → Customize → Site Identity lo logo + site icon upload cheyandi (PWA icon kuda ide).',
		),
		array(
			'label'  => 'Primary menu assigned',
			'pass'   => $menu_ok,
			'weight' => 5,
			'fix'    => 'Appearance → Menus → menu create chesi "Main menu (header)" location ki assign cheyandi.',
		),
		array(
			'label'  => 'Featured image on every recent post (Discover large card)',
			'pass'   => 0 === $no_img,
			'weight' => 12,
			/* translators: %d: posts without a featured image. */
			'fix'    => sprintf( '%d posts ki featured image ledu — 1200×675 image pettandi (Discover pedda card ki minimum 1200px width).', $no_img ),
		),
		array(
			'label'  => 'Job data (last date) filled on recent posts',
			'pass'   => 0 === $no_job,
			'weight' => 10,
			/* translators: %d: posts without a last date. */
			'fix'    => sprintf( '%d posts lo "StudentUp job data" box lo last date ledu — adi unte cards, eligibility checker, calendar, compare anni live avutayi.', $no_job ),
		),
		array(
			'label'  => 'WhatsApp + Telegram + Instagram + YouTube links configured',
			'pass'   => ! empty( $soc['whatsapp'] ) && ! empty( $soc['telegram'] ) && ! empty( $soc['instagram'] ) && ! empty( $soc['youtube'] ),
			'weight' => 5,
			'fix'    => 'StudentUp Settings → Social media lo mee real handles pettandi.',
		),
		array(
			'label'  => 'Search Console verification added',
			'pass'   => $gsc_ok,
			'weight' => 5,
			'fix'    => 'Search Console → HTML tag → content value ni StudentUp Settings → Advanced lo paste cheyandi.',
		),
		array(
			'label'  => 'Analytics (GA4) connected',
			'pass'   => $ga_ok,
			'weight' => 4,
			'fix'    => 'GA4 Measurement ID (G-XXXXXXX) ni Advanced tab lo pettandi — consent-aware ga load avutundi.',
		),
		array(
			'label'  => 'AdSense publisher ID saved (approve ayyaka)',
			'pass'   => $ads_ok,
			'weight' => 6,
			'fix'    => 'Approval tarvata ca-pub-XXXXXXXXXXXXXXXX ni Ads tab lo pettandi, "AdSense APPROVED" toggle ON cheyandi, ads.txt line kuda paste cheyandi.',
		),
	);
}

/**
 * Score page render.
 */
function studentup_score_page() {
	$checks = studentup_score_checks();
	$total  = 0;
	$got    = 0;
	foreach ( $checks as $c ) {
		$total += (int) $c['weight'];
		$got   += $c['pass'] ? (int) $c['weight'] : 0;
	}
	$pct  = $total ? (int) round( $got * 100 / $total ) : 0;
	$tone = $pct >= 90 ? '#16a34a' : ( $pct >= 70 ? '#d97706' : '#dc2626' );
	echo '<div class="wrap"><h1>StudentUp — Go-live score</h1>';
	echo '<p>Theme code side anni ready. Ee page live <strong>site data</strong> ni check chestundi — Google, AdSense reviewers, readers eela chustaro alaage.</p>';
	printf(
		'<div style="display:flex;align-items:center;gap:18px;margin:18px 0;padding:18px;border:1px solid #dcdcde;border-radius:14px;background:#fff">
			<div style="font-size:44px;font-weight:800;color:%1$s">%2$d<span style="font-size:18px">/100</span></div>
			<div style="flex:1"><div style="height:12px;border-radius:9px;background:#eee;overflow:hidden">
			<div style="height:100%%;width:%2$d%%;background:%1$s"></div></div>
			<p style="margin:8px 0 0;color:#555">%3$s</p></div></div>',
		esc_attr( $tone ),
		(int) $pct,
		esc_html( $pct >= 90 ? 'Launch ready — AdSense/Discover ki apply cheyyochu.' : ( $pct >= 70 ? 'Almost — kinda unna red items fix cheyandi.' : 'Konni basics missing — kinda list follow avvandi.' ) )
	);
	echo '<table class="widefat striped"><thead><tr><th>Check</th><th style="width:90px">Status</th><th>Fix</th></tr></thead><tbody>';
	foreach ( $checks as $c ) {
		printf(
			'<tr><td><strong>%s</strong></td><td>%s</td><td>%s</td></tr>',
			esc_html( $c['label'] ),
			$c['pass'] ? 'Pass' : 'Fix needed',
			$c['pass'] ? '<span style="color:#666">—</span>' : esc_html( $c['fix'] )
		);
	}
	echo '</tbody></table>';
	echo '<p style="margin-top:16px"><a class="button button-primary" href="' . esc_url( admin_url( 'themes.php?page=studentup-settings' ) ) . '">Open StudentUp Settings</a></p></div>';
}

/**
 * Menu entry under Appearance.
 */
function studentup_score_menu() {
	add_theme_page(
		'StudentUp Go-live score',
		'StudentUp Score',
		'manage_options',
		'studentup-score',
		'studentup_score_page'
	);
}
add_action( 'admin_menu', 'studentup_score_menu' );

/**
 * Dashboard widget: score summary (roju chudadaniki).
 */
function studentup_score_widget() {
	wp_add_dashboard_widget(
		'studentup_score',
		'StudentUp Go-live score',
		function () {
			$checks = studentup_score_checks();
			$total  = 0;
			$got    = 0;
			$pending = array();
			foreach ( $checks as $c ) {
				$total += (int) $c['weight'];
				if ( $c['pass'] ) {
					$got += (int) $c['weight'];
				} else {
					$pending[] = $c['label'];
				}
			}
			$pct = $total ? (int) round( $got * 100 / $total ) : 0;
			printf( '<p style="font-size:26px;margin:0 0 6px"><strong>%d/100</strong></p>', (int) $pct );
			if ( $pending ) {
				echo '<ul style="margin:0 0 8px;padding-left:18px">';
				foreach ( array_slice( $pending, 0, 4 ) as $t ) {
					echo '<li>' . studentup_ui_icon( 'close', 12 ) . ' ' . esc_html( $t ) . '</li>'; // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG
				}
				echo '</ul>';
			} else {
				echo '<p>' . studentup_ui_icon( 'check', 13 ) . ' Anni checks pass — launch ready.</p>'; // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG
			}
			echo '<a href="' . esc_url( admin_url( 'themes.php?page=studentup-score' ) ) . '">Full score →</a>';
		}
	);
}
add_action( 'wp_dashboard_setup', 'studentup_score_widget', 11 );
