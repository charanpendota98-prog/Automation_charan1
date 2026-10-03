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
		array( 'q' => 'Quantitative Aptitude: A train 240 m long crosses a telegraph pole in 12 seconds. What is the speed of the train in km/h?', 'a' => array( '60 km/h', '72 km/h', '54 km/h', '80 km/h' ), 'c' => 1, 'why' => 'Speed = 240m / 12s = 20 m/s. In km/h: 20 * (18/5) = 72 km/h.', 'cat' => 'Aptitude', 'src' => 'SSC CGL / Quantitative Aptitude', 'exam' => 'ssc,rrb,banking' ),
		array( 'q' => 'Logical Reasoning: If \'PAPER\' is coded as \'QBQFS\', how is \'OFFICE\' coded in that logic?', 'a' => array( 'PGGIDF', 'PGGJDF', 'NFFHBD', 'QHHJEG' ), 'c' => 1, 'why' => 'Each letter is shifted forward by +1: O->P, F->G, F->G, I->J, C->D, E->F.', 'cat' => 'Reasoning', 'src' => 'Logical Reasoning / SSC CGL', 'exam' => 'ssc,rrb' ),
		array( 'q' => 'Banking & Economy: Which policy rate does the RBI adjust to inject short-term liquidity into commercial banks?', 'a' => array( 'Reverse Repo Rate', 'Cash Reserve Ratio (CRR)', 'Repo Rate', 'Statutory Liquidity Ratio (SLR)' ), 'c' => 2, 'why' => 'Repo Rate is the interest rate at which RBI lends short-term funds to commercial banks against government securities to infuse liquidity.', 'cat' => 'Banking', 'src' => 'rbi.org.in', 'exam' => 'banking' ),
		array( 'q' => 'Indian Polity: Under which Article can a citizen approach the Supreme Court directly for enforcement of Fundamental Rights?', 'a' => array( 'Article 32', 'Article 226', 'Article 131', 'Article 143' ), 'c' => 0, 'why' => 'Article 32 guarantees the Right to Constitutional Remedies, empowering the Supreme Court to issue writs.', 'cat' => 'Polity', 'src' => 'Constitution of India', 'exam' => 'tspsc,appsc,ssc' ),
		array( 'q' => 'General Studies: Which Constitutional Amendment Act introduced the nationwide Goods and Services Tax (GST) in India?', 'a' => array( '100th Amendment Act', '101st Amendment Act', '102nd Amendment Act', '103rd Amendment Act' ), 'c' => 1, 'why' => 'The 101st Constitutional Amendment Act, 2016 introduced the unified GST nationwide from 1 July 2017.', 'cat' => 'Economy', 'src' => 'Ministry of Finance', 'exam' => 'all' ),
		array( 'q' => 'Quantitative Aptitude: If the cost price of 15 articles is equal to the selling price of 12 articles, what is the profit percentage?', 'a' => array( '20%', '25%', '30%', '16.66%' ), 'c' => 1, 'why' => 'Profit = (15 - 12) / 12 * 100 = 3/12 * 100 = 25%.', 'cat' => 'Aptitude', 'src' => 'Quantitative Aptitude / Banking', 'exam' => 'banking,ssc' ),
		array( 'q' => 'Logical Reasoning: In a row of 35 students, Ramesh is 12th from the left end. What is his position from the right end?', 'a' => array( '23rd', '24th', '25th', '22nd' ), 'c' => 1, 'why' => 'Right position = (Total - Left position) + 1 = (35 - 12) + 1 = 23 + 1 = 24th.', 'cat' => 'Reasoning', 'src' => 'Logical Reasoning / Ranking', 'exam' => 'ssc,rrb' ),
		array( 'q' => 'Indian Polity: Which Schedule of the Indian Constitution contains provisions regarding disqualification on grounds of defection (Anti-Defection Law)?', 'a' => array( '8th Schedule', '9th Schedule', '10th Schedule', '11th Schedule' ), 'c' => 2, 'why' => 'The 10th Schedule was added by the 52nd Constitutional Amendment Act, 1985.', 'cat' => 'Polity', 'src' => 'Constitution of India', 'exam' => 'tspsc,appsc,ssc' ),
		array( 'q' => 'Telangana History: The historic Ramappa Temple (Rudreshwara), inscribed as a UNESCO World Heritage site, was constructed during the reign of which Kakatiya ruler?', 'a' => array( 'Prataparudra', 'Ganapati Deva', 'Rani Rudrama Devi', 'Prolaraja II' ), 'c' => 1, 'why' => 'Ramappa temple was built in 1213 CE by Recharla Rudra, a general of Kakatiya king Ganapati Deva.', 'cat' => 'Telangana', 'src' => 'Telangana State Archaeology', 'exam' => 'tspsc' ),
		array( 'q' => 'Indian Economy: Which institution releases the Consumer Price Index (CPI) combined inflation data in India?', 'a' => array( 'RBI', 'NITI Aayog', 'National Statistical Office (NSO)', 'Department of Financial Services' ), 'c' => 2, 'why' => 'NSO under the Ministry of Statistics and Programme Implementation (MoSPI) releases monthly CPI numbers.', 'cat' => 'Economy', 'src' => 'mospi.gov.in', 'exam' => 'banking,ssc,appsc,tspsc' ),
		array( 'q' => 'General Science: What is the primary propellant combination used in the cryogenic upper stage of ISRO’s LVM3 (GSLV Mk-III) rocket?', 'a' => array( 'Solid HTPB', 'Liquid UDMH + N2O4', 'Liquid Hydrogen (LH2) + Liquid Oxygen (LOX)', 'Kerosene + Liquid Oxygen' ), 'c' => 2, 'why' => 'The C25 cryogenic stage burns liquid hydrogen at -253 deg C and liquid oxygen at -183 deg C.', 'cat' => 'Science', 'src' => 'isro.gov.in', 'exam' => 'rrb,tspsc,appsc,ssc' ),
		array( 'q' => 'Quantitative Aptitude: A sum of money doubles itself in 5 years at simple interest. What is the annual rate of interest?', 'a' => array( '15%', '20%', '25%', '10%' ), 'c' => 1, 'why' => 'SI = P. P = (P * R * 5)/100 => R = 100/5 = 20% per annum.', 'cat' => 'Aptitude', 'src' => 'Quantitative Aptitude', 'exam' => 'ssc,banking,rrb' ),
		array( 'q' => 'Logical Reasoning: Pointing to a photograph, a woman says: "He is the only son of my father-in-law\'s only son." How is the person in the photograph related to her?', 'a' => array( 'Husband', 'Brother', 'Son', 'Nephew' ), 'c' => 2, 'why' => 'Father-in-law\'s only son is her husband. The only son of her husband is her son.', 'cat' => 'Reasoning', 'src' => 'Logical Reasoning / Blood Relations', 'exam' => 'ssc,banking,tspsc,appsc' ),
		array( 'q' => 'Indian Polity: The Comptroller and Auditor General of India (CAG) submits audit reports relating to the accounts of the Union to whom?', 'a' => array( 'Prime Minister', 'Finance Minister', 'President of India', 'Speaker of Lok Sabha' ), 'c' => 2, 'why' => 'Under Article 151, CAG reports relating to the accounts of the Union are submitted to the President, who causes them to be laid before Parliament.', 'cat' => 'Polity', 'src' => 'Constitution of India', 'exam' => 'tspsc,appsc,ssc' ),
		array( 'q' => 'Andhra Pradesh & Geography: The Polavaram Major Multi-purpose National Irrigation Project is being constructed across which river?', 'a' => array( 'Krishna', 'Godavari', 'Pennar', 'Vamsadhara' ), 'c' => 1, 'why' => 'Polavaram Dam is constructed across the Godavari river in Eluru/Alluri Sitharama Raju districts of AP.', 'cat' => 'Andhra Pradesh', 'src' => 'AP Irrigation Dept', 'exam' => 'appsc' ),
		array( 'q' => 'Banking Awareness: In banking terminology, what does the abbreviation \'RTGS\' stand for?', 'a' => array( 'Real Time Gross Settlement', 'Rapid Transfer Government Scheme', 'Real Time General Settlement', 'Regional Treasury Guarantee System' ), 'c' => 0, 'why' => 'RTGS stands for Real Time Gross Settlement, continuous settlement of funds transfers individually on an order by order basis.', 'cat' => 'Banking', 'src' => 'rbi.org.in', 'exam' => 'banking' ),
		array( 'q' => 'Quantitative Aptitude: Two pipes A and B can fill a tank in 20 minutes and 30 minutes respectively. If both pipes are opened together, how long will they take to fill the tank?', 'a' => array( '10 minutes', '12 minutes', '15 minutes', '18 minutes' ), 'c' => 1, 'why' => '1/20 + 1/30 = (3+2)/60 = 5/60 = 1/12. Together they take 12 minutes.', 'cat' => 'Aptitude', 'src' => 'Quantitative Aptitude / Time & Work', 'exam' => 'ssc,rrb,banking' ),
		array( 'q' => 'Indian Polity: Who presides over a Joint Sitting of both Houses of Parliament convened under Article 108?', 'a' => array( 'President of India', 'Vice-President of India', 'Speaker of the Lok Sabha', 'Prime Minister' ), 'c' => 2, 'why' => 'Under Article 118(4), the Speaker of the Lok Sabha presides over a joint sitting of Parliament.', 'cat' => 'Polity', 'src' => 'Constitution of India', 'exam' => 'tspsc,appsc,ssc' ),
		array( 'q' => 'Telangana Movement: The historic \'Gentlemen’s Agreement\' was signed in which year prior to the formation of Andhra Pradesh?', 'a' => array( '1952', '1956', '1969', '1948' ), 'c' => 1, 'why' => 'The Gentlemen\'s Agreement was signed on 20 February 1956 in New Delhi, providing safeguards to the Telangana region.', 'cat' => 'Telangana', 'src' => 'Telangana History / TSPSC', 'exam' => 'tspsc' ),
		array( 'q' => 'General Science: Which vitamin is chemically known as Ascorbic Acid and plays a vital role in collagen synthesis and iron absorption?', 'a' => array( 'Vitamin A', 'Vitamin B12', 'Vitamin C', 'Vitamin D' ), 'c' => 2, 'why' => 'Ascorbic acid is Vitamin C. Its severe deficiency causes scurvy.', 'cat' => 'Science', 'src' => 'NCERT Biology', 'exam' => 'rrb,ssc,tspsc,appsc' ),
		array( 'q' => 'Logical Reasoning: Find the missing number in the series: 3, 7, 15, 31, 63, ?', 'a' => array( '125', '127', '129', '131' ), 'c' => 1, 'why' => 'Pattern: *2 + 1. 3*2+1=7, 7*2+1=15, 15*2+1=31, 31*2+1=63, 63*2+1=127.', 'cat' => 'Reasoning', 'src' => 'Logical Reasoning / Number Series', 'exam' => 'ssc,banking,rrb' ),
		array( 'q' => 'Indian Economy: What is the maximum insurance cover provided per depositor per bank by the DICGC in India?', 'a' => array( 'Rs. 1,00,000', 'Rs. 2,00,000', 'Rs. 5,00,000', 'Rs. 10,00,000' ), 'c' => 2, 'why' => 'DICGC (RBI subsidiary) insures principal and interest up to Rs. 5 lakh per depositor across commercial and cooperative banks.', 'cat' => 'Banking', 'src' => 'dicgc.org.in', 'exam' => 'banking' ),
		array( 'q' => 'Indian Polity: By which Constitutional Amendment Act was the voting age reduced from 21 years to 18 years in India?', 'a' => array( '42nd Amendment Act', '44th Amendment Act', '61st Amendment Act', '73rd Amendment Act' ), 'c' => 2, 'why' => 'The 61st Constitutional Amendment Act, 1988 lowered the voting age for Lok Sabha and Legislative Assemblies from 21 to 18.', 'cat' => 'Polity', 'src' => 'Constitution of India', 'exam' => 'tspsc,appsc,ssc' ),
		array( 'q' => 'Central Schemes: Which flagship scheme provides an annual financial benefit of Rs. 6,000 in three equal installments to eligible farmer families?', 'a' => array( 'PM Fasal Bima Yojana', 'PM-KISAN Samman Nidhi', 'PM Krishi Sinchayee Yojana', 'PM Kisan Maandhan Yojana' ), 'c' => 1, 'why' => 'PM-KISAN provides Rs. 6,000 per year directly transferred to farmers\' bank accounts in three 4-monthly installments of Rs. 2,000.', 'cat' => 'Schemes', 'src' => 'pmkisan.gov.in', 'exam' => 'all' ),
		array( 'q' => 'Quantitative Aptitude: The ratio of ages of two persons A and B is 3:4. Four years hence, the ratio will become 4:5. What is the present age of A?', 'a' => array( '12 years', '16 years', '18 years', '20 years' ), 'c' => 0, 'why' => '(3x + 4)/(4x + 4) = 4/5 => 15x + 20 = 16x + 16 => x = 4. Present age of A = 3 * 4 = 12 years.', 'cat' => 'Aptitude', 'src' => 'Quantitative Aptitude / Ratios', 'exam' => 'ssc,banking,tspsc,appsc' ),
		array( 'q' => 'Geography & Environment: In which state is the Nagarjunasagar-Srisailam Tiger Reserve, the largest tiger reserve in India by area, situated?', 'a' => array( 'Telangana & Andhra Pradesh', 'Madhya Pradesh', 'Karnataka', 'Maharashtra' ), 'c' => 0, 'why' => 'Nagarjunasagar-Srisailam Tiger Reserve spans the Nallamala forest across both Andhra Pradesh and Telangana.', 'cat' => 'Geography', 'src' => 'National Tiger Conservation Authority', 'exam' => 'tspsc,appsc' ),
		array( 'q' => 'Indian Polity: Which Article of the Indian Constitution empowers the President of India to promulgate Ordinances during the recess of Parliament?', 'a' => array( 'Article 110', 'Article 123', 'Article 213', 'Article 356' ), 'c' => 1, 'why' => 'Article 123 empowers the President to issue Ordinances when either House is not in session. Article 213 empowers Governors.', 'cat' => 'Polity', 'src' => 'Constitution of India', 'exam' => 'tspsc,appsc,ssc' ),
		array( 'q' => 'Economy: What type of deficit is calculated by deducting interest payments from the Fiscal Deficit?', 'a' => array( 'Revenue Deficit', 'Monetized Deficit', 'Primary Deficit', 'Effective Revenue Deficit' ), 'c' => 2, 'why' => 'Primary Deficit = Fiscal Deficit - Interest Payments.', 'cat' => 'Economy', 'src' => 'Union Budget / Finance Ministry', 'exam' => 'banking,ssc,appsc,tspsc' ),
		array( 'q' => 'Logical Reasoning: If South-East becomes North, North-East becomes West, and so on, what will West become?', 'a' => array( 'North-East', 'South-East', 'North-West', 'South-West' ), 'c' => 1, 'why' => 'Each direction is rotated 135 degrees clockwise. West rotated 135 degrees clockwise becomes South-East.', 'cat' => 'Reasoning', 'src' => 'Logical Reasoning / Directions', 'exam' => 'ssc,rrb,banking' ),
		array( 'q' => 'Defence & Technology: The BrahMos supersonic cruise missile is a joint venture between India and which country?', 'a' => array( 'United States', 'France', 'Russia', 'Israel' ), 'c' => 2, 'why' => 'BrahMos is developed by BrahMos Aerospace, a joint venture between DRDO of India and NPOM of Russia.', 'cat' => 'Defence', 'src' => 'drdo.gov.in', 'exam' => 'rrb,tspsc,appsc,ssc' ),
	);

	// Check if external bot ingested questions for today
	$daily_store = get_option( 'studentup_daily_quiz_store', array() );
	$today_key   = gmdate( 'Y-m-d' );
	if ( is_array( $daily_store ) && ! empty( $daily_store[ $today_key ] ) && is_array( $daily_store[ $today_key ] ) ) {
		$bank = array_merge( $daily_store[ $today_key ], $bank );
	}

	/**
	 * Filter: add your own questions (site owner / coaching partner).
	 *
	 * @param array<int,array<string,mixed>> $bank Question bank.
	 */
	return apply_filters( 'studentup_quiz_bank', $bank );
}

/**
 * Register REST API route for external bot quiz intake.
 */
function studentup_quiz_register_rest_routes() {
	register_rest_route(
		'studentup/v1',
		'/quiz-intake',
		array(
			'methods'             => 'POST',
			'permission_callback' => 'studentup_quiz_rest_permission',
			'callback'            => 'studentup_quiz_rest_intake',
		)
	);
}
add_action( 'rest_api_init', 'studentup_quiz_register_rest_routes' );

/**
 * REST API permission callback for quiz intake.
 *
 * @param WP_REST_Request $request Request.
 * @return bool|WP_Error
 */
function studentup_quiz_rest_permission( $request ) {
	if ( current_user_can( 'edit_posts' ) ) {
		return true;
	}
	$key = $request->get_header( 'x-studentup-key' );
	if ( ! empty( $key ) ) {
		$expected = get_option( 'studentup_quiz_api_key' );
		if ( empty( $expected ) && defined( 'AUTH_KEY' ) ) {
			$expected = substr( hash( 'sha256', AUTH_KEY ), 0, 32 );
		}
		if ( ! empty( $expected ) && hash_equals( (string) $expected, (string) $key ) ) {
			return true;
		}
	}
	return new WP_Error( 'rest_forbidden', 'Unauthorized quiz intake access.', array( 'status' => 401 ) );
}

/**
 * REST API callback: accepts 20 daily questions from external bots.
 *
 * @param WP_REST_Request $request Request.
 * @return WP_REST_Response|WP_Error
 */
function studentup_quiz_rest_intake( $request ) {
	$params = $request->get_json_params();
	if ( empty( $params ) ) {
		$params = $request->get_body_params();
	}
	$raw_questions = array();
	if ( is_array( $params ) ) {
		if ( isset( $params['questions'] ) && is_array( $params['questions'] ) ) {
			$raw_questions = $params['questions'];
		} else {
			$raw_questions = $params;
		}
	}
	if ( empty( $raw_questions ) ) {
		return new WP_Error( 'invalid_data', 'No valid questions array found.', array( 'status' => 400 ) );
	}

	$normalized = array();
	foreach ( $raw_questions as $item ) {
		if ( ! is_array( $item ) ) {
			continue;
		}
		$q_text = sanitize_text_field( $item['q'] ?? ( $item['question'] ?? '' ) );
		if ( empty( $q_text ) ) {
			continue;
		}
		$opts_raw = $item['a'] ?? ( $item['options'] ?? ( $item['choices'] ?? array() ) );
		if ( ! is_array( $opts_raw ) || count( $opts_raw ) < 2 ) {
			continue;
		}
		$opts = array();
		foreach ( array_slice( $opts_raw, 0, 4 ) as $opt_txt ) {
			$opts[] = sanitize_text_field( (string) $opt_txt );
		}
		while ( count( $opts ) < 4 ) {
			$opts[] = 'Option ' . chr( 65 + count( $opts ) );
		}

		$c_val = $item['c'] ?? ( $item['answer'] ?? ( $item['correct'] ?? 0 ) );
		$c_idx = 0;
		if ( is_numeric( $c_val ) ) {
			$c_idx = max( 0, min( 3, absint( $c_val ) ) );
		} elseif ( is_string( $c_val ) ) {
			$c_upper = strtoupper( trim( $c_val ) );
			if ( in_array( $c_upper, array( 'A', 'B', 'C', 'D' ), true ) ) {
				$c_idx = ord( $c_upper ) - ord( 'A' );
			}
		}

		$exam = sanitize_key( $item['exam'] ?? ( $item['target_exam'] ?? 'general' ) );
		if ( empty( $exam ) ) {
			$exam = 'general';
		}

		$normalized[] = array(
			'q'    => $q_text,
			'a'    => $opts,
			'c'    => $c_idx,
			'why'  => sanitize_text_field( $item['why'] ?? ( $item['explanation'] ?? 'Official answer verification.' ) ),
			'cat'  => sanitize_text_field( $item['cat'] ?? ( $item['category'] ?? 'General Studies' ) ),
			'src'  => sanitize_text_field( $item['src'] ?? ( $item['source'] ?? 'Verified Exam Paper' ) ),
			'exam' => $exam,
		);
	}

	if ( empty( $normalized ) ) {
		return new WP_Error( 'no_valid_questions', 'Failed to normalize questions.', array( 'status' => 422 ) );
	}

	$store = get_option( 'studentup_daily_quiz_store', array() );
	if ( ! is_array( $store ) ) {
		$store = array();
	}
	$today = gmdate( 'Y-m-d' );
	$store[ $today ] = $normalized;
	update_option( 'studentup_daily_quiz_store', $store, false );

	return rest_ensure_response(
		array(
			'status'   => 'ok',
			'imported' => count( $normalized ),
			'day'      => $today,
		)
	);
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

			<div class="su-quiz-exams" role="tablist" aria-label="Select target exam">
				<button type="button" class="su-qtab active" data-exam="all" role="tab" aria-selected="true">All Exams (Daily 20+ Qs)</button>
				<button type="button" class="su-qtab" data-exam="tspsc" role="tab" aria-selected="false">TSPSC (Group 1-4 / Police)</button>
				<button type="button" class="su-qtab" data-exam="appsc" role="tab" aria-selected="false">APPSC / DSC</button>
				<button type="button" class="su-qtab" data-exam="ssc" role="tab" aria-selected="false">SSC (CGL · CHSL · GD)</button>
				<button type="button" class="su-qtab" data-exam="banking" role="tab" aria-selected="false">Banking (IBPS · SBI)</button>
				<button type="button" class="su-qtab" data-exam="rrb" role="tab" aria-selected="false">Railways (RRB NTPC)</button>
			</div>

			<form method="post" class="su-quiz-form" data-su-quiz-form>
				<?php wp_nonce_field( 'su_quiz_submit', 'su_quiz_nonce' ); ?>
				<input type="hidden" name="su_quiz_submitted" value="1">
				<?php foreach ( $qs as $i => $q ) : ?>
					<?php
					$was   = $answered ? (int) ( $picked[ $i ] ?? -1 ) : -1;
					$right = (int) $q['c'];
					?>
					<fieldset class="su-q" data-c="<?php echo esc_attr( (string) $right ); ?>" data-i="<?php echo esc_attr( (string) $i ); ?>" data-exam="<?php echo esc_attr( (string) ( $q['exam'] ?? 'all' ) ); ?>">
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
