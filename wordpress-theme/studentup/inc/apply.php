<?php
/**
 * v131: Apply conversion layer.
 *
 * 1. Sticky "Apply online" action bar on single job posts (CTR booster).
 * 2. Deadline countdown chip ("closes in N days") driven by studentup_last_date.
 * 3. JobPosting JSON-LD built from the admin job box meta (Google Jobs eligible).
 *
 * Every surface is opt-in: it only renders when the post actually carries
 * apply/last-date meta, so editorial posts stay untouched.
 *
 * @package StudentUp
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Read the job meta for a post in one shot.
 *
 * @param int $post_id Post ID.
 * @return array Normalised job fields.
 */
function studentup_apply_meta( $post_id ) {
	$keys = array(
		'last'   => 'studentup_last_date',
		'salary' => 'studentup_salary',
		'vac'    => 'studentup_vacancies',
		'qual'   => 'studentup_qual',
		'apply'  => 'studentup_apply_url',
		'source' => 'studentup_source_url',
	);
	$out  = array();
	foreach ( $keys as $short => $key ) {
		$out[ $short ] = trim( (string) get_post_meta( (int) $post_id, $key, true ) );
	}
	return $out;
}

/**
 * Days left until the last date (null when unknown/invalid).
 *
 * @param string $last Y-m-d string.
 * @return int|null Days remaining.
 */
function studentup_apply_days_left( $last ) {
	if ( ! preg_match( '/^20\d\d-\d\d-\d\d$/', $last ) ) {
		return null;
	}
	$end = strtotime( $last . ' 23:59:59' );
	if ( ! $end ) {
		return null;
	}
	$diff = $end - (int) current_time( 'timestamp' );
	return (int) floor( $diff / DAY_IN_SECONDS );
}

/**
 * Should the apply layer run for the current request?
 *
 * @return bool True when a single job post with apply data is shown.
 */
function studentup_apply_active() {
	if ( ! is_singular( 'post' ) ) {
		return false;
	}
	if ( function_exists( 'studentup_opt' ) && ! studentup_opt( 'apply_bar', '1' ) ) {
		return false;
	}
	$meta = studentup_apply_meta( get_the_ID() );
	return ( '' !== $meta['apply'] || '' !== $meta['last'] );
}

/**
 * v175: CTA label + context by post type (hall ticket / result / job).
 *
 * Hall-ticket download post meeda "Apply online" ani cheppadam wrong UX —
 * student "apply" cheyyaledu, hall ticket download chestunnadu. Category
 * prakaram label maarutundi (alias-aware).
 *
 * @param int $post_id Post id.
 * @return array{label:string,kind:string}
 */
function studentup_apply_cta( $post_id = 0 ) {
	$post_id = $post_id ? (int) $post_id : get_the_ID();
	$labels  = array(
		'hall-tickets'     => array( 'Download Hall Ticket', 'hallticket' ),
		'hall-ticket'      => array( 'Download Hall Ticket', 'hallticket' ),
		'results'          => array( 'View Result', 'result' ),
		'admissions'       => array( 'Open Official Portal', 'admission' ),
	);
	if ( function_exists( 'studentup_used_term' ) ) {
		$ids = wp_get_post_categories( $post_id );
		$ids = array_map( 'intval', $ids );
		foreach ( $labels as $slug => $info ) {
			$term = studentup_used_term( $slug );
			if ( $term && in_array( (int) $term->term_id, $ids, true ) ) {
				return array( 'label' => $info[0], 'kind' => $info[1] );
			}
		}
	}
	return array( 'label' => 'Apply online', 'kind' => 'job' );
}

/**
 * v175: ee post REAL job opportunity aa? (JobPosting schema gate).
 *
 * Hall-ticket/result/admit-card posts lo qual + last_date unnaavu — anduke
 * v174 varaku avi kuda JobPosting schema pattukunevi (Google Jobs ki spam
 * signal). Ippudu: non-job categories levu + okate job signal (apply_url /
 * numeric vacancies / salary) kavali + expired postings schema levu
 * (Google guideline: remove expired).
 *
 * @param array $meta Normalised job fields.
 * @return bool
 */
function studentup_apply_is_job( $meta ) {
	if ( function_exists( 'studentup_used_term' ) ) {
		$ids    = array_map( 'intval', wp_get_post_categories( get_the_ID() ) );
		$nonjob = array( 'hall-tickets', 'hall-ticket', 'results', 'success-stories', 'current-affairs', 'daily-quiz', 'exam-tips', 'online-education', 'admissions' );
		foreach ( $nonjob as $slug ) {
			$term = studentup_used_term( $slug );
			if ( $term && in_array( (int) $term->term_id, $ids, true ) ) {
				return false;
			}
		}
	}
	$has_signal = ( '' !== $meta['apply'] )
		|| ( '' !== $meta['vac'] && is_numeric( str_replace( ',', '', $meta['vac'] ) ) )
		|| '' !== $meta['salary'];
	return $has_signal;
}

/**
 * Sticky apply bar markup.
 *
 * @return void
 */
function studentup_apply_bar() {
	if ( ! studentup_apply_active() ) {
		return;
	}
	$meta = studentup_apply_meta( get_the_ID() );
	$days = studentup_apply_days_left( $meta['last'] );
	$url  = '' !== $meta['apply'] ? $meta['apply'] : $meta['source'];

	$chip  = '';
	$state = 'open';
	if ( null !== $days ) {
		if ( $days < 0 ) {
			$chip  = esc_html__( 'Last date over', 'studentup' );
			$state = 'closed';
		} elseif ( 0 === $days ) {
			$chip  = esc_html__( 'Closes today', 'studentup' );
			$state = 'urgent';
		} elseif ( $days <= 3 ) {
			/* translators: %d: days left. */
			$chip  = sprintf( esc_html__( 'Only %d days left', 'studentup' ), $days );
			$state = 'urgent';
		} else {
			/* translators: %d: days left. */
			$chip = sprintf( esc_html__( '%d days left', 'studentup' ), $days );
		}
	}
	?>
	<div class="su-applybar su-applybar--<?php echo esc_attr( $state ); ?>" role="complementary"
		aria-label="<?php esc_attr_e( 'Apply actions', 'studentup' ); ?>">
		<div class="su-applybar-in">
			<div class="su-applybar-meta">
				<strong class="su-applybar-title"><?php echo esc_html( get_the_title() ); ?></strong>
				<span class="su-applybar-sub">
					<?php if ( '' !== $chip ) : ?>
						<span class="su-applychip"><?php echo esc_html( $chip ); ?></span>
					<?php endif; ?>
					<?php if ( '' !== $meta['vac'] ) : ?>
						<span class="su-applyfact"><?php echo esc_html( $meta['vac'] ); ?> <?php esc_html_e( 'posts', 'studentup' ); ?></span>
					<?php endif; ?>
					<?php if ( '' !== $meta['qual'] && function_exists( 'studentup_qual_pretty' ) ) : ?>
						<span class="su-applyfact"><?php echo esc_html( studentup_qual_pretty( $meta['qual'] ) );   // v175: raw keys kaadu — human labels ?></span>
					<?php endif; ?>
				</span>
			</div>
			<?php if ( '' !== $url && 'closed' !== $state ) : ?>
				<?php $cta = studentup_apply_cta();   // v175: hall ticket/result post lo "Apply online" kaadu. ?>
				<a class="su-applybtn" href="<?php echo esc_url( $url ); ?>"
					rel="nofollow noopener" target="_blank"
					aria-label="<?php echo esc_attr( $cta['label'] ); ?>"
					data-su-apply="1"><?php echo esc_html( $cta['label'] ); ?></a>
			<?php else : ?>
				<a class="su-applybtn su-applybtn--ghost" href="#su-details"><?php esc_html_e( 'Full details', 'studentup' ); ?></a>
			<?php endif; ?>
		</div>
	</div>
	<?php
}
add_action( 'wp_footer', 'studentup_apply_bar', 20 );

/**
 * Body class so other sticky elements can move out of the way.
 *
 * @param array $classes Body classes.
 * @return array Filtered classes.
 */
function studentup_apply_body_class( $classes ) {
	if ( studentup_apply_active() ) {
		$classes[] = 'su-has-applybar';
	}
	return $classes;
}
add_filter( 'body_class', 'studentup_apply_body_class' );

/**
 * JobPosting JSON-LD for single posts that carry real job meta.
 *
 * @return void
 */
function studentup_apply_schema() {
	if ( ! is_singular( 'post' ) ) {
		return;
	}
	$meta = studentup_apply_meta( get_the_ID() );
	if ( '' === $meta['last'] || '' === $meta['qual'] ) {
		return;
	}
	if ( ! preg_match( '/^20\d\d-\d\d-\d\d$/', $meta['last'] ) ) {
		return;
	}
	/*
	 * v175 REAL FIX: hall-ticket/result posts (qual + last_date untayi kaani
	 * job postings kaadu) ki JobPosting attach avvadam valla Google Jobs lo
	 * spam/quality signal. Ippudu:
	 *   1) non-job categories (hall tickets · results · stories · tips …) skip
	 *   2) okate real job signal kavali (apply_url / numeric vacancies / salary)
	 *   3) expired postings ki schema vaddu (Google: remove expired).
	 */
	if ( ! studentup_apply_is_job( $meta ) ) {
		return;
	}
	if ( function_exists( 'studentup_opportunity_is_expired' ) && studentup_opportunity_is_expired( $meta['last'] ) ) {
		return;
	}
	$data = array(
		'@context'           => 'https://schema.org',
		'@type'              => 'JobPosting',
		'title'              => wp_strip_all_tags( get_the_title() ),
		'description'        => wp_strip_all_tags( get_the_excerpt() ),
		'datePosted'         => get_the_date( 'c' ),
		'validThrough'       => $meta['last'] . 'T23:59:59+05:30',
		'employmentType'     => 'FULL_TIME',
		'educationRequirements' => function_exists( 'studentup_qual_pretty' ) ? studentup_qual_pretty( $meta['qual'] ) : $meta['qual'],   // v175: human labels.
		'hiringOrganization' => array(
			'@type' => 'Organization',
			'name'  => get_bloginfo( 'name' ),
			'url'   => home_url( '/' ),
		),
		'jobLocation'        => array(
			'@type'   => 'Place',
			'address' => array(
				'@type'          => 'PostalAddress',
				'addressCountry' => 'IN',
			),
		),
		'directApply'        => ( '' !== $meta['apply'] ),
	);
	if ( '' !== $meta['vac'] && is_numeric( str_replace( ',', '', $meta['vac'] ) ) ) {
		$data['totalJobOpenings'] = (int) str_replace( ',', '', $meta['vac'] );   // v175: "12,000" kuda numeric ga.
	}
	echo "\n<script type=\"application/ld+json\">" .
		wp_json_encode( $data, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE ) .
		"</script>\n";
}
add_action( 'wp_head', 'studentup_apply_schema', 8 );
