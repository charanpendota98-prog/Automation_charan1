<?php
/**
 * v72: Qualification-wise job filter — 10th · 10+2 · ITI · Diploma · Degree · PG · B.Tech.
 *
 * Automatic ela pani chestundi (manual tagging avasaram ledu):
 *   1) Post save ayinappudu (bot post chesinappudu kuda) title + content lo
 *      qualification keywords chusi 'studentup_qual' meta set avutundi.
 *   2) Bot 'studentup_qual' meta pampiste adi priority (bot strong ga cheppindi).
 *   3) Meta lekapote (purana posts) admin/CLI backfill — batch ga, slow avvadu.
 *   4) ?qual=degree → server-side WP_Query meta_query filter (JS ledu, Google clean).
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Filter chips (slug => Telugu label).
 *
 * @return array
 */
function studentup_qual_terms() {
	return array(
		'10th'    => '10వ తరగతి',
		'inter'   => 'ఇంటర్ (10+2)',
		'iti'     => 'ఐటీఐ',
		'diploma' => 'డిప్లొమా',
		'degree'  => 'డిగ్రీ',
		'pg'      => 'పీజీ',
		'btech'   => 'బీటెక్',
	);
}

/**
 * Keyword map — Telugu + English (chinnabbi case tho match avutundi).
 *
 * @return array
 */
function studentup_qual_keywords() {
	return array(
		'10th'    => array( '10వ తరగతి', '10వ', '10th', 'tenth', '10th class', '10th pass', 'పదవ తరగతి', 'sgl', 'group d' ),
		'inter'   => array( 'ఇంటర్', 'inter', 'intermediate', '10+2', 'plus two', 'junior intermediate', 'డిగ్రీ లేదు', 'intermediate pass' ),
		'iti'     => array( 'ఐటీఐ', 'iti', 'nctvt', 'trade certificate', 'ఐ టీ ఐ' ),
		'diploma' => array( 'డిప్లొమా', 'diploma', 'polytechnic', 'పాలిటెక్నిక్' ),
		'degree'  => array( 'డిగ్రీ', 'degree', 'graduate', 'graduation', 'any degree', 'b.a', 'b.sc', 'b.com', 'బీఏ', 'బీఎస్సీ', 'బీకాం' ),
		'pg'      => array( 'పీజీ', 'pg', 'post graduate', 'postgraduate', 'm.a', 'm.sc', 'm.com', 'mba', 'ఎంఏ', 'ఎంఎస్సీ', 'ఎంబీఏ' ),
		'btech'   => array( 'బీటెక్', 'b.tech', 'btech', 'b.e', 'engineering', 'ఇంజినీరింగ్' ),
	);
}

/**
 * Post title + content chusi qualification slugs detect cheyyadam.
 *
 * @param int          $post_id post id.
 * @param WP_Post|null $post    post object (optional).
 * @return string space separated slugs ('degree pg') — ledu ante ''.
 */
function studentup_detect_qual( $post_id = 0, $post = null ) {
	$post = $post ? $post : get_post( $post_id );
	if ( ! $post ) {
		return '';
	}
	$hay = mb_strtolower( $post->post_title . ' ' . wp_strip_all_tags( (string) $post->post_content ) );
	$hit = array();
	foreach ( studentup_qual_keywords() as $slug => $words ) {
		foreach ( $words as $w ) {
			if ( false !== mb_strpos( $hay, mb_strtolower( $w ) ) ) {
				$hit[] = $slug;
				break;
			}
		}
	}
	/**
	 * Filter: theme owner kuda tag add/remove cheyyochu.
	 *
	 * @param array   $hit  detected slugs.
	 * @param WP_Post $post post.
	 */
	$hit = (array) apply_filters( 'studentup_qual_detected', $hit, $post );
	return implode( ' ', array_unique( array_filter( $hit ) ) );
}

/**
 * Meta set (existing value unte touch cheyyamu — correct data protect).
 *
 * @param int $post_id post id.
 * @return string final value.
 */
function studentup_qual_assign( $post_id ) {
	$post = get_post( $post_id );
	if ( ! $post || 'revision' === $post->post_type ) {
		return '';
	}
	$existing = trim( (string) get_post_meta( $post_id, 'studentup_qual', true ) );
	if ( '' !== $existing ) {
		return $existing;
	}
	$detected = studentup_detect_qual( $post_id, $post );
	if ( '' !== $detected ) {
		update_post_meta( $post_id, 'studentup_qual', $detected );
		delete_transient( 'su_qual_counts' );
	}
	return $detected;
}

/**
 * save_post → automatic tag (bot REST push lo kuda idi fire avutundi).
 *
 * @param int $post_id post id.
 */
function studentup_qual_on_save( $post_id ) {
	if ( wp_is_post_revision( $post_id ) || wp_is_post_autosave( $post_id ) ) {
		return;
	}
	$post = get_post( $post_id );
	if ( ! $post || ! in_array( $post->post_type, array( 'post' ), true ) ) {
		return;
	}
	studentup_qual_assign( $post_id );
	delete_transient( 'su_qual_counts' );
}
add_action( 'save_post', 'studentup_qual_on_save', 20 );

/**
 * Purana posts backfill (batch ga — site slow avvadu). Admin lo automatic,
 * CLI lo `wp studentup-qual-backfill` tho motham.
 *
 * @param int $limit batch size.
 * @return int tag chesina posts.
 */
function studentup_qual_backfill( $limit = 40 ) {
	$q = new WP_Query(
		array(
			'post_type'      => 'post',
			'post_status'    => 'publish',
			'posts_per_page' => max( 1, (int) $limit ),
			'fields'         => 'ids',
			'no_found_rows'  => true,
			'meta_query'     => array( // phpcs:ignore WordPress.DB.SlowDBQuery
				array(
					'key'     => 'studentup_qual',
					'compare' => 'NOT EXISTS',
				),
			),
		)
	);
	$done = 0;
	foreach ( $q->posts as $id ) {
		if ( '' !== studentup_qual_assign( $id ) ) {
			$done++;
		} else {
			update_post_meta( $id, 'studentup_qual', '' ); // 'checked' mark — malli malli scan avvadu.
		}
	}
	if ( $done ) {
		delete_transient( 'su_qual_counts' );
	}
	return $done;
}

/**
 * Admin lo automatic backfill (page load ki 20 — background laga).
 */
function studentup_qual_admin_backfill() {
	if ( ! current_user_can( 'edit_posts' ) ) {
		return;
	}
	studentup_qual_backfill( 20 );
}
add_action( 'admin_init', 'studentup_qual_admin_backfill' );

/**
 * WP-CLI: wp studentup-qual-backfill [--limit=500]
 */
if ( defined( 'WP_CLI' ) && WP_CLI ) {
	WP_CLI::add_command(
		'studentup-qual-backfill',
		function ( $args, $assoc ) {
			$limit = isset( $assoc['limit'] ) ? (int) $assoc['limit'] : 500;
			$total = 0;
			for ( $i = 0; $i < 50; $i++ ) {
				$n = studentup_qual_backfill( min( 100, $limit ) );
				$total += $n;
				if ( 0 === $n ) {
					break;
				}
			}
			WP_CLI::success( "qual tags: {$total} posts" );
		}
	);
}

/**
 * REST lo meta write allow (bot 'studentup_qual' + 'studentup_last_date' pampistundi).
 */
function studentup_register_qual_meta() {
	$keys = array( 'studentup_qual', 'studentup_last_date', 'studentup_apply_url' );
	foreach ( $keys as $key ) {
		register_post_meta(
			'post',
			$key,
			array(
				'show_in_rest'  => true,
				'single'        => true,
				'type'          => 'string',
				'auth_callback' => function ( $allowed, $meta_key, $post_id ) {
					return current_user_can( 'edit_post', $post_id );
				},
			)
		);
	}
}
add_action( 'init', 'studentup_register_qual_meta' );

/**
 * Card lo chip kosam — 'degree pg' → ['డిగ్రీ','పీజీ'].
 *
 * @param int $post_id post id.
 * @param int $max     max chips.
 * @return array slugs => labels
 */
function studentup_qual_labels( $post_id = 0, $max = 3 ) {
	$post_id = $post_id ? $post_id : get_the_ID();
	$raw     = trim( (string) get_post_meta( $post_id, 'studentup_qual', true ) );
	if ( '' === $raw ) {
		$raw = studentup_qual_assign( $post_id );
	}
	$terms = studentup_qual_terms();
	$out   = array();
	foreach ( preg_split( '/[\s,]+/', strtolower( $raw ) ) as $slug ) {
		if ( isset( $terms[ $slug ] ) ) {
			$out[ $slug ] = $terms[ $slug ];
		}
	}
	return array_slice( $out, 0, max( 1, (int) $max ), true );
}

/**
 * Closing-soon badge (data-last → 'studentup_last_date' meta).
 *
 * @param int $post_id post id.
 * @return string HTML ('' ledu ante).
 */
function studentup_last_date_badge( $post_id = 0 ) {
	$post_id = $post_id ? $post_id : get_the_ID();
	$iso     = trim( (string) get_post_meta( $post_id, 'studentup_last_date', true ) );
	if ( '' === $iso || ! preg_match( '/^\d{4}-\d{2}-\d{2}$/', $iso ) ) {
		return '';
	}
	$left = (int) floor( ( strtotime( $iso . ' 23:59:59' ) - current_time( 'timestamp' ) ) / DAY_IN_SECONDS ); // phpcs:ignore WordPress.DateTime.CurrentTimeTimestamp
	if ( $left < 0 ) {
		return '<span class="qbadge done">గడువు ముగిసింది</span>';
	}
	if ( $left <= 7 ) {
		$txt = ( 0 === $left ) ? 'ఈరోజే చివరి రోజు' : $left . ' రోజుల్లో ముగుస్తుంది';
		return '<span class="qbadge soon">⏳ ' . esc_html( $txt ) . '</span>';
	}
	return '';
}

/**
 * Current filter (URL nunchi, whitelist).
 *
 * @return string slug | 'all'
 */
function studentup_qual_current() {
	$terms = studentup_qual_terms();
	$raw   = isset( $_GET['qual'] ) ? sanitize_key( wp_unslash( $_GET['qual'] ) ) : ''; // phpcs:ignore WordPress.Security.NonceVerification
	if ( isset( $terms[ $raw ] ) ) {
		return $raw;
	}
	if ( 'closing' === $raw ) {
		return 'closing';
	}
	return 'all';
}

/**
 * Server-side filter — main query (home/archive/search).
 *
 * @param WP_Query $query query.
 */
function studentup_qual_pre_get_posts( $query ) {
	if ( is_admin() || ! $query->is_main_query() ) {
		return;
	}
	$qual = studentup_qual_current();
	if ( 'all' === $qual ) {
		return;
	}
	$meta = $query->get( 'meta_query' );
	$meta = is_array( $meta ) ? $meta : array();
	if ( 'closing' === $qual ) {
		$today = current_time( 'Y-m-d' );
		$week  = gmdate( 'Y-m-d', strtotime( $today . ' +7 days' ) );
		$meta[] = array(
			'key'     => 'studentup_last_date',
			'value'   => array( $today, $week ),
			'compare' => 'BETWEEN',
			'type'    => 'DATE',
		);
	} else {
		$meta[] = array(
			'key'     => 'studentup_qual',
			'value'   => $qual,
			'compare' => 'LIKE',
		);
	}
	$query->set( 'meta_query', $meta ); // phpcs:ignore WordPress.DB.SlowDBQuery
	$query->set( 'studentup_qual_filter', $qual );
}
add_action( 'pre_get_posts', 'studentup_qual_pre_get_posts' );

/**
 * Chip count (transient cache 15 min — expensive query okate sari).
 *
 * @param string $slug slug.
 * @return int
 */
function studentup_qual_count( $slug ) {
	$counts = get_transient( 'su_qual_counts' );
	if ( ! is_array( $counts ) ) {
		$counts = array();
		foreach ( studentup_qual_terms() as $key => $label ) {
			$q = new WP_Query(   // found-rows-needed: chips counts ki found_posts kavali
				array(
					'post_type'      => 'post',
					'post_status'    => 'publish',
					'posts_per_page' => 1,
					'fields'         => 'ids',
					'no_found_rows'  => false,
					'meta_query'     => array( // phpcs:ignore WordPress.DB.SlowDBQuery
						array(
							'key'     => 'studentup_qual',
							'value'   => $key,
							'compare' => 'LIKE',
						),
					),
				)
			);
			$counts[ $key ] = (int) $q->found_posts;
		}
		set_transient( 'su_qual_counts', $counts, 15 * MINUTE_IN_SECONDS );
	}
	return isset( $counts[ $slug ] ) ? (int) $counts[ $slug ] : 0;
}

/**
 * Filter bar — home/archive lo chips (server-side links; JS ledu = SEO safe).
 */
function studentup_qual_bar() {
	if ( ! studentup_opt( 'qual_filter', '1' ) ) {
		return;
	}
	$terms   = studentup_qual_terms();
	$current = studentup_qual_current();
	echo '<nav class="qrow" aria-label="అర్హత ప్రకారం ఉద్యోగాలు">';
	echo '<span class="catlabel" aria-hidden="true">అర్హత:</span>';
	echo '<a class="chip qchip' . ( 'all' === $current ? ' active' : '' ) . '" data-qual="all" href="' . esc_url( home_url( '/' ) ) . '">అన్నీ</a>';
	foreach ( $terms as $slug => $label ) {
		$n   = studentup_qual_count( $slug );
		$url = add_query_arg( 'qual', $slug, home_url( '/' ) );
		echo '<a class="chip qchip' . ( $current === $slug ? ' active' : '' ) . '" data-qual="' . esc_attr( $slug ) . '"'
			. ' href="' . esc_url( $url ) . '" rel="nofollow">' . esc_html( $label )
			. ( $n ? ' <span class="qnum">' . (int) $n . '</span>' : '' ) . '</a>';
	}
	echo '</nav>';
}

/**
 * WP_Query args ki qualification filter ni merge cheyyadam (custom queries kosam).
 *
 * Enduku: front-page.php lo `new WP_Query()` vaadutunnam — main query kaadu, anduku
 * `pre_get_posts` akkada pani cheyyadu. Ee helper rendu chota okate filter istundi.
 *
 * @param array $args WP_Query args.
 * @return array
 */
function studentup_qual_query_args( $args = array() ) {
	$qual = studentup_qual_current();
	if ( 'all' === $qual ) {
		return $args;
	}
	$meta = isset( $args['meta_query'] ) && is_array( $args['meta_query'] ) ? $args['meta_query'] : array();
	if ( 'closing' === $qual ) {
		$today  = current_time( 'Y-m-d' );
		$week   = gmdate( 'Y-m-d', strtotime( $today . ' +7 days' ) );
		$meta[] = array(
			'key'     => 'studentup_last_date',
			'value'   => array( $today, $week ),
			'compare' => 'BETWEEN',
			'type'    => 'DATE',
		);
		$args['meta_key'] = 'studentup_last_date'; // phpcs:ignore WordPress.DB.SlowDBQuery
		$args['orderby']  = 'meta_value';
		$args['order']    = 'ASC';
	} else {
		$meta[] = array(
			'key'     => 'studentup_qual',
			'value'   => $qual,
			'compare' => 'LIKE',
		);
	}
	$args['meta_query'] = $meta; // phpcs:ignore WordPress.DB.SlowDBQuery
	return $args;
}

/**
 * Filter active unnappudu chinna note (count tho) — "అర్హత: డిగ్రీ · 6 ఉద్యోగాలు".
 *
 * @param int $count posts count.
 */
function studentup_qual_active_note( $count = 0 ) {
	$qual = studentup_qual_current();
	if ( 'all' === $qual ) {
		return;
	}
	$terms = studentup_qual_terms();
	$label = ( 'closing' === $qual ) ? '⏳ 7 రోజుల్లో ముగిసేవి' : ( $terms[ $qual ] ?? $qual );
	echo '<p class="qnote">అర్హత: <b>' . esc_html( $label ) . '</b>';
	if ( $count ) {
		echo ' · ' . (int) $count . ' ఉద్యోగాలు';
	}
	echo ' · <a href="' . esc_url( home_url( '/' ) ) . '">అన్నీ చూడండి</a></p>';
}

/**
 * JS tho దాచిన గడువు ముగిసిన ఉద్యోగాల note (element mattrame — JS nimpustundi).
 */
function studentup_hidden_note() {
	echo '<p class="qnote qhidden" id="su-hidden-note" hidden></p>';
}

/**
 * Admin dashboard widget — ఏ అర్హతకు ఎన్ని ఉద్యోగాలు ఉన్నాయి (advanced view).
 * Bot/owner ki okka chota clear picture; counts 15 min cache (page slow avvadu).
 */
function studentup_qual_dashboard_widget() {
	if ( ! current_user_can( 'edit_posts' ) ) {
		return;
	}
	wp_add_dashboard_widget(
		'studentup_qual_widget',
		'StudentUp · విద్యార్హత ప్రకారం ఉద్యోగాలు',
		function () {
			$terms = studentup_qual_terms();
			echo '<p style="margin:0 0 8px;color:#64748b">Post save ayinappudu tag automatic ga set avutundi. Purana posts ki backfill:</p>';
			echo '<p><code>wp studentup-qual-backfill --limit=500</code></p><table class="widefat striped"><tbody>';
			foreach ( $terms as $slug => $label ) {
				$n = studentup_qual_count( $slug );
				echo '<tr><td>' . esc_html( $label ) . '</td><td style="text-align:right"><b>' . (int) $n . '</b></td></tr>';
			}
			$missing = studentup_qual_missing_count();
			echo '<tr><td>ట్యాగ్ లేని పోస్టులు</td><td style="text-align:right">' . (int) $missing . '</td></tr>';
			echo '</tbody></table>';
		}
	);
}
add_action( 'wp_dashboard_setup', 'studentup_qual_dashboard_widget' );

/**
 * Tag ledu ane posts count (backfill avasaram undo telusukovadaniki).
 *
 * @return int
 */
function studentup_qual_missing_count() {
	$q = new WP_Query(   // found-rows-needed: backfill count ki found_posts kavali
		array(
			'post_type'      => 'post',
			'post_status'    => 'publish',
			'posts_per_page' => 1,
			'fields'         => 'ids',
			'update_post_meta_cache' => false,
			'update_post_term_cache' => false,
			'meta_query'     => array( // phpcs:ignore WordPress.DB.SlowDBQuery
				array(
					'key'     => 'studentup_qual',
					'compare' => 'NOT EXISTS',
				),
			),
		)
	);
	return (int) $q->found_posts;
}

/**
 * v72.1: "అర్హత ప్రకారం చూడండి" విభాగాలు — grid cards nunchi JS automatic ga nimpustundi.
 *
 * Enduku JS: prathi qualification ki separate WP_Query chesthe page slow (7 extra queries).
 * JS okkasari ne already render ayina cards nunchi groups build chestundi — kotha post
 * vasthe automatic ga kanipistundi (manual tagging/editing ledu).
 */
function studentup_qual_directory() {
	if ( ! studentup_opt( 'qual_filter', '1' ) || ! is_front_page() ) {
		return;
	}
	$groups = array_merge( array_keys( studentup_qual_terms() ), array( 'closing' ) );
	?>
	<section class="qualsplit" id="qualsplit" aria-label="అర్హత ప్రకారం ఉద్యోగాలు">
		<div class="qsplit-head">
			<h2>అర్హత ప్రకారం చూడండి</h2>
			<p>మీ చదువుకు సరిపోయే ఉద్యోగాలు — కొత్త పోస్ట్ వచ్చిన ప్రతిసారీ ఇవి ఆటోమేటిక్‌గా అప్డేట్ అవుతాయి.</p>
		</div>
		<div class="qsplit-grid" id="qsplit">
			<?php foreach ( $groups as $g ) : ?>
				<article class="qgroup" data-qgroup="<?php echo esc_attr( $g ); ?>" hidden></article>
			<?php endforeach; ?>
		</div>
	</section>
	<?php
}
add_action( 'wp_footer', 'studentup_qual_directory', 5 );

/**
 * Card lo qualification chip (template.php nunchi call avutundi).
 *
 * @param int $post_id post id.
 */
function studentup_qual_chip( $post_id = 0 ) {
	$labels = studentup_qual_labels( $post_id, 3 );
	if ( ! $labels ) {
		return;
	}
	echo '<span class="qchips">';
	foreach ( $labels as $slug => $label ) {
		echo '<span class="tag qual" data-qual="' . esc_attr( $slug ) . '">' . esc_html( $label ) . '</span>';
	}
	echo '</span>';
}
