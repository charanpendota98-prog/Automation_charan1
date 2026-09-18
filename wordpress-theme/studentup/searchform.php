<?php
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}
?>
<?php
/**
 * Search form — Telugu label (design lo laga).
 *
 * @package studentup
 */
?>
<form role="search" method="get" class="chips" action="<?php echo esc_url( home_url( '/' ) ); ?>">
	<label class="screen-reader-text" for="s">వెతకండి</label>
	<input type="search" id="s" name="s" value="<?php echo esc_attr( get_search_query() ); ?>"
		placeholder="ఉద్యోగం / పరీక్ష / ఫలితం వెతకండి…"
		style="flex:1;min-width:220px;border:1px solid var(--line);border-radius:12px;padding:11px 14px;font-size:14px">
	<button type="submit" class="chip active">వెతకండి</button>
</form>
