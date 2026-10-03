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
	$defs = array(
		array( 'slug' => 'ts-jobs', 'label' => 'Latest Govt Jobs', 'icn' => 'bolt', 'tone' => 'fire' ),
		array( 'slug' => 'scholarships', 'label' => 'Scholarships', 'icn' => 'school', 'tone' => 'grape' ),
		array( 'slug' => 'results', 'label' => 'Results', 'icn' => 'board', 'tone' => 'sky' ),
		array( 'slug' => 'hall-tickets', 'label' => 'Hall Tickets', 'icn' => 'tag', 'tone' => 'mint' ),
	);
	foreach ( $defs as $d ) {
		$term = studentup_used_term( $d['slug'] );
		if ( ! $term ) {
			continue;
		}
		$d['url'] = get_category_link( $term );
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
	$posts_count = (int) wp_count_posts()->publish;
	$today       = (int) count(
		get_posts(
			array(
				'posts_per_page' => 20,
				'fields'         => 'ids',
				'no_found_rows'  => true,
				'date_query'     => array( array( 'after' => '24 hours ago' ) ),
			)
		)
	);
	?>
	<section class="su-hero" aria-label="StudentUp search and quick links">
		<span class="su-hero-orb su-orb1" aria-hidden="true"></span>
		<span class="su-hero-orb su-orb2" aria-hidden="true"></span>
		<div class="wrap su-hero-in">
			<p class="su-hero-kicker"><span class="su-live-dot" aria-hidden="true"></span> Live updates · Telangana · Andhra Pradesh · Central</p>
			<h2 class="su-hero-title">One place for every <span>job, scholarship &amp; result</span></h2>
			<p class="su-hero-sub">Verified notifications, last dates and direct apply links — checked by hand before posting.</p>

			<form class="su-hero-search" role="search" method="get" action="<?php echo esc_url( home_url( '/' ) ); ?>">
				<span class="su-hs-ico" aria-hidden="true"><?php echo studentup_ui_icon( 'search', 19 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?></span>
				<input type="search" name="s" value="<?php echo esc_attr( get_search_query() ); ?>"
					placeholder="Search SSC, TSPSC, scholarships, hall tickets…" aria-label="Search StudentUp">
				<button type="submit">Search</button>
			</form>

			<div class="su-hero-acts">
				<?php foreach ( studentup_hero_actions() as $a ) : ?>
					<a class="su-hact su-t-<?php echo esc_attr( $a['tone'] ); ?>" href="<?php echo esc_url( $a['url'] ); ?>">
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

			<ul class="su-hero-stats">
				<li><b><?php echo esc_html( number_format_i18n( $posts_count ) ); ?></b><span>Updates published</span></li>
				<li><b><?php echo esc_html( number_format_i18n( $today ) ); ?></b><span>Added in 24 hours</span></li>
				<li><b>100%</b><span>Official source links</span></li>
			</ul>
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
 * v191 WORLDCLASS: calculator wall → ONE neat tabbed card.
 *
 * Enduku: modata home lo 8 tool blocks oka daggara oka render ayyevi
 * (salary · age · fee · score · calendar · admit card · resume · syllabus) —
 * phone lo adi "widget wall", reader 3 screens scroll chesina first job card
 * kanipinchedi kaadu. Ippudu aa 8 okate card lo tabs ga — okka sari lo okkati,
 * migatha antha neat ga hidden. Prathi tab keyboard tho kuda switch avutundi
 * (arrow keys), screen reader ki role="tab"/aria-selected correct ga untundi.
 */
function studentup_tools_tabs() {
	$tools = array(
		array( 'id' => 'salary',   'icon' => 'wallet',   'label' => 'In-hand salary',    'fn' => 'studentup_salary_calc' ),
		array( 'id' => 'age',      'icon' => 'person',   'label' => 'Age checker',        'fn' => 'studentup_age_calculator_block' ),
		array( 'id' => 'fee',      'icon' => 'doc',      'label' => 'Fee & concession',   'fn' => 'studentup_fee_calculator_block' ),
		array( 'id' => 'score',    'icon' => 'chart',    'label' => 'Score & negative',   'fn' => 'studentup_score_calculator_block' ),
		array( 'id' => 'calendar', 'icon' => 'calendar', 'label' => 'Last-date calendar', 'fn' => 'studentup_job_calendar' ),
		array( 'id' => 'admit',    'icon' => 'ticket',   'label' => 'Admit card helper',  'fn' => 'studentup_admit_card_block' ),
		array( 'id' => 'resume',   'icon' => 'doc',      'label' => 'Resume maker',       'fn' => 'studentup_resume_maker_block' ),
		array( 'id' => 'syllabus', 'icon' => 'book',     'label' => 'Syllabus tracker',   'fn' => 'studentup_syllabus_tracker_block' ),
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
	?>
	<section class="su-tools" id="tools" aria-label="<?php esc_attr_e( 'Free tools for students', 'studentup' ); ?>">
		<div class="su-tools-head">
			<div class="sectionhead" style="margin:0 0 6px">
				<div>
					<h2><?php esc_html_e( 'Free tools for students', 'studentup' ); ?></h2>
					<p><?php esc_html_e( 'Tap a tab — okka sari lo okkati, screen clean ga untundi.', 'studentup' ); ?></p>
				</div>
			</div>
		</div>
		<div class="su-tooltabs" role="tablist" aria-label="<?php esc_attr_e( 'Student tools', 'studentup' ); ?>">
			<?php foreach ( $tools as $i => $t ) : ?>
				<button type="button" class="su-ttab" role="tab"
					id="su-ttab-<?php echo esc_attr( $t['id'] ); ?>"
					aria-controls="su-tool-<?php echo esc_attr( $t['id'] ); ?>"
					aria-selected="<?php echo esc_attr( 0 === $i ? 'true' : 'false' ); ?>"
					tabindex="<?php echo esc_attr( 0 === $i ? '0' : '-1' ); ?>"><?php echo studentup_ui_icon( isset( $t['icon'] ) ? $t['icon'] : 'bolt', 16 ); // v192: emoji badulu SVG ?> <span><?php echo esc_html( $t['label'] ); ?></span></button>
			<?php endforeach; ?>
		</div>
		<?php foreach ( $tools as $i => $t ) : ?>
			<div class="su-toolpanel<?php echo esc_attr( 0 === $i ? ' on' : '' ); ?>"
				id="su-tool-<?php echo esc_attr( $t['id'] ); ?>" role="tabpanel"
				aria-labelledby="su-ttab-<?php echo esc_attr( $t['id'] ); ?>"<?php echo esc_attr( 0 === $i ? '' : ' hidden' ); ?>>
				<?php call_user_func( $t['fn'] ); ?>
			</div>
		<?php endforeach; ?>
	</section>
	<?php
}
