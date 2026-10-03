<?php
/**
 * v197 Daily Quiz & Polls page template (slug: daily-quiz).
 *
 * Why a page, not only a home block:
 *  · Quiz + poll = repeat-visit content → own URL for search ("daily quiz",
 *    "current affairs quiz") and for WhatsApp shares.
 *  · Home page stays content+ads only (owner rule) — the heavy interactive
 *    block lives here and the home shows a compact version.
 *
 * Server-rendered (works without JS), ISR-free, no personal data.
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

get_header();
?>
<main id="main" class="wrap su-quizpage">
	<?php
	while ( have_posts() ) :
		the_post();
		?>
		<nav class="crumbs" aria-label="Breadcrumb">
			<a href="<?php echo esc_url( home_url( '/' ) ); ?>">Home</a> › <?php the_title(); ?>
		</nav>
		<h1 class="su-quizpage-title"><?php the_title(); ?></h1>
		<p class="su-ic-page-sub">
			<?php esc_html_e( 'Five fresh questions every morning, explained answers, and one reader poll that decides what we build next. Free, no login, nothing stored about you.', 'studentup' ); ?>
		</p>
		<?php
		if ( trim( (string) get_the_content() ) !== '' ) {
			echo '<div class="su-quizpage-intro">';
			the_content();
			echo '</div>';
		}

		// 1. Today's quiz (server-rendered, JS instant).
		studentup_daily_quiz(
			array(
				'id'      => 'daily-quiz',
				'heading' => 'Today\'s 5 questions',
				'kicker'  => 'DAILY QUIZ',
			)
		);

		// 2. Today's poll (real votes).
		studentup_daily_poll(
			array(
				'kicker' => 'READER POLL',
			)
		);

		// 3. Past poll results (only polls that actually got votes).
		$su_recent = function_exists( 'studentup_poll_recent' ) ? studentup_poll_recent( 7 ) : array();
		if ( $su_recent ) :
			?>
			<section class="su-railed" aria-label="<?php esc_attr_e( 'Recent poll results', 'studentup' ); ?>" style="margin-top:22px">
				<h2 style="font-size:18px;margin:0 0 10px"><?php esc_html_e( 'How readers voted this week', 'studentup' ); ?></h2>
				<ul class="su-mini">
					<?php foreach ( $su_recent as $su_r ) : ?>
						<li>
							<b><?php echo esc_html( $su_r['date'] ); ?></b> — <?php echo esc_html( $su_r['q'] ); ?>
							<br><small><?php echo esc_html( $su_r['win'] ); ?> · <?php echo esc_html( (string) $su_r['pct'] ); ?>% of <?php echo esc_html( number_format_i18n( $su_r['total'] ) ); ?> votes</small>
						</li>
					<?php endforeach; ?>
				</ul>
			</section>
		<?php endif; ?>

		<section class="su-railed" aria-label="<?php esc_attr_e( 'How this works', 'studentup' ); ?>" style="margin-top:22px">
			<h2 style="font-size:18px;margin:0 0 10px"><?php esc_html_e( 'How the daily quiz works', 'studentup' ); ?></h2>
			<ul class="su-mini">
				<li><?php esc_html_e( 'Questions rotate every day and are sourced from official notifications (SSC, TSPSC, APPSC, IBPS, Railways).', 'studentup' ); ?></li>
				<li><?php esc_html_e( 'Every answer has a one-line explanation and the source — so you learn, not just guess.', 'studentup' ); ?></li>
				<li><?php esc_html_e( 'Your score and streak stay in your browser. We never see them and never ask for a phone number.', 'studentup' ); ?></li>
				<li><?php esc_html_e( 'Polls are open (not scientific): only the count is stored, never who voted.', 'studentup' ); ?></li>
			</ul>
			<?php
			// Internal links: keep readers in the habit loop (quiz → current affairs → jobs).
			$su_ca   = studentup_used_term( 'current-affairs' );
			$su_jobs = studentup_used_term( 'ts-jobs' );
			?>
			<p class="su-ic-page-actions">
				<?php if ( $su_ca ) : ?>
					<a class="su-cta su-cta--ghost" href="<?php echo esc_url( get_category_link( $su_ca ) ); ?>"><?php esc_html_e( 'Daily current affairs →', 'studentup' ); ?></a>
				<?php endif; ?>
				<?php if ( $su_jobs ) : ?>
					<a class="su-cta su-cta--ghost" href="<?php echo esc_url( get_category_link( $su_jobs ) ); ?>"><?php esc_html_e( 'Today\'s Telangana jobs →', 'studentup' ); ?></a>
				<?php endif; ?>
				<?php $su_tools = studentup_mega_page_url( array( 'tools' ) ); ?>
				<?php if ( $su_tools ) : ?>
					<a class="su-cta su-cta--ghost" href="<?php echo esc_url( $su_tools ); ?>"><?php esc_html_e( 'Free exam tools →', 'studentup' ); ?></a>
				<?php endif; ?>
			</p>
		</section>

		<?php studentup_ad( 'below-content' ); // ad slot — page footer, content tarvata mattrame. ?>
	<?php endwhile; ?>
</main>
<?php
get_footer();
