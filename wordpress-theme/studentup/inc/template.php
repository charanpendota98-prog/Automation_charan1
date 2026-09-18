<?php
/**
 * Template helpers — proof tiles, deadline countdown, post cards, trust note.
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Trust proof tiles — LIVE WordPress numbers (fake numbers ledu).
 * Bot option 'studentup_proof_json' pedithe keyword/source numbers kuda vasthayi.
 *
 * @return array[]
 */
function studentup_proof_tiles() {
	$posts   = (int) wp_count_posts()->publish;
	$cats    = (int) wp_count_terms( array( 'taxonomy' => 'category', 'hide_empty' => true ) );
	$tiles   = array(
		array( 'value' => number_format_i18n( $posts ), 'label' => 'ప్రచురిత కథనాలు' ),
		array( 'value' => number_format_i18n( $cats ), 'label' => 'విభాగాలు (జాబ్/పరీక్షలు)' ),
	);
	$proof = json_decode( (string) get_option( 'studentup_proof_json', '' ), true );
	if ( is_array( $proof ) ) {
		if ( ! empty( $proof['keywords'] ) ) {
			$tiles[] = array( 'value' => number_format_i18n( (int) $proof['keywords'] ), 'label' => 'ట్రాక్ చేసిన కీవర్డ్‌లు' );
		} elseif ( ! empty( $proof['sources'] ) ) {
			$tiles[] = array( 'value' => number_format_i18n( (int) $proof['sources'] ), 'label' => 'అధికారిక మూలాల గ్రిడ్' );
		}
	} else {
		$tiles[] = array( 'value' => 'రోజూ', 'label' => 'కొత్త అప్డేట్‌లు' );
	}
	return $tiles;
}

/**
 * Live countdown target (bot option 'studentup_deadline_json' = {"title":…,"date":"2026-10-15T17:00:00+05:30"}).
 *
 * @return array
 */
function studentup_deadline() {
	$out   = array( 'title' => '', 'date' => '' );
	$raw   = json_decode( (string) get_option( 'studentup_deadline_json', '' ), true );
	if ( is_array( $raw ) && ! empty( $raw['date'] ) ) {
		$out['title'] = isset( $raw['title'] ) ? wp_strip_all_tags( (string) $raw['title'] ) : '';
		$out['date']  = sanitize_text_field( (string) $raw['date'] );
	}
	return $out;
}

/**
 * Kotha deadline option (bot nunchi).
 *
 * @param string $title title.
 * @param string $iso   ISO date.
 */
function studentup_set_deadline( $title, $iso ) {
	update_option(
		'studentup_deadline_json',
		wp_json_encode( array( 'title' => (string) $title, 'date' => (string) $iso ) ),
		false
	);
}

/**
 * Category slug → count (most-used tiles ki).
 *
 * @param string $slug category slug.
 * @return int
 */
function studentup_cat_count( $slug ) {
	$term = get_category_by_slug( $slug );
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
	return sanitize_html_class( $cats[0]->slug );
}

/**
 * Post card — design (preview) markup same.
 *
 * @param int $idx index (thumb colour rotation).
 */
function studentup_card( $idx = 0 ) {
	$cat   = studentup_card_cat();
	$terms = get_the_category();
	$label = $terms ? $terms[0]->name : 'అప్డేట్';
	$tones = array( '', 't2', 't3' );
	$tone  = $tones[ $idx % 3 ];
	?>
	<article class="news" data-cat="<?php echo esc_attr( $cat ); ?>" data-text="<?php echo esc_attr( mb_strtolower( get_the_title() . ' ' . get_the_excerpt() ) ); ?>">
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
				<time class="statechip" datetime="<?php echo esc_attr( get_the_date( DATE_W3C ) ); ?>"><?php echo esc_html( studentup_ago( get_the_date( DATE_W3C ) ) ); ?></time>
			</div>
			<h3><a href="<?php the_permalink(); ?>" style="color:inherit"><?php the_title(); ?></a></h3>
			<p><?php echo esc_html( wp_trim_words( get_the_excerpt(), 20, '…' ) ); ?></p>
			<div class="newsfoot">
				<span><?php echo esc_html( studentup_reading_time() ); ?></span>
				<b><?php echo esc_html( 'మార్గదర్శి చదవండి →' ); ?></b>
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
	return $minutes . ' నిమిషాల పఠనం';
}

/**
 * Trust note (corrections email) — prathi post kindha.
 */
function studentup_trust_note() {
	$email = (string) get_option( 'admin_email', '' );
	echo '<div class="trustnote">✅ ఈ కథనం అధికారిక మూలాలతో పరిశీలించి, సులభ తెలుగులో రాసింది. '
		. 'తప్పు కనిపిస్తే ' . esc_html( $email ) . ' కు తెలియజేయండి — 24 గంటల్లో సవరిస్తాము. '
		. 'తుది తేదీలు/సంఖ్యలు అధికారిక నోటిఫికేషన్‌లో నిర్ధారించుకోండి.</div>';
}

/**
 * Default menu (Appearance → Menus lo 'primary' assign cheyyakapote) — design order same.
 */
function studentup_menu_fallback() {
	$items = array(
		array( 'label' => 'హోమ్', 'url' => home_url( '/' ) ),
	);
	foreach ( studentup_most_used() as $m ) {
		$term = get_category_by_slug( $m['slug'] );
		if ( $term ) {
			$items[] = array( 'label' => $m['label'], 'url' => get_category_link( $term ), 'desc' => $m['hint'] );
		}
	}
	$items[] = array( 'label' => 'బ్రేకింగ్ న్యూస్', 'url' => home_url( '/#breaking' ), 'class' => 'navbrk' );
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
	$out = '<a href="' . esc_url( home_url( '/' ) ) . '">హోమ్</a>';
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
 * v67: కామెంట్లు OFF (admin option) → comment form + list render avvadu.
 *
 * @param bool $open Comments open state.
 * @return bool
 */
function studentup_comments_open( $open ) {
	return '0' === (string) studentup_opt( 'comments_on', '1' ) ? false : $open;
}
add_filter( 'comments_open', 'studentup_comments_open' );
