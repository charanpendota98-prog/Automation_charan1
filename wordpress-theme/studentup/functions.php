<?php
/**
 * StudentUp Telugu News — theme setup (v61).
 *
 * Design: preview/index.html lo unna design ne WordPress lo ki teesukostundi —
 * Breaking ticker · "Most searched by students" · job cards · ad slots.
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

define( 'STUDENTUP_VERSION', '1.9.6' );  // v95: in-content image + contextual links (.su-figure/.su-ctx)

require_once get_template_directory() . '/inc/options.php';
require_once get_template_directory() . '/inc/qual-filter.php';  // v72: 10th/Inter/Degree/PG filter (auto tags)
require_once get_template_directory() . '/inc/breaking.php';
require_once get_template_directory() . '/inc/ads.php';
require_once get_template_directory() . '/inc/template.php';
require_once get_template_directory() . '/inc/seo-bridge.php';
require_once get_template_directory() . '/inc/toc.php';
require_once get_template_directory() . '/inc/schema.php';
require_once get_template_directory() . '/inc/author-box.php';
require_once get_template_directory() . '/inc/consent.php';
require_once get_template_directory() . '/inc/ads-txt.php';
require_once get_template_directory() . '/inc/perf.php';
require_once get_template_directory() . '/inc/news-sitemap.php';
require_once get_template_directory() . '/inc/security.php';
require_once get_template_directory() . '/inc/indexnow.php';
require_once get_template_directory() . '/inc/pwa.php';
require_once get_template_directory() . '/inc/cta.php';
require_once get_template_directory() . '/inc/editor.php';
require_once get_template_directory() . '/inc/redirects.php';  // v80: 301 redirect manager
require_once get_template_directory() . '/inc/health.php';     // v81: admin SEO-health widget
require_once get_template_directory() . '/inc/notify.php';    // v90: alert queue (admin notices + critical public banner + REST)
require_once get_template_directory() . '/inc/telegram.php';  // v91: Telegram channel join/share (private channel support)
require_once get_template_directory() . '/inc/saved.php';     // v92: reader bookmarks (localStorage) + saved panel/page
require_once get_template_directory() . '/inc/discover.php';  // v94: Discover large-card image + og dims + CLS/INP

/**
 * "Most searched by students" — order okkate source (bot lo autoblog/breaking.py
 * MOST_USED + preview site + tests anni ide order vaadutayi).
 */
function studentup_most_used() {
	return array(
		array( 'slug' => 'ts-jobs', 'label' => 'TS Government Jobs', 'icon' => '🏛', 'hint' => 'TSPSC · Police · Gurukul' ),
		array( 'slug' => 'ap-jobs', 'label' => 'AP Government Jobs', 'icon' => '🏛', 'hint' => 'APPSC · Police · DSC · Secretariat' ),
		array( 'slug' => 'central-jobs', 'label' => 'Central Govt Jobs', 'icon' => '🇮🇳', 'hint' => 'SSC · UPSC · Railways · Banks' ),
		array( 'slug' => 'hall-tickets', 'label' => 'Hall Tickets', 'icon' => '🎫', 'hint' => 'Admit card · key instructions' ),
		array( 'slug' => 'results', 'label' => 'Results', 'icon' => '📄', 'hint' => 'Board · competitive exams · keys' ),
		array( 'slug' => 'walkin-jobs', 'label' => 'Walk-in Interviews', 'icon' => '🚶', 'hint' => 'This week\'s drives · venues' ),
		array( 'slug' => 'software-jobs', 'label' => 'Software Jobs', 'icon' => '💻', 'hint' => 'IT · developer · fresher' ),
		array( 'slug' => 'private-jobs', 'label' => 'Private Jobs', 'icon' => '🏢', 'hint' => 'TCS · Infosys · Off-campus' ),
		array( 'slug' => 'current-affairs', 'label' => 'Current Affairs', 'icon' => '📰', 'hint' => 'Daily GK · for exams' ),
	);
}

/**
 * v89: Category alias map — theme slug → live-site slug candidates.
 *
 * Root cause of the "TS/AP Govt Jobs kanipinchaledu" bug: the bot creates live
 * categories with names like "TS Govt Jobs" (slug `ts-govt-jobs`) while the
 * theme list uses short slugs (`ts-jobs`). `get_category_by_slug()` then returns
 * false and the card/menu/chip silently DISAPPEARS. This resolver tries every
 * candidate and returns the first category that really exists on the site.
 *
 * @return array theme-slug => candidate live slugs (priority order)
 */
function studentup_cat_aliases() {
	return array(
		'ts-jobs'         => array( 'ts-govt-jobs', 'telangana-govt-jobs', 'ts-jobs' ),
		'ap-jobs'         => array( 'ap-govt-jobs', 'ap-jobs' ),
		'central-jobs'    => array( 'central-govt-jobs', 'central-jobs', 'central' ),
		'hall-tickets'    => array( 'hall-tickets', 'hallticket', 'hall-ticket' ),
		'results'         => array( 'results' ),
		'walkin-jobs'     => array( 'walkin-jobs', 'walkin', 'walk-in-jobs' ),
		'software-jobs'   => array( 'software-jobs', 'software' ),
		'private-jobs'    => array( 'private-jobs', 'private' ),
		'current-affairs' => array( 'current-affairs', 'current' ),
	);
}

/**
 * First real WP_Term for a theme slug (alias-aware) — else null.
 *
 * @param string $slug theme slug (studentup_most_used).
 * @return WP_Term|null
 */
function studentup_used_term( $slug ) {
	$map    = studentup_cat_aliases();
	$tried  = array();
	$cands  = isset( $map[ $slug ] ) ? $map[ $slug ] : array( $slug );
	foreach ( $cands as $cand ) {
		if ( isset( $tried[ $cand ] ) ) {
			continue;
		}
		$tried[ $cand ] = true;
		$term           = get_category_by_slug( $cand );
		if ( $term && ! is_wp_error( $term ) ) {
			return $term;
		}
	}
	return null;
}

/**
 * Reverse map — live category slug → theme chip slug.
 * Card data-cat lu eppudu theme slug ne (ts-govt-jobs → ts-jobs), anduke
 * chips live filter + preview order rendu break avvavu.
 *
 * @param string $live_slug real WP category slug.
 * @return string theme slug (fallback: input as-is)
 */
function studentup_theme_cat( $live_slug ) {
	$live_slug = (string) $live_slug;
	foreach ( studentup_cat_aliases() as $theme_slug => $cands ) {
		if ( in_array( $live_slug, $cands, true ) ) {
			return $theme_slug;
		}
	}
	return $live_slug;
}

/**
 * Theme setup.
 */
function studentup_setup() {
	load_theme_textdomain( 'studentup', get_template_directory() . '/languages' );

	add_theme_support( 'title-tag' );
	add_theme_support( 'post-thumbnails' );
	add_theme_support( 'automatic-feed-links' );
	add_theme_support( 'responsive-embeds' );
	add_theme_support( 'editor-styles' );        // v69: block editor lo front-end look same
	add_theme_support( 'wp-block-styles' );      // v69: core block default styles
	add_editor_style( 'assets/css/editor.css' ); // v69: editor parity
	add_theme_support( 'align-wide' );
	add_theme_support( 'html5', array( 'search-form', 'comment-form', 'comment-list', 'gallery', 'caption', 'style', 'script' ) );
	add_theme_support( 'custom-logo', array( 'height' => 44, 'width' => 220, 'flex-width' => true, 'flex-height' => true ) );
	add_theme_support( 'customize-selective-refresh-widgets' );

	register_nav_menus(
		array(
			'primary' => 'Main menu (header)',
			'mobile'  => 'Mobile menu',
			'footer'  => 'Footer menu',
		)
	);

	add_image_size( 'studentup-card', 640, 360, true );
}
add_action( 'after_setup_theme', 'studentup_setup' );

/**
 * Styles + scripts (no jQuery — speed).
 */
function studentup_assets() {
	wp_enqueue_style( 'studentup', get_stylesheet_uri(), array(), STUDENTUP_VERSION );
	wp_enqueue_script( 'studentup', get_template_directory_uri() . '/assets/js/studentup.js', array(), STUDENTUP_VERSION, true );
	// v72: PWA install prompt (app-laga install) — pwa option ON unte mattrame
	if ( studentup_opt( 'pwa', '1' ) ) {
		wp_enqueue_script( 'studentup-pwa', get_template_directory_uri() . '/assets/js/studentup-pwa.js', array( 'studentup' ), STUDENTUP_VERSION, true );
	}
	wp_localize_script(
		'studentup',
		'STUDENTUP',
		array(
			'home'     => esc_url_raw( home_url( '/' ) ),
			'rest'     => esc_url_raw( rest_url( 'wp/v2/' ) ),   // v89: live search endpoint
			'aliases'  => studentup_cat_aliases(),               // v89: chip ↔ live-slug map
			'chips'    => true,
			'i18n'     => array(
				'updates'   => 'updates',
				'soon'      => 'Soon',
				'none'      => 'No posts in this section yet — coming soon.',
				'searching' => 'Searching…',
				'noresults' => 'No posts found — press Enter to see the full search page',
				'viewall'   => 'See all results',
			),
		)
	);
	if ( is_singular() && comments_open() && get_option( 'thread_comments' ) ) {
		wp_enqueue_script( 'comment-reply' );
	}
}
add_action( 'wp_enqueue_scripts', 'studentup_assets' );

/**
 * Widgets — sidebar + footer (optional; design single-column tho kuda perfect ga untundi).
 */
function studentup_widgets() {
	register_sidebar(
		array(
			'name'          => 'Sidebar',
			'id'            => 'sidebar-1',
			'description'   => 'Beside post pages (optional).',
			'before_widget' => '<section id="%1$s" class="sidecard widget %2$s">',
			'after_widget'  => '</section>',
			'before_title'  => '<h3>',
			'after_title'   => '</h3>',
		)
	);
	for ( $i = 1; $i <= 3; $i++ ) {
		register_sidebar(
			array(
				/* translators: %d: footer column number. */
				'name'          => sprintf( 'Footer column %d', $i ),
				'id'            => 'footer-' . $i,
				'before_widget' => '<div id="%1$s" class="widget %2$s">',
				'after_widget'  => '</div>',
				'before_title'  => '<h4>',
				'after_title'   => '</h4>',
			)
		);
	}
}
add_action( 'widgets_init', 'studentup_widgets' );

/**
 * Excerpt — Telugu clean, fixed length.
 */
function studentup_excerpt_length( $length ) {
	return 22;
}
add_filter( 'excerpt_length', 'studentup_excerpt_length' );

function studentup_excerpt_more( $more ) {
	return ' …';
}
add_filter( 'excerpt_more', 'studentup_excerpt_more' );

/**
 * Performance + security hygiene (small, safe wins).
 */
function studentup_head_cleanup() {
	remove_action( 'wp_head', 'wp_generator' );
	remove_action( 'wp_head', 'print_emoji_detection_script', 7 );
	remove_action( 'wp_print_styles', 'print_emoji_styles' );
	remove_action( 'admin_print_scripts', 'print_emoji_detection_script' );
}
add_action( 'init', 'studentup_head_cleanup' );

/**
 * 429 (polite) — bot posts ni rate-limit cheyyalsina avasaram ledu; kottha posts ki
 * pingback header pampadam WordPress default. Extra: oEmbed discovery off (privacy).
 */
function studentup_disable_emoji_title() {
	return 'StudentUp — the platform for Telangana & Andhra Pradesh students';
}


/**
 * v69: menu lo **prastuta page** ki `aria-current="page"` (a11y + SEO crawl signal).
 */
function studentup_nav_link_aria( $atts, $item, $args ) {
	if ( ! empty( $atts['aria-current'] ) ) {
		return $atts;
	}
	if ( isset( $args->theme_location ) && in_array( $args->theme_location, array( 'primary', 'menu-1' ), true ) ) {
		$current_id = (int) get_queried_object_id();
		if ( $current_id && (int) $item->object_id === $current_id ) {
			$atts['aria-current'] = 'page';
		}
	}
	return $atts;
}
add_filter( 'nav_menu_link_attributes', 'studentup_nav_link_aria', 10, 3 );
