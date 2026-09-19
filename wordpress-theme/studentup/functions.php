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

define( 'STUDENTUP_VERSION', '1.7.2' );  // v74: exam portal + dead exam link teesesaam · shortcuts = Jobs/Qualification/Results/Quiz

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

/**
 * "Most searched by students" — order okkate source (bot lo autoblog/breaking.py
 * MOST_USED + preview site + tests anni ide order vaadutayi).
 */
function studentup_most_used() {
	return array(
		array( 'slug' => 'ts-jobs', 'label' => 'TS Government Jobs', 'icon' => '🏛', 'hint' => 'TSPSC · Police · Gurukul' ),
		array( 'slug' => 'ap-jobs', 'label' => 'AP Government Jobs', 'icon' => '🏛', 'hint' => 'APPSC · Police · DSC · Secretariat' ),
		array( 'slug' => 'hall-tickets', 'label' => 'Hall Tickets', 'icon' => '🎫', 'hint' => 'Admit card · key instructions' ),
		array( 'slug' => 'results', 'label' => 'Results', 'icon' => '📄', 'hint' => 'Board · competitive exams · keys' ),
		array( 'slug' => 'walkin-jobs', 'label' => 'Walk-in Interviews', 'icon' => '🚶', 'hint' => 'This week\'s drives · venues' ),
		array( 'slug' => 'software-jobs', 'label' => 'Software Jobs', 'icon' => '💻', 'hint' => 'IT · developer · fresher' ),
		array( 'slug' => 'private-jobs', 'label' => 'Private Jobs', 'icon' => '🏢', 'hint' => 'TCS · Infosys · Off-campus' ),
		array( 'slug' => 'current-affairs', 'label' => 'Current Affairs', 'icon' => '📰', 'hint' => 'Daily GK · for exams' ),
	);
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
			'chips'    => true,
			'i18n'     => array(
				'updates' => 'updates',
				'soon'    => 'Soon',
				'none'    => 'No posts in this section yet — coming soon.',
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
