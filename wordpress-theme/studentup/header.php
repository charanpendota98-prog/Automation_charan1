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
<meta name="color-scheme" content="light dark">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<script>
/* v191.3 A11Y FIX: pinch-zoom block TEESESAAM (WCAG 1.4.4 — users zoom cheyyali
   anukune hakku undali; paatha zoom-block meta + gesture JS valla phone lo
   text peddaga cheyyadam impossible ayyedi). Double-tap zoom ki mattrame CSS
   touch-action chestundi (worldclass.css), so accidental zoom inka undadu. */
</script>
<link rel="profile" href="https://gmpg.org/xfn/11">
<?php wp_head(); ?>
</head>
<body <?php body_class(); ?>>
<script>
/* v185 NO-FLASH THEME: dark-mode readers ki page paint ayye mundu class set
   chestam (footer JS deferred — adi aagithe oka kshanam white flash kanipistundi).
   Preference: saved choice > system (prefers-color-scheme) > light. ~180 bytes. */
(function () {
  var el = document.body;
  if (!el) { return; }
  var saved = "";
  try { saved = localStorage.getItem("su_theme") || ""; } catch (e) {}
  var dark = saved === "dark" || (!saved && window.matchMedia &&
    window.matchMedia("(prefers-color-scheme: dark)").matches);
  if (dark) { el.classList.add("dark"); }
  el.setAttribute("data-su-theme", dark ? "dark" : "light");
})();
</script>
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
				<button type="button" class="iconbtn su-hdr-saved" data-su-saved-open aria-expanded="false" aria-controls="su-saved-panel" aria-label="<?php echo esc_attr__( 'Saved posts', 'studentup' ); ?>"><?php echo studentup_ui_icon( 'bookmark', 20 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?><span class="su-saved-count" data-su-saved-count hidden>0</span></button>
			<?php endif; ?>
			<button type="button" class="iconbtn" id="searchbtn" aria-label="Search" aria-expanded="false" aria-controls="searchpanel"><?php echo studentup_ui_icon( 'search', 20 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?></button>
			<button type="button" class="iconbtn" id="theme" aria-label="Dark mode" aria-pressed="false"><?php echo studentup_ui_icon( 'moon', 20 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?></button>
			<button type="button" class="menubtn" id="menubtn" aria-label="Menu" aria-expanded="false" aria-controls="mpanel"><?php echo studentup_ui_icon( 'menu', 22 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?></button>
		</div>
	</div>
	<div class="searchpanel" id="searchpanel" hidden>
		<div class="wrap">
			<span class="spanel-icon" aria-hidden="true"><?php echo studentup_ui_icon( 'search', 20 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?></span>
			<form class="spanel-form" role="search" method="get" action="<?php echo esc_url( home_url( '/' ) ); ?>" autocomplete="off">
				<div class="su-livesearch" role="combobox" aria-expanded="false" aria-haspopup="listbox" aria-owns="su-sres">
					<input id="qtop" type="search" name="s" autocomplete="off" value="<?php echo esc_attr( get_search_query() ); ?>"
						placeholder="Search jobs, exams, results, scholarships…" aria-label="Search this site"
						aria-autocomplete="list" aria-controls="su-sres" spellcheck="false">
					<div class="su-sres" id="su-sres" role="listbox" aria-label="Search results" hidden></div>
				</div>
				<button type="submit" class="bluebtn">Search</button>
			</form>
			<button type="button" class="iconbtn" id="searchclose" aria-label="Close"><?php echo studentup_ui_icon( 'close', 16 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?></button>
		</div>
	</div>
</header>

<?php
// v72: Breaking section default OFF (admin → StudentUp Options lo on cheyyachu).
studentup_breaking_ticker();
?>

<div class="mbackdrop" id="mbackdrop" aria-hidden="true"></div>
<div class="mpanel" id="mpanel" role="dialog" aria-label="Site menu" aria-modal="true" aria-hidden="true">
	<div class="mpanel-head"><strong>StudentUp</strong><button type="button" id="mpanelclose" aria-label="Close menu"><?php echo studentup_ui_icon( 'close', 20 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?></button></div>
	<div class="mlabel">Explore</div>
	<a href="<?php echo esc_url( home_url( '/' ) ); ?>"><?php echo studentup_ui_icon( 'home' ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> Home</a>
	<a href="<?php echo esc_url( home_url( '/?s=' ) ); ?>"><?php echo studentup_ui_icon( 'search' ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> Search</a>
	<a class="su-mobile-board-link" href="<?php echo esc_url( studentup_opportunity_board_url() ); ?>"><?php echo studentup_ui_icon( 'board' ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> Latest active jobs</a>
	<?php if ( function_exists( 'studentup_saved_on' ) && studentup_saved_on() ) : ?>
		<a href="#" class="su-msaved" data-su-saved-open><?php echo studentup_ui_icon( 'bookmark' ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> <?php echo esc_html__( 'Saved', 'studentup' ); ?></a>
	<?php endif; ?>
	<?php if ( function_exists( 'studentup_workspace_on' ) && studentup_workspace_on() && studentup_workspace_url() ) : ?>
		<a href="<?php echo esc_url( studentup_workspace_url() ); ?>"><?php echo studentup_ui_icon( 'person' ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> My Workspace</a>
	<?php endif; ?>
	<?php
	// v197: quiz + poll ki dedicated page undi (lekapote front-page anchor).
	$su_quiz_url = function_exists( 'studentup_mega_page_url' )
		? studentup_mega_page_url( array( 'daily-quiz', 'quiz' ) )
		: '';
	$su_quiz_url = $su_quiz_url ? $su_quiz_url : home_url( '/#daily-quiz' );
	?>
	<a href="<?php echo esc_url( $su_quiz_url ); ?>"><?php echo studentup_ui_icon( 'chart' ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> Daily Quiz &amp; Polls</a>
	<a href="<?php echo esc_url( home_url( '/#age-calculator' ) ); ?>"><?php echo studentup_ui_icon( 'person' ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> Age Calculator</a>
	<a href="<?php echo esc_url( home_url( '/#fee-calculator' ) ); ?>"><?php echo studentup_ui_icon( 'card' ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> Fee Calculator</a>
	<a href="<?php echo esc_url( home_url( '/#syllabus-tracker' ) ); ?>"><?php echo studentup_ui_icon( 'book' ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> Syllabus Tracker</a>
	<a href="<?php echo esc_url( home_url( '/#salary-calculator' ) ); ?>"><?php echo studentup_ui_icon( 'wallet' ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> Salary Calculator</a>
	<a href="<?php echo esc_url( home_url( '/#alerts' ) ); ?>"><?php echo studentup_ui_icon( 'bell' ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> Instant alerts</a>
	<?php
	// v123: Scholarships mobile menu lo eppudu kanipinchali.
	$su_schol = studentup_used_term( 'scholarships' );
	if ( $su_schol ) :
		?>
		<a href="<?php echo esc_url( get_category_link( $su_schol ) ); ?>"><?php echo studentup_ui_icon( 'school' ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> Scholarships</a>
	<?php endif; ?>
	<?php if ( function_exists( 'studentup_mega_mobile_groups' ) ) : ?>
		<div class="mlabel">Browse everything</div>
		<?php
		foreach ( studentup_mega_mobile_groups() as $su_gi => $su_group ) {
			studentup_mega_mobile_accordion( $su_group, 0 === $su_gi );
		}
		?>
	<?php endif; ?>
	<div class="mlabel">Most searched by students</div>
	<?php foreach ( studentup_most_used() as $m ) : ?>
		<?php
		$term = studentup_used_term( $m['slug'] );   // v89: alias-aware — TS/AP/Central eppudu kanipistayi
		if ( ! $term ) {
			continue;
		}
		?>
		<a href="<?php echo esc_url( get_category_link( $term ) ); ?>"><?php echo studentup_ui_icon( $m['icon'], 15 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> <?php echo esc_html( $m['label'] ); ?></a>
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
