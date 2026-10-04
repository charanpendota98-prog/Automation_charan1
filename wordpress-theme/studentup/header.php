<?php
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}
?>
<!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
<meta charset="<?php bloginfo( 'charset' ); ?>">
<meta name="color-scheme" content="light dark">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<link rel="profile" href="https://gmpg.org/xfn/11">
<?php wp_head(); ?>
</head>
<body <?php body_class(); ?>>
<script>
(function () {
  var saved = "";
  try { saved = localStorage.getItem("su_theme") || ""; } catch (e) {}
  var dark = saved === "dark" || (!saved && window.matchMedia &&
    window.matchMedia("(prefers-color-scheme: dark)").matches);
  if (dark) { document.body.classList.add("dark"); }
  document.body.setAttribute("data-su-theme", dark ? "dark" : "light");
})();
</script>
<?php wp_body_open(); ?>
<?php studentup_notify_public_banner(); ?>
<a class="skip-link screen-reader-text" href="#main">Skip to content</a>

<header class="header">
	<div class="wrap headrow">
		<?php if ( has_custom_logo() ) : ?>
			<div class="logo"><?php the_custom_logo(); ?></div>
		<?php else : ?>
			<a class="logo" href="<?php echo esc_url( home_url( '/' ) ); ?>" aria-label="<?php echo esc_attr( get_bloginfo( 'name' ) ); ?> home">
				<span class="brand"><?php bloginfo( 'name' ); ?></span>
			</a>
		<?php endif; ?>

		<nav class="nav" aria-label="Main menu">
			<?php studentup_menu_fallback(); ?>
		</nav>

		<div class="headactions">
			<?php if ( ! is_front_page() && ! is_home() && studentup_saved_on() ) : ?>
				<button type="button" class="iconbtn su-hdr-saved" data-su-saved-open aria-expanded="false" aria-controls="su-saved-panel" aria-label="<?php echo esc_attr__( 'Saved posts', 'studentup' ); ?>">
					<?php echo studentup_ui_icon( 'bookmark', 20 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?>
					<span class="su-saved-count" data-su-saved-count hidden>0</span>
				</button>
			<?php endif; ?>
			<button type="button" class="iconbtn" id="searchbtn" aria-label="Search" aria-expanded="false" aria-controls="searchpanel"><?php echo studentup_ui_icon( 'search', 20 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?></button>
			<button type="button" class="iconbtn" id="theme" aria-label="Dark mode" aria-pressed="false"><?php echo studentup_ui_icon( 'moon', 20 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?></button>
			<button type="button" class="menubtn" id="menubtn" aria-label="Open menu" aria-expanded="false" aria-controls="mpanel"><?php echo studentup_ui_icon( 'menu', 20 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?><span class="menubtn-label">Menu</span></button>
		</div>
	</div>

	<div class="searchpanel" id="searchpanel" hidden>
		<div class="wrap">
			<form class="spanel-form" role="search" method="get" action="<?php echo esc_url( home_url( '/' ) ); ?>" autocomplete="off">
				<div class="su-livesearch" role="combobox" aria-expanded="false" aria-haspopup="listbox" aria-owns="su-sres">
					<input id="qtop" type="search" name="s" autocomplete="off" value="<?php echo esc_attr( get_search_query() ); ?>"
						placeholder="Search government jobs and notifications" aria-label="Search this site"
						aria-autocomplete="list" aria-controls="su-sres" spellcheck="false">
					<div class="su-sres" id="su-sres" role="listbox" aria-label="Search results" hidden></div>
				</div>
				<button type="submit" class="bluebtn">Search</button>
			</form>
			<button type="button" class="iconbtn" id="searchclose" aria-label="Close search"><?php echo studentup_ui_icon( 'close', 16 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?></button>
		</div>
	</div>
</header>

<div class="mbackdrop" id="mbackdrop" aria-hidden="true"></div>
<div class="mpanel" id="mpanel" role="dialog" aria-label="Site menu" aria-modal="true" aria-hidden="true" inert>
	<div class="mpanel-head">
		<strong><?php bloginfo( 'name' ); ?></strong>
		<button type="button" id="mpanelclose" aria-label="Close menu"><?php echo studentup_ui_icon( 'close', 20 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?></button>
	</div>
	<nav class="su-mobile-nav" aria-label="Mobile menu">
		<a href="<?php echo esc_url( home_url( '/' ) ); ?>"><?php echo studentup_ui_icon( 'home', 18 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> Home</a>
		<?php foreach ( studentup_primary_job_items() as $item ) : ?>
			<a href="<?php echo esc_url( $item['url'] ); ?>"><?php echo studentup_ui_icon( 'bank', 18 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> <?php echo esc_html( $item['label'] ); ?></a>
		<?php endforeach; ?>
	</nav>
	<?php $su_more_items = studentup_menu_more_items(); ?>
	<details class="mgroup su-mobile-more" id="su-mobile-more">
		<summary><span>More categories</span></summary>
		<div class="mgroup-body">
			<?php foreach ( $su_more_items as $item ) : ?>
				<a href="<?php echo esc_url( $item['url'] ); ?>"><?php echo esc_html( $item['label'] ); ?></a>
			<?php endforeach; ?>
		</div>
	</details>
</div>
