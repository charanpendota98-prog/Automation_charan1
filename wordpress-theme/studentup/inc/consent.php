<?php
/**
 * v66: Google CONSENT MODE v2 + CMP bridge.
 *
 * Enduku (real revenue issue): EEA/UK/CH users ki consent lekunda AdSense ads
 * **serve avvavu** (Google policy + law). Consent Mode v2 tho:
 *   · default = denied (privacy-compliant)
 *   · CMP (Google-certified: AdSense → Privacy & messaging) consent isthe ads start
 *   · non-EEA users (India!) ki ads eppudu serve avutayi — revenue protected
 *
 * Option: StudentUp → Advanced → consent_regions (default: EEA + UK + CH)
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Consent Mode v2 defaults — CMP script kanna mundu run avvali (head lo).
 */
function studentup_consent_mode_head() {
	if ( is_admin() || ! studentup_opt( 'consent_mode', '1' ) ) {
		return;
	}
	$regions = (string) studentup_opt( 'consent_regions', 'EEA,GB,CH' );
	// region codes: A-Z0-9 mattrame (JSON injection impossible)
	$list    = array();
	foreach ( explode( ',', $regions ) as $rc ) {
		$rc = preg_replace( '/[^A-Za-z0-9]/', '', trim( $rc ) );
		if ( '' !== $rc ) {
			$list[] = strtoupper( $rc );
		}
	}
	$region_json = wp_json_encode( $list );
	if ( ! is_string( $region_json ) ) {
		$region_json = '[]';
	}
	$js = "window.dataLayer=window.dataLayer||[];"
		. "function gtag(){dataLayer.push(arguments);}"
		. "gtag('consent','default',{ad_storage:'denied',ad_user_data:'denied',"
		. "ad_personalization:'denied',analytics_storage:'denied',wait_for_update:500,"
		. "region:" . $region_json . "});"
		. "gtag('consent','default',{ad_storage:'granted',ad_user_data:'granted',"
		. "ad_personalization:'granted',analytics_storage:'granted'});"
		. "gtag('set','ads_data_redaction',true);";
	echo '<script>' . $js . '</script>' . "\n"; // phpcs:ignore WordPress.Security.EscapeOutput
}
add_action( 'wp_head', 'studentup_consent_mode_head', 1 );

/**
 * CMP (Google-certified) script — AdSense → Privacy & messaging lo CMP ON chesi
 * mee CMP script/ID ni ikkada pettandi (option: consent_cmp_id).
 */
function studentup_consent_cmp() {
	$cmp = (string) studentup_opt( 'consent_cmp_id', '' );
	if ( ! $cmp || is_admin() ) {
		return;
	}
	// Google Funding Choices / AdSense CMP snippet (site owner nimpistadu)
	echo wp_kses_post( $cmp );
}
add_action( 'wp_head', 'studentup_consent_cmp', 2 );

/**
 * v80 (P24/P25): Search Console verification meta + consent-aware GA4.
 *
 * GA4 gtag.js load aina — consent defaults (prio 1, denied in EEA/UK/CH)
 * valla analytics hits consent varaku hold avutayi; India lo direct.
 * ID format G-XXXXXXXXXX kakapothe load avvadu (typo-safe, no dummy hits).
 */
function studentup_ga4_head() {
	if ( is_admin() ) {
		return;
	}
	$gsc = trim( (string) studentup_opt( 'gsc_verify', '' ) );
	if ( '' !== $gsc ) {
		echo '<meta name="google-site-verification" content="' . esc_attr( $gsc ) . '">' . "\n";
	}
	$ga4 = trim( (string) studentup_opt( 'ga4_id', '' ) );
	if ( '' === $ga4 || ! preg_match( '/^G-[A-Z0-9]{6,}$/', $ga4 ) ) {
		return;
	}
	$src = 'https://www.googletagmanager.com/gtag/js?id=' . rawurlencode( $ga4 );
	echo '<script async src="' . esc_url( $src ) . '"></script>' . "\n";
	echo '<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}'
		. "gtag('js',new Date());gtag('config','" . esc_js( $ga4 ) . "',{'anonymize_ip':true});</script>\n";
}
add_action( 'wp_head', 'studentup_ga4_head', 3 );

/**
 * Ads render avvala? — consent + option check (AdSense Serve avvakapovadam ledu).
 */
function studentup_consent_ok() {
	if ( ! studentup_opt( 'consent_mode', '1' ) ) {
		return true; // consent mode off (owner ISHTAM) — ads always
	}
	// CMP client-side update chesaka ads block 'granted' avutundi; server side lo
	// mana default = allow (Google Consent Mode ee pani client lo chestundi —
	// denied unte Google ads_data_redaction tho serve kaadu, mana markup block kaadu).
	return true;
}
