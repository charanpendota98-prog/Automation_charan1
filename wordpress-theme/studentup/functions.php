<?php
/**
 * StudentUp Telugu News — theme setup (v61).
 *
 * Design: preview/index.html lo unna design ne WordPress lo ki teesukostundi —
 * బ్రేకింగ్ టికర్ · "విద్యార్థులు ఎక్కువగా వెతికేవి" · ఉద్యోగం కార్డులు · ad slots.
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

define( 'STUDENTUP_VERSION', '1.4.0' );  // v69: theme standards pass 3 (version sync · editor styles · post_class)

require_once get_template_directory() . '/inc/options.php';
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

/**
 * "విద్యార్థులు ఎక్కువగా వెతికేవి" — order okkate source (bot lo autoblog/breaking.py
 * MOST_USED + preview site + tests anni ide order vaadutayi).
 */
function studentup_most_used() {
	return array(
		array( 'slug' => 'ts-jobs', 'label' => 'టీఎస్ ప్రభుత్వ ఉద్యోగాలు', 'icon' => '🏛', 'hint' => 'TSPSC · పోలీస్ · గురుకుల్' ),
		array( 'slug' => 'ap-jobs', 'label' => 'ఏపీ ప్రభుత్వ ఉద్యోగాలు', 'icon' => '🏛', 'hint' => 'APPSC · పోలీస్ · DSC · సచివాలయం' ),
		array( 'slug' => 'hall-tickets', 'label' => 'హాల్ టికెట్లు', 'icon' => '🎫', 'hint' => 'అడ్మిట్ కార్డ్ · ముఖ్య సూచనలు' ),
		array( 'slug' => 'results', 'label' => 'ఫలితాలు', 'icon' => '📄', 'hint' => 'బోర్డు · పోటీ పరీక్షలు · కీలు' ),
		array( 'slug' => 'walkin-jobs', 'label' => 'వాక్-ఇన్ ఇంటర్వ్యూ', 'icon' => '🚶', 'hint' => 'ఈ వారం డ్రైవ్‌లు · వేదికలు' ),
		array( 'slug' => 'software-jobs', 'label' => 'సాఫ్ట్‌వేర్ ఉద్యోగాలు', 'icon' => '💻', 'hint' => 'IT · డెవలపర్ · ఫ్రెషర్' ),
		array( 'slug' => 'private-jobs', 'label' => 'ప్రైవేట్ ఉద్యోగాలు', 'icon' => '🏢', 'hint' => 'TCS · ఇన్ఫోసిస్ · ఆఫ్-క్యాంపస్' ),
		array( 'slug' => 'current-affairs', 'label' => 'ప్రస్తుతాంశాలు', 'icon' => '📰', 'hint' => 'రోజు GK · పరీక్షలకు' ),
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
			'primary' => 'ప్రధాన మెనూ (హెడర్)',
			'mobile'  => 'మొబైల్ మెనూ',
			'footer'  => 'ఫుటర్ మెనూ',
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
	wp_localize_script(
		'studentup',
		'STUDENTUP',
		array(
			'home'     => esc_url_raw( home_url( '/' ) ),
			'apiBase'  => esc_url_raw( (string) get_option( 'studentup_api_base', '' ) ),
			'deadline' => studentup_deadline(),
			'chips'    => true,
			'i18n'     => array(
				'updates' => 'అప్డేట్‌లు',
				'soon'    => 'త్వరలో',
				'none'    => 'ఈ విభాగంలో ఇంకా పోస్టులు లేవు — త్వరలో వస్తాయి.',
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
			'name'          => 'సైడ్‌బార్',
			'id'            => 'sidebar-1',
			'description'   => 'పోస్ట్ పేజీ పక్కన (optional).',
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
				'name'          => sprintf( 'ఫుటర్ కాలమ్ %d', $i ),
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
	return 'StudentUp — తెలంగాణ & ఆంధ్రప్రదేశ్ విద్యార్థుల వేదిక';
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
