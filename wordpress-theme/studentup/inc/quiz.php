<?php
/**
 * v197 DAILY QUIZ v2 — real quiz (v123 lo render avvatledu, ippudu FULL).
 *
 * Enduku rewrite:
 *  · v123 `studentup_daily_quiz()` **eppudu call avvaledu** — front page lo quiz
 *    ledu, preview lo `href="#quiz"` dead link. Ippudu front-page + /daily-quiz/
 *    page rendu chotla render avutundi.
 *  · Server-side HTML: prathi question + 4 options + explanation markup lo ne
 *    untayi → **JS lekapoyina quiz pani chestundi** (form submit → server score),
 *    Google ki crawlable text, reader ki instant paint (JS ki wait ledu).
 *  · JS (`studentup-engage.js`) unte: instant grading, streak, share, keyboard
 *    1–4. JS ledu aithe: radios + "Check answers" button → same result.
 *  · Quiz JSON-LD schema (valid `Quiz` + `Question`), honest — practice content,
 *    government exam claims ledu.
 *  · No personal data: score localStorage lo mattrame (server ki vote ledu).
 *
 * Telugu ledu (v73 invariant) — UI + questions English.
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Question bank. Each: q, a[4], c (correct index), why, cat, src.
 *
 * `src` = official/verifiable source name (E-E-A-T: answer ki proof).
 *
 * @return array<int,array<string,mixed>>
 */
function studentup_quiz_bank() {
	$bank = array(
		array( 'q' => 'Telangana state formation day?', 'a' => array( '1 November 1956', '2 June 2014', '15 August 1947', '26 January 1950' ), 'c' => 1, 'why' => 'Telangana became India\'s 29th state on 2 June 2014.', 'cat' => 'Telangana', 'src' => 'Telangana government' ),
		array( 'q' => 'SSC CGL exam is conducted by?', 'a' => array( 'UPSC', 'Staff Selection Commission', 'RRB', 'IBPS' ), 'c' => 1, 'why' => 'SSC conducts CGL for Group B and C central posts.', 'cat' => 'Central', 'src' => 'ssc.gov.in' ),
		array( 'q' => 'Which bank is India\'s central bank?', 'a' => array( 'SBI', 'NABARD', 'Reserve Bank of India', 'ICICI' ), 'c' => 2, 'why' => 'RBI, established 1935, is the central bank.', 'cat' => 'Banking', 'src' => 'rbi.org.in' ),
		array( 'q' => 'Capital of Andhra Pradesh (de facto, 2026)?', 'a' => array( 'Amaravati', 'Vizag', 'Kurnool', 'Tirupati' ), 'c' => 0, 'why' => 'Amaravati is the declared capital of Andhra Pradesh.', 'cat' => 'Andhra Pradesh', 'src' => 'AP government' ),
		array( 'q' => 'APPSC Group-1 mains ki qualification?', 'a' => array( '10th pass', 'Intermediate', 'Any degree', 'Post graduation' ), 'c' => 2, 'why' => 'Any bachelor degree is the base eligibility for Group-1.', 'cat' => 'Andhra Pradesh', 'src' => 'psc.ap.gov.in' ),
		array( 'q' => 'Which article deals with Right to Education?', 'a' => array( 'Article 21A', 'Article 19', 'Article 32', 'Article 44' ), 'c' => 0, 'why' => 'Article 21A guarantees free education for ages 6–14.', 'cat' => 'Polity', 'src' => 'Constitution of India' ),
		array( 'q' => 'RRB NTPC lo NTPC ante?', 'a' => array( 'National Technical Power Cell', 'Non-Technical Popular Categories', 'New Train Post Cadre', 'National Transport Public Cell' ), 'c' => 1, 'why' => 'NTPC = Non-Technical Popular Categories.', 'cat' => 'Railways', 'src' => 'indianrailways.gov.in' ),
		array( 'q' => 'IBPS PO selection lo final stage?', 'a' => array( 'Prelims', 'Mains', 'Interview', 'Typing test' ), 'c' => 2, 'why' => 'Prelims → Mains → Interview is the IBPS PO flow.', 'cat' => 'Banking', 'src' => 'ibps.in' ),
		array( 'q' => 'Largest river in South India?', 'a' => array( 'Krishna', 'Godavari', 'Kaveri', 'Tungabhadra' ), 'c' => 1, 'why' => 'Godavari is the longest peninsular river.', 'cat' => 'Geography', 'src' => 'NCERT' ),
		array( 'q' => 'National Scholarship Portal ni run chesedi?', 'a' => array( 'State governments only', 'Ministry of Education, Govt of India', 'UGC', 'NITI Aayog' ), 'c' => 1, 'why' => 'NSP is run by the Ministry of Education for central schemes.', 'cat' => 'Scholarships', 'src' => 'scholarships.gov.in' ),
		array( 'q' => 'UPSC Civil Services prelims lo papers enni?', 'a' => array( '1', '2', '3', '4' ), 'c' => 1, 'why' => 'GS Paper-I and CSAT Paper-II.', 'cat' => 'UPSC', 'src' => 'upsc.gov.in' ),
		array( 'q' => 'Hall ticket ki inko peru?', 'a' => array( 'Answer key', 'Admit card', 'Merit list', 'Cut-off' ), 'c' => 1, 'why' => 'Hall ticket = admit card, exam ki entry pass.', 'cat' => 'Exams', 'src' => 'Exam notifications' ),
		array( 'q' => 'TSPSC headquarters ekkada?', 'a' => array( 'Warangal', 'Hyderabad', 'Karimnagar', 'Nizamabad' ), 'c' => 1, 'why' => 'TSPSC office is in Hyderabad.', 'cat' => 'Telangana', 'src' => 'tspsc.gov.in' ),
		array( 'q' => 'Which exam is for banking clerks?', 'a' => array( 'IBPS Clerk', 'NEET', 'JEE', 'CAT' ), 'c' => 0, 'why' => 'IBPS Clerk recruits clerical cadre in public sector banks.', 'cat' => 'Banking', 'src' => 'ibps.in' ),
		array( 'q' => 'Indian Constitution adopted on?', 'a' => array( '26 Nov 1949', '15 Aug 1947', '26 Jan 1950', '2 Oct 1950' ), 'c' => 0, 'why' => 'Adopted 26 Nov 1949, came into force 26 Jan 1950.', 'cat' => 'Polity', 'src' => 'Constitution of India' ),
		array( 'q' => 'TS EAMCET counselling ni naduputundi?', 'a' => array( 'TSCHE', 'UGC', 'AICTE', 'NTA' ), 'c' => 0, 'why' => 'Telangana State Council of Higher Education runs EAMCET counselling.', 'cat' => 'Telangana', 'src' => 'tseamcet.nic.in' ),
		array( 'q' => 'SSC CHSL lo minimum qualification?', 'a' => array( '10th pass', 'Intermediate', 'Degree', 'PG' ), 'c' => 1, 'why' => 'CHSL (LDC/DEO) requires Intermediate (12th).', 'cat' => 'Central', 'src' => 'ssc.gov.in' ),
		array( 'q' => 'Panchayat Secretary (TS) recruit chesedi?', 'a' => array( 'TSPSC', 'SSC', 'RRB', 'APPSC' ), 'c' => 0, 'why' => 'TSPSC recruits for Telangana state panchayat posts.', 'cat' => 'Telangana', 'src' => 'tspsc.gov.in' ),
		array( 'q' => 'Which one is a central armed police force?', 'a' => array( 'CRPF', 'TSSP', 'APSP', 'Gurukul' ), 'c' => 0, 'why' => 'CRPF is a central armed police force under the Ministry of Home Affairs.', 'cat' => 'Defence', 'src' => 'mha.gov.in' ),
		array( 'q' => 'NSP scholarship ki Aadhaar linkage avasarama?', 'a' => array( 'Avasaram ledu', 'Avasaram (DBT ki)', 'Only for girls', 'Only for PG' ), 'c' => 1, 'why' => 'DBT transfer ki bank account + Aadhaar seeding kavali.', 'cat' => 'Scholarships', 'src' => 'scholarships.gov.in' ),
		array( 'q' => 'Railway Group D selection lo first stage?', 'a' => array( 'CBT', 'Interview', 'PET', 'Document verification' ), 'c' => 0, 'why' => 'Computer Based Test (CBT) is the first stage; then PET/DV.', 'cat' => 'Railways', 'src' => 'rrbcdg.gov.in' ),
		array( 'q' => 'Chief Minister of a state ni appoint chesedi?', 'a' => array( 'President', 'Governor', 'Chief Justice', 'Speaker' ), 'c' => 1, 'why' => 'The Governor appoints the Chief Minister.', 'cat' => 'Polity', 'src' => 'Constitution of India' ),
		array( 'q' => 'India Post GDS recruitment ki age limit (general, years)?', 'a' => array( '18–40', '18–30', '21–30', '18–27' ), 'c' => 3, 'why' => 'General category GDS upper limit is 27 years; OBC 30, SC/ST 32.', 'cat' => 'Central', 'src' => 'indiapostgdsonline.gov.in' ),
		array( 'q' => 'Digital India land records portal peru?', 'a' => array( 'DILRMP', 'NSP', 'ePASS', 'DigiLocker' ), 'c' => 0, 'why' => 'DILRMP digitises land records across states.', 'cat' => 'Schemes', 'src' => 'dilrmp.gov.in' ),
		array( 'q' => 'Odisha lo anna scholarships ni e-portal?', 'a' => array( 'ePASS', 'NSP only', 'eKYC', 'SIMS' ), 'c' => 0, 'why' => 'ePASS (Telangana) / state portals handle state-level scholarship applications.', 'cat' => 'Scholarships', 'src' => 'telanganaepass.cgg.gov.in' ),
	);
	/**
	 * Filter: add your own questions (site owner / coaching partner).
	 *
	 * @param array<int,array<string,mixed>> $bank Question bank.
	 */
	return apply_filters( 'studentup_quiz_bank', $bank );
}

/**
 * Today's questions — same for everyone, rotates daily (date seed).
 *
 * @param int $count How many questions (default 5).
 * @param int $shift Day offset (practice mode: yesterday = -1).
 * @return array<int,array<string,mixed>>
 */
function studentup_quiz_today( $count = 5, $shift = 0 ) {
	$bank = array_values( studentup_quiz_bank() );
	$n    = count( $bank );
	if ( ! $n ) {
		return array();
	}
	$count  = max( 1, min( 10, (int) $count ) );
	$shift  = (int) $shift;
	$now    = current_time( 'timestamp' );
	$day    = (int) gmdate( 'z', $now ) + ( (int) gmdate( 'Y', $now ) * 366 ) + $shift;
	$out    = array();
	$take   = min( $count, $n );
	for ( $i = 0; $i < $take; $i++ ) {
		$out[] = $bank[ ( $day * 5 + $i * 7 ) % $n ];
	}
	/**
	 * Filter: replace today's set (e.g. current-affairs questions from a post).
	 *
	 * @param array<int,array<string,mixed>> $out   Questions.
	 * @param int                            $shift Day offset.
	 */
	return apply_filters( 'studentup_quiz_today', $out, $shift );
}

/**
 * No-JS path: read + verify the quiz form (never fatal, never stores data).
 *
 * @return array<int,int> picked answers (question index => option index).
 */
function studentup_quiz_answers_from_post() {
	if ( empty( $_POST['su_quiz_nonce'] ) ) {
		return array();
	}
	$nonce = sanitize_text_field( wp_unslash( $_POST['su_quiz_nonce'] ) );
	if ( ! wp_verify_nonce( $nonce, 'su_quiz_submit' ) ) {
		return array();
	}
	$out = array();
	foreach ( studentup_quiz_today() as $i => $q ) {
		$key = 'suq_' . (int) $i;
		if ( isset( $_POST[ $key ] ) ) {
			$val = absint( wp_unslash( $_POST[ $key ] ) );
			if ( $val >= 0 && $val < count( (array) $q['a'] ) ) {
				$out[ $i ] = $val;
			}
		}
	}
	return $out;
}

/**
 * Quiz JSON-LD (valid Quiz + Question). Honest: practice content, no claims.
 *
 * @param array<int,array<string,mixed>> $qs Questions.
 * @return string
 */
function studentup_quiz_schema( $qs ) {
	if ( ! $qs ) {
		return '';
	}
	$items = array();
	foreach ( $qs as $q ) {
		$ans = array();
		foreach ( (array) $q['a'] as $ai => $txt ) {
			$ans[] = array(
				'@type'        => 'Answer',
				'text'         => (string) $txt,
				'position'     => $ai,
				'isCorrect'    => ( (int) $q['c'] === (int) $ai ),
				'comment'      => (string) $q['why'],
			);
		}
		$items[] = array(
			'@type'           => 'Question',
			'name'            => (string) $q['q'],
			'eduQuestionType' => 'Multiple choice',
			'suggestedAnswer' => $ans,
			'acceptedAnswer'  => array(
				'@type'    => 'Answer',
				'text'     => (string) $q['a'][ (int) $q['c'] ],
				'position' => (int) $q['c'],
			),
		);
	}
	$graph = array(
		'@context'      => 'https://schema.org',
		'@type'         => 'Quiz',
		'name'          => 'StudentUp Daily Quiz — ' . date_i18n( 'M j, Y' ),
		'about'         => 'Government exam practice questions for Telangana, Andhra Pradesh and Central exams',
		'inLanguage'    => 'en-IN',
		'educationalLevel' => 'Intermediate to graduate',
		'hasPart'       => $items,
	);
	return wp_json_encode( $graph, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES );
}

/**
 * Render the daily quiz (server-side, JS-enhanced).
 *
 * @param array<string,mixed> $args Args: count, shift, id, heading, kicker.
 * @return void
 */
function studentup_daily_quiz( $args = array() ) {
	if ( ! studentup_opt( 'daily_quiz', '1' ) ) {
		return;
	}
	$args = wp_parse_args(
		$args,
		array(
			'count'   => 5,
			'shift'   => 0,
			'id'      => 'daily-quiz',
			'heading' => 'Roju 5 questions — 2 minutes chaalu',
			'kicker'  => 'DAILY QUIZ',
		)
	);
	$qs = studentup_quiz_today( (int) $args['count'], (int) $args['shift'] );
	if ( ! $qs ) {
		return;
	}
	$picked   = studentup_quiz_answers_from_post();
	$answered = array() !== $picked;
	$score    = 0;
	foreach ( $qs as $i => $q ) {
		if ( $answered && isset( $picked[ $i ] ) && (int) $picked[ $i ] === (int) $q['c'] ) {
			$score++;
		}
	}
	$cat   = studentup_used_term( 'daily-quiz' );
	$more  = $cat ? get_category_link( $cat ) : studentup_mega_page_url( array( 'daily-quiz', 'quiz' ) );
	$pct   = $answered ? (int) round( ( $score / max( 1, count( $qs ) ) ) * 100 ) : 0;
	$line  = $answered
		? sprintf( 'You scored %1$d of %2$d (%3$d%%)', $score, count( $qs ), $pct )
		: '';
	$share = rawurlencode( 'I scored ' . $score . '/' . count( $qs ) . ' in today\'s StudentUp Daily Quiz. Practice free: ' . home_url( '/' ) );
	?>
	<section class="su-quiz" id="<?php echo esc_attr( (string) $args['id'] ); ?>" aria-label="<?php esc_attr_e( 'Daily quiz', 'studentup' ); ?>">
		<div class="su-quiz-card">
			<div class="su-quiz-head">
				<div>
					<p class="su-quiz-kick"><?php echo esc_html( (string) $args['kicker'] ); ?> · <?php echo esc_html( date_i18n( 'M j, Y' ) ); ?></p>
					<h2><?php echo esc_html( (string) $args['heading'] ); ?></h2>
				</div>
				<div class="su-quiz-score" role="status" aria-live="polite">
					<b data-su-quiz-score><?php echo esc_html( (string) $score ); ?></b><span>/ <?php echo esc_html( (string) count( $qs ) ); ?></span>
				</div>
			</div>
			<div class="su-quiz-bar"><i data-su-quiz-bar style="width:<?php echo esc_attr( (string) ( $answered ? $pct : 0 ) ); ?>%"></i></div>

			<form method="post" class="su-quiz-form" data-su-quiz-form>
				<?php wp_nonce_field( 'su_quiz_submit', 'su_quiz_nonce' ); ?>
				<input type="hidden" name="su_quiz_submitted" value="1">
				<?php foreach ( $qs as $i => $q ) : ?>
					<?php
					$was   = $answered ? (int) ( $picked[ $i ] ?? -1 ) : -1;
					$right = (int) $q['c'];
					?>
					<fieldset class="su-q" data-c="<?php echo esc_attr( (string) $right ); ?>" data-i="<?php echo esc_attr( (string) $i ); ?>">
						<legend class="su-q-title"><span class="su-q-n"><?php echo esc_html( (string) ( $i + 1 ) ); ?></span> <?php echo esc_html( (string) $q['q'] ); ?></legend>
						<div class="su-q-opts">
							<?php foreach ( (array) $q['a'] as $ai => $txt ) : ?>
								<?php
								$cls = 'su-opt';
								if ( $answered ) {
									if ( $ai === $right ) {
										$cls .= ' right';
									} elseif ( $ai === $was ) {
										$cls .= ' wrong';
									}
								}
								?>
								<label class="<?php echo esc_attr( $cls ); ?>">
									<input type="radio" name="suq_<?php echo esc_attr( (string) $i ); ?>" value="<?php echo esc_attr( (string) $ai ); ?>"<?php checked( $was, (int) $ai ); ?>>
									<span class="su-opt-key"><?php echo esc_html( chr( 65 + (int) $ai ) ); ?></span>
									<span class="su-opt-t"><?php echo esc_html( (string) $txt ); ?></span>
								</label>
							<?php endforeach; ?>
						</div>
						<p class="su-why" data-su-why<?php echo esc_attr( $answered ? '' : ' hidden' ); ?>>
							<strong><?php esc_html_e( 'Why:', 'studentup' ); ?></strong> <?php echo esc_html( (string) $q['why'] ); ?>
							<?php if ( ! empty( $q['src'] ) ) : ?>
								<em>· <?php echo esc_html( (string) $q['src'] ); ?></em>
							<?php endif; ?>
						</p>
					</fieldset>
				<?php endforeach; ?>
				<div class="su-quiz-foot">
					<button type="submit" class="su-quiz-restart" data-su-quiz-check><?php echo studentup_ui_icon( 'check', 14 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> Check answers</button>
					<button type="button" class="su-quiz-restart" data-su-quiz-restart hidden><?php echo studentup_ui_icon( 'refresh', 13 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> Restart</button>
					<a class="su-quiz-more su-quiz-share" data-su-quiz-share rel="nofollow noopener" target="_blank"
						href="<?php echo esc_url( 'https://wa.me/?text=' . $share ); ?>" hidden><?php echo studentup_ui_icon( 'upload', 13 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> Share my score</a>
					<span class="su-quiz-streak" data-su-quiz-streak hidden></span>
					<?php if ( $more ) : ?>
						<a class="su-quiz-more" href="<?php echo esc_url( $more ); ?>">More practice questions →</a>
					<?php endif; ?>
				</div>
			</form>

			<?php if ( $answered ) : ?>
				<div class="su-quiz-done" role="status">
					<b><?php echo esc_html( $line ); ?></b>
					<p>
						<?php
						if ( $pct >= 80 ) {
							esc_html_e( 'Strong — keep this streak alive tomorrow.', 'studentup' );
						} elseif ( $pct >= 40 ) {
							esc_html_e( 'Decent start. Read the "why" lines once and retry.', 'studentup' );
						} else {
							esc_html_e( 'No problem — practice is the point. Try again tomorrow.', 'studentup' );
						}
						?>
					</p>
				</div>
			<?php endif; ?>
			<p class="su-quiz-legend"><?php esc_html_e( 'Answers are explained, not just marked. Score stays on your device — we do not store it.', 'studentup' ); ?></p>
		</div>
		<?php
		$json = studentup_quiz_schema( $qs );
		if ( $json ) {
			printf( '<script type="application/ld+json">%s</script>', $json ); // phpcs:ignore WordPress.Security.EscapeOutput -- wp_json_encode output
		}
		?>
	</section>
	<?php
}

/**
 * Days in the current month that already had a quiz (practice-mode links).
 *
 * @param int $days How many past days to expose.
 * @return array<int,string> ISO date => label.
 */
function studentup_quiz_recent_days( $days = 7 ) {
	$out = array();
	for ( $i = 1; $i <= max( 1, (int) $days ); $i++ ) {
		$ts  = current_time( 'timestamp' ) - ( $i * DAY_IN_SECONDS );
		$out[] = date_i18n( 'D, M j', $ts );
	}
	return $out;
}
