<?php
/**
 * v91: Telegram tools — theme side (theme 1.9.2).
 *
 * Bot side (`autoblog/telegram_tools.py`) = test/broadcast/alert CLI.
 * Theme side (idi) = readers ki channel reach:
 *   1) `studentup_tg_channel_url()` — option override (`telegram_channel_url`)
 *      unte adi (PRIVATE channel invite link support: t.me/+AbC… / -100 bot
 *      posting bot lo), lekapote social_telegram username → t.me/<user>.
 *   2) `studentup_tg_join_block()` — compact join chip (footer lo render;
 *      icon + Telugu CTA). AdSense-safe: ad slots ni block cheyyadu.
 *   3) `studentup_tg_share_url()` — single post TG share link
 *      (t.me/share/url?url=…&text=…) — v89 share row lo extend.
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Channel URL resolve — override option first, username fallback second.
 *
 * @return string https URL (empty kaadu — worst case default channel).
 */
function studentup_tg_channel_url() {
	$override = trim( (string) studentup_opt( 'telegram_channel_url', '' ) );
	if ( '' !== $override && preg_match( '#^https?://(t\.me|telegram\.me)/#i', $override ) ) {
		return esc_url_raw( $override ); // private invite (t.me/+…) kuda valid.
	}
	$user = trim( (string) studentup_opt( 'social_telegram', 'studentup_in' ) );
	$user = preg_replace( '#^@#', '', $user );
	$user = preg_replace( '#^https?://(t\.me|telegram\.me)/#i', '', $user );
	$user = trim( (string) $user, " \t\n\r\0\x0B/" );
	if ( '' === $user ) {
		$user = 'studentup_in';
	}
	return 'https://t.me/' . rawurlencode( $user );
}

/**
 * Join chip — footer/join surfaces lo compact Telegram CTA.
 *
 * @param string $context render context label (footer|single|cta) — CSS hook.
 */
function studentup_tg_join_block( $context = 'footer' ) {
	try {
		$url = studentup_tg_channel_url();
		if ( '' === $url ) {
			return;
		}
		?>
		<a class="su-tgjoin su-tgjoin-<?php echo esc_attr( sanitize_key( $context ) ); ?>"
			href="<?php echo esc_url( $url ); ?>" target="_blank" rel="noopener"
			aria-label="<?php esc_attr_e( 'Join our Telegram channel', 'studentup' ); ?>">
			<?php echo studentup_social_icon( 'telegram', 16 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?>
			<span>Join our Telegram channel</span>
		</a>
		<?php
	} catch ( Exception $e ) { // phpcs:ignore Generic.CodeAnalysis.EmptyStatement
		// join block fail ayina page render continue.
	}
}

/**
 * Post share URL — Telegram share dialog (title auto).
 *
 * @return string t.me/share/url… (current post)
 */
function studentup_tg_share_url() {
	$title = is_singular() ? get_the_title() : get_bloginfo( 'name' );
	$link  = is_singular() ? get_permalink() : home_url( '/' );
	return 'https://t.me/share/url?url=' . rawurlencode( (string) $link ) .
		'&text=' . rawurlencode( (string) $title );
}
