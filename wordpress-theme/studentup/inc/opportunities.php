<?php
/**
 * StudentUp Active Opportunities Board.
 *
 * The board is a live view over published posts. It never deletes article
 * URLs; it simply hides a notice from the active list after its verified
 * studentup_last_date has passed. Missing dates remain visible with "Not
 * announced" rather than receiving a guessed deadline.
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

function studentup_opportunity_sections() {
	return array(
		'ts'          => array( 'label' => 'Telangana Government Jobs', 'icon' => 'bank' ),
		'ap'          => array( 'label' => 'Andhra Pradesh Government Jobs', 'icon' => 'bank' ),
		'central'     => array( 'label' => 'Central Government Jobs', 'icon' => 'flag' ),
		'walkin'      => array( 'label' => 'Walk-in Jobs', 'icon' => 'walk' ),
		'outsourcing' => array( 'label' => 'Outsourcing & Contract Jobs', 'icon' => 'person' ),
		'job-melas'   => array( 'label' => 'Job Melas & Job Fairs', 'icon' => 'person' ),
		'software'    => array( 'label' => 'Software Jobs', 'icon' => 'laptop' ),
		'private'     => array( 'label' => 'Private Jobs', 'icon' => 'building' ),
		'scholarships'=> array( 'label' => 'Scholarships', 'icon' => 'school' ),
		'results'     => array( 'label' => 'Results', 'icon' => 'doc' ),
		'hall-tickets' => array( 'label' => 'Hall Tickets', 'icon' => 'ticket' ),
		'current-affairs' => array( 'label' => 'Daily Current Affairs', 'icon' => 'news' ),
	);
}

function studentup_opportunity_last_date( $post_id ) {
	$iso = trim( (string) get_post_meta( $post_id, 'studentup_last_date', true ) );
	if ( ! preg_match( '/^20\d{2}-\d{2}-\d{2}$/', $iso ) ) {
		return '';
	}
	$date = DateTime::createFromFormat( '!Y-m-d', $iso );
	return $date && $date->format( 'Y-m-d' ) === $iso ? $iso : '';
}

function studentup_opportunity_is_expired( $last_date ) {
	if ( '' === $last_date ) {
		return false; // Unknown is not the same as expired.
	}
	$stamp = strtotime( $last_date . ' 23:59:59' );
	return $stamp && $stamp < current_time( 'timestamp' ); // phpcs:ignore WordPress.DateTime.CurrentTimeTimestamp
}

function studentup_opportunity_days_left( $last_date ) {
	if ( '' === $last_date ) {
		return null;
	}
	$end   = strtotime( $last_date . ' 23:59:59' );
	$today = current_time( 'timestamp' ); // phpcs:ignore WordPress.DateTime.CurrentTimeTimestamp
	return (int) floor( ( $end - $today ) / DAY_IN_SECONDS );
}

function studentup_source_verification_notice( $post_id = 0 ) {
	$post_id      = $post_id ? (int) $post_id : (int) get_the_ID();
	$source_url   = trim( (string) get_post_meta( $post_id, 'studentup_source_url', true ) );
	$checked      = trim( (string) get_post_meta( $post_id, 'studentup_source_checked', true ) );
	$application  = trim( (string) get_post_meta( $post_id, 'studentup_apply_url', true ) );
	if ( ! wp_http_validate_url( $source_url ) ) {
		return '';
	}
	$checked_stamp = preg_match( '/^20\d{2}-\d{2}-\d{2}$/', $checked ) ? strtotime( $checked . ' 12:00:00' ) : false;
	$html = '<div class="su-source-trust" role="note"><strong>Source verification</strong> · ';
	$html .= $checked_stamp ? esc_html( 'Checked ' . wp_date( 'd M Y', $checked_stamp ) ) : esc_html__( 'Official source registered; check the notice before applying.', 'studentup' );
	$html .= ' · <a href="' . esc_url( $source_url ) . '" target="_blank" rel="noopener noreferrer">Open official source</a>';
	if ( wp_http_validate_url( $application ) ) {
		$html .= ' · <a href="' . esc_url( $application ) . '" target="_blank" rel="noopener noreferrer">Official application</a>';
	}
	return $html . '</div>';
}

/**
 * v184: deadline cheppakapoyina chala puratana post ni board nunchi teestam.
 *
 * Govt notices ki last date cheppakapovadam common (results / admit card).
 * Kaani 120+ rojula puratana notice "active" ga chupinchadam reader ni confuse
 * chestundi. Filter tho marchachu: add_filter( 'studentup_opportunity_stale_days',
 * fn() => 0 );  (0 = off)
 */
function studentup_opportunity_stale_days() {
	$days = (int) apply_filters( 'studentup_opportunity_stale_days', 120 );
	return max( 0, $days );
}

function studentup_opportunity_is_stale( $post ) {
	$stale = studentup_opportunity_stale_days();
	if ( $stale < 1 ) {
		return false;
	}
	if ( '' !== studentup_opportunity_last_date( $post->ID ) ) {
		return false; // deadline unte adi ne decide chestundi.
	}
	$published = strtotime( (string) $post->post_date_gmt . ' UTC' );
	if ( ! $published ) {
		return false; // date teliyadu → guess cheyyadu.
	}
	return ( time() - $published ) > ( $stale * DAY_IN_SECONDS );
}

/**
 * v184: same recruitment ki kotha post vaste puratana di board nunchi teesestam.
 *
 * Bot `title_key()` (autoblog/opportunity_digest.py) tho same rules: SEO
 * suffixes + year + punctuation teesi first 60 chars; chinna title (<10) ki key
 * ledu (collision risk). Telugu titles ki key raadu — adi kuda safe (dedupe ledu).
 */
function studentup_opportunity_title_key( $title ) {
	$text = strtolower( wp_strip_all_tags( (string) $title ) );
	$text = preg_replace( '/\b20\d{2}\b/', ' ', $text );
	$text = preg_replace(
		'/\b(?:notification|notifications|recruitment|apply online|application|' .
		'complete details|complete guide|latest update|official notification|' .
		'result|results|hall ticket|admit card|merit list|answer key|' .
		'revised|extended|update|job|jobs|posts?|vacancy|vacancies)\b/',
		' ', $text );
	$text = preg_replace( '/[^a-z0-9]+/', '', $text );
	return strlen( $text ) >= 10 ? substr( $text, 0, 60 ) : '';
}

function studentup_opportunity_lower( $text ) {
	$text = (string) $text;
	return function_exists( 'mb_strtolower' ) ? mb_strtolower( $text, 'UTF-8' ) : strtolower( $text );
}

function studentup_opportunity_contains_ci( $haystack, $needle ) {
	return false !== strpos(
		studentup_opportunity_lower( $haystack ),
		studentup_opportunity_lower( $needle )
	);
}

function studentup_opportunity_category_slugs( $post_id ) {
	return array_map( 'sanitize_key', wp_list_pluck( (array) get_the_category( $post_id ), 'slug' ) );
}

function studentup_opportunity_section_for_post( $post_id ) {
	$cats  = studentup_opportunity_category_slugs( $post_id );
	$title = studentup_opportunity_lower( wp_strip_all_tags( get_the_title( $post_id ) . ' ' . get_post_field( 'post_content', $post_id ) ) );
	$blob  = $title . ' ' . implode( ' ', $cats );
	$has   = static function ( $needles ) use ( $blob ) {
		foreach ( $needles as $needle ) {
			if ( studentup_opportunity_contains_ci( $blob, $needle ) ) {
				return true;
			}
		}
		return false;
	};

	// A mela is a useful sub-section even when older posts are stored under
	// Walkin Jobs. Check this before the broader walk-in match.
	if ( $has( array( 'job mela', 'job fair', 'mega job fair', 'employment fair', 'mela' ) ) ) {
		return 'job-melas';
	}
	$aliases = array(
		'ts'           => array( 'ts-jobs', 'ts-govt-jobs', 'telangana-govt-jobs' ),
		'ap'           => array( 'ap-jobs', 'ap-govt-jobs', 'andhra-pradesh-govt-jobs' ),
		'central'      => array( 'central', 'central-jobs', 'central-govt-jobs' ),
		'walkin'       => array( 'walkin', 'walkin-jobs', 'walk-in-jobs' ),
		'outsourcing'  => array( 'outsourcing', 'outsourcing-jobs', 'contract', 'contract-basis' ),
		'software'     => array( 'software', 'software-jobs' ),
		'private'      => array( 'private', 'private-jobs' ),
		'scholarships' => array( 'scholarship', 'scholarships' ),
		'results'      => array( 'result', 'results' ),
		'hall-tickets' => array( 'hall-ticket', 'hall-tickets', 'hallticket' ),
		'current-affairs' => array( 'current', 'current-affairs', 'daily-current-affairs' ),
	);
	foreach ( $aliases as $key => $values ) {
		if ( array_intersect( $cats, $values ) ) {
			return $key;
		}
	}
	// Legacy category repair view: a misfiled old article still lands in the
	// reader's expected section without silently changing its taxonomy.
	if ( $has( array( 'scholarship', 'fellowship', 'nsp', 'epass', 'e-pass' ) ) ) {
		return 'scholarships';
	}
	if ( $has( array_merge( array( 'result', 'scorecard', 'answer key', 'merit list' ), studentup_topic_keywords( 'result' ) ) ) ) {
		return 'results';
	}
	if ( $has( array_merge( array( 'hall ticket', 'admit card', 'call letter' ), studentup_topic_keywords( 'hallticket' ) ) ) ) {
		return 'hall-tickets';
	}
	if ( $has( array( 'current affairs', 'daily current', 'daily gk', 'daily news' ) ) ) {
		return 'current-affairs';
	}
	// v183: outsourcing/contract posts (pipeline lo 'Outsourcing Jobs' category) —
	// idi lekapote aa posts board lo e section lo kanipinchavu.
	if ( $has( array( 'outsourcing', 'contract basis', 'contractual', 'outsourced',
		'guest faculty', 'honorarium' ) ) ) {
		return 'outsourcing';
	}
	if ( $has( array( 'walk-in', 'walk in', 'walkin', 'direct interview' ) ) ) {
		return 'walkin';
	}
	if ( $has( array( 'software', 'developer', 'full stack', 'data analyst', 'devops', 'it job' ) ) ) {
		return 'software';
	}
	if ( $has( array( 'tcs', 'infosys', 'wipro', 'private job', 'off campus', 'mnc' ) ) ) {
		return 'private';
	}
	if ( $has( array( 'tspsc', 'tgpsc', 'telangana', 'ts police', 'gurukul' ) ) ) {
		return 'ts';
	}
	if ( $has( array( 'appsc', 'andhra pradesh', 'ap police', 'apsrtc', 'ap dsc' ) ) ) {
		return 'ap';
	}
	if ( $has( array( 'ssc', 'upsc', 'rrb', 'railway', 'ibps', 'sbi', 'army', 'navy' ) ) ) {
		return 'central';
	}
	return '';
}

function studentup_opportunity_board_posts( $limit = 180 ) {
	$q = new WP_Query(
		array(
			'post_type'           => 'post',
			'post_status'         => 'publish',
			'posts_per_page'      => max( 20, (int) $limit ),
			'orderby'             => 'date',
			'order'               => 'DESC',
			'ignore_sticky_posts' => true,
			'no_found_rows'       => true,
		)
	);
	$out = array();
	foreach ( $q->posts as $post ) {
		$last = studentup_opportunity_last_date( $post->ID );
		if ( studentup_opportunity_is_expired( $last ) ) {
			continue; // last date ayyipoyindi → board nunchi out.
		}
		if ( studentup_opportunity_is_stale( $post ) ) {
			continue; // v184: deadline lekunda 120+ rojula puratana → out.
		}
		$section = studentup_opportunity_section_for_post( $post->ID );
		if ( '' === $section ) {
			continue;
		}
		$apply_url = trim( (string) get_post_meta( $post->ID, 'studentup_apply_url', true ) );
		if ( ! wp_http_validate_url( $apply_url ) ) {
			$apply_url = '';
		}
		$source_url = trim( (string) get_post_meta( $post->ID, 'studentup_source_url', true ) );
		if ( ! wp_http_validate_url( $source_url ) ) {
			$source_url = '';
		}
		$source_checked = trim( (string) get_post_meta( $post->ID, 'studentup_source_checked', true ) );
		if ( ! preg_match( '/^20\d{2}-\d{2}-\d{2}$/', $source_checked ) ) {
			$source_checked = '';
		}
		$out[] = array(
			'id'         => (int) $post->ID,
			'title'      => get_the_title( $post->ID ),
			'link'       => get_permalink( $post->ID ),
			'last_date'  => $last,
			'days_left'  => studentup_opportunity_days_left( $last ),
			'section'    => $section,
			'qualification' => trim( (string) get_post_meta( $post->ID, 'studentup_qual', true ) ),
			'salary'     => trim( (string) get_post_meta( $post->ID, 'studentup_salary', true ) ),
			'vacancies'  => trim( (string) get_post_meta( $post->ID, 'studentup_vacancies', true ) ),
			'apply_url'  => $apply_url,
			'source_url' => $source_url,
			'source_checked' => $source_checked,
			'date'       => get_the_date( 'c', $post->ID ),
			'updated'    => get_the_modified_date( 'c', $post->ID ),
			'thumbnail'  => get_the_post_thumbnail_url( $post->ID, 'studentup-card' ),
		);
	}
	// v184: same recruitment ki kotha post vaste puratana di teesestam
	// (newest wins; okate section + okate title key).
	$by_key = array();
	$deduped = array();
	foreach ( $out as $row ) {
		$key = $row['section'] . '|' . studentup_opportunity_title_key( $row['title'] );
		if ( '|' === substr( $key, -1 ) ) {
			$deduped[] = $row;
			continue;
		}
		if ( ! isset( $by_key[ $key ] ) ) {
			$by_key[ $key ] = count( $deduped );
			$deduped[] = $row;
			continue;
		}
		$idx = $by_key[ $key ];
		if ( strtotime( $row['date'] ) > strtotime( $deduped[ $idx ]['date'] ) ) {
			$deduped[ $idx ] = $row;
		}
	}
	$out = $deduped;
	// Closing dates are more useful at the top; undated posts follow newest-first.
	usort(
		$out,
		static function ( $a, $b ) {
			$ad = null === $a['days_left'] ? 999999 : (int) $a['days_left'];
			$bd = null === $b['days_left'] ? 999999 : (int) $b['days_left'];
			if ( $ad !== $bd ) {
				return $ad <=> $bd;
			}
			return strcmp( (string) $b['date'], (string) $a['date'] );
		}
	);
	return $out;
}

/**
 * Fail-closed homepage relevance check: taxonomy alone is not enough when old
 * editorial guides were filed under a government-jobs category. Keep actual
 * recruitment/exam notices; reject scholarships, results, explainers, private
 * company hiring and other categories even when their category tags are wrong.
 *
 * @param array<string,mixed> $row Opportunity row.
 * @return bool
 */
function studentup_home_opportunity_is_notice( $row ) {
	if ( ! is_array( $row ) || empty( $row['id'] ) || empty( $row['title'] )
		|| ! in_array( (string) ( $row['section'] ?? '' ), array( 'ts', 'ap', 'central' ), true ) ) {
		return false;
	}

	$categories = studentup_opportunity_category_slugs( (int) $row['id'] );
	$non_job_categories = array(
		'scholarship', 'scholarships', 'fellowship', 'fellowships',
		'internship', 'internships', 'result', 'results', 'hall-ticket', 'hall-tickets',
		'hallticket', 'current', 'current-affairs', 'education-news', 'success-stories',
		'admission', 'admissions', 'private', 'private-jobs', 'software', 'software-jobs',
		'walkin', 'walkin-jobs', 'walk-in-jobs', 'outsourcing', 'outsourcing-jobs',
		'part-time', 'part-time-jobs', 'abroad', 'abroad-jobs', 'job-mela', 'job-melas',
		'job-fairs',
	);
	if ( array_intersect( $categories, $non_job_categories ) ) {
		return false;
	}

	$title = studentup_opportunity_lower( wp_strip_all_tags( (string) $row['title'] ) );
	$editorial_or_other = '/\\b(?:internships?|scholarships?|fellowships?|admissions?|hall[ -]?tickets?|admit[ -]?cards?|results?|merit lists?|scorecards?|cut[ -]?offs?|answer[ -]?keys?|selection lists?|selected candidates?|previous[ -]?(?:papers?|questions?)|current affairs|success stories|syllab(?:us|i)|preparation|preparing|fitness|career advice|study plan|exam tips|guide|work from home|private[ -]?(?:compan(?:y|ies)|sector|jobs?|hiring)|mnc|bpo|top\\s+\\d+\\s+(?:government\\s+)?jobs?)\\b|(?:స్కాలర్.?షిప్|ఇంటర్న్.?షిప్|హాల్.?టికెట్|అడ్మిట్.?కార్డు|ఫలితాలు?|ప్రిపరేషన్|గైడ్|సిద్ధం.?కావాలి)/iu';
	if ( preg_match( $editorial_or_other, $title ) ) {
		return false;
	}

	// Company names commonly misfiled in Central Govt categories are private hiring.
	if ( preg_match( '/\b(?:infor|infosys|tcs|wipro|hcl|accenture|amazon|google|microsoft|ibm|deloitte|cognizant|capgemini|tech mahindra|zoho|oracle|flipkart)\b/iu', $title ) ) {
		return false;
	}

	$recruitment_signal = '/\b(?:recruit(?:ment|ing)?|notification|vacanc(?:y|ies)|apply(?: online)?|application|posts?|openings?|hiring|exam(?:ination)?|selection|interviews?|tspsc|tgpsc|appsc|upsc|ssc|rrb|ibps|sbi|nabard|railway|police|constable|sub[ -]?inspector|group[ -]?[1-4]|teacher|forest service|defen[cs]e|army|navy)\b|(?:నియామక|రిక్రూట్.?మెంట్|నోటిఫికేషన్|ఖాళీలు?|దరఖాస్తు|ఉద్యోగ ప్రకటన|పోస్టులు)/iu';
	return (bool) preg_match( $recruitment_signal, $title );
}

/**
 * Homepage rows: only active Telangana, Andhra Pradesh and Central-government
 * notices (not generic guides or other categories), sorted newest-published
 * first. The board helper has already removed expired/stale notices and duplicates.
 *
 * @return array<int,array<string,mixed>>
 */
function studentup_home_opportunity_rows() {
	static $rows = null;
	if ( null !== $rows ) {
		return $rows;
	}

	$allowed = array( 'ts', 'ap', 'central' );
	$rows    = array_values(
		array_filter(
			studentup_opportunity_board_posts( 400 ),
			static function ( $row ) use ( $allowed ) {
				return isset( $row['section'] )
					&& in_array( $row['section'], $allowed, true )
					&& studentup_home_opportunity_is_notice( $row );
			}
		)
	);
	usort(
		$rows,
		static function ( $a, $b ) {
			$ad = isset( $a['date'] ) ? strtotime( (string) $a['date'] ) : 0;
			$bd = isset( $b['date'] ) ? strtotime( (string) $b['date'] ) : 0;
			if ( $ad === $bd ) {
				return (int) $b['id'] <=> (int) $a['id'];
			}
			return $bd <=> $ad;
		}
	);
	return $rows;
}

function studentup_opportunity_section_label( $section ) {
	$labels = array(
		'ts'      => 'Telangana',
		'ap'      => 'Andhra Pradesh',
		'central' => 'Central Govt',
	);
	return isset( $labels[ $section ] ) ? $labels[ $section ] : 'Government Jobs';
}

function studentup_opportunity_board_url() {
	return home_url( '/latest-jobs/' );
}

function studentup_opportunity_render_card( $row ) {
	$days       = $row['days_left'];
	$days_value = null === $days ? 'unknown' : (string) $days;
	$updated    = ! empty( $row['updated'] ) ? strtotime( $row['updated'] ) : false;
	?>
	<article class="su-op-card" data-su-op-card data-su-op-title="<?php echo esc_attr( studentup_opportunity_lower( wp_strip_all_tags( $row['title'] ) ) ); ?>" data-su-op-section="<?php echo esc_attr( $row['section'] ); ?>" data-su-op-qual="<?php echo esc_attr( studentup_opportunity_lower( (string) $row['qualification'] ) ); ?>" data-su-op-days="<?php echo esc_attr( $days_value ); ?>">
		<div class="su-op-card-copy">
			<h3><a href="<?php echo esc_url( $row['link'] ); ?>"><?php echo esc_html( $row['title'] ); ?></a></h3>
			<?php if ( ! empty( $row['qualification'] ) ) : ?>
				<p class="su-op-qual"><?php echo studentup_ui_icon( 'school', 13 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> <?php echo esc_html( studentup_qual_pretty( $row['qualification'] ) ); ?></p>
			<?php endif; ?>
			<?php if ( ! empty( $row['salary'] ) || ! empty( $row['vacancies'] ) ) : ?>
				<p class="su-op-facts">
					<?php if ( ! empty( $row['vacancies'] ) ) : ?>
						<span class="su-op-fact"><?php echo studentup_ui_icon( 'work', 12 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> <?php echo esc_html( $row['vacancies'] ); ?> posts</span>
					<?php endif; ?>
					<?php if ( ! empty( $row['salary'] ) ) : ?>
						<span class="su-op-fact su-op-fact-pay"><?php echo studentup_ui_icon( 'wallet', 12 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> <?php echo esc_html( $row['salary'] ); ?></span>
					<?php endif; ?>
				</p>
			<?php endif; ?>
			<?php if ( '' !== $row['last_date'] ) : ?>
				<?php $date_class = 'su-op-date' . ( ( null !== $days && $days <= 7 ) ? ' is-soon' : '' ); ?>
				<p class="<?php echo esc_attr( $date_class ); ?>">
					<?php echo studentup_ui_icon( 'calendar', 13 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> Last date: <strong><?php echo esc_html( wp_date( 'd M Y', strtotime( $row['last_date'] . ' 12:00:00' ) ) ); ?></strong>
					<?php if ( null !== $days ) : ?>
						<span><?php echo esc_html( 0 === $days ? 'Last day today' : $days . ' days left' ); ?></span>
					<?php endif; ?>
				</p>
			<?php else : ?>
				<p class="su-op-date is-unknown"><?php echo studentup_ui_icon( 'calendar', 13 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> Last date: <strong>Not announced</strong></p>
			<?php endif; ?>
			<?php if ( $updated ) : ?>
				<p class="su-op-updated">Updated <?php echo esc_html( wp_date( 'd M Y', $updated ) ); ?></p>
			<?php endif; ?>
			<?php if ( ! empty( $row['source_url'] ) ) : ?>
				<p class="su-op-source"><?php echo studentup_ui_icon( 'check', 12 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> Source checked<?php echo ! empty( $row['source_checked'] ) ? ' ' . esc_html( wp_date( 'd M Y', strtotime( $row['source_checked'] . ' 12:00:00' ) ) ) : ''; ?> · <a href="<?php echo esc_url( $row['source_url'] ); ?>" target="_blank" rel="noopener noreferrer">Official source</a></p>
			<?php endif; ?>
		</div>
		<div class="su-op-actions">
			<a class="su-op-open" href="<?php echo esc_url( $row['link'] ); ?>" aria-label="Open <?php echo esc_attr( $row['title'] ); ?>">Details&nbsp;→</a>
			<?php if ( ! empty( $row['apply_url'] ) ) : ?>
				<a class="su-op-apply" href="<?php echo esc_url( $row['apply_url'] ); ?>" target="_blank" rel="noopener noreferrer" aria-label="Open official application link for <?php echo esc_attr( $row['title'] ); ?>">Official Apply</a>
			<?php endif; ?>
			<?php if ( function_exists( 'studentup_save_button' ) ) : ?>
				<?php echo wp_kses_post( studentup_save_button( $row['id'], 'su-save-opportunity' ) ); ?>
			<?php endif; ?>
			<?php if ( function_exists( 'studentup_tool_buttons' ) ) : ?>
				<?php echo wp_kses_post( studentup_tool_buttons( $row['id'], 'card' ) ); ?>
			<?php endif; ?>
		</div>
	</article>
	<?php
}


function studentup_home_opportunity_render_card( $row ) {
	$section = isset( $row['section'] ) ? sanitize_key( (string) $row['section'] ) : '';
	$slug    = array(
		'ts'      => 'ts-jobs',
		'ap'      => 'ap-jobs',
		'central' => 'central-jobs',
	);
	$data_cat = isset( $slug[ $section ] ) ? $slug[ $section ] : '';
	$icon     = 'central' === $section ? 'flag' : 'bank';
	$qual     = isset( $row['qualification'] ) ? trim( (string) $row['qualification'] ) : '';
	$last     = isset( $row['last_date'] ) ? (string) $row['last_date'] : '';
	$image    = ! empty( $row['thumbnail'] ) ? (string) $row['thumbnail'] : '';
	?>
	<article class="news su-op-card" data-su-home-card data-cat="<?php echo esc_attr( $data_cat ); ?>" data-qual="<?php echo esc_attr( strtolower( $qual ) ); ?>" data-last="<?php echo esc_attr( $last ); ?>">
		<div class="su-op-thumb" aria-hidden="true">
			<?php if ( $image ) : ?>
				<img src="<?php echo esc_url( $image ); ?>" alt="" width="144" height="112" loading="lazy" decoding="async">
			<?php else : ?>
				<span class="su-op-thumb-fallback"><?php echo studentup_ui_icon( $icon, 26 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?></span>
			<?php endif; ?>
		</div>
		<div class="su-op-card-main">
			<div class="su-op-topline"><span class="su-op-region"><?php echo esc_html( studentup_opportunity_section_label( $section ) ); ?></span></div>
			<h3><a href="<?php echo esc_url( $row['link'] ); ?>"><?php echo esc_html( $row['title'] ); ?></a></h3>
			<p class="su-op-meta"><span>Qualification</span><strong><?php echo esc_html( $qual ? studentup_qual_pretty( $qual ) : 'Not specified' ); ?></strong></p>
			<p class="su-op-meta su-op-deadline"><span>Last date</span>
				<strong><?php echo esc_html( $last ? wp_date( 'd M Y', strtotime( $last . ' 12:00:00' ) ) : 'Not announced' ); ?></strong>
			</p>
			<div class="su-op-actions">
				<a class="su-op-open" href="<?php echo esc_url( $row['link'] ); ?>">Details</a>
				<?php if ( ! empty( $row['apply_url'] ) ) : ?>
					<a class="su-op-apply" href="<?php echo esc_url( $row['apply_url'] ); ?>" target="_blank" rel="noopener noreferrer">Official Apply</a>
				<?php endif; ?>
			</div>
		</div>
	</article>
	<?php
}

function studentup_opportunities_template( $template ) {
	if ( get_query_var( 'studentup_opportunities' ) ) {
		global $wp_query;
		if ( $wp_query ) {
			$wp_query->is_404 = false;
		}
		status_header( 200 );
		nocache_headers();
		return get_template_directory() . '/page-opportunities.php';
	}
	return $template;
}
add_filter( 'template_include', 'studentup_opportunities_template' );

function studentup_opportunities_rewrite() {
	add_rewrite_rule( '^latest-jobs/?$', 'index.php?studentup_opportunities=1', 'top' );
}
add_action( 'init', 'studentup_opportunities_rewrite', 1 );

function studentup_opportunities_query_var( $vars ) {
	$vars[] = 'studentup_opportunities';
	return $vars;
}
add_filter( 'query_vars', 'studentup_opportunities_query_var' );

function studentup_opportunities_activate() {
	studentup_opportunities_rewrite();
	flush_rewrite_rules();
}
add_action( 'after_switch_theme', 'studentup_opportunities_activate' );
