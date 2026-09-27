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
		array( 'slug' => 'ts-jobs', 'label' => 'Latest Govt Jobs', 'icon' => '🔥', 'tone' => 'fire' ),
		array( 'slug' => 'scholarships', 'label' => 'Scholarships', 'icon' => '🎓', 'tone' => 'grape' ),
		array( 'slug' => 'results', 'label' => 'Results', 'icon' => '📢', 'tone' => 'sky' ),
		array( 'slug' => 'hall-tickets', 'label' => 'Hall Tickets', 'icon' => '🎫', 'tone' => 'mint' ),
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
				<span class="su-hs-ico" aria-hidden="true">🔍</span>
				<input type="search" name="s" value="<?php echo esc_attr( get_search_query() ); ?>"
					placeholder="Search SSC, TSPSC, scholarships, hall tickets…" aria-label="Search StudentUp">
				<button type="submit">Search</button>
			</form>

			<div class="su-hero-acts">
				<?php foreach ( studentup_hero_actions() as $a ) : ?>
					<a class="su-hact su-t-<?php echo esc_attr( $a['tone'] ); ?>" href="<?php echo esc_url( $a['url'] ); ?>">
						<span aria-hidden="true"><?php echo esc_html( $a['icon'] ); ?></span><?php echo esc_html( $a['label'] ); ?>
					</a>
				<?php endforeach; ?>
			</div>

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
	foreach ( array( 'ts-jobs', 'ap-jobs', 'central-jobs', 'private-jobs' ) as $s ) {
		$t = studentup_used_term( $s );
		if ( $t ) {
			$cats[] = (int) $t->term_id;
		}
	}
	$q = new WP_Query(
		array(
			'posts_per_page'      => (int) $limit,
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
			<h2>🔥 Top <?php echo esc_html( (int) $limit ); ?> hot jobs today</h2>
			<a href="<?php echo esc_url( studentup_opportunity_board_url() ); ?>">All active jobs →</a>
		</div>
		<div class="su-hot-rail">
			<?php
			$n = 0;
			while ( $q->have_posts() ) :
				$q->the_post();
				$n++;
				$last = get_post_meta( get_the_ID(), 'su_last_date', true );
				$pay  = get_post_meta( get_the_ID(), 'su_salary', true );
				?>
				<article class="su-hotcard">
					<a class="su-hot-thumb" href="<?php the_permalink(); ?>">
						<?php if ( has_post_thumbnail() ) : ?>
							<?php the_post_thumbnail( 'studentup-card', array( 'loading' => 'lazy', 'alt' => esc_attr( get_the_title() ) ) ); ?>
						<?php else : ?>
							<span class="su-hot-ph" aria-hidden="true">🎯</span>
						<?php endif; ?>
						<span class="su-hot-rank">#<?php echo esc_html( $n ); ?></span>
					</a>
					<div class="su-hot-body">
						<h3><a href="<?php the_permalink(); ?>"><?php the_title(); ?></a></h3>
						<div class="su-hot-meta">
							<span class="su-pill su-pill-amber">📅 <?php echo esc_html( $last ? $last : get_the_date( 'M j' ) ); ?></span>
							<?php if ( $pay ) : ?>
								<span class="su-pill su-pill-green">💰 <?php echo esc_html( $pay ); ?></span>
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
			<h2>🎓 Scholarships open now</h2>
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
				<h2>🔔 Get every update as a notification</h2>
				<p>Kotha job, result, hall ticket post chesina vent<span>a</span>ne — mee phone lo alert. Free, ekkada signup avasaram ledu.</p>
			</div>
			<div class="su-alerts-btns">
				<button type="button" class="su-alert-on" data-su-push>🔔 Turn on alerts</button>
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
		<a href="<?php echo esc_url( home_url( '/' ) ); ?>" class="<?php echo is_front_page() ? 'on' : ''; ?>"><span aria-hidden="true">🏠</span>Home</a>
		<a href="<?php echo esc_url( $jobs_u ); ?>"><span aria-hidden="true">💼</span>Jobs</a>
		<a href="<?php echo esc_url( $sch_u ); ?>"><span aria-hidden="true">🎓</span>Scholar</a>
		<a href="<?php echo esc_url( home_url( '/#alerts' ) ); ?>"><span aria-hidden="true">🔔</span>Alerts</a>
		<button type="button" class="su-bnav-search" id="su-bnav-search"><span aria-hidden="true">🔍</span>Search</button>
	</nav>
	<?php
}
add_action( 'wp_footer', 'studentup_bottom_nav', 5 );
