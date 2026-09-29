<?php
/**
 * v123 DAILY QUIZ — asalu quiz ledu ani problem; ippudu theme lone real quiz.
 *
 * · 5 questions per day, deterministic (date seed) — anduke andariki same quiz.
 * · Bank: `studentup_quiz_bank()` filter tho extend cheyyachu, or admin
 *   "Daily Quiz" category lo posts unte avi kuda link avutayi.
 * · Colorful rotating conic ring (CSS) — chutu thiriginattu.
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Question bank. Each: q, a[4], c (correct index), why.
 *
 * @return array<int,array<string,mixed>>
 */
function studentup_quiz_bank() {
	$bank = array(
		array( 'q' => 'Telangana state formation day?', 'a' => array( '1 November 1956', '2 June 2014', '15 August 1947', '26 January 1950' ), 'c' => 1, 'why' => 'Telangana became India\'s 29th state on 2 June 2014.' ),
		array( 'q' => 'SSC CGL exam is conducted by?', 'a' => array( 'UPSC', 'Staff Selection Commission', 'RRB', 'IBPS' ), 'c' => 1, 'why' => 'SSC conducts CGL for Group B and C central posts.' ),
		array( 'q' => 'Which bank is India\'s central bank?', 'a' => array( 'SBI', 'NABARD', 'Reserve Bank of India', 'ICICI' ), 'c' => 2, 'why' => 'RBI, established 1935, is the central bank.' ),
		array( 'q' => 'Capital of Andhra Pradesh (de facto, 2026)?', 'a' => array( 'Amaravati', 'Vizag', 'Kurnool', 'Tirupati' ), 'c' => 0, 'why' => 'Amaravati is the declared capital of Andhra Pradesh.' ),
		array( 'q' => 'APPSC Group-1 mains ki qualification?', 'a' => array( '10th pass', 'Intermediate', 'Any degree', 'Post graduation' ), 'c' => 2, 'why' => 'Any bachelor degree is the base eligibility for Group-1.' ),
		array( 'q' => 'Which article deals with Right to Education?', 'a' => array( 'Article 21A', 'Article 19', 'Article 32', 'Article 44' ), 'c' => 0, 'why' => 'Article 21A guarantees free education for ages 6–14.' ),
		array( 'q' => 'RRB NTPC lo NTPC ante?', 'a' => array( 'National Technical Power Cell', 'Non-Technical Popular Categories', 'New Train Post Cadre', 'National Transport Public Cell' ), 'c' => 1, 'why' => 'NTPC = Non-Technical Popular Categories.' ),
		array( 'q' => 'IBPS PO selection lo final stage?', 'a' => array( 'Prelims', 'Mains', 'Interview', 'Typing test' ), 'c' => 2, 'why' => 'Prelims → Mains → Interview is the IBPS PO flow.' ),
		array( 'q' => 'Largest river in South India?', 'a' => array( 'Krishna', 'Godavari', 'Kaveri', 'Tungabhadra' ), 'c' => 1, 'why' => 'Godavari is the longest peninsular river.' ),
		array( 'q' => 'National Scholarship Portal ni run chesedi?', 'a' => array( 'State governments only', 'Ministry of Education, Govt of India', 'UGC', 'NITI Aayog' ), 'c' => 1, 'why' => 'NSP is run by the Ministry of Education for central schemes.' ),
		array( 'q' => 'UPSC Civil Services prelims lo papers enni?', 'a' => array( '1', '2', '3', '4' ), 'c' => 1, 'why' => 'GS Paper-I and CSAT Paper-II.' ),
		array( 'q' => 'Hall ticket ki inko peru?', 'a' => array( 'Answer key', 'Admit card', 'Merit list', 'Cut-off' ), 'c' => 1, 'why' => 'Hall ticket = admit card, exam ki entry pass.' ),
		array( 'q' => 'TSPSC headquarters ekkada?', 'a' => array( 'Warangal', 'Hyderabad', 'Karimnagar', 'Nizamabad' ), 'c' => 1, 'why' => 'TSPSC office is in Hyderabad.' ),
		array( 'q' => 'Which exam is for banking clerks?', 'a' => array( 'IBPS Clerk', 'NEET', 'JEE', 'CAT' ), 'c' => 0, 'why' => 'IBPS Clerk recruits clerical cadre in public sector banks.' ),
		array( 'q' => 'Indian Constitution adopted on?', 'a' => array( '26 Nov 1949', '15 Aug 1947', '26 Jan 1950', '2 Oct 1950' ), 'c' => 0, 'why' => 'Adopted 26 Nov 1949, came into force 26 Jan 1950.' ),
	);
	/** Filter: site owners can add their own daily-quiz questions. */
	return apply_filters( 'studentup_quiz_bank', $bank );
}

/**
 * Today's 5 questions — same for everyone, rotates daily.
 *
 * @return array<int,array<string,mixed>>
 */
function studentup_quiz_today() {
	$bank = array_values( studentup_quiz_bank() );
	$n    = count( $bank );
	if ( ! $n ) {
		return array();
	}
	$day  = (int) gmdate( 'z', current_time( 'timestamp' ) ) + ( (int) gmdate( 'Y', current_time( 'timestamp' ) ) * 366 );
	$out  = array();
	$take = min( 5, $n );
	for ( $i = 0; $i < $take; $i++ ) {
		$out[] = $bank[ ( $day * 5 + $i * 7 ) % $n ];
	}
	return $out;
}

/**
 * Render the daily quiz card (colorful rotating ring + instant scoring).
 */
function studentup_daily_quiz() {
	if ( ! studentup_opt( 'daily_quiz', '1' ) ) {
		return;
	}
	$qs = studentup_quiz_today();
	if ( ! $qs ) {
		return;
	}
	$cat   = studentup_used_term( 'daily-quiz' );
	$more  = $cat ? get_category_link( $cat ) : '';
	$data  = array();
	foreach ( $qs as $q ) {
		$data[] = array(
			'q'   => (string) $q['q'],
			'a'   => array_map( 'strval', (array) $q['a'] ),
			'c'   => (int) $q['c'],
			'why' => (string) $q['why'],
		);
	}
	?>
	<section class="su-quiz" id="daily-quiz" aria-label="Daily quiz">
		<div class="su-quiz-ring" aria-hidden="true"></div>
		<div class="su-quiz-card">
			<div class="su-quiz-head">
				<div>
					<p class="su-quiz-kick">DAILY QUIZ · <?php echo esc_html( date_i18n( 'M j, Y' ) ); ?></p>
					<h2>Roju 5 questions — 2 nimishalu chaalu 🧠</h2>
				</div>
				<div class="su-quiz-score"><b data-su-quiz-score>0</b><span>/ <?php echo esc_html( count( $qs ) ); ?></span></div>
			</div>
			<div class="su-quiz-bar"><i data-su-quiz-bar style="width:0%"></i></div>
			<div class="su-quiz-body" data-su-quiz='<?php echo esc_attr( wp_json_encode( $data ) ); ?>'>
				<p class="su-quiz-loading">Loading today’s questions…</p>
			</div>
			<div class="su-quiz-foot">
				<button type="button" class="su-quiz-restart" data-su-quiz-restart>↻ Restart</button>
				<?php if ( $more ) : ?>
					<a class="su-quiz-more" href="<?php echo esc_url( $more ); ?>">More practice questions →</a>
				<?php endif; ?>
			</div>
		</div>
	</section>
	<?php
}
