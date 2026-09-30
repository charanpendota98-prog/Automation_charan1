<?php
/**
 * Text-to-Speech Web Audio Article Reader.
 *
 * Provides in-browser speech synthesis for article headlines and key summary details.
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Render Audio Article Reader Bar.
 *
 * @return void
 */
function studentup_audio_reader() {
	if ( ! is_singular( 'post' ) || ! studentup_opt( 'audio_reader', '1' ) ) {
		return;
	}

	$post_id   = get_the_ID();
	$title     = get_the_title( $post_id );
	$vacancies = get_post_meta( $post_id, 'studentup_vacancies', true );
	$last_date = get_post_meta( $post_id, 'studentup_last_date', true );

	// Audio summary script for speech synthesis
	$speech_parts = array( $title );
	if ( $vacancies ) {
		$speech_parts[] = 'Total vacancies ' . $vacancies . '.';
	}
	if ( $last_date ) {
		$speech_parts[] = 'Last date to apply is ' . $last_date . '.';
	}
	$speech_parts[] = 'Read the full notification details below.';
	$speech_text = implode( ' ', $speech_parts );

	?>
	<div class="su-audio-reader-box" id="su-audio-box" data-speech="<?php echo esc_attr( $speech_text ); ?>" aria-label="Audio Article Reader">
		<div class="su-audio-left">
			<button type="button" id="su-audio-btn" class="su-audio-btn" aria-label="Listen to audio summary">
				<span class="su-audio-icon" id="su-audio-icon"><?php echo studentup_ui_icon( 'speaker', 16 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?></span>
				<span class="su-audio-label" id="su-audio-label">Listen to Article</span>
			</button>
			<div class="su-audio-waves" id="su-audio-waves" aria-hidden="true" style="display:none;">
				<span class="su-wave-bar"></span>
				<span class="su-wave-bar"></span>
				<span class="su-wave-bar"></span>
				<span class="su-wave-bar"></span>
			</div>
		</div>
		<div class="su-audio-controls" id="su-audio-controls" style="display:none;">
			<button type="button" id="su-audio-stop" class="su-audio-ctrl-btn" aria-label="Stop audio">⏹ Stop</button>
			<span class="su-audio-speed" id="su-audio-speed-btn" role="button" tabindex="0" title="Change speed">1.0x</span>
		</div>
	</div>
	<?php
}
