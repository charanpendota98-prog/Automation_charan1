<?php
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}
?>
<?php
/**
 * Header — logo, menu (jobs/exams dropdown), actions, mobile panel.
 *
 * Menu: Appearance → Menus lo 'primary' menu assign cheyyandi. Lekapote
 * studentup_menu_fallback() default menu (TS · AP · Central · … ) chupistundi.
 *
 * @package studentup
 */

?><!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
<meta charset="<?php bloginfo( 'charset' ); ?>">
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="profile" href="https://gmpg.org/xfn/11">
<?php wp_head(); ?>
</head>
<body <?php body_class(); ?>>
<?php wp_body_open(); ?>
<?php studentup_notify_public_banner(); // v90: critical alerts site-wide banner (option gate + localStorage dismiss) ?>
<a class="skip-link screen-reader-text" href="#main">Skip to content</a>

<header class="header">
	<div class="wrap headrow">
		<?php if ( has_custom_logo() ) : ?>
			<div class="logo"><?php the_custom_logo(); ?></div>
		<?php else : ?>
			<a class="logo" href="<?php echo esc_url( home_url( '/' ) ); ?>">
				<span class="mark" aria-hidden="true">S</span>
				<span class="brand"><?php bloginfo( 'name' ); ?></span>
			</a>
		<?php endif; ?>

		<nav class="nav" aria-label="Main menu">
			<?php
			wp_nav_menu(
				array(
					'theme_location' => 'primary',
					'menu_class'     => 'menu-primary',
					'container'      => false,
					'depth'          => 2,
					'fallback_cb'    => 'studentup_menu_fallback',
				)
			);
			?>
		</nav>

		<div class="headactions">
			<?php if ( studentup_saved_on() ) : ?>
				<button type="button" class="iconbtn su-hdr-saved" data-su-saved-open aria-expanded="false" aria-controls="su-saved-panel" aria-label="<?php echo esc_attr__( 'Saved posts', 'studentup' ); ?>">🔖<span class="su-saved-count" data-su-saved-count hidden>0</span></button>
			<?php endif; ?>
			<button type="button" class="iconbtn" id="searchbtn" aria-label="Search" aria-expanded="false" aria-controls="searchpanel">🔍</button>
			<button type="button" class="iconbtn" id="theme" aria-label="Dark mode" aria-pressed="false">☾</button>
			<button type="button" class="menubtn" id="menubtn" aria-label="Menu" aria-expanded="false" aria-controls="mpanel">☰</button>
		</div>
	</div>
	<div class="searchpanel" id="searchpanel" hidden>
		<div class="wrap">
			<span class="spanel-icon" aria-hidden="true">🔍</span>
			<form class="spanel-form" role="search" method="get" action="<?php echo esc_url( home_url( '/' ) ); ?>" autocomplete="off">
				<div class="su-livesearch" role="combobox" aria-expanded="false" aria-haspopup="listbox" aria-owns="su-sres">
					<input id="qtop" type="search" name="s" autocomplete="off" value="<?php echo esc_attr( get_search_query() ); ?>"
						placeholder="Search jobs, exams, results, scholarships…" aria-label="Search this site"
						aria-autocomplete="list" aria-controls="su-sres" spellcheck="false">
					<div class="su-sres" id="su-sres" role="listbox" aria-label="Search results" hidden></div>
				</div>
				<button type="submit" class="bluebtn">Search</button>
			</form>
			<button type="button" class="iconbtn" id="searchclose" aria-label="Close">✕</button>
		</div>
	</div>
</header>

<?php
// v72: Breaking section default OFF (admin → StudentUp Options lo on cheyyachu).
studentup_breaking_ticker();
?>

<div class="mbackdrop" id="mbackdrop" aria-hidden="true"></div>
<div class="mpanel" id="mpanel" role="dialog" aria-label="Site menu" aria-modal="true" aria-hidden="true">
	<div class="mpanel-head"><strong>StudentUp</strong><button type="button" id="mpanelclose" aria-label="Close menu">✕</button></div>
	<div class="mlabel">Explore</div>
	<a href="<?php echo esc_url( home_url( '/' ) ); ?>">🏠 Home</a>
	<a href="<?php echo esc_url( home_url( '/?s=' ) ); ?>">🔍 Search</a>
	<?php if ( function_exists( 'studentup_saved_on' ) && studentup_saved_on() ) : ?>
		<a href="#" class="su-msaved" data-su-saved-open>🔖 <?php echo esc_html__( 'Saved', 'studentup' ); ?></a>
	<?php endif; ?>
	<div class="mlabel">Most searched by students</div>
	<?php foreach ( studentup_most_used() as $m ) : ?>
		<?php
		$term = studentup_used_term( $m['slug'] );   // v89: alias-aware — TS/AP/Central eppudu kanipistayi
		if ( ! $term ) {
			continue;
		}
		?>
		<a href="<?php echo esc_url( get_category_link( $term ) ); ?>"><?php echo esc_html( $m['icon'] . ' ' . $m['label'] ); ?></a>
	<?php endforeach; ?>
	<div class="mlabel">More</div>
	<?php
	if ( has_nav_menu( 'mobile' ) ) {
		wp_nav_menu(
			array(
				'theme_location' => 'mobile',
				'container'      => false,
				'depth'          => 1,
				'fallback_cb'    => false,
			)
		);
	}
	?>
	<div class="mlabel">Social</div>
	<?php $su_soc = studentup_social_links(); ?>
	<a class="su-msoc su-msoc-wa" href="<?php echo esc_url( $su_soc['whatsapp'] ); ?>" target="_blank" rel="noopener"><?php echo studentup_social_icon( 'whatsapp', 16 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> WhatsApp</a>
	<a class="su-msoc su-msoc-tg" href="<?php echo esc_url( $su_soc['telegram'] ); ?>" target="_blank" rel="noopener"><?php echo studentup_social_icon( 'telegram', 16 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> Telegram</a>
	<a class="su-msoc su-msoc-ig" href="<?php echo esc_url( $su_soc['instagram'] ); ?>" target="_blank" rel="noopener"><?php echo studentup_social_icon( 'instagram', 16 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> Instagram</a>
	<a class="su-msoc su-msoc-yt" href="<?php echo esc_url( $su_soc['youtube'] ); ?>" target="_blank" rel="noopener"><?php echo studentup_social_icon( 'youtube', 16 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> YouTube</a>
</div>
