<?php
/**
 * v133: First-run setup.
 *
 * Goal: upload the zip, activate, and the site is already shaped the way the
 * theme (and the publishing bot) expects — categories, menus, policy pages,
 * permalinks and reading settings. Nothing destructive: existing categories,
 * pages and menus are reused, never overwritten or deleted.
 *
 * The setup runs once on activation and can be re-run any time from
 * Appearance -> StudentUp Setup.
 *
 * @package StudentUp
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Categories the theme templates link to.
 *
 * @return array List of slug => array( name, description ).
 */
function studentup_setup_categories() {
	return array(
		'ts-jobs'         => array( 'Telangana Jobs', 'TSPSC, TS police, TS teacher and other Telangana government jobs.' ),
		'ap-jobs'         => array( 'Andhra Pradesh Jobs', 'APPSC, AP police, AP teacher and other Andhra Pradesh government jobs.' ),
		'central-jobs'    => array( 'Central Govt Jobs', 'SSC, UPSC, Railway, Bank, Defence and other central government jobs.' ),
		'private-jobs'    => array( 'Private Jobs', 'Verified private sector openings for students and freshers.' ),
		'walkin-jobs'     => array( 'Walk-in Jobs', 'Direct walk-in interviews with date, venue and documents.' ),
		'software-jobs'   => array( 'IT / Software Jobs', 'Fresher and experienced IT openings in Hyderabad and beyond.' ),
		'results'         => array( 'Results', 'Exam results with direct download links.' ),
		'hall-ticket'     => array( 'Hall Tickets', 'Admit cards and hall ticket download links.' ),
		'admissions'      => array( 'Admissions', 'Entrance notifications, counselling and admission dates.' ),
		'scholarships'    => array( 'Scholarships', 'Central, state and private scholarships with last dates.' ),
		'internships'     => array( 'Internships', 'Stipend, remote and college internships.' ),
		'current-affairs' => array( 'Current Affairs', 'Daily current affairs for competitive exams.' ),
		'success-stories' => array( 'Success Stories', 'Real student journeys and preparation strategies.' ),
	);
}

/**
 * Pages the theme and AdSense review both expect.
 *
 * @return array List of slug => title.
 */
function studentup_setup_pages() {
return array(
	'about'            => 'About Us',
	'contact'          => 'Contact Us',
	'privacy'          => 'Privacy Policy',
	'disclaimer'       => 'Disclaimer',
	'terms'            => 'Terms and Conditions',
	'editorial-policy' => 'Editorial Policy',
	'workspace'        => 'My Workspace',
	'saved'            => 'Saved Posts',
	// v176: Compare Jobs page — page-compare.php template + shortcode ekkada
	// attach avtundo ani deal chesi, /compare/ URL automatic ga ready avutundi.
	'compare'          => 'Compare Jobs',
	// v196: deadline calendar · transparent offline-service page · corrections log.
	'exam-calendar'    => 'Exam & Application Calendar',
	'internet-center'  => 'Students Internet Center',
	'corrections'      => 'Corrections & Updates',
);
}

/**
 * Starter body copy for an auto-created page.
 *
 * @param string $slug  Page slug.
 * @param string $title Page title.
 * @return string Page content.
 */
function studentup_setup_page_body( $slug, $title ) {
	$site = get_bloginfo( 'name' );
	$mail = get_option( 'admin_email' );
	// v194: AdSense/News reviewers read these pages literally. The old auto note
	// ("theme was activated ... replace before applying to any ad network") made
	// every policy page look like an untouched template. Slug-wise copy is real,
	// so the note stays blank; workspace/saved/compare have their own builders.
	$base = '';

	$map = array(
		'about'            => '<p>' . esc_html( $site ) . ' publishes government job notifications, results, hall tickets, ' .
			'admissions and scholarship updates for students in Telangana and Andhra Pradesh. Every update links back to the ' .
			'official notification so readers can verify it themselves.</p>',
		'contact'          => '<p>Questions, corrections or partnership requests: <a href="mailto:' . esc_attr( $mail ) . '">' .
			esc_html( $mail ) . '</a>. We reply to corrections first.</p>',
		'privacy'          => '<p>We explain here what data this site collects, how cookies and browser storage are used, and ' .
			'how advertising partners work. Third-party vendors, including Google, may use cookies to serve ads based on a ' .
			'user\'s prior visits to this or other websites. Users can opt out of personalised advertising in Google Ads ' .
			'Settings or at aboutads.info/choices.</p>',
		'disclaimer'       => '<p>All notifications are summarised from official sources. Before applying, always confirm the ' .
			'details on the official website of the recruiting organisation. We are not a government body.</p>',
		'terms'            => '<p>By using this website you agree to use the information for personal, non-commercial reference. ' .
			'Content may not be republished without permission.</p>',
		'editorial-policy' => '<p>Every post names its official source, carries a last-updated date and is corrected publicly ' .
			'when a mistake is found. We never publish paid content as editorial.</p>',
	);

	$body = isset( $map[ $slug ] ) ? $map[ $slug ] : '<p>' . esc_html( $title ) . '</p>';
	$svc  = studentup_setup_service_block();
	if ( '' !== $svc && in_array( $slug, array( 'about', 'contact', 'privacy', 'disclaimer', 'terms', 'editorial-policy' ), true ) ) {
		$body .= "\n" . $svc;
	}
	return $base ? $body . "\n\n" . $base : $body;
}

/**
 * v194: Students Internet Center disclosure — separated from the publisher.
 *
 * Enduku: live site lo ee offline paid service block e page meeda padindi
 * (About/Privacy kuda), kaani "StudentUp website content" ki "paid form
 * filling service" ki madhya distinction ledu. AdSense reviewer ki ee
 * separation kaavali — so ee block 4 sangati clear ga cheptundi:
 *   1. Service website content kaadu, separate/optional.
 *   2. Fee gurinchi, documents WhatsApp lo — service ki matrame.
 *   3. StudentUp content chadavatam/alert ravadam ki em fee ledu, documents ledu.
 *   4. Anni details official notification ne follow avutayi.
 *
 * @return string HTML block (khali = WhatsApp number set cheyyaledu).
 */
function studentup_setup_service_block() {
	$raw = (string) studentup_opt( 'social_whatsapp', '9182739312' );
	$wa  = function_exists( 'studentup_wa_number' ) ? studentup_wa_number( $raw ) : preg_replace( '/\D/', '', $raw );
	if ( '' === $wa ) {
		return '';
	}
	return '<h2>' . esc_html__( 'Students Internet Center (separate offline service)', 'studentup' ) . '</h2>' .
		'<p>' . esc_html__( 'Outside this website we run a small offline Students Internet Center that helps students fill government application forms. This is optional: every job, result, hall ticket and scholarship update on this website is free to read and you never need this service to use the site.', 'studentup' ) . '</p>' .
		'<p>' . esc_html__( 'Only for that offline service, documents are shared on WhatsApp at', 'studentup' ) . ' <a href="https://wa.me/' . esc_attr( $wa ) . '" rel="nofollow noopener" target="_blank">+' . esc_html( $wa ) . '</a>. ' .
		esc_html__( 'Fees, documents and eligibility for any government application are always as per the official notification.', 'studentup' ) . '</p>';
}

/**
 * v172: Workspace page body — functional page (policy $base note vaddu).
 * Shortcode ye content — admin edit cheyyalsina emi ledu.
 *
 * @return string
 */
function studentup_setup_workspace_body() {
	return '<p>Set your qualification, age and state once — eligible jobs, deadlines and your application pipeline appear here automatically. Everything is stored in your browser only.</p>' . "\n\n" . '[studentup_workspace]';
}

/**
 * v173: Saved page body — [studentup_saved] grid (localStorage powered).
 *
 * @return string
 */
function studentup_setup_saved_body() {
	return '<p>Everything you save with the Save button is kept in this browser — no account needed. Your application status (Applied / Interview / Result) is tracked here too.</p>' . "\n\n" . '[studentup_saved]';
}

/**
 * v194: repair a site that an OLDER theme version set up.
 *
 * Live audit (studentup.in) lo kanipinchina 3 problems ni okka click tho fix
 * chestundi — read-only checks tho, delete cheyyadu:
 *   1. "This page was created automatically..." template note (Google/AdSense
 *      reviewer ee note chusi "template site" ani decide chestadu).
 *   2. Students Internet Center disclosure ledu → publisher vs paid service
 *      separation clear ga cheyyali.
 *   3. Duplicate policy pages (/privacy/ vs /privacy-policy/ vs -2,
 *      /terms/ vs /terms-conditions/, /contact/ vs /contact-us/) → thin
 *      duplicate content. Canonical page unte, duplicate ni DRAFT loki
 *      pampistundi (trash kaadu — malli publish cheyyachu) + redirect note.
 *
 * @return array Human readable report lines.
 */
function studentup_repair_pages_run() {
	$report = array();
	$stale  = 'This page was created automatically when the StudentUp theme was activated.';
	$stale2 = 'Please replace this text with your own details before applying to any ad network.';

	// 1 + 2: stale note teyyadam, missing di service block add cheyyadam.
	$fixed = 0;
	$svc   = studentup_setup_service_block();
	$pages = get_posts(
		array(
			'post_type'      => 'page',
			'post_status'    => array( 'publish', 'draft' ),
			'posts_per_page' => 200,
			'fields'         => 'ids',
		)
	);
	foreach ( $pages as $pid ) {
		$content = (string) get_post_field( 'post_content', $pid );
		$before  = $content;
		if ( false !== strpos( $content, $stale ) ) {
			$content = str_replace( array( '<p>' . $stale . ' ' . $stale2 . '</p>', $stale, $stale2, '(undefined)' ), '', $content );
			$content = trim( preg_replace( "/\n{3,}/", "\n\n", $content ) );
		}
		$slug = (string) get_post_field( 'post_name', $pid );
		if ( '' !== $svc && ! in_array( $slug, array( 'workspace', 'saved', 'compare' ), true )
			&& false === strpos( $content, 'Students Internet Center' )
			&& in_array( $slug, array( 'about', 'contact', 'contact-us', 'privacy', 'privacy-policy', 'privacy-policy-2', 'disclaimer', 'terms', 'terms-conditions', 'editorial-policy' ), true ) ) {
			$content .= "\n" . $svc;
		}
		if ( $content !== $before ) {
			wp_update_post( array( 'ID' => (int) $pid, 'post_content' => $content ) );
			++$fixed;
		}
	}
	$report[] = sprintf( 'Policy/About pages cleaned: %d updated (template note removed, service disclosure added).', $fixed );

	// 3: duplicate policy pages → draft (canonical version publish lo untundi).
	$dupes = array(
		'privacy-policy'   => 'privacy',
		'privacy-policy-2' => 'privacy',
		'terms-conditions' => 'terms',
		'contact-us'       => 'contact',
	);
	$drafted = 0;
	foreach ( $dupes as $dup => $canon ) {
		$d = get_page_by_path( $dup );
		$c = get_page_by_path( $canon );
		if ( $d instanceof WP_Post && $c instanceof WP_Post && 'publish' === $d->post_status
			&& 'publish' === $c->post_status && strlen( trim( (string) $c->post_content ) ) > 40 ) {
			wp_update_post( array( 'ID' => (int) $d->ID, 'post_status' => 'draft' ) );
			$report[] = sprintf( 'Duplicate page /%s/ → draft (canonical /%s/). Redirect 301 pettandi: Rank Math → Redirections.', $dup, $canon );
			++$drafted;
		}
	}
	if ( 0 === $drafted ) {
		$report[] = 'Duplicate policy pages: emi ledu (already clean).';
	}

	// 4: compare page ki template assign (shortcode unna, layout onte).
	$cmp = get_page_by_path( 'compare' );
	if ( $cmp instanceof WP_Post && 'page-compare.php' !== (string) get_post_meta( $cmp->ID, '_wp_page_template', true ) ) {
		update_post_meta( $cmp->ID, '_wp_page_template', 'page-compare.php' );
		$report[] = 'Compare Jobs page template set (page-compare.php).';
	}

	$report[] = 'Next: demo/junk Gutenberg blocks (placeholder text) + internal checklist pages ni delete cheyyandi — avi sitemap lo unte AdSense review fail avutundi.';
	return $report;
}

/**
 * v196: page content per slug (workspace · saved · compare · calendar · IC · corrections).
 *
 * @param string $slug  Page slug.
 * @param string $title Page title.
 * @return string
 */
function studentup_setup_page_content_for( $slug, $title ) {
	if ( 'workspace' === $slug && function_exists( 'studentup_setup_workspace_body' ) ) {
		return studentup_setup_workspace_body();
	}
	if ( 'saved' === $slug && function_exists( 'studentup_setup_saved_body' ) ) {
		return studentup_setup_saved_body();
	}
	$shortcodes = array(
		'compare'       => '[studentup_compare limit="12"]',
		'exam-calendar' => '[studentup_calendar]',
	);
	if ( isset( $shortcodes[ $slug ] ) ) {
		return $shortcodes[ $slug ];
	}
	if ( 'internet-center' === $slug ) {
		return studentup_setup_internet_center_body();
	}
	if ( 'corrections' === $slug ) {
		return studentup_setup_corrections_body();
	}
	return studentup_setup_page_body( $slug, $title );
}

/**
 * v196: template assignment for pages that need a dedicated template file.
 *
 * @param int    $id   Page ID.
 * @param string $slug Page slug.
 * @return void
 */
function studentup_setup_assign_template( $id, $slug ) {
	$map = array(
		'exam-calendar'   => 'page-exam-calendar.php',
		'internet-center' => 'page-internet-center.php',
		'corrections'     => 'page-corrections.php',
	);
	if ( isset( $map[ $slug ] ) ) {
		update_post_meta( (int) $id, '_wp_page_template', $map[ $slug ] );
	}
}

/**
 * v196: Students Internet Center page body (short intro; the template renders
 * the price list, rules and contact block).
 *
 * @return string
 */
function studentup_setup_internet_center_body() {
	return '<p>' . esc_html__( 'We run a small offline Students Internet Center that helps students fill government application forms. This page shows the exact price list, what is included, what we never do and how to cancel - so you can decide before you pay anything.', 'studentup' ) . '</p>';
}

/**
 * v196: corrections page body (the template lists the corrected posts).
 *
 * @return string
 */
function studentup_setup_corrections_body() {
	return '<p>' . esc_html__( 'StudentUp publishes a correction log. Every fixed mistake stays visible with its date instead of being silently edited.', 'studentup' ) . '</p>';
}

/**
 * v195: hub page body — [studentup_hub] shortcode + honest intro.
 *
 * @param string $slug Hub slug.
 * @return string
 */
function studentup_setup_hub_body( $slug ) {
	$plan = function_exists( 'studentup_hub_plan' ) ? studentup_hub_plan() : array();
	if ( ! isset( $plan[ $slug ] ) ) {
		return '<p>' . esc_html__( 'New notifications are added every day.', 'studentup' ) . '</p>';
	}
	$info = $plan[ $slug ];
	$cats = implode( ',', (array) $info[1] );
	return '<p>' . esc_html( $info[2] ) . '</p>' . "\n\n"
		. '[studentup_hub cats="' . esc_attr( $cats ) . '"]' . "\n\n"
		. '<p><em>' . esc_html__( 'Every entry links back to the official notification — always confirm the details there before applying.', 'studentup' ) . '</em></p>';
}

/**
 * v195: editorial team page body — real person + verification process.
 *
 * @return string
 */
function studentup_setup_editorial_body() {
	return '<p>' . esc_html__( 'StudentUp publishes government job, result, hall ticket and scholarship updates for Telangana and Andhra Pradesh students. This page names who writes and verifies them.', 'studentup' ) . '</p>'
		. "\n\n[studentup_author_profile]\n\n"
		. '<h3>' . esc_html__( 'Corrections', 'studentup' ) . '</h3>'
		. '<p>' . esc_html__( 'Found a mistake? Write to the email above with the page link. Verified corrections are published with the updated date, and the post keeps a correction note.', 'studentup' ) . '</p>';
}

/**
 * Menu blueprint: header/mobile menu items in student-first order.
 *
 * @return array Items with type + key + label.
 */
function studentup_setup_menu_plan() {
	return array(
		array( 'home', '', 'Home' ),
		array( 'cat', 'ts-jobs', 'Telangana Jobs' ),
		array( 'cat', 'ap-jobs', 'AP Jobs' ),
		array( 'cat', 'central-jobs', 'Central Jobs' ),
		array( 'cat', 'results', 'Results' ),
		array( 'cat', 'hall-ticket', 'Hall Tickets' ),
		array( 'cat', 'scholarships', 'Scholarships' ),
		array( 'cat', 'admissions', 'Admissions' ),
		array( 'cat', 'internships', 'Internships' ),
		array( 'cat', 'current-affairs', 'Current Affairs' ),
	);
}

/**
 * Create the categories, pages, menus and settings the theme expects.
 *
 * @return array Human readable report lines.
 */
function studentup_run_first_setup() {
	$report = array();

	// 1. Categories.
	$made = 0;
	foreach ( studentup_setup_categories() as $slug => $info ) {
		if ( term_exists( $slug, 'category' ) ) {
			continue;
		}
		$res = wp_insert_term(
			$info[0],
			'category',
			array(
				'slug'        => $slug,
				'description' => $info[1],
			)
		);
		if ( ! is_wp_error( $res ) ) {
			++$made;
		}
	}
	$report[] = sprintf( 'Categories ready (%d new).', $made );

	// 2. Pages.
	$pages = array();
	$made  = 0;
	foreach ( studentup_setup_pages() as $slug => $title ) {
		$existing = get_page_by_path( $slug );
		if ( $existing instanceof WP_Post ) {
			$pages[ $slug ] = (int) $existing->ID;
			studentup_setup_assign_template( $existing->ID, $slug );   // v196: idempotent
			continue;
		}
		$id = wp_insert_post(
			array(
				'post_title'   => $title,
				'post_name'    => $slug,
				'post_content' => studentup_setup_page_content_for( $slug, $title ),
				'post_status'  => 'publish',
				'post_type'    => 'page',
			)
		);
		if ( $id && ! is_wp_error( $id ) ) {
			$pages[ $slug ] = (int) $id;
			studentup_setup_assign_template( $id, $slug );
			++$made;
		}
	}
	$report[] = sprintf( 'Policy pages ready (%d new).', $made );

	// 2b. v195: hub pages + editorial team page (topic clusters + E-E-A-T).
	$hubs = 0;
	if ( function_exists( 'studentup_hub_plan' ) ) {
		foreach ( studentup_hub_plan() as $hslug => $hinfo ) {
			if ( get_page_by_path( $hslug ) instanceof WP_Post ) {
				continue;
			}
			$hid = wp_insert_post(
				array(
					'post_title'   => $hinfo[0],
					'post_name'    => $hslug,
					'post_content' => studentup_setup_hub_body( $hslug ),
					'post_status'  => 'publish',
					'post_type'    => 'page',
				)
			);
			if ( $hid && ! is_wp_error( $hid ) ) {
				$pages[ $hslug ] = (int) $hid;
				++$hubs;
			}
		}
	}
	if ( ! ( get_page_by_path( 'editorial-team' ) instanceof WP_Post ) ) {
		$eid = wp_insert_post(
			array(
				'post_title'   => 'Editorial Team & Fact-checking',
				'post_name'    => 'editorial-team',
				'post_content' => studentup_setup_editorial_body(),
				'post_status'  => 'publish',
				'post_type'    => 'page',
			)
		);
		if ( $eid && ! is_wp_error( $eid ) ) {
			$pages['editorial-team'] = (int) $eid;
		}
	}
	$report[] = sprintf( 'Hub pages ready (%d new) + editorial team page.', $hubs );

	// 3. Header + mobile menu.
	$menu_name = 'StudentUp Main';
	$menu      = wp_get_nav_menu_object( $menu_name );
	if ( ! $menu ) {
		$menu_id = wp_create_nav_menu( $menu_name );
	} else {
		$menu_id = (int) $menu->term_id;
	}
	$added = 0;
	if ( $menu_id && ! is_wp_error( $menu_id ) ) {
		$have = array();
		foreach ( (array) wp_get_nav_menu_items( $menu_id ) as $item ) {
			$have[] = strtolower( $item->title );
		}
		foreach ( studentup_setup_menu_plan() as $plan ) {
			list( $type, $key, $label ) = $plan;
			if ( in_array( strtolower( $label ), $have, true ) ) {
				continue;
			}
			if ( 'home' === $type ) {
				$args = array(
					'menu-item-title'  => $label,
					'menu-item-url'    => home_url( '/' ),
					'menu-item-status' => 'publish',
					'menu-item-type'   => 'custom',
				);
			} else {
				$term = get_term_by( 'slug', $key, 'category' );
				if ( ! $term ) {
					continue;
				}
				$args = array(
					'menu-item-title'     => $label,
					'menu-item-object'    => 'category',
					'menu-item-object-id' => (int) $term->term_id,
					'menu-item-type'      => 'taxonomy',
					'menu-item-status'    => 'publish',
				);
			}
			if ( wp_update_nav_menu_item( $menu_id, 0, $args ) ) {
				++$added;
			}
		}
	}

	// 4. Footer menu with the policy pages.
	$foot_name = 'StudentUp Footer';
	$foot      = wp_get_nav_menu_object( $foot_name );
	$foot_id   = $foot ? (int) $foot->term_id : wp_create_nav_menu( $foot_name );
	if ( $foot_id && ! is_wp_error( $foot_id ) ) {
		$have = array();
		foreach ( (array) wp_get_nav_menu_items( $foot_id ) as $item ) {
			$have[] = strtolower( $item->title );
		}
		$foot_items = studentup_setup_pages();
		if ( function_exists( 'studentup_hub_plan' ) ) {
			foreach ( studentup_hub_plan() as $hslug => $hinfo ) {
				$foot_items[ $hslug ] = $hinfo[0];
			}
		}
		$foot_items['editorial-team'] = 'Editorial Team & Fact-checking';
		foreach ( $foot_items as $slug => $title ) {
			if ( ! isset( $pages[ $slug ] ) || in_array( strtolower( $title ), $have, true ) ) {
				continue;
			}
			wp_update_nav_menu_item(
				$foot_id,
				0,
				array(
					'menu-item-title'     => $title,
					'menu-item-object'    => 'page',
					'menu-item-object-id' => $pages[ $slug ],
					'menu-item-type'      => 'post_type',
					'menu-item-status'    => 'publish',
				)
			);
		}
	}
	$report[] = sprintf( 'Menus built (%d links added).', $added );

	// 5. Menu locations.
	$locations = (array) get_theme_mod( 'nav_menu_locations', array() );
	if ( $menu_id && ! is_wp_error( $menu_id ) ) {
		$locations['primary'] = (int) $menu_id;
		$locations['mobile']  = (int) $menu_id;
	}
	if ( $foot_id && ! is_wp_error( $foot_id ) ) {
		$locations['footer'] = (int) $foot_id;
	}
	set_theme_mod( 'nav_menu_locations', $locations );
	$report[] = 'Menu locations assigned (header, mobile, footer).';

	// 6. Reading + permalink settings that the templates and SEO rely on.
	if ( (int) get_option( 'posts_per_page' ) > 12 ) {
		update_option( 'posts_per_page', 10 );
	}
	$structure = (string) get_option( 'permalink_structure' );
	if ( '' === $structure || false === strpos( $structure, '%postname%' ) ) {
		update_option( 'permalink_structure', '/%postname%/' );
	}
	if ( '' !== (string) get_option( 'privacy_policy_page_id' ) && isset( $pages['privacy'] ) ) {
		update_option( 'wp_page_for_privacy_policy', $pages['privacy'] );
	}
	update_option( 'timezone_string', get_option( 'timezone_string' ) ? get_option( 'timezone_string' ) : 'Asia/Kolkata' );
	flush_rewrite_rules();
	$report[] = 'Permalinks, page size and timezone checked.';

	update_option( 'su_firstrun_stamp', gmdate( 'c' ) );
	update_option( 'su_firstrun_version', STUDENTUP_VERSION );   // v176: version-aware.
	return $report;
}

/**
 * Run once when the theme is activated.
 *
 * @return void
 */
function studentup_first_setup_on_activate() {
	/*
	 * v176 REAL FIX: okasari set ayite eppudu malli run cheyyaledu — theme
	 * update chesina kuda kotha pages (v176: Compare Jobs) purathana site lo
	 * create avvaledu. Version marite malli run (idempotent: existing content
	 * ni touch cheyyadu, missing vitini matrame add chestundi).
	 */
	if ( get_option( 'su_firstrun_stamp' ) && STUDENTUP_VERSION === (string) get_option( 'su_firstrun_version' ) ) {
		return;
	}
	studentup_run_first_setup();
}
add_action( 'after_switch_theme', 'studentup_first_setup_on_activate', 20 );

/**
 * Appearance -> StudentUp Setup page (re-runnable).
 *
 * @return void
 */
function studentup_setup_menu_page() {
	add_theme_page(
		'StudentUp Setup',
		'StudentUp Setup',
		'manage_options',
		'studentup-setup',
		'studentup_setup_page_render'
	);
}
add_action( 'admin_menu', 'studentup_setup_menu_page' );

/**
 * Render the setup screen.
 *
 * @return void
 */
function studentup_setup_page_render() {
	if ( ! current_user_can( 'manage_options' ) ) {
		return;
	}
	$lines = array();
	if ( isset( $_POST['studentup_setup_run'] ) &&
		check_admin_referer( 'studentup_setup', 'studentup_setup_nonce' ) ) {
		$lines = studentup_run_first_setup();
	}
	if ( isset( $_POST['studentup_repair_run'] ) &&
		check_admin_referer( 'studentup_setup', 'studentup_setup_nonce' ) ) {
		$lines = studentup_repair_pages_run();
	}
	$done = (string) get_option( 'su_firstrun_stamp', '' );
	?>
	<div class="wrap">
		<h1>StudentUp Setup</h1>
		<p>One click builds the categories, policy pages, header/mobile/footer menus and the
			reading settings this theme expects. It never deletes or overwrites anything that
			already exists, so it is safe to run again after adding content.</p>
		<?php if ( '' !== $done ) : ?>
			<p><strong>Last run:</strong> <?php echo esc_html( $done ); ?></p>
		<?php endif; ?>
		<?php if ( ! empty( $lines ) ) : ?>
			<div class="notice notice-success"><ul style="margin:8px 0 8px 18px;list-style:disc">
				<?php foreach ( $lines as $line ) : ?>
					<li><?php echo esc_html( $line ); ?></li>
				<?php endforeach; ?>
			</ul></div>
		<?php endif; ?>
		<form method="post">
			<?php wp_nonce_field( 'studentup_setup', 'studentup_setup_nonce' ); ?>
			<p><button type="submit" name="studentup_setup_run" value="1" class="button button-primary">
				Run setup now</button></p>
		</form>
		<h2>Repair live pages (older sites)</h2>
		<p>Already-running site ki ee button okkasari kottandi: policy/about pages nunchi
			&ldquo;created automatically&rdquo; template note teestundi, Students Internet Center
			disclosure add chestundi, duplicate privacy/terms/contact pages ni draft loki
			pampistundi. Emi delete cheyyadu.</p>
		<form method="post">
			<?php wp_nonce_field( 'studentup_setup', 'studentup_setup_nonce' ); ?>
			<p><button type="submit" name="studentup_repair_run" value="1" class="button">
				Repair live pages</button></p>
		</form>
		<h2>After setup</h2>
		<ol>
			<li>Appearance &rarr; StudentUp: social links, AdSense IDs, homepage sections.</li>
			<li>Appearance &rarr; StudentUp Score: go-live readiness for AdSense and Discover.</li>
			<li>Edit any job post and fill the Job data box (last date, apply URL, qualification)
				so the apply bar, eligibility checker and Google Jobs schema switch on.</li>
		</ol>
	</div>
	<?php
}

/**
 * Nudge the owner once, right after activation.
 *
 * @return void
 */
function studentup_setup_notice() {
	if ( ! current_user_can( 'manage_options' ) || ( get_option( 'su_firstrun_stamp' ) && STUDENTUP_VERSION === (string) get_option( 'su_firstrun_version' ) ) ) {
		return;
	}
	$url = esc_url( admin_url( 'themes.php?page=studentup-setup' ) );
	echo '<div class="notice notice-info"><p><strong>StudentUp:</strong> finish the one-click setup ' .
		'(categories, menus, policy pages) &mdash; <a href="' . esc_url( $url ) . '">open setup</a>.</p></div>';
}
add_action( 'admin_notices', 'studentup_setup_notice' );
