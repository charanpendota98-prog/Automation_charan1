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
	$base = '<p>This page was created automatically when the StudentUp theme was activated. ' .
		'Please replace this text with your own details before applying to any ad network.</p>';

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
	return $body . "\n" . $base;
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
			continue;
		}
		$id = wp_insert_post(
			array(
				'post_title'   => $title,
				'post_name'    => $slug,
				'post_content' => ( 'workspace' === $slug && function_exists( 'studentup_setup_workspace_body' ) )
					? studentup_setup_workspace_body()
					: studentup_setup_page_body( $slug, $title ),
				'post_status'  => 'publish',
				'post_type'    => 'page',
			)
		);
		if ( $id && ! is_wp_error( $id ) ) {
			$pages[ $slug ] = (int) $id;
			++$made;
		}
	}
	$report[] = sprintf( 'Policy pages ready (%d new).', $made );

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
		foreach ( studentup_setup_pages() as $slug => $title ) {
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
	return $report;
}

/**
 * Run once when the theme is activated.
 *
 * @return void
 */
function studentup_first_setup_on_activate() {
	if ( get_option( 'su_firstrun_stamp' ) ) {
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
	if ( ! current_user_can( 'manage_options' ) || get_option( 'su_firstrun_stamp' ) ) {
		return;
	}
	$url = esc_url( admin_url( 'themes.php?page=studentup-setup' ) );
	echo '<div class="notice notice-info"><p><strong>StudentUp:</strong> finish the one-click setup ' .
		'(categories, menus, policy pages) &mdash; <a href="' . esc_url( $url ) . '">open setup</a>.</p></div>';
}
add_action( 'admin_notices', 'studentup_setup_notice' );
