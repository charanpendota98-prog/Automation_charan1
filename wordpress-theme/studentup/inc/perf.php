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
	$img = wp_get_attachment_image_src( get_post_thumbnail_id(), 'full' );
	if ( ! $img ) {
		return;
	}
	printf(
		'<link rel="preload" as="image" href="%s" fetchpriority="high">' . "\n",
		esc_url( $img[0] )
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
