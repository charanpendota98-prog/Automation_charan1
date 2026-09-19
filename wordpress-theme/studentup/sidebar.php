<?php
/**
 * Sidebar — widget area + sticky ad (desktop lo viewability ekkuva → RPM ekkuva).
 *
 * Widgets lekapote asalu markup render avvadu (layout break avvadu).
 * Registered widget areas: `sidebar-1` (main) — `inc/template.php` lo chusandi.
 *
 * @package studentup
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

$su_has_widgets = is_active_sidebar( 'sidebar-1' );
$su_has_ad      = studentup_ads_allowed( 'sidebar' );
if ( ! $su_has_widgets && ! $su_has_ad ) {
	return;
}
?>
<aside class="su-sidebar" aria-label="<?php esc_attr_e( 'Sidebar', 'studentup' ); ?>">
	<?php if ( $su_has_ad ) : ?>
		<div class="su-sidebar-ad">
			<?php studentup_ad( 'sidebar' ); ?>
		</div>
	<?php endif; ?>

	<?php
	if ( $su_has_widgets ) {
		dynamic_sidebar( 'sidebar-1' );
	}
	?>
</aside>
