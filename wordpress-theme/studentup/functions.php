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

define( 'STUDENTUP_VERSION', '1.9.37' );  // v188 HOOK LEAD: 'main enti' first line (su-hook, dark/print safe) + Telugu daily list hooks; v185 WORLD-CLASS PASS: no-flash dark mode (pre-paint) + color-scheme (native controls) + single H1 per view + card containment + fresh min.css; v184 ACTIVE BOARD HYGIENE: expired out + stale sweep (120d) + same-recruitment dedupe (site ↔ bot parity); v183 FORWARD LIST: outsourcing/contract board section (site + bot daily list align); v181 SEARCH-DEMAND LOG (readers' queries → content gaps); v180 SVG SPRITE (home -30KB) + live-JS-clean; v179 ATTACHMENT-REDIRECT + RICH FEEDS; v178 ALIAS-MERGE ARCHIVES + PWA icons; v177 SHARE-CARD + ICONS: og/twitter for home+archives, archive canonicals, favicon fallback, llms tools; v176 REAL-INSTALL AUDIT: home pagination + og:image guarantee + baseSalary; v175 CONTEXT-AWARE CTAs + schema gates; v174 BOARD RICHNESS + pretty labels; v173 REAL-INSTALL FIXES (hot rail meta keys + days-left, paginate null fatal, saved page auto-create); v172 COMMAND CENTER: My Workspace (profile → eligible jobs → application pipeline → deadline radar); v171 SVG icons + critical CSS + apply tracker; v170 phone mode

require_once get_template_directory() . '/inc/options.php';
require_once get_template_directory() . '/inc/icons.php';        // v171: pro SVG UI icons (emoji UI badulu).
require_once get_template_directory() . '/inc/critical-css.php'; // v171: above-fold inline CSS + async full CSS.
require_once get_template_directory() . '/inc/qual-filter.php';  // v72: 10th/Inter/Degree/PG filter (auto tags)
require_once get_template_directory() . '/inc/breaking.php';
require_once get_template_directory() . '/inc/ads.php';
require_once get_template_directory() . '/inc/template.php';
require_once get_template_directory() . '/inc/jobtable.php'; // v142: FreeJobAlert-style scannable table
require_once get_template_directory() . '/inc/engage.php'; // v144: freshness stamp + helpful box
require_once get_template_directory() . '/inc/remind.php'; // v151: saved-job deadline reminders
require_once get_template_directory() . '/inc/searchindex.php'; // v153: static instant search index
require_once get_template_directory() . '/inc/autolink.php'; // v154: internal link engine
require_once get_template_directory() . '/inc/personal.php'; // v156: personalised picks + calendar reminders
require_once get_template_directory() . '/inc/keyfacts.php'; // v158: key-facts strip + HowTo schema
require_once get_template_directory() . '/inc/adfill.php';  // v159: unfilled ad slot collapse
require_once get_template_directory() . '/inc/slotlab.php'; // v162: ad slot A/B variant assignment
require_once get_template_directory() . '/inc/webpush.php'; // v163: real web push (VAPID)
require_once get_template_directory() . '/inc/agecalc.php'; // v165: interactive age & eligibility calculator
require_once get_template_directory() . '/inc/audioreader.php'; // v165: Telugu text-to-speech audio reader
require_once get_template_directory() . '/inc/faqschema.php'; // v165: FAQ accordion & FAQPage schema
require_once get_template_directory() . '/inc/quicksummary.php'; // v166: 1-minute key highlights box
require_once get_template_directory() . '/inc/readerbar.php'; // v166: font size sizer & community pulse card
require_once get_template_directory() . '/inc/feecalc.php'; // v167: application fee & concession calculator
require_once get_template_directory() . '/inc/syllabustracker.php'; // v167: syllabus & study progress tracker
require_once get_template_directory() . '/inc/statuscard.php'; // v167: 1-click WhatsApp status card generator
require_once get_template_directory() . '/inc/admitcard.php'; // v168: hall ticket & admit card download helper
require_once get_template_directory() . '/inc/scorecalc.php'; // v168: exam score & negative marking calculator
require_once get_template_directory() . '/inc/resumemaker.php'; // v168: instant fresher resume & bio-data builder
require_once get_template_directory() . '/inc/sponsorhub.php'; // v169: high-RPM contextual sponsor & study partner box
require_once get_template_directory() . '/inc/videoplayer.php'; // v169: smart high-CPM video / outstream ad container
require_once get_template_directory() . '/inc/searchlog.php'; // v181: on-site search demand log (readers em adigaro → content gaps)
require_once get_template_directory() . '/inc/smartrecirc.php'; // v169: scroll-depth high-RPM smart recirculation unit
require_once get_template_directory() . '/inc/seo-bridge.php';
require_once get_template_directory() . '/inc/toc.php';
require_once get_template_directory() . '/inc/schema.php';
require_once get_template_directory() . '/inc/author-box.php';
require_once get_template_directory() . '/inc/consent.php';
require_once get_template_directory() . '/inc/ads-txt.php';
require_once get_template_directory() . '/inc/perf.php';
require_once get_template_directory() . '/inc/news-sitemap.php';
require_once get_template_directory() . '/inc/llms-txt.php';
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
require_once get_template_directory() . '/inc/upnext.php';    // v96: Up Next session-depth (real pageviews, policy-safe ad refresh)
require_once get_template_directory() . '/inc/share.php';     // v98: viral share engine (in-content share bar + native sheet)
require_once get_template_directory() . '/inc/success-stories.php'; // v117: consented TS/AP story intake CTA
require_once get_template_directory() . '/inc/student-tools.php'; // v120: compare, reminders and print/PDF utility layer
require_once get_template_directory() . '/inc/opportunities.php'; // v121: live active list, expiry-safe sections and job board
require_once get_template_directory() . '/inc/premium.php'; // v123: hero, hot jobs, scholarships, alerts, bottom nav
require_once get_template_directory() . '/inc/firstrun.php';   // v133: one-click site setup on activation
require_once get_template_directory() . '/inc/apply.php';      // v131: sticky apply bar + JobPosting schema
require_once get_template_directory() . '/inc/ogimage.php';     // v129: auto branded social card
require_once get_template_directory() . '/inc/stories.php';     // v129: quick story cards
require_once get_template_directory() . '/inc/score.php';       // v128: go-live score (AdSense/Discover readiness)
require_once get_template_directory() . '/inc/speed.php';       // v127: speculation rules, view transitions, command palette
require_once get_template_directory() . '/inc/jobmeta.php';     // v126: admin job data box
require_once get_template_directory() . '/inc/compare-page.php'; // v126: compare table page/shortcode
require_once get_template_directory() . '/inc/smart.php';   // v124: AI job match, eligibility, salary calc, calendar
require_once get_template_directory() . '/inc/workspace.php'; // v172: My Workspace command center (profile · pipeline · radar)
require_once get_template_directory() . '/inc/quiz.php';    // v123: real daily quiz
require_once get_template_directory() . '/inc/shortlinks.php'; // v122: first-party /slug redirects + click counts
require_once get_template_directory() . '/inc/livefix.php';   // v194: demo page noindex, attachment/empty-search 301 (live audit fixes)
require_once get_template_directory() . '/inc/hubs.php';      // v195: hub pages (topic clusters) + ItemList schema + autolink targets
require_once get_template_directory() . '/inc/author-profile.php'; // v195: Person/ProfilePage schema + editorial profile shortcode
require_once get_template_directory() . '/inc/calendar.php';   // v196: exam calendar + .ics export + Event schema

/**
 * "Most searched by students" — order okkate source (bot lo autoblog/breaking.py
 * MOST_USED + preview site + tests anni ide order vaadutayi).
 */
function studentup_most_used() {
	/* v173: icon values = studentup_ui_icon() keys (emoji kadu — pro SVG). */
	return array(
		array( 'slug' => 'ts-jobs', 'label' => 'TS Government Jobs', 'icon' => 'bank', 'hint' => 'TSPSC · Police · Gurukul' ),
		array( 'slug' => 'ap-jobs', 'label' => 'AP Government Jobs', 'icon' => 'bank', 'hint' => 'APPSC · Police · DSC · Secretariat' ),
		array( 'slug' => 'central-jobs', 'label' => 'Central Govt Jobs', 'icon' => 'flag', 'hint' => 'SSC · UPSC · Railways · Banks' ),
		array( 'slug' => 'hall-tickets', 'label' => 'Hall Tickets', 'icon' => 'ticket', 'hint' => 'Admit card · key instructions' ),
		array( 'slug' => 'results', 'label' => 'Results', 'icon' => 'doc', 'hint' => 'Board · competitive exams · keys' ),
		array( 'slug' => 'walkin-jobs', 'label' => 'Walk-in Interviews', 'icon' => 'walk', 'hint' => 'This week\'s drives · venues' ),
		array( 'slug' => 'software-jobs', 'label' => 'Software Jobs', 'icon' => 'laptop', 'hint' => 'IT · developer · fresher' ),
		array( 'slug' => 'success-stories', 'label' => 'Success Stories', 'icon' => 'trophy', 'hint' => 'Verified journeys · lessons' ),
		array( 'slug' => 'private-jobs', 'label' => 'Private Jobs', 'icon' => 'building', 'hint' => 'TCS · Infosys · Off-campus' ),
		array( 'slug' => 'current-affairs', 'label' => 'Current Affairs', 'icon' => 'news', 'hint' => 'Daily GK · for exams' ),
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
		'ts-jobs'         => array( 'ts-govt-jobs', 'telangana-govt-jobs', 'ts-jobs', 'ts-government-jobs' ),
		'ap-jobs'         => array( 'ap-govt-jobs', 'ap-jobs', 'ap-government-jobs' ),
		'central-jobs'    => array( 'central-govt-jobs', 'central-jobs', 'central', 'central-government-jobs' ),
		'hall-tickets'    => array( 'hall-tickets', 'hallticket', 'hall-ticket' ),
		'results'         => array( 'results' ),
		'walkin-jobs'     => array( 'walkin-jobs', 'walkin', 'walk-in-jobs' ),
		'software-jobs'   => array( 'software-jobs', 'software' ),
		'success-stories' => array( 'success-stories', 'success-story' ),
		'private-jobs'    => array( 'private-jobs', 'private' ),
		'current-affairs' => array( 'current-affairs', 'current' ),
		'scholarships'    => array( 'scholarships', 'scholarship', 'scholarships-2026' ),
		'daily-quiz'      => array( 'daily-quiz', 'quiz', 'daily-quiz-gk' ),
		'internships'     => array( 'internships', 'internship' ),
		'admissions'      => array( 'admissions', 'admission', 'online-education' ),
		'upcoming-exams'  => array( 'upcoming-exams', 'exam-calendar' ),
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
 * v178 REAL FIX (live-install proof): category archive pages alias group ni
 * merge cheyyaledu — menu link /category/ts-jobs/ ki 0 posts kanipistunnayi,
 * ee roju unna posts anni /category/ts-govt-jobs/ lo (import/bot alternate
 * slug family). Menu pradhana links → EMPTY pages. Ippudu archive query
 * alias group anni terms ni cover chestundi:
 *   /category/ts-jobs/  → ts-jobs + ts-govt-jobs + telangana-govt-jobs …
 * Rendu slug families lo ekkadaina posts unte menu link eppadu empty kavadu.
 *
 * @param WP_Query $query main query.
 * @return void
 */
function studentup_alias_archive_expand( $query ) {
	if ( is_admin() || ! $query->is_main_query() || ! $query->is_category() ) {
		return;
	}
	$slug = (string) $query->get( 'category_name' );
	if ( '' !== $slug && false !== strpos( $slug, '/' ) ) {
		$slug = trim( substr( $slug, strrpos( $slug, '/' ) + 1 ) );   // parent/child form.
	}
	if ( '' === $slug ) {
		$cat_id = (int) $query->get( 'cat' );
		if ( ! $cat_id ) {
			return;
		}
		$term = get_term( $cat_id, 'category' );
		if ( $term && ! is_wp_error( $term ) ) {
			$slug = $term->slug;
		}
	}
	if ( '' === $slug ) {
		return;
	}
	$map   = studentup_cat_aliases();
	$group = null;
	foreach ( $map as $theme_slug => $aliases ) {
		if ( $slug === $theme_slug || in_array( $slug, $aliases, true ) ) {
			$group = array_merge( array( $theme_slug ), $aliases );
			break;
		}
	}
	if ( ! $group ) {
		return;   // ee category alias group lo ledu — normal query.
	}
	$ids = array();
	foreach ( array_unique( $group ) as $s ) {
		$t = get_term_by( 'slug', $s, 'category' );
		if ( $t && ! is_wp_error( $t ) ) {
			$ids[] = (int) $t->term_id;
		}
	}
	if ( count( $ids ) > 1 ) {
		/*
		 * WP core parse_tax_query: category_name + cat + category__in anni
		 * separate AND-ed clauses ga build chestundi — original vars clear
		 * cheyakunte merge work avvadu (live install lo prove ayyindi:
		 * cat 21 AND (21,2) → 0 posts).
		 */
		$query->set( 'category__in', $ids );
		$query->set( 'cat', '' );
		$query->set( 'category_name', '' );
	}
}
add_action( 'pre_get_posts', 'studentup_alias_archive_expand', 20 );

/**
 * v178: alias group lo "primary" term — posts ekkuva unna sibling.
 *
 * Category identity (H1 · <title> · canonical · og:title) ee term tho
 * deterministic: term-ID order meeda depend cheyyadu, empty theme-slug term
 * ki posts unna sibling madya confusion vaddu.
 *
 * @param WP_Term|mixed $term queried term.
 * @return WP_Term|mixed
 */
function studentup_alias_primary_term( $term ) {
	if ( ! $term instanceof WP_Term || 'category' !== $term->taxonomy ) {
		return $term;
	}
	$map = studentup_cat_aliases();
	foreach ( $map as $theme_slug => $aliases ) {
		$group = array_merge( array( $theme_slug ), $aliases );
		if ( in_array( $term->slug, $group, true ) ) {
			$best = $term;
			foreach ( $group as $s ) {
				$t = get_term_by( 'slug', $s, 'category' );
				if ( $t && ! is_wp_error( $t ) && (int) $t->count > (int) $best->count ) {
					$best = $t;
				}
			}
			return $best;
		}
	}
	return $term;
}

/**
 * v178: category archives document <title> — primary alias term name.
 *
 * @param array $parts title parts.
 * @return array
 */
function studentup_alias_archive_title_parts( $parts ) {
	if ( is_admin() || ! ( is_category() || is_tag() ) ) {
		return $parts;
	}
	$obj = get_queried_object();
	if ( function_exists( 'studentup_alias_primary_term' ) ) {
		$obj = studentup_alias_primary_term( $obj );
	}
	if ( $obj instanceof WP_Term ) {
		$parts['title'] = $obj->name;
	}
	return $parts;
}
add_filter( 'document_title_parts', 'studentup_alias_archive_title_parts', 20 );

/**
 * Seed the categories the bot and homepage expect when the theme is activated.
 *
 * This is deliberately idempotent and alias-aware: if an existing site already
 * has `ts-jobs`, the theme does not create a second `ts-govt-jobs` archive.
 * The admin-init retry covers a theme update where WordPress does not fire the
 * activation hook again. It never creates posts or changes existing terms.
 */
function studentup_seed_categories() {
	$version = '2026-09-category-seed-1';
	if ( $version === (string) get_option( 'studentup_category_seed_version', '' ) ) {
		return;
	}
	$seed = array(
		'ts-jobs'         => array( 'TS Govt Jobs', 'ts-govt-jobs' ),
		'ap-jobs'         => array( 'AP Govt Jobs', 'ap-govt-jobs' ),
		'central-jobs'    => array( 'Central Govt Jobs', 'central-govt-jobs' ),
		'hall-tickets'    => array( 'Hall Tickets', 'hall-tickets' ),
		'results'         => array( 'Results', 'results' ),
		'walkin-jobs'     => array( 'Walkin Jobs', 'walkin-jobs' ),
		'software-jobs'   => array( 'Software Jobs', 'software-jobs' ),
		'success-stories' => array( 'Success Stories', 'success-stories' ),
		'private-jobs'    => array( 'Private Jobs', 'private-jobs' ),
		'current-affairs' => array( 'Current Affairs', 'current-affairs' ),
		'scholarships'    => array( 'Scholarships', 'scholarships' ),
		'part-time-jobs'  => array( 'Part Time Jobs', 'part-time-jobs' ),
		'outsourcing-jobs'=> array( 'Outsourcing Jobs', 'outsourcing-jobs' ),
		'internships'     => array( 'Internships', 'internships' ),
		'online-education'=> array( 'Online Education', 'online-education' ),
		'exam-tips'       => array( 'Exam Tips', 'exam-tips' ),
		'upcoming-exams'  => array( 'Upcoming Exams', 'upcoming-exams' ),
		'abroad-jobs'     => array( 'Abroad Jobs', 'abroad-jobs' ),
		'daily-quiz'      => array( 'Daily Quiz', 'daily-quiz' ),
	);
	$aliases = studentup_cat_aliases();
	$failed  = false;
	foreach ( $seed as $theme_slug => $item ) {
		$candidates = isset( $aliases[ $theme_slug ] ) ? $aliases[ $theme_slug ] : array( $item[1] );
		$found      = false;
		foreach ( $candidates as $candidate ) {
			if ( get_category_by_slug( $candidate ) ) {
				$found = true;
				break;
			}
		}
		if ( $found || get_category_by_slug( sanitize_title( $item[0] ) ) ) {
			continue;
		}
		$result = wp_insert_term( $item[0], 'category', array( 'slug' => $item[1] ) );
		if ( is_wp_error( $result ) ) {
			$failed = true;
		}
	}
	if ( ! $failed ) {
		update_option( 'studentup_category_seed_version', $version, false );
	}
}
add_action( 'after_switch_theme', 'studentup_seed_categories' );
add_action( 'admin_init', 'studentup_seed_categories' );

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
/**
 * v152: minified stylesheet URL when the build produced one.
 *
 * `tools/minify_assets.py` writes `*.min.css` next to each source. If the file
 * is missing (dev checkout, manual edit) the readable source is used, so the
 * theme can never end up with no stylesheet.
 *
 * @param string $rel Path relative to the theme root, e.g. 'assets/css/premium.css'.
 * @return string Absolute URL to the best available file.
 */
function studentup_css_url( $rel ) {
	$min = preg_replace( '/\.css$/', '.min.css', $rel );
	if ( ! defined( 'SCRIPT_DEBUG' ) || ! SCRIPT_DEBUG ) {
		if ( file_exists( get_template_directory() . '/' . $min ) ) {
			return get_template_directory_uri() . '/' . $min;
		}
	}
	return get_template_directory_uri() . '/' . $rel;
}

function studentup_assets() {
	wp_enqueue_style( 'studentup', studentup_css_url( 'style.css' ), array(), STUDENTUP_VERSION );
	// v123: premium layer — style.css tarvata load (overrides work).
	wp_enqueue_style( 'studentup-premium', studentup_css_url( 'assets/css/premium.css' ), array( 'studentup' ), STUDENTUP_VERSION );
	// v191 WORLDCLASS v2: mobile-first design layer (horizontal scan-cards on phone,
	// 3-col + right rail on laptop, 44px targets, sticky bottom nav, anchor ad slot).
	// style.css + premium.css tarvata load → overrides safe.
	wp_enqueue_style( 'studentup-worldclass', studentup_css_url( 'assets/css/worldclass.css' ), array( 'studentup-premium' ), STUDENTUP_VERSION );
	wp_enqueue_script( 'studentup', get_template_directory_uri() . '/assets/js/studentup.js', array(), STUDENTUP_VERSION, true );
	wp_enqueue_script( 'studentup-premium', get_template_directory_uri() . '/assets/js/studentup-premium.js', array( 'studentup' ), STUDENTUP_VERSION, true );
	// v127: command palette (Ctrl/⌘+K). v191.4 PERF: phone ki idi nishprayojanam
	// (keyboard ledu) — 9 KB mattrame save avutundi; desktop ki mattrame load.
	if ( ! wp_is_mobile() ) {
		wp_enqueue_script( 'studentup-cmdk', get_template_directory_uri() . '/assets/js/studentup-cmdk.js', array( 'studentup' ), STUDENTUP_VERSION, true );
	}
	if ( is_front_page() || is_home() ) {
		// v124: smart tools homepage lo mattrame — article pages fast ga untayi.
		wp_enqueue_script( 'studentup-smart', get_template_directory_uri() . '/assets/js/studentup-smart.js', array( 'studentup-premium' ), STUDENTUP_VERSION, true );
	}
	// v72: PWA install prompt (app-laga install) — pwa option ON unte mattrame
	if ( studentup_opt( 'pwa', '1' ) ) {
		wp_enqueue_script( 'studentup-pwa', get_template_directory_uri() . '/assets/js/studentup-pwa.js', array( 'studentup' ), STUDENTUP_VERSION, true );
	}
	wp_localize_script(
		'studentup',
		'STUDENTUP',
		array(
			'home'     => esc_url_raw( home_url( '/' ) ),
			'icon'     => esc_url_raw( (string) get_site_icon_url( 192 ) ),   // v123: notification icon
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
 * v170: theme JS ki `defer` — script download HTML/CSS tho parallel ga
 * start avutundi (slow phone network lo 200-400ms fast). Anni theme files
 * DOM ready tarvata matrame pani chestayi (IIFE + DOMContentLoaded), anduke
 * defer 100% safe.
 */
function studentup_defer_scripts( $tag, $handle ) {
	if ( is_admin() ) {
		return $tag;
	}
	$defer = array(
		'studentup',
		'studentup-premium',
		'studentup-cmdk',
		'studentup-smart',
		'studentup-pwa',
		'studentup-saved',
		'studentup-tools',
		'studentup-opportunities',
		'studentup-workspace',
	);
	if ( in_array( $handle, $defer, true ) && false !== strpos( $tag, ' src=' ) ) {
		$tag = str_replace( ' src=', ' defer src=', $tag );
	}
	return $tag;
}
add_filter( 'script_loader_tag', 'studentup_defer_scripts', 10, 2 );

/**
 * Remove WordPress payload that this theme does not need on ordinary public
 * pages. Keep block CSS and wp-embed when the current post really uses them;
 * this avoids breaking editors while trimming unused mobile bytes.
 */
function studentup_trim_frontend_assets() {
	if ( is_admin() ) {
		return;
	}
	$uses_embed = false;
	if ( is_singular() ) {
		$post = get_post();
		$body = $post ? (string) $post->post_content : '';
		$uses_embed = (bool) preg_match( '/\[embed(?:\s|\])|wp:embed|<iframe\b/i', $body );
	}
	if ( ! $uses_embed ) {
		wp_deregister_script( 'wp-embed' );
	}
	$uses_blocks = false;
	if ( is_singular() && function_exists( 'has_blocks' ) ) {
		$uses_blocks = has_blocks( get_post() );
	}
	if ( ! $uses_blocks ) {
		wp_dequeue_style( 'wp-block-library' );
		wp_dequeue_style( 'wp-block-library-theme' );
	}
}
add_action( 'wp_enqueue_scripts', 'studentup_trim_frontend_assets', 100 );

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
	remove_action( 'wp_head', 'wp_oembed_add_discovery_links' );
	remove_action( 'wp_head', 'wp_oembed_add_host_js' );
	remove_action( 'wp_head', 'wp_shortlink_wp_head' );
	remove_action( 'wp_head', 'rsd_link' );
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
