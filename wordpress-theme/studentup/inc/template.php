<?php
/**
 * Template helpers — post cards, breadcrumbs, trust note, share/qualification bits.
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Category slug → count (most-used tiles ki).
 *
 * @param string $slug category slug.
 * @return int
 */
function studentup_cat_count( $slug ) {
	$term = studentup_used_term( $slug );   // v89: alias-aware (live slugs differ)
	return $term ? (int) $term->count : 0;
}

/**
 * Card category slug (WP category slug nunchi design chips ki).
 *
 * @param int $post_id post id.
 * @return string
 */
function studentup_card_cat( $post_id = 0 ) {
	$post_id = $post_id ? $post_id : get_the_ID();
	$cats    = get_the_category( $post_id );
	if ( ! $cats ) {
		return 'current-affairs';
	}
	// v89: live slug (‑govt heavy) → theme chip slug — TS/AP/Central chips filter match avvali.
	foreach ( $cats as $c ) {
		$theme_slug = studentup_theme_cat( $c->slug );
		if ( $theme_slug !== $c->slug || in_array( $theme_slug, wp_list_pluck( studentup_most_used(), 'slug' ), true ) ) {
			return sanitize_html_class( $theme_slug );
		}
	}
	return sanitize_html_class( studentup_theme_cat( $cats[0]->slug ) );
}

/**
 * Post card — design (preview) markup same.
 *
 * @param int $idx index (thumb colour rotation).
 */
function studentup_card( $idx = 0 ) {
	$cat   = studentup_card_cat();
	$terms = get_the_category();
$label = $terms ? $terms[0]->name : 'Update';
	$tones = array( '', 't2', 't3' );
	$tone  = $tones[ $idx % 3 ];
	?>
	<?php
	$su_qual_raw = trim( (string) get_post_meta( get_the_ID(), 'studentup_qual', true ) );
	$su_last_raw = trim( (string) get_post_meta( get_the_ID(), 'studentup_last_date', true ) );
	?>
	<article <?php post_class( 'news' ); ?> data-cat="<?php echo esc_attr( $cat ); ?>"
		data-qual="<?php echo esc_attr( $su_qual_raw ); ?>"
		data-last="<?php echo esc_attr( $su_last_raw ); ?>"
		data-text="<?php echo esc_attr( mb_strtolower( get_the_title() . ' ' . get_the_excerpt() ) ); ?>">
		<?php if ( has_post_thumbnail() ) : ?>
			<a class="thumb <?php echo esc_attr( $tone ); ?>" href="<?php the_permalink(); ?>" aria-hidden="true" tabindex="-1">
				<?php the_post_thumbnail( 'studentup-card', array( 'loading' => 'lazy', 'alt' => esc_attr( get_the_title() ) ) ); ?>
			</a>
		<?php else : ?>
			<a class="thumb <?php echo esc_attr( $tone ); ?>" href="<?php the_permalink(); ?>" aria-hidden="true" tabindex="-1"><?php echo esc_html( wp_trim_words( get_the_title(), 5, '…' ) ); ?></a>
		<?php endif; ?>
		<div class="newsbody">
			<div class="tagrow">
				<span class="tag"><?php echo esc_html( $label ); ?></span>
				<?php studentup_qual_chip(); ?>
				<time class="statechip" datetime="<?php echo esc_attr( get_the_date( DATE_W3C ) ); ?>"><?php echo esc_html( studentup_ago( get_the_date( DATE_W3C ) ) ); ?></time>
			</div>
			<h3><a href="<?php the_permalink(); ?>" style="color:inherit"><?php the_title(); ?></a></h3>
			<p><?php echo esc_html( wp_trim_words( get_the_excerpt(), 20, '…' ) ); ?></p>
			<div class="newsfoot">
				<span><?php echo esc_html( studentup_reading_time() ); ?></span>
				<?php
				if ( function_exists( 'studentup_last_date_badge' ) ) {
					echo wp_kses_post( studentup_last_date_badge() );
				}
				?>
				<a class="su-readmore" href="<?php the_permalink(); ?>"><?php echo esc_html__( 'Read more', 'studentup' ) . ' →'; ?></a>
			</div>
		</div>
	</article>
	<?php
}

/**
 * Reading time (Telugu label).
 *
 * @param int $post_id post.
 * @return string
 */
function studentup_reading_time( $post_id = 0 ) {
	$post_id = $post_id ? $post_id : get_the_ID();
	$words   = str_word_count( wp_strip_all_tags( (string) get_post_field( 'post_content', $post_id ) ) );
	$words   = max( $words, mb_strlen( wp_strip_all_tags( (string) get_post_field( 'post_content', $post_id ) ) ) / 6 );
	$minutes = max( 2, (int) ceil( $words / 220 ) );
	return $minutes . ' min read';
}

/**
 * Trust note (corrections email) — prathi post kindha.
 */
function studentup_trust_note() {
	$email = (string) get_option( 'admin_email', '' );
	echo '<div class="trustnote">✅ This article was checked against official sources and written in simple language. '
		. 'If you spot a mistake, ' . esc_html( $email ) . ' — we correct it within 24 hours. '
		. 'Always confirm deadlines and numbers in the official notification.</div>';
}

/**
 * Default menu (Appearance → Menus lo 'primary' assign cheyyakapote) — design order same.
 */
function studentup_menu_fallback() {
	$items = array(
		array( 'label' => 'Home', 'url' => home_url( '/' ) ),
	);
	foreach ( studentup_most_used() as $m ) {
		$term = studentup_used_term( $m['slug'] );   // v89: alias-aware (ts-jobs → ts-govt-jobs)
		if ( $term ) {
			$items[] = array( 'label' => $m['label'], 'url' => get_category_link( $term ), 'desc' => $m['hint'] );
		}
	}
	echo '<ul class="menu-primary">';
	foreach ( $items as $it ) {
		$cls = isset( $it['class'] ) ? ' class="' . esc_attr( $it['class'] ) . '"' : '';
		printf(
			'<li%s><a href="%s">%s%s</a></li>',
			$cls,
			esc_url( $it['url'] ),
			esc_html( $it['label'] ),
			isset( $it['desc'] ) ? '<small>' . esc_html( $it['desc'] ) . '</small>' : ''
		);
	}
	echo '</ul>';
}

/**
 * Breadcrumbs (Rank Math unte adi — ledu aithe idi).
 *
 * @return string
 */
function studentup_breadcrumbs() {
	if ( function_exists( 'rank_math_the_breadcrumbs' ) ) {
		ob_start();
		rank_math_the_breadcrumbs();
		return (string) ob_get_clean();
	}
	$out = '<a href="' . esc_url( home_url( '/' ) ) . '">Home</a>';
	if ( is_singular() ) {
		$cats = get_the_category();
		if ( $cats ) {
			$out .= ' › <a href="' . esc_url( get_category_link( $cats[0] ) ) . '">' . esc_html( $cats[0]->name ) . '</a>';
		}
		$out .= ' › ' . esc_html( wp_trim_words( get_the_title(), 8, '…' ) );
	} elseif ( is_archive() ) {
		$out .= ' › ' . esc_html( wp_strip_all_tags( get_the_archive_title() ) );
	}
	return $out;
}

/**
 * v67: comments OFF (admin option) → comment form + list are not rendered.
 *
 * @param bool $open Comments open state.
 * @return bool
 */
function studentup_comments_open( $open ) {
	return '0' === (string) studentup_opt( 'comments_on', '1' ) ? false : $open;
}
add_filter( 'comments_open', 'studentup_comments_open' );

/**
 * v80 (P16): subcategory chips for category archives (child cats + counts).
 * Child categories levu → output emi ledu (honest empty, no dummy chips).
 */
function studentup_subcat_chips( $cat_id ) {
	$cat_id = (int) $cat_id;
	if ( $cat_id <= 0 ) {
		return;
	}
	$kids = get_categories(
		array(
			'parent'     => $cat_id,
			'hide_empty' => true,
			'number'     => 12,
		)
	);
	if ( ! $kids ) {
		return;
	}
	echo '<nav class="su-subcats" aria-label="Subcategories">';
	foreach ( $kids as $kid ) {
		printf(
			'<a href="%s">%s <span>(%d)</span></a>',
			esc_url( get_category_link( $kid ) ),
			esc_html( $kid->name ),
			(int) $kid->count
		);
	}
	echo '</nav>';
}
