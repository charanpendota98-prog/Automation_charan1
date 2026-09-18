<?php
/**
 * Comments template — clean, fast, Telugu labels (top-theme standard).
 *
 * Skip link ledu, spam-safe (Akismet/plugin tho), avatar lazy, link-flood guard
 * `inc/security.php` lo. Comments OFF unna post ki idi render avvadu.
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

if ( post_password_required() ) {
	return;
}
?>
<section id="comments" class="su-comments">
	<?php if ( have_comments() ) : ?>
		<h2 class="su-comments-title">
			<?php
			$su_count = (int) get_comments_number();
			printf(
				/* translators: %s: comment count */
				esc_html( _n( '%s కామెంట్', '%s కామెంట్లు', $su_count, 'studentup' ) ),
				esc_html( number_format_i18n( $su_count ) )
			);
			?>
		</h2>
		<ol class="su-comment-list">
			<?php
			wp_list_comments(
				array(
					'style'      => 'ol',
					'short_ping' => true,
					'avatar_size' => 40,
				)
			);
			?>
		</ol>
		<?php
		the_comments_pagination(
			array(
				'prev_text' => '← ' . esc_html__( 'పాత కామెంట్లు', 'studentup' ),
				'next_text' => esc_html__( 'కొత్త కామెంట్లు', 'studentup' ) . ' →',
			)
		);
		?>
	<?php endif; ?>

	<?php if ( ! comments_open() && get_comments_number() && post_type_supports( get_post_type(), 'comments' ) ) : ?>
		<p class="su-comments-closed"><?php esc_html_e( 'కామెంట్లు మూసివేయబడ్డాయి.', 'studentup' ); ?></p>
	<?php endif; ?>

	<?php
	comment_form(
		array(
			'title_reply'          => esc_html__( 'మీ అభిప్రాయం రాయండి', 'studentup' ),
			'title_reply_to'       => esc_html__( '%s కి జవాబు రాయండి', 'studentup' ),
			'label_submit'         => esc_html__( 'కామెంట్ పంపండి', 'studentup' ),
			'class_submit'         => 'su-btn',
			'comment_notes_before' => '<p class="su-comment-note">'
				. esc_html__( 'మీ ఇమెయిల్ ప్రచురించబడదు. అధికారిక సమాచారం కోసం మాత్రమే వ్యక్తిగత వివరాలు ఇవ్వండి.', 'studentup' )
				. '</p>',
			'comment_field'        => '<p class="comment-form-comment"><label for="comment">'
				. esc_html__( 'కామెంట్', 'studentup' ) . '</label>'
				. '<textarea id="comment" name="comment" cols="45" rows="5" required></textarea></p>',
		)
	);
	?>
</section>
