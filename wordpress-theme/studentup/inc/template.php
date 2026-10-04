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
/**
 * v191.1 WORLDCLASS: card category accent (left/top edge colour).
 *
 * Enduku: list lo okka look tho "TS job aa, AP job aa, result aa" teliyali —
 * reader scan speed perigutundi, bounce taggutundi. Guess ledu: mee category
 * peru nunchi mattrame decide chestundi.
 *
 * @param string $label first category name.
 * @return string accent slug.
 */
function studentup_card_accent( $label = '' ) {
	$key = strtolower( (string) $label );
	if ( false !== strpos( $key, 'result' ) ) {
		return 'result';
	}
	if ( false !== strpos( $key, 'scholarship' ) ) {
		return 'scholarship';
	}
	if ( false !== strpos( $key, 'central' ) || false !== strpos( $key, 'ssc' ) || false !== strpos( $key, 'rrb' ) ) {
		return 'central';
	}
	if ( false !== strpos( $key, 'ap ' ) || false !== strpos( $key, 'andhra' ) ) {
		return 'ap';
	}
	if ( false !== strpos( $key, 'ts ' ) || false !== strpos( $key, 'telangana' ) ) {
		return 'ts';
	}
	return 'update';
}

/**
 * v192: monogram for the designed cover art ("Central Govt" → "CG", "TS Jobs" → "TS").
 *
 * @param string $label Category label.
 * @return string 1-3 uppercase characters.
 */
function studentup_card_monogram( $label ) {
	$label = trim( preg_replace( '/\s+/u', ' ', (string) $label ) );
	if ( '' === $label ) {
		return 'SU';
	}
	$words = preg_split( '/\s+/u', $label );
	$first = mb_strtoupper( $words[0] );
	// "SSC CHSL" → SSC · "TSPSC Group" → TSP · "Central Govt" → CG · "Results" → RE
	if ( mb_strlen( $first ) <= 3 ) {
		return $first;
	}
	$mono = mb_substr( $first, 0, 2 );
	if ( isset( $words[1] ) && mb_strlen( $mono ) < 2 ) {
		$mono .= mb_strtoupper( mb_substr( $words[1], 0, 1 ) );
	}
	return $mono;
}

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
	// v156: state tags for the personalised strip - derived from the real
	// category slugs, never guessed.
	$su_states = array();
	foreach ( (array) get_the_category() as $su_term ) {
		$su_slug = isset( $su_term->slug ) ? $su_term->slug : '';
		if ( false !== strpos( $su_slug, 'ts-' ) || false !== strpos( $su_slug, 'telangana' ) ) {
			$su_states[] = 'ts';
		}
		if ( false !== strpos( $su_slug, 'ap-' ) || false !== strpos( $su_slug, 'andhra' ) ) {
			$su_states[] = 'ap';
		}
		if ( false !== strpos( $su_slug, 'central' ) ) {
			$su_states[] = 'central';
		}
	}
	$su_states = implode( ' ', array_unique( $su_states ) );
	// v191.1: home first card = editorial lead (peddha card) + category accent.
	$su_accent = studentup_card_accent( $label );
	$su_lead   = ( 0 === (int) $idx && ( is_front_page() || is_home() ) ) ? ' news--lead' : '';
	?>
	<article <?php post_class( 'news' . $su_lead ); ?> data-accent="<?php echo esc_attr( $su_accent ); ?>" data-su-card data-cat="<?php echo esc_attr( $cat ); ?>"
		data-qual="<?php echo esc_attr( $su_qual_raw ); ?>"
		data-state="<?php echo esc_attr( $su_states ); ?>"
		data-last="<?php echo esc_attr( $su_last_raw ); ?>"
		data-text="<?php echo esc_attr( mb_strtolower( get_the_title() . ' ' . get_the_excerpt() ) ); ?>">
		<?php if ( has_post_thumbnail() ) : ?>
			<a class="thumb <?php echo esc_attr( $tone ); ?>" href="<?php the_permalink(); ?>" aria-hidden="true" tabindex="-1">
				<?php
				// v157 LCP: the first card image is usually the largest element
				// above the fold, so it must NOT be lazy-loaded. Everything
				// after it stays lazy.
				$su_img_attr = array( 'alt' => esc_attr( get_the_title() ) );
				if ( 0 === (int) $idx ) {
					$su_img_attr['loading']       = 'eager';
					$su_img_attr['fetchpriority'] = 'high';
				} else {
					$su_img_attr['loading'] = 'lazy';
				}
				the_post_thumbnail( 'studentup-card', $su_img_attr );
				?>
			</a>
		<?php else : ?>
			<?php // v192: photo lekapote DESIGNED cover (gradient + monogram + category pill) —
			// purathana version post title ni plain text box lo print chesedi, adi wireframe la kanipinchedi. ?>
			<a class="thumb thumb--auto <?php echo esc_attr( $tone ); ?>" href="<?php the_permalink(); ?>" aria-hidden="true" tabindex="-1">
				<span class="su-cov">
					<b class="su-cov-mono"><?php echo esc_html( studentup_card_monogram( $label ) ); ?></b>
					<span class="su-cov-cat"><?php echo esc_html( $label ); ?></span>
					<span class="su-cov-brand">StudentUp</span>
				</span>
			</a>
		<?php endif; ?>
		<div class="newsbody">
			<div class="tagrow">
				<span class="tag"><?php echo esc_html( $label ); ?></span>
				<?php
				// v140: honest freshness tag — only for posts actually published
				// in the last 24 hours. No fake "HOT" on an old notification.
				if ( ( time() - (int) get_post_time( 'U', true ) ) < DAY_IN_SECONDS ) {
					echo '<span class="su-fresh">' . esc_html__( 'NEW', 'studentup' ) . '</span>';
				}
				?>
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
				<?php
				$su_share_title = rawurlencode( get_the_title() );
				$su_share_url   = rawurlencode( get_permalink() );
				?>
				<a class="su-card-wa" href="https://wa.me/?text=<?php echo esc_attr( $su_share_title . '%20' . $su_share_url ); ?>" target="_blank" rel="noopener" title="Share on WhatsApp">
					<svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M12.04 2C6.58 2 2.13 6.45 2.13 11.91C2.13 13.66 2.59 15.36 3.45 16.86L2.05 22L7.3 20.62C8.75 21.41 10.38 21.83 12.04 21.83C17.5 21.83 21.95 17.38 21.95 11.92C21.95 9.27 20.92 6.78 19.05 4.91C17.18 3.03 14.69 2 12.04 2Z"/></svg> Share
				</a>
				<?php echo studentup_save_button( 0, 'su-save-card' ); // v92: 🔖 save-for-later (escaped in helper) ?>
				<?php if ( function_exists( 'studentup_tool_buttons' ) ) : ?>
					<?php echo wp_kses_post( studentup_tool_buttons( 0, 'card' ) ); ?>
				<?php endif; ?>
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
	echo '<div class="trustnote">' . studentup_ui_icon( 'check', 13 ) . ' This article was checked against official sources and written in simple language. '
		. 'If you spot a mistake, ' . esc_html( $email ) . ' — we correct it within 24 hours. '
		. 'Always confirm deadlines and numbers in the official notification.</div>';
}

/**
 * Default menu (Appearance → Menus lo 'primary' assign cheyyakapote).
 *
 * v93 (UI fix): ippati varaku idi Home + 9 categories ni **flat ga** render chesindi —
 * prathi item ki description line tho. Result: header lo 10 items, 2 lines each,
 * overflow — menu chala cluttered ga kanipinchindi (approved preview design ki
 * polika ledu). Preview design lo menu **grouped dropdowns**:
 *   Home · Jobs ▾ · Hall Tickets · Results · Current Affairs · More ▾
 *
 * Ippudu fallback kuda ade structure istundi (`menu-item-has-children` +
 * `ul.sub-menu`) — anduke theme CSS dropdown anni pani chestayi, and
 * `wp_nav_menu` (user menu) tho markup **okate** feel.
 *
 * Rules:
 *   · Terms eppudu alias-aware (`studentup_used_term`) — TS/AP/Central missing aithe
 *     aa item automatic ga skip (empty link ledu).
 *   · Ee category okkati kuda exist kaakapote parent **khali dropdown** chupinchadu —
 *     daaniki badulu flat Home-only menu (site clean).
 *   · Page links (Saved / Contact / Quiz) unte mattrame chupistundi (404 ledu).
 *
 * @return void
 */
function studentup_primary_job_items() {
	$definitions = array(
		array( 'slug' => 'ts-jobs', 'section' => 'ts', 'label' => 'Telangana' ),
		array( 'slug' => 'ap-jobs', 'section' => 'ap', 'label' => 'Andhra Pradesh' ),
		array( 'slug' => 'central-jobs', 'section' => 'central', 'label' => 'Central Govt' ),
	);
	$items = array();
	foreach ( $definitions as $definition ) {
		$term = studentup_used_term( $definition['slug'] );
		$items[] = array(
			'slug'  => $definition['slug'],
			'label' => $definition['label'],
			'url'   => $term ? get_category_link( $term ) : home_url( '/#cat-' . $definition['slug'] ),
		);
	}
	return $items;
}

/**
 * Remaining categories for the controlled desktop More dropdown and mobile
 * accordion. Missing terms are omitted instead of linking to empty archives.
 *
 * @return array<int,array<string,string>>
 */
function studentup_menu_more_items() {
	$definitions = array(
		array( 'slug' => 'walkin-jobs', 'label' => 'Walk-in Interviews' ),
		array( 'slug' => 'software-jobs', 'label' => 'Software Jobs' ),
		array( 'slug' => 'private-jobs', 'label' => 'Private Jobs' ),
		array( 'slug' => 'outsourcing-jobs', 'label' => 'Outsourcing & Contract Jobs' ),
		array( 'slug' => 'part-time-jobs', 'label' => 'Part-time Jobs' ),
		array( 'slug' => 'internships', 'label' => 'Internships' ),
		array( 'slug' => 'abroad-jobs', 'label' => 'Abroad Jobs' ),
		array( 'slug' => 'results', 'label' => 'Results' ),
		array( 'slug' => 'hall-tickets', 'label' => 'Hall Tickets' ),
		array( 'slug' => 'scholarships', 'label' => 'Scholarships' ),
		array( 'slug' => 'current-affairs', 'label' => 'Current Affairs' ),
		array( 'slug' => 'success-stories', 'label' => 'Success Stories' ),
		array( 'slug' => 'upcoming-exams', 'label' => 'Upcoming Exams' ),
		array( 'slug' => 'admissions', 'label' => 'Admissions' ),
		array( 'slug' => 'daily-quiz', 'label' => 'Daily Quiz' ),
	);
	$alias_map    = studentup_cat_aliases();
	$canonical_for = static function ( $slug ) use ( $alias_map ) {
		foreach ( $alias_map as $canonical => $aliases ) {
			if ( $slug === $canonical || in_array( $slug, $aliases, true ) ) {
				return $canonical;
			}
		}
		return $slug;
	};
	$items        = array();
	$seen_groups  = array();
	$seen_terms   = array();

	// Keep the three primary job sections out of More even if their live slugs
	// differ from the theme's canonical slugs.
	foreach ( studentup_primary_job_items() as $primary ) {
		$seen_groups[ $canonical_for( $primary['slug'] ) ] = true;
		$term = studentup_used_term( $primary['slug'] );
		if ( $term ) {
			$seen_terms[ (int) $term->term_id ] = true;
		}
	}

	// Put the familiar categories first, in a predictable order.
	foreach ( $definitions as $definition ) {
		$group = $canonical_for( $definition['slug'] );
		if ( isset( $seen_groups[ $group ] ) ) {
			continue;
		}
		$term = studentup_used_term( $definition['slug'] );
		if ( ! $term ) {
			continue;
		}
		$seen_groups[ $group ]                 = true;
		$seen_terms[ (int) $term->term_id ]    = true;
		$items[] = array(
			'label' => $definition['label'],
			'url'   => get_category_link( $term ),
		);
	}

	// Include other live non-empty categories too, so a newly added category is
	// still reachable under More without expanding the desktop navigation row.
	$all_terms = get_categories( array( 'hide_empty' => true, 'orderby' => 'name', 'order' => 'ASC' ) );
	if ( is_array( $all_terms ) ) {
		foreach ( $all_terms as $term ) {
			if ( ! is_object( $term ) || empty( $term->term_id ) || empty( $term->slug ) || empty( $term->name ) ) {
				continue;
			}
			$slug = sanitize_key( (string) $term->slug );
			if ( '' === $slug || 'uncategorized' === $slug || isset( $seen_terms[ (int) $term->term_id ] ) ) {
				continue;
			}
			$group = $canonical_for( $slug );
			if ( isset( $seen_groups[ $group ] ) ) {
				continue;
			}
			$seen_groups[ $group ]              = true;
			$seen_terms[ (int) $term->term_id ] = true;
			$items[] = array(
				'label' => (string) $term->name,
				'url'   => get_category_link( $term ),
			);
		}
	}

	// A Breaking News entry appears only when real, fresh, verified TS/AP local
	// news exists; it stays in More rather than taking a primary-nav slot.
	if ( function_exists( 'studentup_breaking_items' )
		&& function_exists( 'studentup_breaking_enabled' )
		&& studentup_breaking_enabled()
		&& studentup_opt( 'breaking_nav', '1' )
		&& studentup_breaking_items( 1 )
	) {
		$items[] = array(
			'label' => 'Breaking News · TS/AP local updates',
			'url'   => home_url( '/#breaking' ),
		);
	}

	$items[] = array(
		'label' => 'All active opportunities',
		'url'   => studentup_opportunity_board_url(),
	);
	return $items;
}

/**
 * Controlled primary navigation. Do not call wp_nav_menu() here: an assigned
 * WordPress menu must not flatten or replace the required Home / TS / AP /
 * Central / More hierarchy.
 *
 * @return void
 */
function studentup_menu_fallback() {
	$home = home_url( '/' );
	echo '<ul id="primary-menu" class="menu-primary">';
	printf(
		'<li class="menu-item%s"><a href="%s">%s</a></li>',
		is_front_page() ? ' current-menu-item' : '',
		esc_url( $home ),
		esc_html__( 'Home', 'studentup' )
	);

	foreach ( studentup_primary_job_items() as $item ) {
		$term = studentup_used_term( $item['slug'] );
		printf(
			'<li class="menu-item%s"><a href="%s">%s</a></li>',
			$term && is_category( $term ) ? ' current-menu-item' : '',
			esc_url( $item['url'] ),
			esc_html( $item['label'] )
		);
	}

	$more = studentup_menu_more_items();
	printf(
		'<li class="menu-item menu-item-has-children su-more-menu"><a href="%s" aria-haspopup="true" aria-expanded="false" aria-controls="su-more-menu">%s</a>',
		esc_url( studentup_opportunity_board_url() ),
		esc_html__( 'More', 'studentup' )
	);
	echo '<ul class="sub-menu" id="su-more-menu" aria-label="' . esc_attr__( 'More categories', 'studentup' ) . '">';
	foreach ( $more as $item ) {
		printf(
			'<li class="menu-item"><a href="%s">%s</a></li>',
			esc_url( $item['url'] ),
			esc_html( $item['label'] )
		);
	}
	echo '</ul></li></ul>';
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
