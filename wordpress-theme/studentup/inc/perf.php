<?php
/**
 * v66: PERFORMANCE + AD VIEWABILITY (Core Web Vitals + RPM).
 *
 * Enduku (revenue + Google both):
 *   · LCP image (featured) ni preload + fetchpriority=high → LCP fast
 *   · Below-fold ad slots ni **lazy** (viewport loki vachaka load) → CLS thakkuva,
 *     viewability ekkuva → AdSense RPM ekkuva (Google viewability tho pay chestundi)
 *   · Reserved height (min-height) → CLS 0
 *   · AdSense script ni idle varaku aapadam (render-blocking ledu)
 *   · content-visibility: below-fold cards ki (paint cost thakkuva)
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Featured image ni LCP ga preload (single post lo mattrame).
 */
function studentup_preload_lcp() {
	if ( is_admin() || ! is_singular() || ! has_post_thumbnail() ) {
		return;
	}
	$size = function_exists( 'studentup_big_image_size' )
		? studentup_big_image_size( get_the_ID() ) : 'large';
	$size = $size ? $size : 'large';
	$img  = wp_get_attachment_image_src( get_post_thumbnail_id(), $size );
	if ( ! $img ) {
		return;
	}
	printf(
		'<link rel="preload" as="image" href="%s" fetchpriority="high" type="image/%s">' . "\n",
		esc_url( $img[0] ),
		esc_attr( pathinfo( wp_parse_url( $img[0], PHP_URL_PATH ), PATHINFO_EXTENSION ) ?: 'jpeg' )
	);
}
add_action( 'wp_head', 'studentup_preload_lcp', 2 );

/**
 * Content images: decoding async + lazy (WP default lazy ni confirm).
 */
function studentup_img_attrs( $attr, $attachment, $size ) { // phpcs:ignore
	if ( is_admin() ) {
		return $attr;
	}
	$attr['decoding'] = 'async';
	return $attr;
}
add_filter( 'wp_get_attachment_image_attributes', 'studentup_img_attrs', 10, 3 );

/**
 * Below-fold lazy ad loader: ad slot ki data-su-lazy unte viewport loki vachaka
 * tarvata injaa load + push (AdSense policy: click-prompt ledu, content same).
 */
function studentup_lazy_ads_js() {
	if ( is_admin() ) {
		return;
	}
	?>
	<script>
	(function () {
		var slots = document.querySelectorAll('.su-ad-lazy[data-su-lazy]');
		if (!slots.length) { return; }
		var load = function (el) {
			if (el.dataset.suLoaded) { return; }
			el.dataset.suLoaded = '1';
			var ins = el.querySelectorAll('ins.adsbygoogle');
			for (var i = 0; i < ins.length; i++) {
				(adsbygoogle = window.adsbygoogle || []).push({});
			}
			el.classList.remove('su-ad-lazy');
		};
		if (!('IntersectionObserver' in window)) {
			for (var j = 0; j < slots.length; j++) { load(slots[j]); }
			return;
		}
		var io = new IntersectionObserver(function (entries) {
			entries.forEach(function (e) {
				if (e.isIntersecting) { load(e.target); io.unobserve(e.target); }
			});
		}, { rootMargin: '300px 0px' });
		for (var k = 0; k < slots.length; k++) { io.observe(slots[k]); }
	})();
	</script>
	<?php
}
add_action( 'wp_footer', 'studentup_lazy_ads_js', 20 );

/**
 * v67: preconnect / dns-prefetch — 3rd-party (ads/analytics) latency thagginchadam.
 *
 * AdSense + GA connection setup ~200-400ms thintundi; preconnect tho ad load fast
 * avutundi → viewability + RPM penchutundi (adi nijamaina revenue lever).
 */
function studentup_resource_hints( $hints, $relation_type ) {
	// Do not open third-party connections before approval/measurement is
	// configured. An unused preconnect can itself cost mobile startup time.
	$ads_client = function_exists( 'studentup_adsense_client' )
		? (string) studentup_adsense_client() : '';
	$ga4_id = (string) studentup_opt( 'ga4_id', '' );
	if ( 'preconnect' === $relation_type && ( $ads_client || $ga4_id ) ) {
		if ( $ads_client ) {
			$hints[] = array( 'href' => 'https://pagead2.googlesyndication.com', 'crossorigin' => 'anonymous' );
			$hints[] = array( 'href' => 'https://googleads.g.doubleclick.net', 'crossorigin' => 'anonymous' );
		}
		if ( $ga4_id ) {
			$hints[] = 'https://www.googletagmanager.com';
			$hints[] = 'https://www.google-analytics.com';
		}
	}
	// No hosted font is enqueued by the theme, so fonts.gstatic.com would be an
	// unused connection. Keep dns-prefetch empty rather than paying that cost.
	return $hints;
}
add_filter( 'wp_resource_hints', 'studentup_resource_hints', 10, 2 );

/**
 * v67: thin pages ki noindex — search results + 404 index ayyi crawl budget thinakunda.
 *
 * Archive/paginated pages index lo undali (Google ni crawl cheyyali) — so only
 * search + 404 (+ v84 date archives) ni block chestunnamu.
 */
function studentup_robots_thin( $robots ) {
	if ( is_search() ) {
		$robots['noindex'] = true;
		$robots['follow']  = true;
		unset( $robots['index'] );
	}
	if ( is_404() ) {
		$robots['noindex'] = true;
		$robots['nofollow'] = true;
		unset( $robots['index'], $robots['follow'] );
	}
	if ( is_date() ) {
		// v84: date archives = thin duplicates (crawl budget waste).
		// Author pages index lone (E-E-A-T); tags/categories meaningful.
		$robots['noindex'] = true;
		$robots['follow']  = true;
		unset( $robots['index'] );
	}
	if ( isset( $_GET['qual'] ) ) { // phpcs:ignore WordPress.Security.NonceVerification
		// v81 (§72): filter combos ki independent search value ledu —
		// canonical category page kevalam index (duplicates ledu).
		$robots['noindex'] = true;
		$robots['follow']  = true;
		unset( $robots['index'] );
	}
	return $robots;
}
add_filter( 'wp_robots', 'studentup_robots_thin' );

/**
 * v67: content-visibility toggle — ON unte body ki `su-cv` class (CSS aa class ki
 * content-visibility apply chestundi). Option ni nijam ga wire chestundi (dead field kaadu).
 *
 * @param array $classes Body classes.
 * @return array
 */
function studentup_cv_body_class( $classes ) {
	if ( '0' !== (string) studentup_opt( 'content_visibility', '1' ) ) {
		$classes[] = 'su-cv';
	}
	return $classes;
}
add_filter( 'body_class', 'studentup_cv_body_class' );
