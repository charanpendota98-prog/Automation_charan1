<?php
/**
 * v154 — internal link engine.
 *
 * Every article should point at the other articles a reader actually needs
 * next. Doing that by hand across hundreds of posts never happens, so this
 * links automatically - but with hard brakes, because aggressive auto-linking
 * is a classic spam signal:
 *
 *   - at most `studentup_autolink_max()` links per article (default 3),
 *   - one link per target post, first mention only,
 *   - never inside headings, existing links, images, shortcodes or code,
 *   - only exact title-phrase matches of at least 14 characters, so a link is
 *     only added when the phrase genuinely names that post,
 *   - never links a post to itself.
 *
 * The candidate list reuses the cached search index, so this costs no extra
 * database work.
 *
 * @package StudentUp
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Maximum auto links per article.
 *
 * @return int
 */
function studentup_autolink_max() {
	$n = (int) studentup_opt( 'autolink_max', '3' );
	if ( $n < 0 ) {
		$n = 0;
	}
	if ( $n > 6 ) {
		$n = 6;
	}
	return $n;
}

/**
 * Candidate phrases -> permalinks, longest phrase first.
 *
 * @return array
 */
function studentup_autolink_map() {
	if ( ! function_exists( 'studentup_build_search_index' ) ) {
		return array();
	}
	$index = studentup_build_search_index();
	$map   = array();
	if ( empty( $index['items'] ) || ! is_array( $index['items'] ) ) {
		return $map;
	}
	foreach ( $index['items'] as $item ) {
		$title = isset( $item['t'] ) ? trim( (string) $item['t'] ) : '';
		$url   = isset( $item['u'] ) ? (string) $item['u'] : '';
		if ( '' === $title || '' === $url ) {
			continue;
		}
		// Long, specific phrases only - short titles match too much text.
		if ( mb_strlen( $title ) < 14 ) {
			continue;
		}
		$map[ $title ] = $url;
	}
	uksort(
		$map,
		function ( $a, $b ) {
			return mb_strlen( $b ) - mb_strlen( $a );
		}
	);
	return $map;
}

/**
 * Add internal links to the article body.
 *
 * @param string $content Post content.
 * @return string
 */
function studentup_autolink_content( $content ) {
	if ( ! is_singular( 'post' ) || ! in_the_loop() || ! is_main_query() ) {
		return $content;
	}
	if ( '1' !== studentup_opt( 'autolink', '1' ) ) {
		return $content;
	}
	$budget = studentup_autolink_max();
	if ( $budget < 1 ) {
		return $content;
	}

	$self = get_permalink();
	$map  = studentup_autolink_map();
	if ( ! $map ) {
		return $content;
	}

	// Split into linkable text and protected blocks (tags we must not touch).
	$protected = '#(<a\b[^>]*>.*?</a>|<h[1-6]\b[^>]*>.*?</h[1-6]>|<script\b[^>]*>.*?</script>|<style\b[^>]*>.*?</style>|<code\b[^>]*>.*?</code>|<pre\b[^>]*>.*?</pre>|<[^>]+>)#is';
	$parts     = preg_split( $protected, $content, -1, PREG_SPLIT_DELIM_CAPTURE );
	if ( ! is_array( $parts ) ) {
		return $content;
	}

	$used = array();
	foreach ( $parts as $i => $part ) {
		if ( $budget < 1 ) {
			break;
		}
		// Odd chunks are the protected delimiters - leave them alone.
		if ( 1 === $i % 2 || '' === trim( $part ) ) {
			continue;
		}
		foreach ( $map as $phrase => $url ) {
			if ( $budget < 1 ) {
				break;
			}
			if ( $url === $self || isset( $used[ $url ] ) ) {
				continue;
			}
			$pos = mb_stripos( $part, $phrase );
			if ( false === $pos ) {
				continue;
			}
			$found   = mb_substr( $part, $pos, mb_strlen( $phrase ) );
			$replace = sprintf(
				'<a class="su-autolink" href="%1$s">%2$s</a>',
				esc_url( $url ),
				esc_html( $found )
			);
			$part = mb_substr( $part, 0, $pos ) . $replace . mb_substr( $part, $pos + mb_strlen( $phrase ) );
			$used[ $url ] = true;
			--$budget;
		}
		$parts[ $i ] = $part;
	}

	return implode( '', $parts );
}
add_filter( 'the_content', 'studentup_autolink_content', 16 );
