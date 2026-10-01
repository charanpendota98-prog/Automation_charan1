<?php
/**
 * v129 AUTO SOCIAL CARD — featured image lekapote kuda prathi post ki branded
 * 1200×630 share/Discover image automatic ga generate avutundi.
 *
 * Enduku: WhatsApp/Telegram/Twitter/Discover lo image lekunda share aithe CTR
 * sagam paddipotundi. Editor image marchipoina site eppudu "khali card" ga
 * kanipinchakoodadu.
 *
 * Elaa pani chestundi:
 *   · `/studentup-card/<post-id>/` endpoint (rewrite) → GD tho PNG render
 *   · uploads/studentup-og/ lo cache (post update aithe regenerate)
 *   · GD lekapote / font dorakakapote → silently OFF (og:image ledu; fake
 *     image eppudu serve cheyyadu)
 *   · Featured image unte ee generator eppudu use avvadu (real photo > branded card)
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Generator vaadatanikaina server ready unda?
 *
 * @return bool
 */
function studentup_og_supported() {
	return function_exists( 'imagecreatetruecolor' ) && function_exists( 'imagettftext' ) && '' !== studentup_og_font();
}

/**
 * Text render ki TTF font path (theme lo font ship cheyyaledu — license clean;
 * server lo unna common DejaVu/Liberation fonts vaadutundi).
 *
 * @return string '' = font ledu
 */
function studentup_og_font() {
	$candidates = array(
		'/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
		'/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
		'/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
		'/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf',
		'/usr/share/fonts/TTF/DejaVuSans-Bold.ttf',
		'/System/Library/Fonts/Supplemental/Arial Bold.ttf',
	);
	/** Filter: site owner tana font path ivvachu. */
	$candidates = apply_filters( 'studentup_og_font_candidates', $candidates );
	foreach ( $candidates as $path ) {
		if ( is_string( $path ) && file_exists( $path ) && is_readable( $path ) ) {
			return $path;
		}
	}
	return '';
}

/**
 * Rewrite endpoint: /studentup-card/<id>/
 */
function studentup_og_rewrite() {
	add_rewrite_rule( '^studentup-card/([0-9]+)/?$', 'index.php?studentup_card_id=$matches[1]', 'top' );
}
add_action( 'init', 'studentup_og_rewrite' );

/**
 * Query var.
 *
 * @param array $vars vars.
 * @return array
 */
function studentup_og_query_var( $vars ) {
	$vars[] = 'studentup_card_id';
	return $vars;
}
add_filter( 'query_vars', 'studentup_og_query_var' );

/**
 * Cache file path for a post.
 *
 * @param int $post_id post.
 * @return array{path:string,url:string}
 */
function studentup_og_cache_paths( $post_id ) {
	$up   = wp_upload_dir();
	$dir  = trailingslashit( $up['basedir'] ) . 'studentup-og';
	$url  = trailingslashit( $up['baseurl'] ) . 'studentup-og';
	$hash = substr( md5( get_the_modified_time( 'U', $post_id ) . '|' . get_the_title( $post_id ) . '|' . get_bloginfo( 'name' ) ), 0, 10 );
	return array(
		'path' => $dir . '/' . (int) $post_id . '-' . $hash . '.png',
		'url'  => $url . '/' . (int) $post_id . '-' . $hash . '.png',
		'dir'  => $dir,
	);
}

/**
 * Render (and cache) the branded card. Returns the file path or ''.
 *
 * @param int $post_id post.
 * @return string
 */
function studentup_og_render( $post_id ) {
	$post_id = (int) $post_id;
	if ( ! $post_id || 'publish' !== get_post_status( $post_id ) || ! studentup_og_supported() ) {
		return '';
	}
	$paths = studentup_og_cache_paths( $post_id );
	if ( file_exists( $paths['path'] ) ) {
		return $paths['path'];
	}
	if ( ! wp_mkdir_p( $paths['dir'] ) ) {
		return '';
	}

	$w    = 1200;
	$h    = 630;
	$img  = imagecreatetruecolor( $w, $h );
	$font = studentup_og_font();

	// Brand gradient background (indigo → violet → pink).
	for ( $x = 0; $x < $w; $x++ ) {
		$t = $x / max( 1, $w - 1 );
		$r = (int) round( 79 + ( 236 - 79 ) * $t );
		$g = (int) round( 70 + ( 72 - 70 ) * $t );
		$b = (int) round( 229 + ( 153 - 229 ) * $t );
		imagefilledrectangle( $img, $x, 0, $x, $h, imagecolorallocate( $img, $r, $g, $b ) );
	}
	// Dark panel for text contrast (WCAG-safe).
	$panel = imagecolorallocatealpha( $img, 12, 18, 40, 38 );
	imagefilledrectangle( $img, 48, 48, $w - 48, $h - 48, $panel );

	$white = imagecolorallocate( $img, 255, 255, 255 );
	$soft  = imagecolorallocate( $img, 214, 222, 245 );

	// Kicker: category + site name.
	$cats   = get_the_category( $post_id );
	$kicker = strtoupper( ( $cats ? $cats[0]->name . '  ·  ' : '' ) . get_bloginfo( 'name' ) );
	imagettftext( $img, 20, 0, 86, 130, $soft, $font, $kicker );

	// Title — manual word wrap (max 4 lines).
	$title = wp_strip_all_tags( get_the_title( $post_id ) );
	$size  = 44;
	$lines = array();
	$line  = '';
	foreach ( preg_split( '/\s+/', $title ) as $word ) {
		$try = '' === $line ? $word : $line . ' ' . $word;
		$box = imagettfbbox( $size, 0, $font, $try );
		if ( $box && ( $box[2] - $box[0] ) > ( $w - 190 ) && '' !== $line ) {
			$lines[] = $line;
			$line    = $word;
			if ( count( $lines ) >= 4 ) {
				break;
			}
		} else {
			$line = $try;
		}
	}
	if ( '' !== $line && count( $lines ) < 4 ) {
		$lines[] = $line;
	}
	$y = 220;
	foreach ( $lines as $l ) {
		imagettftext( $img, $size, 0, 86, $y, $white, $font, $l );
		$y += 64;
	}

	// Footer: last date (unte) + domain.
	$last   = function_exists( 'studentup_opportunity_last_date' ) ? studentup_opportunity_last_date( $post_id ) : '';
	$footer = $last ? 'Last date: ' . date_i18n( 'M j, Y', strtotime( $last ) ) : get_the_date( 'M j, Y', $post_id );
	imagettftext( $img, 22, 0, 86, $h - 92, $soft, $font, $footer );
	$domain = wp_parse_url( home_url( '/' ), PHP_URL_HOST );
	imagettftext( $img, 22, 0, 86, $h - 92 + 38, $white, $font, (string) $domain );

	imagepng( $img, $paths['path'], 6 );
	imagedestroy( $img );
	return file_exists( $paths['path'] ) ? $paths['path'] : '';
}

/**
 * Serve the endpoint.
 */
function studentup_og_serve() {
	$id = (int) get_query_var( 'studentup_card_id' );
	if ( ! $id ) {
		return;
	}
	$file = studentup_og_render( $id );
	if ( ! $file ) {
		status_header( 404 );
		nocache_headers();
		exit;
	}
	status_header( 200 );
	header( 'Content-Type: image/png' );
	header( 'Cache-Control: public, max-age=604800, immutable' );
	readfile( $file ); // phpcs:ignore WordPress.WP.AlternativeFunctions.file_system_operations_readfile
	exit;
}
add_action( 'template_redirect', 'studentup_og_serve', 1 );

/**
 * Public URL for a post's auto card ('' = generator off).
 *
 * @param int $post_id post.
 * @return string
 */
function studentup_og_url( $post_id ) {
	if ( ! studentup_opt( 'auto_og', '1' ) || ! studentup_og_supported() ) {
		return '';
	}
	$post_id = (int) $post_id;
	if ( ! $post_id || has_post_thumbnail( $post_id ) ) {
		return '';   // Real featured image eppudu better.
	}
	$paths = studentup_og_cache_paths( $post_id );
	if ( file_exists( $paths['path'] ) ) {
		return $paths['url'];
	}
	return home_url( '/studentup-card/' . $post_id . '/' );
}

/**
 * og:image / twitter:image fallback (Rank Math unte adi already istundi —
 * appudu ee tag duplicate avvadu: theme og tags Rank Math absence lo mattrame).
 *
 * v176 REAL FIX: GD/fonts leni server meeda generated card image ledu —
 * appudu og:image EDU ledu (live install proof). WhatsApp shares nagna
 * link la ga poyevi. Ippudu chain: post thumbnail (seo-bridge) → generated
 * card (GD unte) → static brand card (assets/og-default.png — guaranteed).
 */
function studentup_og_meta() {
	if ( ! is_singular( 'post' ) ) {
		return;
	}
	$id = (int) get_the_ID();
	if ( has_post_thumbnail( $id ) ) {
		return;   // seo-bridge.php prints og:image for thumbnails.
	}
	$url = studentup_og_url( $id );
	if ( ! $url ) {
		// v176: static brand card — server GD/folder em support cheyyakapoina
		// share ki oka chala beautiful image guaranteed.
		$url = get_template_directory_uri() . '/assets/og-default.png';
	}
	if ( class_exists( 'RankMath' ) || defined( 'WPSEO_VERSION' ) ) {
		// SEO plugin already prints og:image — duplicate vaddu.
		return;
	}
	echo '<meta property="og:image" content="' . esc_url( $url ) . '">' . "\n";
	echo '<meta property="og:image:width" content="1200">' . "\n";
	echo '<meta property="og:image:height" content="630">' . "\n";
	echo '<meta property="og:image:alt" content="' . esc_attr( wp_strip_all_tags( get_the_title() ) ) . '">' . "\n";
	/*
	 * v177 FIX: twitter:card ikkada print cheyyatam vaddu — seo-bridge fallback
	 * already card + title + description istundi (live install lo 2 duplicates
	 * kanipinchayi). twitter:image matrame ikkada (seo-bridge aa tag ivvadu).
	 */
	echo '<meta name="twitter:image" content="' . esc_url( $url ) . '">' . "\n";
}
add_action( 'wp_head', 'studentup_og_meta', 7 );

/**
 * Theme activation / update lo rewrite rules refresh.
 */
function studentup_og_flush() {
	studentup_og_rewrite();
	flush_rewrite_rules( false );
}
add_action( 'after_switch_theme', 'studentup_og_flush' );
