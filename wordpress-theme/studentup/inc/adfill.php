<?php
/**
 * v159 — Unfilled ad slot collapse.
 *
 * Problem: prati ad slot ki memu `min-height` reserve chestamu (CLS ki adi
 * correct). Kani AdSense aa slot ni **fill cheyakapote** (unfilled — new
 * sites lo chala common), aa reserved space blank ga migilipotundi. Blank
 * gap = reader scroll waste, content thakkuva kanipistundi, page "empty"
 * ga anipistundi.
 *
 * Fix: AdSense prati `<ins>` ki `data-ad-status="filled|unfilled"` set
 * chestundi. Unfilled ayithe wrapper ni collapse chestam — **load ayye
 * varaku reserve ye untundi**, so CLS penalty raadu (collapse anedi
 * user interaction taruvata kaadu, ad response taruvata).
 *
 * Policy: ad ni move cheyyam, refresh cheyyam, click prompt cheyyam —
 * unfilled box ni matrame dachipettam. Adi Google ye recommend chesedi.
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Collapse script — footer lo, no dependency.
 */
function studentup_adfill_js() {
	if ( is_admin() || is_feed() || ! studentup_opt( 'collapse_unfilled', '1' ) ) {
		return;
	}
	if ( ! function_exists( 'studentup_adsense_client' ) || ! studentup_adsense_client() ) {
		return; // AdSense ye ledu — script ki panledu.
	}
	?>
	<script>
	(function () {
		var W = window, D = document;
		if (!('MutationObserver' in W)) { return; }

		function settle(ins) {
			var box = ins.closest ? ins.closest('.su-ad-reserved') : null;
			var status = ins.getAttribute('data-ad-status');
			if (!box || !status) { return false; }
			if (status === 'unfilled') {
				box.classList.add('su-ad-empty');
				box.style.minHeight = '0px';
				box.setAttribute('aria-hidden', 'true');
			} else if (status === 'filled') {
				box.classList.add('su-ad-filled');
			}
			return true;
		}

		var slots = D.querySelectorAll('ins.adsbygoogle');
		if (!slots.length) { return; }

		Array.prototype.forEach.call(slots, function (ins) {
			if (settle(ins)) { return; }
			var mo = new MutationObserver(function () {
				if (settle(ins)) { mo.disconnect(); }
			});
			mo.observe(ins, { attributes: true, attributeFilter: ['data-ad-status'] });
			// Ad response raakapote 12s taruvata observer ni vadileyyadam
			// (memory leak avvakunda). Box reserved ga ne untundi.
			W.setTimeout(function () { mo.disconnect(); }, 12000);
		});
	})();
	</script>
	<?php
}
add_action( 'wp_footer', 'studentup_adfill_js', 22 );
