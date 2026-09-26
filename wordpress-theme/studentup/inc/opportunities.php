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
		'ts'          => array( 'label' => 'Telangana Government Jobs', 'icon' => '🏛️' ),
		'ap'          => array( 'label' => 'Andhra Pradesh Government Jobs', 'icon' => '🏛️' ),
		'central'     => array( 'label' => 'Central Government Jobs', 'icon' => '🇮🇳' ),
		'walkin'      => array( 'label' => 'Walk-in Jobs', 'icon' => '🚶' ),
		'job-melas'   => array( 'label' => 'Job Melas & Job Fairs', 'icon' => '🤝' ),
		'software'    => array( 'label' => 'Software Jobs', 'icon' => '💻' ),
		'private'     => array( 'label' => 'Private Jobs', 'icon' => '🏢' ),
		'scholarships'=> array( 'label' => 'Scholarships', 'icon' => '🎓' ),
		'results'     => array( 'label' => 'Results', 'icon' => '📄' ),
		'hall-tickets' => array( 'label' => 'Hall Tickets', 'icon' => '🎫' ),
		'current-affairs' => array( 'label' => 'Daily Current Affairs', 'icon' => '📰' ),
	);
}

function studentup_opportunity_last_date( $post_id ) {
	$iso = trim( (string) get_post_meta( $post_id, 'studentup_last_date', true ) );
	return preg_match( '/^20\d{2}-\d{2}-\d{2}$/', $iso ) ? $iso : '';
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

function studentup_opportunity_category_slugs( $post_id ) {
	return array_map( 'sanitize_key', wp_list_pluck( (array) get_the_category( $post_id ), 'slug' ) );
}

function studentup_opportunity_section_for_post( $post_id ) {
	$cats  = studentup_opportunity_category_slugs( $post_id );
	$title = mb_strtolower( wp_strip_all_tags( get_the_title( $post_id ) . ' ' . get_post_field( 'post_content', $post_id ) ) );
	$blob  = $title . ' ' . implode( ' ', $cats );
	$has   = static function ( $needles ) use ( $blob ) {
		foreach ( $needles as $needle ) {
			if ( false !== mb_strpos( $blob, mb_strtolower( $needle ) ) ) {
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
	if ( $has( array( 'result', 'scorecard', 'answer key', 'merit list', 'ఫలిత' ) ) ) {
		return 'results';
	}
	if ( $has( array( 'hall ticket', 'admit card', 'call letter', 'హాల్ టికెట్' ) ) ) {
		return 'hall-tickets';
	}
	if ( $has( array( 'current affairs', 'daily current', 'daily gk', 'daily news' ) ) ) {
		return 'current-affairs';
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
			continue;
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
			'apply_url'  => $apply_url,
			'source_url' => $source_url,
			'source_checked' => $source_checked,
			'date'       => get_the_date( 'c', $post->ID ),
			'updated'    => get_the_modified_date( 'c', $post->ID ),
			'thumbnail'  => get_the_post_thumbnail_url( $post->ID, 'studentup-card' ),
		);
	}
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

function studentup_opportunity_board_url() {
	return home_url( '/latest-jobs/' );
}

function studentup_opportunity_render_card( $row ) {
	$days       = $row['days_left'];
	$days_value = null === $days ? 'unknown' : (string) $days;
	$updated    = ! empty( $row['updated'] ) ? strtotime( $row['updated'] ) : false;
	?>
	<article class="su-op-card" data-su-op-card data-su-op-title="<?php echo esc_attr( mb_strtolower( wp_strip_all_tags( $row['title'] ) ) ); ?>" data-su-op-section="<?php echo esc_attr( $row['section'] ); ?>" data-su-op-qual="<?php echo esc_attr( mb_strtolower( (string) $row['qualification'] ) ); ?>" data-su-op-days="<?php echo esc_attr( $days_value ); ?>">
		<div class="su-op-card-copy">
			<h3><a href="<?php echo esc_url( $row['link'] ); ?>"><?php echo esc_html( $row['title'] ); ?></a></h3>
			<?php if ( ! empty( $row['qualification'] ) ) : ?>
				<p class="su-op-qual">🎓 <?php echo esc_html( $row['qualification'] ); ?></p>
			<?php endif; ?>
			<?php if ( '' !== $row['last_date'] ) : ?>
				<?php $date_class = 'su-op-date' . ( ( null !== $days && $days <= 7 ) ? ' is-soon' : '' ); ?>
				<p class="<?php echo esc_attr( $date_class ); ?>">
					🗓️ Last date: <strong><?php echo esc_html( wp_date( 'd M Y', strtotime( $row['last_date'] . ' 12:00:00' ) ) ); ?></strong>
					<?php if ( null !== $days ) : ?>
						<span><?php echo esc_html( 0 === $days ? 'Last day today' : $days . ' days left' ); ?></span>
					<?php endif; ?>
				</p>
			<?php else : ?>
				<p class="su-op-date is-unknown">🗓️ Last date: <strong>Not announced</strong></p>
			<?php endif; ?>
			<?php if ( $updated ) : ?>
				<p class="su-op-updated">Updated <?php echo esc_html( wp_date( 'd M Y', $updated ) ); ?></p>
			<?php endif; ?>
			<?php if ( ! empty( $row['source_url'] ) ) : ?>
				<p class="su-op-source">✓ Source checked<?php echo ! empty( $row['source_checked'] ) ? ' ' . esc_html( wp_date( 'd M Y', strtotime( $row['source_checked'] . ' 12:00:00' ) ) ) : ''; ?> · <a href="<?php echo esc_url( $row['source_url'] ); ?>" target="_blank" rel="noopener noreferrer">Official source</a></p>
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
