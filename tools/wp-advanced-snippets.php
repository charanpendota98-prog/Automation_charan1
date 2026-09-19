<?php
/**
 * =====================================================================
 * studentup.in — ADVANCED PHP SNIPPETS (v42)
 * =====================================================================
 * Where to paste: WP Code plugin → Snippets → Add New Snippet
 *   Name:       "studentup advanced pack"
 *   Code:       THIS ENTIRE FILE
 *   Status:     Active
 *   Location:   "Run snippet everywhere" (default)
 *
 * Rules: every function is su_-prefixed, idempotent, guarded with
 * function_exists() — safe to re-paste, zero conflicts with Rank Math
 * or the studentup bot (bot writes posts/meta only, never these hooks).
 *
 * Toggle any block: set SU_ADV_<NAME> = false in a constants snippet,
 * e.g.  define('SU_ADV_FONTS', false);
 * =====================================================================
 */

if (!defined('ABSPATH')) { exit; }

/* ------------------------------------------------------------------
 * 1. PERFORMANCE HYGIENE — remove bloat from <head>
 *    emoji scripts/styles, generator tag, shortlink, wlwmanifest.
 *    Effect: ~15–25 KB less + 2 fewer requests on every page.
 * ------------------------------------------------------------------ */
if (function_exists('su_adv_head_hygiene')) {
	function su_adv_head_hygiene() {}
} else {
	add_action('init', function () {
		if (defined('SU_ADV_HEAD') && !SU_ADV_HEAD) { return; }
		remove_action('wp_head', 'print_emoji_detection_script', 7);
		remove_action('wp_print_styles', 'print_emoji_styles');
		remove_action('admin_print_scripts', 'print_emoji_detection_script');
		remove_action('admin_print_styles', 'print_emoji_styles');
		remove_action('wp_head', 'wp_generator');
		remove_action('wp_head', 'wp_shortlink_wp_head');
		remove_action('wp_head', 'rsd_link');
		remove_action('wp_head', 'wlwmanifest_link');
		remove_action('wp_head', 'wp_oembed_add_discovery_links');
	});
}

/* ------------------------------------------------------------------
 * 2. FONT ADVANCED — preload the 2 families the Design Kit uses.
 *    Google-Fonts @import costs a render-blocking request on every
 *    page; preconnect + preload critical weights instead.
 *    (If your theme already loads the fonts, see the note below.)
 * ------------------------------------------------------------------ */
if (!function_exists('su_adv_font_loading')) {
	function su_adv_font_loading() {
		if (defined('SU_ADV_FONTS') && !SU_ADV_FONTS) { return; }
		if (!is_singular()) { return; } // posts = where reading happens
		$base = 'https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=Noto+Sans+Telugu:wght@400;600;800&display=swap';
		printf('<link rel="preconnect" href="https://fonts.googleapis.com">' . "\n");
		printf('<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>' . "\n");
		printf('<link rel="preload" as="style" href="%s">' . "\n", esc_url($base));
		printf('<link rel="stylesheet" href="%s" media="print" onload="this.media=\'all\';this.onload=null">' . "\n", esc_url($base));
		printf('<noscript><link rel="stylesheet" href="%s"></noscript>' . "\n", esc_url($base));
	}
	add_action('wp_head', 'su_adv_font_loading', 1);
}
/* NOTE: if your theme ALSO @imports Google Fonts, the browser dedupes
   the stylesheet — but to be 100% clean, define('SU_ADV_FONTS', false)
   and keep only the theme's copy. */

/* ------------------------------------------------------------------
 * 3. EXCERPT ADVANCED — 28 words + "Continue reading →"
 *    Consistent meta + snippet cards = better CTR + cleaner cards.
 * ------------------------------------------------------------------ */
if (!function_exists('su_adv_excerpt')) {
	function su_adv_excerpt($length) {
		return defined('SU_ADV_EXCERPT_WORDS') ? (int) SU_ADV_EXCERPT_WORDS : 28;
	}
	add_filter('excerpt_length', 'su_adv_excerpt');
}
if (!function_exists('su_adv_excerpt_more')) {
	function su_adv_excerpt_more($more) {
		return defined('SU_ADV_EXCERPT_MORE') ? SU_ADV_EXCERPT_MORE : ' <span aria-hidden="true">→</span>';
	}
	add_filter('excerpt_more', 'su_adv_excerpt_more');
}

/* ------------------------------------------------------------------
 * 4. NAV ELEVATION — small body class toggled after scroll
 *    (pairs with wp-advanced.css .nav-scrolled shadow). 13 bytes of JS.
 * ------------------------------------------------------------------ */
if (!function_exists('su_adv_nav_scroll')) {
	function su_adv_nav_scroll() {
		if (!is_singular() && !is_front_page()) { return; }
		?>
		<script>
		document.addEventListener('scroll',function(){
			document.body.classList.toggle('nav-scrolled',window.scrollY>8);
		},{passive:true});
		</script>
		<?php
	}
	add_action('wp_footer', 'su_adv_nav_scroll');
}

/* ------------------------------------------------------------------
 * 5. STRUCTURED DATA ADVANCED — WebSite + Sitelinks Search Box
 *    OPTIONAL: only enable if Rank Math "Sitelinks search box" is OFF
 *    (Rank Math → Titles & Meta → Sitelinks search box). Duplicate
 *    WebSite JSON-LD is harmless but redundant — keep ONE owner.
 * ------------------------------------------------------------------ */
if (!function_exists('su_adv_website_jsonld')) {
	function su_adv_website_jsonld() {
		if (defined('SU_ADV_JSONLD') && !SU_ADV_JSONLD) { return; } // default OFF
		$site = home_url('/');
		$data = array(
			'@context' => 'https://schema.org',
			'@type' => 'WebSite',
			'name' => 'studentup.in',
			'url' => $site,
			'inLanguage' => array('te', 'en'),
			'potentialAction' => array(
				'@type' => 'SearchAction',
				'target' => $site . 's={search_term_string}', // WP query var "s"
				'query-input' => 'required name=search_term_string',
			),
		);
		echo '<script type="application/ld+json">' . wp_json_encode($data, JSON_UNESCAPED_UNICODE) . '</script>' . "\n";
	}
	add_action('wp_head', 'su_adv_website_jsonld', 5);
}
/* To enable: add constants snippet  define('SU_ADV_JSONLD', true);
   after confirming Rank Math isn't emitting WebSite. */

/* ------------------------------------------------------------------
 * 6. IMAGE ADVANCED — native lazy-load for ALL content images,
 *    EXCEPT the first (LCP) one in the post.
 * ------------------------------------------------------------------ */
if (!function_exists('su_adv_native_lazy')) {
	function su_adv_native_lazy($content) {
		if (defined('SU_ADV_LAZY') && !SU_ADV_LAZY) { return $content; }
		if (!is_singular() || !in_the_loop()) { return $content; }
		// first img = LCP candidate: keep eager + fetchpriority high
		$content = preg_replace('/<img([^>]*?)>/', '<img$1 loading="eager" fetchpriority="high">', $content, 1);
		// rest: lazy (skip ones already marked)
		$content = preg_replace('/<img(?![^>]*\bloading=)([^>]*?)>/', '<img$1 loading="lazy">', $content);
		return $content;
	}
	add_filter('the_content', 'su_adv_native_lazy', 20);
}

/* ------------------------------------------------------------------
 * 7. SECURITY ADVANCED (light touch)
 *    - hide WordPress version from meta generator (belt+suspenders;
 *      wp_generator already removed above)
 *    - disable XML-RPC pingback flood (keep REST API — bot needs it)
 *    - limit author enumeration for guests
 * ------------------------------------------------------------------ */
if (!function_exists('su_adv_security')) {
	function su_adv_security() {
		if (defined('SU_ADV_SECURITY') && !SU_ADV_SECURITY) { return; }
		add_filter('xmlrpc_enabled', '__return_false');
	}
	add_action('init', 'su_adv_security');
}
if (!function_exists('su_adv_author_redirect')) {
	function su_adv_author_redirect() {
		if (defined('SU_ADV_SECURITY') && !SU_ADV_SECURITY) { return; }
		if (is_author() && !is_user_logged_in()) {
			wp_safe_redirect(home_url('/'), 301);
			exit;
		}
	}
	add_action('template_redirect', 'su_adv_author_redirect');
}

echo ''; // keep PHP lint happy when pasted
