<?php
/**
 * v197 STUDENT POLLS — "miru em anukuntunnaru?" (daily poll, real votes).
 *
 * Enduku: site lo engagement blocks (quiz) unnaayi kaani reader **opinion**
 * cheppadaniki chotu ledu. Poll = return visits + comments-free engagement +
 * content ideas (bot ki: winning option ni batti article plan).
 *
 * Design laws (AdSense + privacy safe):
 *  1. **No personal data** — IP ni eppudu store cheyyamu. Voter identity =
 *     `wp_hash( ip + user-agent + auth salt )` (one-way). Cookie kuda same hash.
 *  2. Okka vote per person per poll (hash-dedupe). Rate limit: 20s per voter.
 *  3. Counts mattrame DB lo — wp_options, autoload OFF.
 *  4. **JS lekunda kuda vote** — plain form POST (admin-post.php) + redirect
 *     back. JS unte: instant bars + % (no reload).
 *  5. Honest: "votes are open, not scientific" note. No fake numbers eppudu —
 *     vote lekunda results 0% ga chupistamu, 47% ani kalpamu.
 *  6. Bot daily: `--daily-engage` poll question + options ni REST options tho
 *     push chestundi (`poll_question`, `poll_opts`, `poll_id`).
 *
 * Telugu ledu (v73 invariant) — UI + poll bank English.
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/* ------------------------------------------------------------------ 1. data */

/**
 * Poll bank — one question per weekday slot, rotates daily.
 *
 * @return array<int,array<string,mixed>>
 */
function studentup_poll_bank() {
	$bank = array(
		array( 'q' => 'Which update do you want first on WhatsApp?', 'opts' => array( 'New job notifications', 'Exam date changes', 'Results & hall tickets', 'Scholarship deadlines' ), 'note' => 'This decides what the morning list leads with.' ),
		array( 'q' => 'Which exam are you preparing for right now?', 'opts' => array( 'TSPSC / Group-2', 'APPSC / Group-1', 'SSC CGL / CHSL', 'Banking (IBPS / RRB)' ), 'note' => 'Practice questions follow the most-voted exam.' ),
		array( 'q' => 'What stops you from applying to a government job?', 'opts' => array( 'Fee / documents cost', 'Not sure I am eligible', 'Form filling is confusing', 'I miss the last date' ), 'note' => 'Guides are written around the top answer.' ),
		array( 'q' => 'Where do you read StudentUp mostly?', 'opts' => array( 'Phone', 'Laptop', 'College computer', 'Internet center' ), 'note' => 'Design priority follows this.' ),
		array( 'q' => 'Which free tool should be built next?', 'opts' => array( 'Resume builder', 'Exam date planner', 'Cut-off predictor', 'Study timetable' ), 'note' => 'Top option gets built first.' ),
		array( 'q' => 'Do you want a Telugu version of every article?', 'opts' => array( 'Yes — Telugu first', 'English is fine', 'Both side by side', 'Only for exams' ), 'note' => 'Honest answer helps us plan translation work.' ),
		array( 'q' => 'How many notifications per day is OK for you?', 'opts' => array( 'Only urgent (max 2)', '3–5 updates', 'One morning list', 'No alerts, I check myself' ), 'note' => 'We cap alerts based on this.' ),
	);
	/**
	 * Filter: own poll questions.
	 *
	 * @param array<int,array<string,mixed>> $bank Poll bank.
	 */
	return apply_filters( 'studentup_poll_bank', $bank );
}

/**
 * Poll id for a given day (stable + short).
 *
 * @param int $shift Day offset.
 * @return string
 */
function studentup_poll_id( $shift = 0 ) {
	$ts = current_time( 'timestamp' ) - ( (int) $shift * DAY_IN_SECONDS );
	return 'd' . gmdate( 'Ymd', $ts );
}

/**
 * Today's poll — admin custom (bot-pushed) wins, else daily rotation.
 *
 * @param int $shift Day offset.
 * @return array<string,mixed>
 */
function studentup_poll_today( $shift = 0 ) {
	$shift = (int) $shift;
	$id    = studentup_poll_id( $shift );

	if ( 0 === $shift ) {
		$q = trim( (string) studentup_opt( 'poll_question', '' ) );
		if ( '' !== $q && '0' !== (string) studentup_opt( 'polls', '1' ) ) {
			$raw  = (string) studentup_opt( 'poll_opts', '' );
			$opts = array_values( array_filter( array_map( 'trim', preg_split( '/\r\n|\r|\n/', $raw ) ?: array() ) ) );
			$opts = array_slice( $opts, 0, 5 );
			if ( count( $opts ) >= 2 ) {
				$forced = trim( (string) studentup_opt( 'poll_id', '' ) );
				return array(
					'id'   => $forced ? sanitize_key( $forced ) : $id,
					'q'    => $q,
					'opts' => $opts,
					'note' => trim( (string) studentup_opt( 'poll_note', '' ) ),
					'own'  => true,
				);
			}
		}
	}

	$bank = array_values( studentup_poll_bank() );
	$n    = count( $bank );
	if ( ! $n ) {
		return array();
	}
	$now  = current_time( 'timestamp' ) - ( $shift * DAY_IN_SECONDS );
	$day  = (int) gmdate( 'z', $now ) + ( (int) gmdate( 'Y', $now ) * 366 );
	$item = $bank[ $day % $n ];
	return array(
		'id'   => $id,
		'q'    => (string) $item['q'],
		'opts' => array_map( 'strval', (array) $item['opts'] ),
		'note' => (string) ( $item['note'] ?? '' ),
		'own'  => false,
	);
}

/* --------------------------------------------------------------- 2. storage */

/**
 * Counts option key.
 *
 * @param string $id Poll id.
 * @return string
 */
function studentup_poll_key( $id ) {
	return 'su_poll_counts_' . sanitize_key( $id );
}

/**
 * Vote counts (never created lazily on read — no ghost rows).
 *
 * @param string $id Poll id.
 * @return int[]
 */
function studentup_poll_counts( $id ) {
	$data = get_option( studentup_poll_key( $id ), array() );
	if ( ! is_array( $data ) ) {
		return array();
	}
	return array_map( 'intval', array_values( $data ) );
}

/**
 * Total votes on a poll.
 *
 * @param string $id Poll id.
 * @return int
 */
function studentup_poll_total( $id ) {
	return array_sum( studentup_poll_counts( $id ) );
}

/**
 * One-way voter hash — IP/UA never stored, only this digest.
 *
 * @return string
 */
function studentup_poll_voter() {
	$cookie = isset( $_COOKIE['su_pv'] ) ? sanitize_text_field( wp_unslash( $_COOKIE['su_pv'] ) ) : '';
	if ( $cookie && preg_match( '/^[a-f0-9]{20,64}$/', $cookie ) ) {
		return $cookie;
	}
	$ip  = isset( $_SERVER['REMOTE_ADDR'] ) ? sanitize_text_field( wp_unslash( $_SERVER['REMOTE_ADDR'] ) ) : '0.0.0.0';
	$ua  = isset( $_SERVER['HTTP_USER_AGENT'] ) ? sanitize_text_field( wp_unslash( $_SERVER['HTTP_USER_AGENT'] ) ) : '';
	$raw = $ip . '|' . $ua . '|' . ( function_exists( 'wp_salt' ) ? wp_salt( 'auth' ) : 'su' );
	return substr( wp_hash( $raw ), 0, 40 );
}

/**
 * Has this voter already voted on this poll?
 *
 * @param string $id Poll id.
 * @return bool
 */
function studentup_poll_has_voted( $id ) {
	$seen = get_option( 'su_poll_seen_' . sanitize_key( $id ), array() );
	if ( ! is_array( $seen ) ) {
		return false;
	}
	return in_array( studentup_poll_voter(), $seen, true );
}

/**
 * Record a vote. Returns true on success, false when rejected (dup/rate/bad).
 *
 * @param string $id  Poll id.
 * @param int    $opt Option index.
 * @return bool
 */
function studentup_poll_record( $id, $opt ) {
	$id  = sanitize_key( $id );
	$opt = absint( $opt );
	if ( '' === $id || $opt < 0 || $opt > 9 ) {
		return false;
	}

	$voter = studentup_poll_voter();

	/* rate limit: okka voter 20s lo okkate vote (spam bots) */
	$rl = 'su_poll_rl_' . $voter;
	if ( get_transient( $rl ) ) {
		return false;
	}

	$seen_key = 'su_poll_seen_' . $id;
	$seen     = get_option( $seen_key, array() );
	$seen     = is_array( $seen ) ? $seen : array();
	if ( in_array( $voter, $seen, true ) ) {
		return false;
	}

	$key    = studentup_poll_key( $id );
	$counts = get_option( $key, array() );
	$counts = is_array( $counts ) ? array_map( 'intval', array_values( $counts ) ) : array();
	while ( count( $counts ) <= $opt ) {
		$counts[] = 0;
	}
	$counts[ $opt ]++;

	update_option( $key, $counts, false ); // autoload OFF — counts per poll.

	/* dedupe list cap: 5000 hashes (beyond that cookie + rate limit guard) */
	$seen[] = $voter;
	if ( count( $seen ) > 5000 ) {
		$seen = array_slice( $seen, -2500 );
	}
	update_option( $seen_key, $seen, false );

	set_transient( $rl, 1, 20 );

	if ( ! headers_sent() ) {
		setcookie( 'su_pv', $voter, time() + YEAR_IN_SECONDS, COOKIEPATH ? COOKIEPATH : '/', COOKIE_DOMAIN, is_ssl(), true );
	}
	return true;
}

/* ----------------------------------------------------------------- 3. REST */

/**
 * REST: GET = results · POST = vote (public poll, no personal data stored).
 *
 * @return void
 */
function studentup_register_poll_route() {
	register_rest_route(
		'studentup/v1',
		'/poll',
		array(
			array(
				'methods'             => 'GET',
				'permission_callback' => '__return_true',
				'callback'            => 'studentup_rest_poll_get',
				'args'                => array(
					'id' => array( 'sanitize_callback' => 'sanitize_key' ),
				),
			),
			array(
				'methods'             => 'POST',
				'permission_callback' => '__return_true',
				'callback'            => 'studentup_rest_poll_post',
				'args'                => array(
					'id'   => array( 'sanitize_callback' => 'sanitize_key' ),
					'opt'  => array( 'sanitize_callback' => 'absint' ),
					'poll' => array( 'sanitize_callback' => 'sanitize_key' ),
				),
			),
		)
	);
}
add_action( 'rest_api_init', 'studentup_register_poll_route' );

/**
 * GET /poll — counts + totals.
 *
 * @param WP_REST_Request $req Request.
 * @return WP_REST_Response
 */
function studentup_rest_poll_get( $req ) {
	$id     = (string) $req->get_param( 'id' );
	$poll   = $id ? null : studentup_poll_today();
	$id     = $id ? $id : (string) ( $poll['id'] ?? '' );
	$counts = studentup_poll_counts( $id );
	return new WP_REST_Response(
		array(
			'ok'     => true,
			'id'     => $id,
			'total'  => array_sum( $counts ),
			'counts' => array_values( $counts ),
			'voted'  => studentup_poll_has_voted( $id ),
		),
		200
	);
}

/**
 * POST /poll — record one vote, return fresh results.
 *
 * @param WP_REST_Request $req Request.
 * @return WP_REST_Response
 */
function studentup_rest_poll_post( $req ) {
	$id  = (string) $req->get_param( 'id' );
	$opt = (int) $req->get_param( 'opt' );
	if ( '' === $id ) {
		$poll = studentup_poll_today();
		$id   = (string) ( $poll['id'] ?? '' );
	}
	$ok = studentup_poll_record( $id, $opt );
	if ( ! $ok ) {
		$counts = studentup_poll_counts( $id );
		return new WP_REST_Response(
			array(
				'ok'     => false,
				'reason' => studentup_poll_has_voted( $id ) ? 'already_voted' : 'rejected',
				'id'     => $id,
				'total'  => array_sum( $counts ),
				'counts' => array_values( $counts ),
				'voted'  => studentup_poll_has_voted( $id ),
			),
			200
		);
	}
	$counts = studentup_poll_counts( $id );
	return new WP_REST_Response(
		array(
			'ok'     => true,
			'id'     => $id,
			'total'  => array_sum( $counts ),
			'counts' => array_values( $counts ),
			'voted'  => true,
		),
		200
	);
}

/* ------------------------------------------------- 4. no-JS form endpoint */

/**
 * admin-post.php handler — JS lekunda vote (plain form POST + redirect back).
 *
 * @return void
 */
function studentup_poll_form_handler() {
	$nonce = isset( $_POST['su_poll_nonce'] ) ? sanitize_text_field( wp_unslash( $_POST['su_poll_nonce'] ) ) : '';
	if ( ! wp_verify_nonce( $nonce, 'su_poll_vote' ) ) {
		wp_safe_redirect( home_url( '/' ) );
		exit;
	}
	$id  = isset( $_POST['su_poll_id'] ) ? sanitize_key( wp_unslash( $_POST['su_poll_id'] ) ) : '';
	$opt = isset( $_POST['su_poll_opt'] ) ? absint( wp_unslash( $_POST['su_poll_opt'] ) ) : -1;
	studentup_poll_record( $id, $opt );

	$back = wp_get_referer();
	$back = $back ? $back : home_url( '/' );
	wp_safe_redirect( add_query_arg( 'su_voted', '1', $back ) . '#su-poll-' . rawurlencode( $id ) );
	exit;
}
add_action( 'admin_post_nopriv_studentup_poll_vote', 'studentup_poll_form_handler' );
add_action( 'admin_post_studentup_poll_vote', 'studentup_poll_form_handler' );

/* ------------------------------------------------------------- 5. renderer */

/**
 * Poll schema (Question + suggestedAnswer). Valid, no rich-result promises.
 *
 * @param array<string,mixed> $poll  Poll.
 * @param int[]               $counts Counts.
 * @param int                 $total  Total.
 * @return string
 */
function studentup_poll_schema( $poll, $counts, $total ) {
	$answers = array();
	foreach ( (array) $poll['opts'] as $i => $txt ) {
		$c         = isset( $counts[ $i ] ) ? (int) $counts[ $i ] : 0;
		$pct       = $total > 0 ? (int) round( ( $c / $total ) * 100 ) : 0;
		$answers[] = array(
			'@type'         => 'Answer',
			'text'          => (string) $txt,
			'position'      => (int) $i,
			'aggregateVotes'=> $c,
			'comment'       => $pct . '% of readers chose this',
		);
	}
	$graph = array(
		'@context'        => 'https://schema.org',
		'@type'           => 'Question',
		'name'            => (string) $poll['q'],
		'text'            => (string) $poll['q'],
		'answerCount'     => $total,
		'suggestedAnswer' => $answers,
		'inLanguage'      => 'en-IN',
	);
	return wp_json_encode( $graph, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES );
}

/**
 * Render the daily poll (server-side results, JS instant upgrade).
 *
 * @param array<string,mixed> $args Args: id, kicker, heading, compact.
 * @return void
 */
function studentup_daily_poll( $args = array() ) {
	if ( '0' === (string) studentup_opt( 'polls', '1' ) ) {
		return;
	}
	$args = wp_parse_args( $args, array( 'id' => '', 'kicker' => 'READER POLL', 'heading' => '' ) );
	$poll = studentup_poll_today();
	if ( ! $poll ) {
		return;
	}
	$id     = $args['id'] ? sanitize_key( (string) $args['id'] ) : (string) $poll['id'];
	$counts = studentup_poll_counts( $id );
	$total  = array_sum( $counts );
	$voted  = studentup_poll_has_voted( $id ) || isset( $_GET['su_voted'] ); // phpcs:ignore WordPress.Security.NonceVerification -- read-only flag
	$opts   = array_values( (array) $poll['opts'] );
	$n      = count( $opts );
	$best   = 0;
	$best_i = -1;
	for ( $i = 0; $i < $n; $i++ ) {
		$c = isset( $counts[ $i ] ) ? (int) $counts[ $i ] : 0;
		if ( $c > $best ) {
			$best   = $c;
			$best_i = $i;
		}
	}
	?>
	<section class="su-poll" id="su-poll-<?php echo esc_attr( $id ); ?>" data-su-poll="<?php echo esc_attr( $id ); ?>" aria-label="<?php esc_attr_e( 'Reader poll', 'studentup' ); ?>">
		<p class="su-poll-kick"><?php echo esc_html( (string) $args['kicker'] ); ?></p>
		<h3><?php echo esc_html( (string) $poll['q'] ); ?></h3>
		<p class="su-poll-sub">
			<?php
			if ( $total > 0 ) {
				printf(
					/* translators: %s: vote count. */
					esc_html__( '%s readers voted — tap an option to see live results.', 'studentup' ),
					esc_html( number_format_i18n( $total ) )
				);
			} else {
				esc_html_e( 'Be the first to vote — results show as soon as people answer.', 'studentup' );
			}
			?>
		</p>

		<form method="post" action="<?php echo esc_url( admin_url( 'admin-post.php' ) ); ?>" class="su-poll-form" data-su-poll-form>
			<input type="hidden" name="action" value="studentup_poll_vote">
			<input type="hidden" name="su_poll_id" value="<?php echo esc_attr( $id ); ?>">
			<?php wp_nonce_field( 'su_poll_vote', 'su_poll_nonce' ); ?>
			<div class="su-poll-opts">
				<?php
				foreach ( $opts as $i => $txt ) :
					$c   = isset( $counts[ $i ] ) ? (int) $counts[ $i ] : 0;
					$pct = $total > 0 ? (int) round( ( $c / $total ) * 100 ) : 0;
					$on  = ( $voted && $i === $best_i && $total > 0 );
					?>
					<label class="su-poll-opt<?php echo esc_attr( $on ? ' on' : '' ); ?>" data-opt="<?php echo esc_attr( (string) $i ); ?>"<?php echo esc_attr( $voted ? ' data-su-done="1"' : '' ); ?>>
						<span class="su-poll-bar" data-su-bar style="width:<?php echo esc_attr( (string) ( $voted ? $pct : 0 ) ); ?>%"></span>
						<input type="radio" name="su_poll_opt" value="<?php echo esc_attr( (string) $i ); ?>"<?php echo esc_attr( $voted ? ' disabled' : '' ); ?>>
						<span class="su-poll-radio" aria-hidden="true"></span>
						<span class="su-poll-lbl"><?php echo esc_html( (string) $txt ); ?></span>
						<span class="su-poll-pct" data-su-pct><?php echo esc_html( $voted ? $pct . '%' : '' ); ?></span>
					</label>
				<?php endforeach; ?>
			</div>
			<div class="su-poll-foot">
				<?php if ( ! $voted ) : ?>
					<button type="submit" class="su-poll-vote" data-su-poll-vote><?php esc_html_e( 'Vote', 'studentup' ); ?></button>
					<span><?php esc_html_e( 'No login. One vote per device.', 'studentup' ); ?></span>
				<?php else : ?>
					<span class="su-poll-thanks" data-su-thanks><?php esc_html_e( 'Thanks — your vote is counted.', 'studentup' ); ?></span>
					<span data-su-total><?php echo esc_html( number_format_i18n( $total ) ); ?> votes</span>
				<?php endif; ?>
			</div>
		</form>
		<?php if ( ! empty( $poll['note'] ) ) : ?>
			<p class="su-poll-foot"><?php echo esc_html( (string) $poll['note'] ); ?></p>
		<?php endif; ?>
		<p class="su-quiz-legend"><?php esc_html_e( 'Open poll, not a scientific survey. We store only the count — never who voted.', 'studentup' ); ?></p>
		<?php
		$json = studentup_poll_schema( $poll, $counts, $total );
		if ( $json ) {
			printf( '<script type="application/ld+json">%s</script>', $json ); // phpcs:ignore WordPress.Security.EscapeOutput -- wp_json_encode output
		}
		?>
	</section>
	<?php
}

/**
 * Past polls with their totals (page archive strip; shows only voted polls).
 *
 * @param int $days How many past days.
 * @return array<int,array<string,mixed>>
 */
function studentup_poll_recent( $days = 7 ) {
	$out = array();
	for ( $i = 1; $i <= max( 1, (int) $days ); $i++ ) {
		$poll = studentup_poll_today( $i );
		if ( empty( $poll['id'] ) ) {
			continue;
		}
		$counts = studentup_poll_counts( (string) $poll['id'] );
		$total  = array_sum( $counts );
		if ( $total < 1 ) {
			continue; // honest: no votes → no fake archive entry
		}
		$best   = 0;
		$best_i = -1;
		foreach ( array_values( (array) $poll['opts'] ) as $oi => $otxt ) {
			$c = isset( $counts[ $oi ] ) ? (int) $counts[ $oi ] : 0;
			if ( $c > $best ) {
				$best   = $c;
				$best_i = $oi;
			}
		}
		$out[] = array(
			'date'  => date_i18n( 'D, M j', current_time( 'timestamp' ) - ( $i * DAY_IN_SECONDS ) ),
			'q'     => (string) $poll['q'],
			'win'   => $best_i >= 0 ? (string) $poll['opts'][ $best_i ] : '',
			'pct'   => $total > 0 && $best_i >= 0 ? (int) round( ( $best / $total ) * 100 ) : 0,
			'total' => (int) $total,
		);
	}
	return $out;
}
