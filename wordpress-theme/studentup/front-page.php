<?php
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}
?>
<?php
/**
 * Front page — design (preview/index.html) same order:
 * టికర్ → "విద్యార్థులు ఎక్కువగా వెతికేవి" → ప్రకటన → hero (countdown) →
 * బ్రేకింగ్ న్యూస్ → తాజా అవకాశాలు grid (chips filter) → footer.
 *
 * @package studentup
 */

get_header();
$su_deadline = studentup_deadline();
?>

<section class="usedwrap" aria-label="విద్యార్థులు ఎక్కువగా వెతికేవి">
	<div class="wrap">
		<div class="usedhead">
			<b>విద్యార్థులు ఎక్కువగా వెతికేవి</b>
			<span>ఒక్క ట్యాప్‌తో ఆ అవకాశాలన్నీ — తెలంగాణ · ఆంధ్రప్రదేశ్ ముందు</span>
		</div>
		<div class="usedgrid">
			<?php
			foreach ( studentup_most_used() as $i => $m ) :
				$term = get_category_by_slug( $m['slug'] );
				if ( ! $term ) {
					continue;
				}
				$count   = (int) $term->count;
				$hot     = ( $i < 2 ) ? ' hot' : '';
				$badge   = $count ? number_format_i18n( $count ) . ' అప్డేట్‌లు' : 'త్వరలో';
				?>
				<a class="usedcard<?php echo esc_attr( $hot ); ?>" href="<?php echo esc_url( get_category_link( $term ) ); ?>">
					<span class="ui" aria-hidden="true"><?php echo esc_html( $m['icon'] ); ?></span>
					<div><b><?php echo esc_html( $m['label'] ); ?></b><small><?php echo esc_html( $m['hint'] ); ?></small></div>
					<em class="ucount"><?php echo esc_html( $badge ); ?></em>
				</a>
			<?php endforeach; ?>
		</div>
	</div>
</section>

<div class="wrap"><?php studentup_ad( 'leaderboard' ); ?></div>

<section class="hero">
	<div class="wrap hero-grid">
		<div>
			<span class="eyebrow"><i aria-hidden="true"></i> ధృవీకృత విద్యార్థి అప్డేట్‌లు · తెలంగాణ + ఆంధ్రప్రదేశ్</span>
			<h1><?php echo esc_html( get_bloginfo( 'description' ) ? get_bloginfo( 'description' ) : 'తెలంగాణ & ఆంధ్రప్రదేశ్ విద్యార్థులకు ఉద్యోగాలు, స్కాలర్‌షిప్‌లు, ఫలితాలు' ); ?> — <em>నమ్మదగిన ఒకే వేదిక.</em></h1>
			<p class="lede">అధికారిక మూలాలతో పరిశీలించి, సులభ తెలుగులో వివరిస్తాము. ఫేక్ పోర్టల్‌ల నుండి రక్షణ చర్యలు ఇక్కడే.</p>
			<div class="hero-actions">
				<a class="bluebtn" href="#jobs">అవకాశాలు చూడండి →</a>
				<?php if ( get_option( 'studentup_exam_url' ) ) : ?>
					<a class="ghostbtn" href="<?php echo esc_url( (string) get_option( 'studentup_exam_url' ) ); ?>">🎓 ప్రత్యక్ష పరీక్షల పోర్టల్</a>
				<?php endif; ?>
			</div>
		</div>
		<div class="hero-card">
			<div class="hcard-top"><span class="hcard-title">ముఖ్య గడువు</span><span class="live">● లైవ్ కౌంట్‌డౌన్</span></div>
			<?php if ( ! empty( $su_deadline['date'] ) ) : ?>
				<div class="deadline">
					<small>ముఖ్య గడువు</small>
					<h3><?php echo esc_html( $su_deadline['title'] ? $su_deadline['title'] : 'దరఖాస్తు కాలం ముగుస్తోంది' ); ?></h3>
					<div class="timer" role="timer" data-deadline="<?php echo esc_attr( $su_deadline['date'] ); ?>">
						<div class="time"><b data-cd="d">--</b><span>రోజులు</span></div>
						<div class="time"><b data-cd="h">--</b><span>గంటలు</span></div>
						<div class="time"><b data-cd="m">--</b><span>నిమిషాలు</span></div>
						<div class="time"><b data-cd="s">--</b><span>సెకన్లు</span></div>
					</div>
				</div>
				<p class="hcard-note">తుది తేదీని అధికారిక నోటిఫికేషన్‌లో నిర్ధారించుకోండి.</p>
			<?php else : ?>
				<div class="deadline">
					<small>ఎప్పుడూ అప్డేట్</small>
					<h3>రోజూ కొత్త ఉద్యోగ, పరీక్ష అప్డేట్‌లు — అధికారిక మూలాలతో</h3>
				</div>
				<p class="hcard-note">గడువు కౌంట్‌డౌన్ కోసం బాట్ <code>studentup_deadline_json</code> option set chestundi.</p>
			<?php endif; ?>
			<div class="hcard-row"><span class="mini-icon" aria-hidden="true">✓</span><div><b>అర్హత వివరాలు</b><span>విద్యార్హత · వయస్సు · ఫీజు మినహాయింపు · పత్రాలు</span></div></div>
			<div class="hcard-row"><span class="mini-icon" aria-hidden="true">↗</span><div><b>మూలం ధృవీకృతం</b><span>అధికారిక .gov.in నోటిఫికేషన్‌లు మాత్రమే</span></div></div>
		</div>
	</div>
</section>

<main id="main">
	<div class="wrap">
		<?php studentup_breaking_section(); ?>

		<div class="sectionhead" id="jobs">
			<div>
				<h2>తాజా అవకాశాలు</h2>
				<p>ఫాక్ట్-చెక్ చేసిన మార్గదర్శకాలు — తెలంగాణ · ఆంధ్రప్రదేశ్ · కేంద్ర</p>
			</div>
		</div>

		<div class="chips" id="chips" role="tablist" aria-label="విభాగ ఫిల్టర్లు">
			<button type="button" class="chip active" data-cat="all" role="tab" aria-selected="true">అన్నీ</button>
			<?php foreach ( studentup_most_used() as $m ) : ?>
				<button type="button" class="chip" data-cat="<?php echo esc_attr( sanitize_html_class( $m['slug'] ) ); ?>" role="tab" aria-selected="false"><?php echo esc_html( $m['label'] ); ?></button>
			<?php endforeach; ?>
		</div>

		<div class="newsgrid" id="grid">
			<?php
			$su_q = new WP_Query(
				array(
					'post_type'           => 'post',
					'posts_per_page'      => 12,
					'ignore_sticky_posts' => false,
					'no_found_rows'       => true,   // v69 perf: pagination ledu → extra SQL query vaddu
				)
			);
			$su_i = 0;
			if ( $su_q->have_posts() ) :
				while ( $su_q->have_posts() ) :
					$su_q->the_post();
					if ( 4 === $su_i ) {
						studentup_ad( 'in-feed' );
					}
					studentup_card( $su_i );
					$su_i++;
				endwhile;
			else :
				?>
				<p class="nores" style="display:block">ఇంకా పోస్టులు లేవు — బాట్ మొదటి అప్డేట్ రాస్తుంది. త్వరలో వస్తాయి.</p>
			<?php endif; ?>
		</div>
		<p class="nores" id="nores">ఈ ఫిల్టర్‌కు అవకాశాలు లేవు — "అన్నీ" ట్యాబ్‌కు వెళ్లి మళ్లీ ప్రయత్నించండి.</p>

		<?php studentup_ad( 'mid' ); ?>

		<nav class="sectionhead" aria-label="పోస్ట్ పేజీలు">
			<div><?php next_posts_link( 'పాత అప్డేట్‌లు →', $su_q->max_num_pages ); ?></div>
		</nav>
	</div>
</main>

<?php
wp_reset_postdata();
get_footer();
