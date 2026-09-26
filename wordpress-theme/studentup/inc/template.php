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
	echo '<div class="trustnote">✅ This article was checked against official sources and written in simple language. '
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
function studentup_menu_fallback() {
	$home = home_url( '/' );

	/** Theme slug → term (alias-aware). Missing = null (skip). */
	$term_of = static function ( $slug ) {
		return studentup_used_term( $slug );
	};

	// Dropdown group definitions (preview design order).
	$groups = array(
		array(
			'label' => 'Jobs',
			'items' => array( 'ts-jobs', 'ap-jobs', 'central-jobs', 'private-jobs', 'walkin-jobs', 'software-jobs' ),
		),
	);
	$top = array( 'hall-tickets', 'results', 'current-affairs' );

	$label_of = array();
	foreach ( studentup_most_used() as $m ) {
		$label_of[ $m['slug'] ] = $m;
	}

	$menu = array();

	/**
	 * Jobs dropdown — terms unte mattrame (lekapote top-level ga chupinchadu).
	 */
	$jobs_children = array();
	foreach ( $groups[0]['items'] as $slug ) {
		$term = $term_of( $slug );
		if ( ! $term || ! isset( $label_of[ $slug ] ) ) {
			continue;
		}
		$jobs_children[] = array(
			'label' => $label_of[ $slug ]['label'],
			'url'   => get_category_link( $term ),
			'desc'  => $label_of[ $slug ]['hint'],
		);
	}
	if ( $jobs_children ) {
		$menu[] = array( 'label' => 'Jobs', 'url' => $jobs_children[0]['url'], 'children' => $jobs_children );
	}

	/**
	 * Top-level singles (only if the term really exists).
	 */
	foreach ( $top as $slug ) {
		$term = $term_of( $slug );
		if ( ! $term || ! isset( $label_of[ $slug ] ) ) {
			continue;
		}
		$menu[] = array(
			'label' => $label_of[ $slug ]['label'],
			'url'   => get_category_link( $term ),
		);
	}

	/**
	 * "More" — page links unte mattrame (404 eppudu ledu).
	 */
	$more = array(
		array( 'label' => 'Latest active jobs', 'url' => studentup_opportunity_board_url(), 'desc' => 'Dates unna active notices only' ),
	);
	$pages = array(
		array( 'slug' => 'saved',   'label' => 'Saved posts', 'desc' => 'Padhukoni tarvata chudandi' ),
		array( 'slug' => 'contact', 'label' => 'Contact',     'desc' => 'Corrections · suggestions' ),
		array( 'slug' => 'about',   'label' => 'About',       'desc' => 'Who writes this' ),
		array( 'slug' => 'quiz',    'label' => 'Daily Quiz',  'desc' => 'Practice questions' ),
	);
	foreach ( $pages as $pg ) {
		$page = get_page_by_path( $pg['slug'] );
		if ( $page && 'publish' === get_post_status( $page ) ) {
			$more[] = array(
				'label' => $pg['label'],
				'url'   => get_permalink( $page ),
				'desc'  => $pg['desc'],
			);
		}
	}
	$more[] = array(
		'label' => 'Jobs by qualification',
		'url'   => $home . '#qualsplit',
		'desc'  => '10th · Inter · Degree · PG',
	);
	$tg = function_exists( 'studentup_tg_channel_url' ) ? studentup_tg_channel_url() : '';
	if ( $tg ) {
		$more[] = array( 'label' => 'Telegram channel', 'url' => $tg, 'desc' => 'Job alerts first' );
	}
	$more[] = array( 'label' => 'All categories', 'url' => $home . '#jobs', 'desc' => 'Every job section' );

	if ( $more ) {
		$menu[] = array(
			'label'    => 'More',
			'url'      => $more[0]['url'],
			'children' => $more,
		);
	}

	/**
	 * Render — `wp_nav_menu` markup ki same (CSS okkate pani chestundi).
	 */
	echo '<ul id="primary-menu" class="menu-primary">';
	printf(
		'<li class="menu-item%s"><a href="%s">%s</a></li>',
		( is_front_page() ? ' current-menu-item' : '' ),
		esc_url( $home ),
		esc_html__( 'Home', 'studentup' )
	);
	foreach ( $menu as $it ) {
		$has_kids = ! empty( $it['children'] );
		printf(
			'<li class="menu-item%s">',
			$has_kids ? ' menu-item-has-children' : ''
		);
		if ( $has_kids ) {
			printf(
				'<a href="%s" aria-haspopup="true" aria-expanded="false">%s</a>',
				esc_url( $it['url'] ),
				esc_html( $it['label'] )
			);
			echo '<ul class="sub-menu">';
			foreach ( $it['children'] as $ch ) {
				printf(
					'<li class="menu-item"><a href="%s">%s%s</a></li>',
					esc_url( $ch['url'] ),
					esc_html( $ch['label'] ),
					( ! empty( $ch['desc'] ) ? '<small>' . esc_html( $ch['desc'] ) . '</small>' : '' )
				);
			}
			echo '</ul>';
		} else {
			printf( '<a href="%s">%s</a>', esc_url( $it['url'] ), esc_html( $it['label'] ) );
		}
		echo '</li>';
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
