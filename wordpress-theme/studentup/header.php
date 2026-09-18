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
 * studentup_menu_fallback() default Telugu menu (TS · AP · కేంద్ర · … · బ్రేకింగ్) chupistundi.
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
<a class="skip-link screen-reader-text" href="#main">కంటెంట్‌కు వెళ్లండి</a>

<header class="header">
	<div class="wrap headrow">
		<?php if ( has_custom_logo() ) : ?>
			<div class="logo"><?php the_custom_logo(); ?></div>
		<?php else : ?>
			<a class="logo" href="<?php echo esc_url( home_url( '/' ) ); ?>">
				<span class="mark" aria-hidden="true">S</span>
				<span class="brand"><?php bloginfo( 'name' ); ?><small><?php bloginfo( 'description' ); ?></small></span>
			</a>
		<?php endif; ?>

		<nav class="nav" aria-label="ప్రధాన మెనూ">
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
			<a class="navbrk" href="<?php echo esc_url( home_url( '/#breaking' ) ); ?>"><span class="dot" aria-hidden="true"></span>బ్రేకింగ్</a>
			<button class="iconbtn" id="theme" aria-label="డార్క్ మోడ్" aria-pressed="false">☾</button>
			<button class="menubtn" id="menubtn" aria-label="మెనూ" aria-expanded="false" aria-controls="mpanel">☰</button>
			<?php if ( get_option( 'studentup_exam_url' ) ) : ?>
				<a class="callbtn" href="<?php echo esc_url( (string) get_option( 'studentup_exam_url' ) ); ?>">🎓 ప్రత్యక్ష పరీక్ష</a>
			<?php endif; ?>
		</div>
	</div>
</header>

<?php studentup_breaking_ticker(); ?>

<div class="mbackdrop" id="mbackdrop" aria-hidden="true"></div>
<div class="mpanel" id="mpanel" role="dialog" aria-label="సైట్ మెనూ">
	<div class="mlabel">అన్వేషించండి</div>
	<a href="<?php echo esc_url( home_url( '/' ) ); ?>">🏠 హోమ్</a>
	<a href="<?php echo esc_url( home_url( '/#breaking' ) ); ?>">🔴 బ్రేకింగ్ న్యూస్</a>
	<div class="mlabel">విద్యార్థులు ఎక్కువగా వెతికేవి</div>
	<?php foreach ( studentup_most_used() as $m ) : ?>
		<?php
		$term = get_category_by_slug( $m['slug'] );
		if ( ! $term ) {
			continue;
		}
		?>
		<a href="<?php echo esc_url( get_category_link( $term ) ); ?>"><?php echo esc_html( $m['icon'] . ' ' . $m['label'] ); ?></a>
	<?php endforeach; ?>
	<div class="mlabel">మరికొన్ని</div>
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
	if ( get_option( 'studentup_exam_url' ) ) :
		?>
		<a class="mcta" href="<?php echo esc_url( (string) get_option( 'studentup_exam_url' ) ); ?>">🎓 ప్రత్యక్ష పరీక్ష</a>
	<?php endif; ?>
	<div class="mlabel">సోషల్</div>
	<a href="https://wa.me/919999999999" target="_blank" rel="noopener">WhatsApp</a>
	<a href="https://t.me/studentup_in" target="_blank" rel="noopener">Telegram</a>
	<a href="https://www.instagram.com/studentup.in" target="_blank" rel="noopener">Instagram</a>
	<a href="https://www.youtube.com/@studentupin" target="_blank" rel="noopener">YouTube</a>
</div>
