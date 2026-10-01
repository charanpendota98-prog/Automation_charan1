<?php
/**
 * v124 SMART LAYER — AI Job Match · Eligibility Checker · Salary Calculator ·
 * Job Calendar · Trending Today · state-first dynamic homepage.
 *
 * Enduku (why): FreeJobAlert/JagranJosh lo lenидi idi — reader tana
 * qualification, state, age select chesthe **instant** ga eligible jobs
 * matrame chupinchadam. Antha browser lo jarugutundi (server load ledu,
 * cookie/profile ledu) — page okasari load ayite filters instant.
 *
 * Data: publish ayina posts + real meta keys (studentup_last_date,
 * studentup_qual, studentup_apply_url, studentup_salary, studentup_age_min/max,
 * studentup_vacancies). Meta lekapote aa field "—" ga chupistundi — eppudu
 * fake number generate cheyyadu.
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * State bucket for a post (category based).
 *
 * @param int $post_id post.
 * @return string ts|ap|central|other
 */
function studentup_smart_state( $post_id ) {
	$map = array(
		'ts'      => studentup_used_term( 'ts-jobs' ),
		'ap'      => studentup_used_term( 'ap-jobs' ),
		'central' => studentup_used_term( 'central-jobs' ),
	);
	$ids = wp_get_post_categories( (int) $post_id );
	foreach ( $map as $key => $term ) {
		if ( $term && in_array( (int) $term->term_id, array_map( 'intval', $ids ), true ) ) {
			return $key;
		}
	}
	return 'other';
}

/**
 * Reader-facing dataset for the smart tools (JSON ga print avutundi).
 *
 * @param int $limit posts.
 * @return array<int,array<string,mixed>>
 */
function studentup_smart_dataset( $limit = 60 ) {
	$cached = wp_cache_get( 'studentup_smart_' . (int) $limit, 'studentup' );
	if ( is_array( $cached ) ) {
		return $cached;
	}
	$q = new WP_Query(
		array(
			'post_type'           => 'post',
			'post_status'         => 'publish',
			'posts_per_page'      => max( 10, (int) $limit ),
			'ignore_sticky_posts' => true,
			'no_found_rows'       => true,
		)
	);
	$out = array();
	foreach ( $q->posts as $post ) {
		$id   = (int) $post->ID;
		$last = function_exists( 'studentup_opportunity_last_date' ) ? studentup_opportunity_last_date( $id ) : '';
		$qual = trim( (string) get_post_meta( $id, 'studentup_qual', true ) );
		$apply = trim( (string) get_post_meta( $id, 'studentup_apply_url', true ) );
		if ( ! wp_http_validate_url( $apply ) ) {
			$apply = '';
		}
		/*
		 * v174: jobs-only dataset — studentup_* meta leni chota posts ("Hello
		 * world!" la vaati) workspace matching lo vaddu. Bot/curator eppudu
		 * aa meta tho ne publish chestayi; meta leni di matrame filter.
		 */
		$pay = trim( (string) get_post_meta( $id, 'studentup_salary', true ) );
		$vac = trim( (string) get_post_meta( $id, 'studentup_vacancies', true ) );
		if ( '' === $last && '' === $qual && '' === $apply && '' === $pay && '' === $vac ) {
			continue;
		}
		$age_min = (int) get_post_meta( $id, 'studentup_age_min', true );
		$age_max = (int) get_post_meta( $id, 'studentup_age_max', true );
		$out[]   = array(
			'id'    => $id,
			'title' => wp_strip_all_tags( get_the_title( $id ) ),
			'link'  => get_permalink( $id ),
			'img'   => (string) get_the_post_thumbnail_url( $id, 'studentup-card' ),
			'qual'  => $qual ? array_values( array_filter( array_map( 'trim', explode( ',', $qual ) ) ) ) : array(),
			'state' => studentup_smart_state( $id ),
			'last'  => $last,
			'days'  => ( $last && function_exists( 'studentup_opportunity_days_left' ) ) ? studentup_opportunity_days_left( $last ) : null,
			'pay'   => $pay,
			'vac'   => $vac,
			'amin'  => $age_min > 0 ? $age_min : 0,
			'amax'  => $age_max > 0 ? $age_max : 0,
			'apply' => $apply,
			'date'  => get_the_date( 'Y-m-d', $id ),
		);
	}
	wp_cache_set( 'studentup_smart_' . (int) $limit, $out, 'studentup', 300 );
	return $out;
}

/**
 * Trending today chips (hero kinda) — latest verified headlines.
 */
function studentup_trending_today() {
	if ( ! studentup_opt( 'trending_today', '1' ) ) {
		return;
	}
	$q = new WP_Query(
		array(
			'posts_per_page'      => 6,
			'ignore_sticky_posts' => true,
			'no_found_rows'       => true,
		)
	);
	if ( ! $q->have_posts() ) {
		wp_reset_postdata();
		return;
	}
	?>
	<div class="su-trend" aria-label="Trending today">
		<span class="su-trend-tag"><?php echo studentup_ui_icon( 'bolt', 12 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> Trending today</span>
		<div class="su-trend-list">
			<?php
			while ( $q->have_posts() ) :
				$q->the_post();
				?>
				<a href="<?php the_permalink(); ?>"><?php echo esc_html( wp_trim_words( get_the_title(), 7, '…' ) ); ?></a>
			<?php endwhile; ?>
		</div>
	</div>
	<?php
	wp_reset_postdata();
}

/**
 * AI Job Match + Eligibility Checker.
 *
 * Reader: qualification + state + age → instant eligible list. Age/qualification
 * data lena posts "check the notification" ga honest ga chupistayi.
 */
function studentup_job_finder() {
	if ( ! studentup_opt( 'job_finder', '1' ) ) {
		return;
	}
	$data = studentup_smart_dataset( 60 );
	if ( ! $data ) {
		return;
	}
	$quals = studentup_qual_terms();
	?>
	<section class="su-finder" id="job-match" aria-label="AI job match and eligibility checker">
		<div class="su-finder-head">
			<div>
				<p class="su-finder-kick"><?php echo studentup_ui_icon( 'person', 14 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> AI JOB MATCH · ELIGIBILITY CHECKER</p>
				<h2>Mee qualification, state, age — eligible jobs instant ga</h2>
			</div>
			<span class="su-finder-count" data-su-finder-count aria-live="polite"></span>
		</div>

		<form class="su-finder-form" data-su-finder='<?php echo esc_attr( wp_json_encode( $data ) ); ?>' onsubmit="return false">
			<label>Qualification
				<select data-su-f-qual>
					<option value="">Any qualification</option>
					<?php foreach ( $quals as $slug => $label ) : ?>
						<option value="<?php echo esc_attr( $slug ); ?>"><?php echo esc_html( $label ); ?></option>
					<?php endforeach; ?>
				</select>
			</label>
			<label>State
				<select data-su-f-state>
					<option value="">All India</option>
					<option value="ts">Telangana</option>
					<option value="ap">Andhra Pradesh</option>
					<option value="central">Central / All India</option>
				</select>
			</label>
			<label>Your age
				<input type="number" min="14" max="60" inputmode="numeric" placeholder="e.g. 25" data-su-f-age>
			</label>
			<label>Show
				<select data-su-f-sort>
					<option value="last">Closing soon first</option>
					<option value="new">Newest first</option>
				</select>
			</label>
			<button type="button" class="su-finder-reset" data-su-f-reset><?php echo studentup_ui_icon( 'refresh', 13 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> Reset</button>
		</form>

		<div class="su-finder-results" data-su-finder-results></div>
		<p class="su-finder-note">Eligibility is a guide from the data we publish — apply cheyyadaniki mundu official notification lo okasari confirm cheyandi.</p>
	</section>
	<?php
}

/**
 * Salary calculator — expected in-hand (7th PC style, transparent formula).
 */
function studentup_salary_calc() {
	if ( ! studentup_opt( 'salary_calc', '1' ) ) {
		return;
	}
	?>
	<section class="su-calc" id="salary-calculator" aria-label="Salary calculator">
		<div class="su-calc-head">
			<h2><?php echo studentup_ui_icon( 'wallet', 17 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> In-hand salary calculator</h2>
			<p>Basic pay + DA + HRA + TA − deductions. Formula open ga undi — mee notification numbers pettandi.</p>
		</div>
		<form class="su-calc-form" onsubmit="return false">
			<label>Basic pay (₹)<input type="number" min="0" step="100" value="25500" data-su-c-basic inputmode="numeric"></label>
			<label>DA %<input type="number" min="0" max="300" step="0.5" value="50" data-su-c-da inputmode="decimal"></label>
			<label>HRA %<input type="number" min="0" max="40" step="1" value="18" data-su-c-hra inputmode="numeric"></label>
			<label>TA (₹)<input type="number" min="0" step="100" value="1800" data-su-c-ta inputmode="numeric"></label>
			<label>Deductions (₹)<input type="number" min="0" step="100" value="3200" data-su-c-ded inputmode="numeric"></label>
		</form>
		<div class="su-calc-out" data-su-calc-out aria-live="polite"></div>
	</section>
	<?php
}

/**
 * Job calendar — ee nela last dates (repeat visits).
 */
function studentup_job_calendar() {
	if ( ! studentup_opt( 'job_calendar', '1' ) ) {
		return;
	}
	$data  = studentup_smart_dataset( 60 );
	$items = array();
	foreach ( $data as $row ) {
		if ( ! empty( $row['last'] ) ) {
			$items[] = array(
				'last'  => $row['last'],
				'title' => $row['title'],
				'link'  => $row['link'],
			);
		}
	}
	if ( ! $items ) {
		return;
	}
	usort(
		$items,
		static function ( $a, $b ) {
			return strcmp( $a['last'], $b['last'] );
		}
	);
	?>
	<section class="su-cal" id="job-calendar" aria-label="Job calendar">
		<div class="su-cal-head">
			<h2><?php echo studentup_ui_icon( 'calendar', 18 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> Job calendar — last dates</h2>
			<span><?php echo esc_html( date_i18n( 'F Y' ) ); ?> onwards</span>
		</div>
		<ol class="su-cal-list">
			<?php foreach ( array_slice( $items, 0, 12 ) as $it ) : ?>
				<?php
				$ts   = strtotime( $it['last'] );
				$days = $ts ? (int) floor( ( $ts - current_time( 'timestamp' ) ) / DAY_IN_SECONDS ) : null;
				?>
				<li>
					<span class="su-cal-date"><b><?php echo esc_html( $ts ? date_i18n( 'j', $ts ) : '—' ); ?></b><small><?php echo esc_html( $ts ? date_i18n( 'M', $ts ) : '' ); ?></small></span>
					<a href="<?php echo esc_url( $it['link'] ); ?>"><?php echo esc_html( $it['title'] ); ?></a>
					<?php if ( null !== $days && $days >= 0 ) : ?>
						<em class="su-cal-left<?php echo ( $days <= 3 ) ? ' hot' : ''; ?>"><?php echo esc_html( 0 === $days ? 'Today' : $days . ' days left' ); ?></em>
					<?php endif; ?>
				</li>
			<?php endforeach; ?>
		</ol>
	</section>
	<?php
}

/**
 * "Your state" switcher — dynamic homepage (TS user ki TS jobs first).
 * JS localStorage lo gurthu pettukuntundi; server-side personalisation ledu
 * (cache-safe + privacy-safe).
 */
function studentup_state_switch() {
	if ( ! studentup_opt( 'state_first', '1' ) ) {
		return;
	}
	?>
	<div class="su-statebar" data-su-state-bar>
		<span><?php echo studentup_ui_icon( 'pin', 13 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> Your state:</span>
		<button type="button" data-su-state="ts">Telangana</button>
		<button type="button" data-su-state="ap">Andhra Pradesh</button>
		<button type="button" data-su-state="central">All India</button>
	</div>
	<?php
}

/**
 * v125: homepage ItemList JSON-LD — Google ki "ee page lo em unnayi" ani clear
 * signal (Discover + rich result eligibility). Real published posts matrame;
 * fake ratings/salary markup eppudu ledu.
 */
function studentup_home_itemlist_schema() {
	if ( ! is_front_page() || ! studentup_opt( 'schema', '1' ) ) {
		return;
	}
	$rows = array_slice( studentup_smart_dataset( 10 ), 0, 10 );
	if ( ! $rows ) {
		return;
	}
	$items = array();
	foreach ( $rows as $i => $row ) {
		$items[] = array(
			'@type'    => 'ListItem',
			'position' => $i + 1,
			'url'      => $row['link'],
			'name'     => $row['title'],
		);
	}
	$data = array(
		'@context'        => 'https://schema.org',
		'@type'           => 'ItemList',
		'@id'             => home_url( '/#latest-updates' ),
		'name'            => 'Latest jobs, results and scholarship updates',
		'itemListOrder'   => 'https://schema.org/ItemListOrderDescending',
		'numberOfItems'   => count( $items ),
		'itemListElement' => $items,
	);
	echo '<script type="application/ld+json">'
		. wp_json_encode( $data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES )
		. '</script>' . "\n";
}
add_action( 'wp_head', 'studentup_home_itemlist_schema', 6 );

/**
 * Popular searches strip — real internal links for long-tail queries.
 *
 * v140: every chip points at a live category archive or an on-site search that
 * actually returns posts, so this is genuine internal linking (crawl depth +
 * long-tail SEO), not a keyword-stuffed footer block.
 *
 * @return void
 */
function studentup_popular_searches() {
	if ( ! studentup_opt( 'popular_searches', '1' ) ) {
		return;
	}
	$queries = array(
		'TSPSC notification',
		'APPSC notification',
		'SSC CGL apply online',
		'AP DSC teacher posts',
		'NSP scholarship last date',
		'railway group d',
		'police constable',
		'hall ticket download',
		'degree jobs',
		'10th pass jobs',
	);
	?>
	<section class="su-popsearch" aria-labelledby="su-popsearch-title">
		<h2 id="su-popsearch-title" class="su-popsearch-title">Popular searches</h2>
		<ul class="su-popsearch-list">
			<?php foreach ( studentup_most_used() as $su_m ) : ?>
				<?php $su_term = studentup_used_term( $su_m['slug'] ); ?>
				<?php if ( $su_term ) : ?>
					<li><a class="su-pop su-pop-cat" href="<?php echo esc_url( get_category_link( $su_term ) ); ?>">
						<span class="su-pop-ico" aria-hidden="true"><?php echo studentup_ui_icon( $su_m['icon'], 15 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?></span><?php echo esc_html( $su_m['label'] ); ?></a></li>
				<?php endif; ?>
			<?php endforeach; ?>
			<?php foreach ( $queries as $su_q ) : ?>
				<li><a class="su-pop" href="<?php echo esc_url( home_url( '/?s=' . rawurlencode( $su_q ) ) ); ?>"><?php echo esc_html( $su_q ); ?></a></li>
			<?php endforeach; ?>
		</ul>
	</section>
	<?php
}
