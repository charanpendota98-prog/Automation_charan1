<?php
/**
 * v123 PREMIUM — hero, hot jobs, scholarships strip, daily quiz, alerts centre,
 * mobile bottom navigation.
 *
 * Endukante (why): home page ni "Tesla of job websites" laga — colorful,
 * click-chese-vidham ga, mobile-first ga marchadaniki. Prathi block option tho
 * on/off cheyyachu (StudentUp Options lo kotha keys, default ON).
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Hero quick-action tiles (Latest Govt Jobs · Scholarships · Results · Hall Tickets).
 *
 * @return array<int,array<string,string>>
 */
function studentup_hero_actions() {
	$out  = array();
	// v201: demo (preview/worldclass) chip set ne — Telugu labels + same order.
	// Slug lekapote filter board (#jobs) ki velthundi — chip eppudu dead kaadu.
	$defs = array(
		array( 'label' => 'Breaking News', 'icn' => 'bolt', 'tone' => 'breaking', 'url' => '/#jobs' ),
		array( 'label' => 'Latest Jobs', 'icn' => 'bolt', 'tone' => '', 'slug' => 'ts-jobs' ),
		array( 'label' => 'TSPSC / Telangana', 'icn' => 'bank', 'tone' => '', 'slug' => 'ts-jobs' ),
		array( 'label' => 'APPSC / Andhra Pradesh', 'icn' => 'bank', 'tone' => '', 'slug' => 'ap-jobs' ),
		array( 'label' => 'Central Govt', 'icn' => 'flag', 'tone' => '', 'slug' => 'central-jobs' ),
		array( 'label' => 'Police / Defence', 'icn' => 'shield', 'tone' => '', 'slug' => 'police-jobs' ),
		array( 'label' => '10th / Inter', 'icn' => 'school', 'tone' => '', 'slug' => '10th-inter' ),
		array( 'label' => 'Results & Keys', 'icn' => 'doc', 'tone' => '', 'slug' => 'results' ),
	);
	foreach ( $defs as $d ) {
		$url = '';
		if ( ! empty( $d['url'] ) ) {
			$url = home_url( $d['url'] );
		} elseif ( ! empty( $d['slug'] ) ) {
			$term = studentup_used_term( $d['slug'] );
			if ( $term ) {
				$url = get_category_link( $term );
			}
		}
		if ( '' === $url ) {
			$url = home_url( '/#jobs' );
		}
		unset( $d['slug'] );
		$d['url'] = $url;
		$out[]    = $d;
	}
	return $out;
}

/**
 * Premium hero — brand line, live search, quick actions, trust counters.
 */
function studentup_hero_premium() {
	if ( ! studentup_opt( 'hero_premium', '1' ) ) {
		return;
	}
	?>
	<section class="su-hero" aria-label="StudentUp search and quick links">
		<div class="wrap su-hero-in">
			<?php /* v201: demo (preview/worldclass) hero ne — visible H1 (page lo okkate H1). */ ?>
			<h1 class="su-hero-title"><?php esc_html_e( 'Government Jobs, Results & Notifications', 'studentup' ); ?></h1>

			<div class="su-search-wrap">
				<form class="su-hero-search" role="search" method="get" action="<?php echo esc_url( home_url( '/' ) ); ?>">
					<span class="su-hs-ico" aria-hidden="true"><?php echo studentup_ui_icon( 'search', 17 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?></span>
					<label class="screen-reader-text" for="su-q"><?php esc_html_e( 'Search StudentUp', 'studentup' ); ?></label>
					<input id="su-q" type="search" name="s" value="<?php echo esc_attr( get_search_query() ); ?>" autocomplete="off"
						placeholder="<?php esc_attr_e( 'Search TSPSC, APPSC, SSC, Hall Tickets, Results, Scholarships…', 'studentup' ); ?>">
					<kbd class="su-kbd" title="<?php esc_attr_e( 'Press / to search', 'studentup' ); ?>">/</kbd>
					<button type="submit"><?php esc_html_e( 'Search', 'studentup' ); ?></button>
				</form>
			</div>

			<div class="su-hero-acts">
				<?php foreach ( studentup_hero_actions() as $a ) : ?>
					<?php $su_cls = 'su-hact' . ( $a['tone'] ? ( 'breaking' === $a['tone'] ? ' su-hact--breaking' : ' su-t-' . $a['tone'] ) : '' ); ?>
					<a class="<?php echo esc_attr( $su_cls ); ?>" href="<?php echo esc_url( $a['url'] ); ?>">
						<span aria-hidden="true"><?php echo studentup_ui_icon( esc_html( $a['icn'] ), 15 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?></span><?php echo esc_html( $a['label'] ); ?>
					</a>
				<?php endforeach; ?>
				<?php if ( function_exists( 'studentup_workspace_url' ) && studentup_workspace_url() ) : ?>
					<a class="su-hact su-t-ink" href="<?php echo esc_url( studentup_workspace_url() ); ?>">
						<span aria-hidden="true"><?php echo studentup_ui_icon( 'person', 15 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?></span>My Workspace
					</a>
				<?php endif; ?>
			</div>

			<?php
			if ( function_exists( 'studentup_trending_today' ) ) {
				studentup_trending_today();   // v124: Trending Today strip
			}
			if ( function_exists( 'studentup_state_switch' ) ) {
				studentup_state_switch();     // v124: state-first dynamic homepage
			}
			?>
		</div>
	</section>
	<?php
}

/**
 * TOP HOT JOBS TODAY — Netflix style cards (image + last date + apply).
 *
 * @param int $limit cards.
 */
function studentup_hot_jobs( $limit = 10 ) {
	if ( ! studentup_opt( 'hot_jobs', '1' ) ) {
		return;
	}
	$cats = array();
	/*
	 * v176 REAL FIX: purathana list lo software/internship/walkin boards levu —
	 * software jobs eppudu "Top 10 hot jobs" rail lo raaledu. Anni job boards
	 * cover chestunna alias list (ts/ap/central/private/software/walkin/intern).
	 */
	foreach ( array( 'ts-jobs', 'ap-jobs', 'central-jobs', 'private-jobs', 'software-jobs', 'walkin-jobs', 'internships' ) as $s ) {
		$t = studentup_used_term( $s );
		if ( $t ) {
			$cats[] = (int) $t->term_id;
		}
	}
	$q = new WP_Query(
		array(
			'posts_per_page'      => (int) $limit * 3,   // v176: signal-gate skip aina tarvata kuda 10 cards ravali.
			'ignore_sticky_posts' => true,
			'no_found_rows'       => true,
			'category__in'        => $cats ? $cats : array(),
		)
	);
	if ( ! $q->have_posts() ) {
		wp_reset_postdata();
		return;
	}
	?>
	<section class="su-hot" aria-label="Top hot jobs today">
		<div class="su-hot-head">
			<h2><?php echo studentup_ui_icon( 'bolt', 18 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> Top <?php echo esc_html( (int) $limit ); ?> hot jobs today</h2>
			<a href="<?php echo esc_url( studentup_opportunity_board_url() ); ?>">All active jobs →</a>
		</div>
		<p class="su-rail-hint"><?php echo studentup_ui_icon( 'chevron', 13 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> <?php esc_html_e( 'Swipe sideways for more', 'studentup' ); ?></p>
		<div class="su-hot-rail">
	<?php
	$n = 0;
	while ( $q->have_posts() ) :
		$q->the_post();
		// v173 REAL FIX: meta keys correct ga (purathana 'su_last_date'/'su_salary'
		// keys eppudu save cheyyaledu — anduke salary/deadline pills kanipinchaledu,
		// and $left define cheyyaledu → PHP warning).
		$last = studentup_opportunity_last_date( get_the_ID() );
		$left = ( $last && function_exists( 'studentup_opportunity_days_left' ) )
			? studentup_opportunity_days_left( $last )
			: null;
		if ( null !== $left && $left < 0 ) {
			continue;   // closed posts "hot jobs today" lo vaddu.
		}
		/*
		 * v176 REAL FIX: job signal leni posts (last_date · salary · vacancies ·
		 * apply_url anni leka poyina) "#1 hot job" ga rank ayyevi — live install
		 * lo no-meta test post #1 lo kanipinchindi. Hot job ante REAL opening
		 * signal undali. Signal gate + count cap.
		 */
		$pay  = trim( (string) get_post_meta( get_the_ID(), 'studentup_salary', true ) );
		$vac  = trim( (string) get_post_meta( get_the_ID(), 'studentup_vacancies', true ) );
		$appl = trim( (string) get_post_meta( get_the_ID(), 'studentup_apply_url', true ) );
		if ( '' === (string) $last && '' === $pay && '' === $vac && '' === $appl ) {
			continue;   // ekkada apply cheyalo teliyani post — "hot job" kadhu.
		}
		if ( $n >= (int) $limit ) {
			break;   // cap reach ayyindi — antara render cheyyaku.
		}
		$n++;   // v174: render aina cards ye count — closed skip ayite rank lo gap radhu.
		// v174: raw ISO date ("2026-10-05") kaadu — human format ("05 Oct").
		$last_show = $last
			? wp_date( 'd M', strtotime( $last . ' 12:00:00' ) )
			: get_the_date( 'M j' );
		?>
				<article class="su-hotcard">
					<a class="su-hot-thumb" href="<?php the_permalink(); ?>">
						<?php if ( has_post_thumbnail() ) : ?>
							<?php
							// v126 LCP: modati card image eager + high priority (Discover/CWV).
							the_post_thumbnail(
								'studentup-card',
								1 === $n
									? array( 'loading' => 'eager', 'fetchpriority' => 'high', 'decoding' => 'async', 'alt' => esc_attr( get_the_title() ) )
									: array( 'loading' => 'lazy', 'decoding' => 'async', 'alt' => esc_attr( get_the_title() ) )
							);
							?>
						<?php else : ?>
							<span class="su-hot-ph" aria-hidden="true"><?php echo studentup_ui_icon( 'work', 22 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?></span>
						<?php endif; ?>
						<span class="su-hot-rank">#<?php echo esc_html( $n ); ?></span>
					</a>
					<div class="su-hot-body">
						<h3><a href="<?php the_permalink(); ?>"><?php the_title(); ?></a></h3>
						<div class="su-hot-meta">
							<span class="su-pill su-pill-amber"><?php echo studentup_ui_icon( 'calendar', 12 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> <?php echo esc_html( $last_show ); ?></span>
							<?php if ( $pay ) : ?>
								<span class="su-pill su-pill-green"><?php echo studentup_ui_icon( 'wallet', 12 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> <?php echo esc_html( $pay ); ?></span>
							<?php endif; ?>
							<?php if ( null !== $left && $left >= 0 && $left <= 10 ) : ?>
								<span class="su-pill su-pill-hot"><?php echo studentup_ui_icon( 'bolt', 12 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> <?php echo esc_html( 0 === $left ? 'Last day' : $left . 'd left' ); ?></span>
							<?php endif; ?>
						</div>
						<a class="su-hot-apply" href="<?php the_permalink(); ?>">Apply / Details →</a>
					</div>
				</article>
	<?php endwhile; ?>
		</div>
	</section>
	<?php
	wp_reset_postdata();
}

/**
 * Scholarships spotlight strip (menu + home lo scholarships clear ga kavali).
 */
function studentup_scholarship_strip() {
	if ( ! studentup_opt( 'scholar_strip', '1' ) ) {
		return;
	}
	$term = studentup_used_term( 'scholarships' );
	if ( ! $term ) {
		return;
	}
	$q = new WP_Query(
		array(
			'posts_per_page' => 4,
			'cat'            => (int) $term->term_id,
			'no_found_rows'  => true,
		)
	); // no_found_rows: pagination ledu → extra SELECT FOUND_ROWS avasaram ledu.
	?>
	<section class="su-schol" aria-label="Scholarships">
		<div class="su-schol-head">
			<h2><?php echo studentup_ui_icon( 'school', 18 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> Scholarships open now</h2>
			<a href="<?php echo esc_url( get_category_link( $term ) ); ?>">See all scholarships →</a>
		</div>
		<?php if ( $q->have_posts() ) : ?>
			<div class="su-schol-grid">
				<?php
				while ( $q->have_posts() ) :
					$q->the_post();
					?>
					<a class="su-scard" href="<?php the_permalink(); ?>">
						<b><?php the_title(); ?></b>
						<small><?php echo esc_html( get_the_date( 'M j, Y' ) ); ?> · apply free</small>
					</a>
				<?php endwhile; ?>
			</div>
		<?php else : ?>
			<p class="su-schol-empty">First scholarship notifications are being verified — check back today.</p>
		<?php endif; ?>
	</section>
	<?php
	wp_reset_postdata();
}

/**
 * Alerts / push permission card — "WhatsApp style" instant alert opt-in.
 */
function studentup_alerts_card() {
	if ( ! studentup_opt( 'alerts_card', '1' ) ) {
		return;
	}
	$soc = studentup_social_links();
	?>
	<section class="su-alerts" id="alerts" aria-label="Instant job alerts">
		<div class="su-alerts-in">
			<div class="su-alerts-copy">
				<h2><?php echo studentup_ui_icon( 'bell', 18 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> Get every update as a notification</h2>
				<p>Kotha job, result, hall ticket post chesina vent<span>a</span>ne — mee phone lo alert. Free, ekkada signup avasaram ledu.</p>
			</div>
			<div class="su-alerts-btns">
				<button type="button" class="su-alert-on" data-su-push><?php echo studentup_ui_icon( 'bell', 15 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> Turn on alerts</button>
				<a class="su-alert-wa" href="<?php echo esc_url( $soc['whatsapp'] ); ?>" target="_blank" rel="noopener"><?php echo studentup_social_icon( 'whatsapp', 16 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> WhatsApp</a>
				<a class="su-alert-tg" href="<?php echo esc_url( $soc['telegram'] ); ?>" target="_blank" rel="noopener"><?php echo studentup_social_icon( 'telegram', 16 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> Telegram</a>
			</div>
			<p class="su-alert-state" data-su-push-state role="status"></p>
		</div>
	</section>
	<?php
}

/**
 * Mobile floating bottom navigation (80%+ readers phone lo).
 */
function studentup_bottom_nav() {
	if ( ! studentup_opt( 'bottom_nav', '1' ) ) {
		return;
	}
	$jobs   = studentup_used_term( 'ts-jobs' );
	$schol  = studentup_used_term( 'scholarships' );
	$jobs_u = $jobs ? get_category_link( $jobs ) : home_url( '/#jobs' );
	$sch_u  = $schol ? get_category_link( $schol ) : home_url( '/#jobs' );
	?>
	<nav class="su-bnav" aria-label="Quick navigation">
		<a href="<?php echo esc_url( home_url( '/' ) ); ?>" class="<?php echo is_front_page() ? 'on' : ''; ?>"><?php echo studentup_ui_icon( 'home', 21 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?>Home</a>
		<a href="<?php echo esc_url( $jobs_u ); ?>"><?php echo studentup_ui_icon( 'work', 21 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?>Jobs</a>
		<a href="<?php echo esc_url( $sch_u ); ?>"><?php echo studentup_ui_icon( 'school', 21 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?>Scholar</a>
		<a href="<?php echo esc_url( home_url( '/#alerts' ) ); ?>"><?php echo studentup_ui_icon( 'bell', 21 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?>Alerts</a>
		<button type="button" class="su-bnav-search" id="su-bnav-search"><?php echo studentup_ui_icon( 'search', 21 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?>Search</button>
	</nav>
	<?php
}
add_action( 'wp_footer', 'studentup_bottom_nav', 5 );


/**
 * v191 WORLDCLASS + v198 TOOLS ADVANCED: calculator wall → ONE neat tabbed card.
 *
 * v198 lo add ayyindi (owner ask: "tools and UI advanced ga vundali, neat ga,
 * phone lo easy ga click vachelaga"):
 *   · TOOL FINDER — search box + category chips (Money · Eligibility · Exams ·
 *     Career · Deadlines) → 8 tools lo kavalsinadi 2 taps lo.
 *   · STICKY STRIP — tab bar header kinda stick avutundi; active tab auto-scroll;
 *     phone lo left/right swipe tho tool maaruthundi (engine lo untundi).
 *   · DEEP LINK — /tools/?tool=age shareable + Back pani chestundi.
 *   · HOW IT WORKS — prathi tool ki formula + source line (data attributes →
 *     assets/js/studentup-tools.js renders a <details>). E-E-A-T: reader ki
 *     "ela vachindi" telustundi.
 *   · ACTIONS — Copy result · Share · Print · Reset (engine renders; original
 *     tool markup as-it-is untundi, so 8 modules em marchaledu).
 *
 * Markup contract (parity audit + tests): .su-tools[data-su-tools] ›
 * .su-toolfind + .su-toolcats + .su-tooltabs[data-su-tool-strip] › .su-ttab
 * (role=tab) + .su-toolpanels[data-su-tool-swipe] › .su-toolpanel (role=tabpanel).
 */
function studentup_tools_tabs() {
	$tools = array(
		array( 'id' => 'salary',   'icon' => 'wallet',   'label' => 'In-hand salary',      'fn' => 'studentup_salary_calc',              'cat' => 'money',        'keys' => 'salary in hand pay gross net da hra pay slip 7th cpc', 'formula' => 'Gross = Basic × (1 + DA% + HRA%); In-hand = Gross − deductions (NPS, tax).', 'source' => '7th CPC fitment table + your department pay slip' ),
		array( 'id' => 'age',      'icon' => 'person',   'label' => 'Age checker',          'fn' => 'studentup_age_calculator_block',     'cat' => 'eligibility',  'keys' => 'age eligibility dob relaxation obc sc st pwd ex servicemen cutoff', 'formula' => 'Age is counted on the cutoff date; category relaxation is added to the upper limit.', 'source' => 'the notification’s age table (TSPSC/APPSC/SSC)' ),
		array( 'id' => 'fee',      'icon' => 'doc',      'label' => 'Fee & concession',     'fn' => 'studentup_fee_calculator_block',     'cat' => 'money',        'keys' => 'fee application fee concession sc st obc ews payment challan', 'formula' => 'Payable = base fee × category share; exemptions are shown as ₹0.', 'source' => 'the official notification fee table' ),
		array( 'id' => 'score',    'icon' => 'chart',    'label' => 'Score & negative',     'fn' => 'studentup_score_calculator_block',   'cat' => 'exams',        'keys' => 'score marks negative marking answer key expected cutoff', 'formula' => 'Marks = correct − (wrong × negative mark per question).', 'source' => 'the exam’s marking scheme' ),
		array( 'id' => 'calendar', 'icon' => 'calendar', 'label' => 'Last-date calendar',   'fn' => 'studentup_job_calendar',             'cat' => 'deadlines',    'keys' => 'last date deadline calendar reminder exam date', 'formula' => 'Only confirmed dates from posts are listed; nothing is estimated.', 'source' => 'every post’s verified last-date field' ),
		array( 'id' => 'admit',    'icon' => 'ticket',   'label' => 'Admit card helper',    'fn' => 'studentup_admit_card_block',         'cat' => 'exams',        'keys' => 'admit card hall ticket download centre instructions', 'formula' => 'Checklist follows the standard hall-ticket instructions.', 'source' => 'the exam authority’s instruction sheet' ),
		array( 'id' => 'resume',   'icon' => 'doc',      'label' => 'Resume maker',         'fn' => 'studentup_resume_maker_block',       'cat' => 'career',       'keys' => 'resume cv bio data government format application', 'formula' => 'Fields fill a plain government-format summary — no account, nothing stored.', 'source' => 'standard government application format' ),
		array( 'id' => 'syllabus', 'icon' => 'book',     'label' => 'Syllabus tracker',     'fn' => 'studentup_syllabus_tracker_block',   'cat' => 'career',       'keys' => 'syllabus tracker preparation progress subjects revision', 'formula' => 'Progress = ticked subjects ÷ total subjects.', 'source' => 'the exam’s official syllabus' ),
	);
	$tools = array_values(
		array_filter(
			$tools,
			static function ( $t ) {
				return function_exists( $t['fn'] );
			}
		)
	);
	if ( ! $tools ) {
		return;
	}
	$cats   = array(
		'all'         => __( 'All tools', 'studentup' ),
		'money'       => __( 'Money', 'studentup' ),
		'eligibility' => __( 'Eligibility', 'studentup' ),
		'exams'       => __( 'Exams', 'studentup' ),
		'career'      => __( 'Career', 'studentup' ),
		'deadlines'   => __( 'Deadlines', 'studentup' ),
	);
	$counts = array( 'all' => count( $tools ) );
	foreach ( $tools as $t ) {
		$c            = isset( $t['cat'] ) ? $t['cat'] : 'all';
		$counts[ $c ] = isset( $counts[ $c ] ) ? $counts[ $c ] + 1 : 1;
	}
	?>
	<section class="su-tools" id="tools" data-su-tools aria-label="<?php esc_attr_e( 'Free tools for students', 'studentup' ); ?>">
		<?php /* v198 no-JS: JS lekapote tabs pani cheyyavu — appudu anni tools one below one chupinchandi (hidden content eppudu undakoodadu). */ ?>
		<noscript><style>.su-toolpanel[hidden]{display:block!important}.su-tooltabs,.su-toolcats,.su-toolfind,.su-tools-top{display:none!important}</style></noscript>
		<div class="su-tools-head">
			<div class="sectionhead" style="margin:0 0 6px">
				<div>
					<h2><?php esc_html_e( 'Free tools for students', 'studentup' ); ?></h2>
					<p><?php esc_html_e( 'Search cheyandi leda tab tap cheyandi — okka sari lo okka tool, screen clean ga untundi.', 'studentup' ); ?></p>
				</div>
			</div>

			<div class="su-toolfind">
				<label class="screen-reader-text" for="su-tool-search"><?php esc_html_e( 'Search tools', 'studentup' ); ?></label>
				<span class="su-toolfind-ic" aria-hidden="true"><?php echo studentup_ui_icon( 'search', 17 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?></span>
				<input id="su-tool-search" type="search" data-su-tool-find autocomplete="off" enterkeyhint="search"
					placeholder="<?php esc_attr_e( 'Search a tool — salary, age, fee, resume…', 'studentup' ); ?>">
				<button type="button" class="su-toolfind-clear" data-su-tool-clear hidden
					aria-label="<?php esc_attr_e( 'Clear search', 'studentup' ); ?>"><?php echo studentup_ui_icon( 'close', 15 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?></button>
			</div>

			<div class="su-toolcats" role="group" aria-label="<?php esc_attr_e( 'Filter tools by category', 'studentup' ); ?>">
				<?php foreach ( $cats as $cid => $clabel ) : ?>
					<?php if ( 'all' !== $cid && empty( $counts[ $cid ] ) ) { continue; } ?>
					<button type="button" class="su-tcat<?php echo 'all' === $cid ? ' on' : ''; ?>" data-su-tool-cat="<?php echo esc_attr( $cid ); ?>"
						aria-pressed="<?php echo 'all' === $cid ? 'true' : 'false'; ?>"><?php echo esc_html( $clabel ); ?> <b><?php echo (int) ( isset( $counts[ $cid ] ) ? $counts[ $cid ] : 0 ); ?></b></button>
				<?php endforeach; ?>
			</div>
			<p class="su-toolfind-none" data-su-tool-none hidden>
				<?php esc_html_e( 'Ee peru tho tool ledu:', 'studentup' ); ?> “<span data-su-tool-q></span>”.
				<?php esc_html_e( 'Try “salary”, “age” leda “resume”.', 'studentup' ); ?>
			</p>
		</div>

		<div class="su-tooltabs" role="tablist" aria-label="<?php esc_attr_e( 'Student tools', 'studentup' ); ?>" data-su-tool-strip>
			<?php foreach ( $tools as $i => $t ) : ?>
				<button type="button" class="su-ttab" role="tab"
					id="su-ttab-<?php echo esc_attr( $t['id'] ); ?>"
					aria-controls="su-tool-<?php echo esc_attr( $t['id'] ); ?>"
					aria-selected="<?php echo esc_attr( 0 === $i ? 'true' : 'false' ); ?>"
					tabindex="<?php echo esc_attr( 0 === $i ? '0' : '-1' ); ?>"
					data-su-cat="<?php echo esc_attr( isset( $t['cat'] ) ? $t['cat'] : 'all' ); ?>"
					data-su-keywords="<?php echo esc_attr( isset( $t['keys'] ) ? $t['keys'] : '' ); ?>"><?php echo studentup_ui_icon( isset( $t['icon'] ) ? $t['icon'] : 'bolt', 16 ); // v192: emoji badulu SVG ?> <span><?php echo esc_html( $t['label'] ); ?></span></button>
			<?php endforeach; ?>
		</div>

		<div class="su-toolpanels" data-su-tool-swipe>
			<?php foreach ( $tools as $i => $t ) : ?>
				<div class="su-toolpanel<?php echo esc_attr( 0 === $i ? ' on' : '' ); ?>"
					id="su-tool-<?php echo esc_attr( $t['id'] ); ?>" role="tabpanel"
					aria-labelledby="su-ttab-<?php echo esc_attr( $t['id'] ); ?>"
					data-su-formula="<?php echo esc_attr( isset( $t['formula'] ) ? $t['formula'] : '' ); ?>"
					data-su-source="<?php echo esc_attr( isset( $t['source'] ) ? $t['source'] : '' ); ?>"<?php echo esc_attr( 0 === $i ? '' : ' hidden' ); ?>>
					<?php call_user_func( $t['fn'] ); ?>
					<div class="su-tool-nav">
						<button type="button" class="su-tnext" data-su-next><?php echo studentup_ui_icon( 'arrow', 15 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> <?php esc_html_e( 'Next tool', 'studentup' ); ?></button>
					</div>
				</div>
			<?php endforeach; ?>
		</div>

		<button type="button" class="su-tools-top" data-su-tool-top hidden><?php echo studentup_ui_icon( 'arrow', 14 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> <?php esc_html_e( 'Back to tools', 'studentup' ); ?></button>
	</section>
	<?php
}
