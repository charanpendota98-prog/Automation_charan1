<?php
/**
 * v71: Block editor parity (advanced theme standard).
 *
 * Editor lo article raaseyappudu kuda front-end laage kanipinchali — anduku same
 * design tokens, typography and content width ni editor ki pass chestunnam.
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Editor support: editor styles + core block styles + wide alignment.
 */
function studentup_editor_setup() {
	add_theme_support( 'editor-styles' );
	add_theme_support( 'wp-block-styles' );
	add_theme_support( 'align-wide' );
	add_theme_support( 'responsive-embeds' );
	add_editor_style( 'assets/css/editor.css' );
}
add_action( 'after_setup_theme', 'studentup_editor_setup' );

/**
 * enqueue_block_editor_assets: WP 6.x ki extra safety (classic editor tho kuda).
 */
function studentup_editor_assets() {
	wp_enqueue_style(
		'studentup-editor',
		get_template_directory_uri() . '/assets/css/editor.css',
		array(),
		STUDENTUP_VERSION
	);
}
add_action( 'enqueue_block_editor_assets', 'studentup_editor_assets' );

/**
 * Block patterns cheyyi — vaatini admin lo copy cheyyalsina avasaram ledu.
 *
 * @param array $categories Pattern categories.
 * @return array
 */
function studentup_block_categories( $categories ) {
	$categories[] = array(
		'slug'  => 'studentup',
		'title' => __( 'StudentUp blocks', 'studentup' ),
	);
	return $categories;
}
add_filter( 'block_categories_all', 'studentup_block_categories', 10, 1 );
