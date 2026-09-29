<?php
/**
 * v151 — saved-job deadline reminders.
 *
 * Students save a job and then forget the last date. This prints a small
 * reminder strip (and, only if the reader explicitly allows it, a browser
 * notification) when something they saved closes within the next few days.
 *
 * Rules kept deliberately strict:
 *   - Data stays in the reader's own localStorage; nothing is sent anywhere.
 *   - No notification permission is requested on page load. The reader must
 *     press the button first (browsers penalise unsolicited prompts).
 *   - Dismissing is remembered for the day, so it never nags.
 *
 * @package StudentUp
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Days ahead that count as "closing soon" for a saved job.
 *
 * @return int
 */
function studentup_remind_window() {
	$days = (int) studentup_opt( 'remind_days', '3' );
	if ( $days < 1 ) {
		$days = 1;
	}
	if ( $days > 14 ) {
		$days = 14;
	}
	return $days;
}

/**
 * Render the reminder strip shell. JS fills it from saved items.
 */
function studentup_remind_strip() {
	if ( '1' !== studentup_opt( 'saved_reminders', '1' ) ) {
		return;
	}
	if ( function_exists( 'studentup_saved_on' ) && ! studentup_saved_on() ) {
		return;
	}
	$days  = studentup_remind_window();
	$store = defined( 'STUDENTUP_SAVED_STORE' ) ? STUDENTUP_SAVED_STORE : 'studentup_saved_v1';
	?>
	<aside class="su-remind" id="su-remind" hidden aria-label="<?php esc_attr_e( 'Saved job reminders', 'studentup' ); ?>">
		<button type="button" class="su-remind-x" id="su-remind-x" aria-label="<?php esc_attr_e( 'Dismiss', 'studentup' ); ?>">×</button>
		<p class="su-remind-title" id="su-remind-title"></p>
		<ul class="su-remind-list" id="su-remind-list"></ul>
		<button type="button" class="su-remind-allow" id="su-remind-allow" hidden>
			<?php esc_html_e( 'Remind me in the browser too', 'studentup' ); ?>
		</button>
	</aside>
	<script>
	(function () {
		var STORE = <?php echo wp_json_encode( $store ); ?>;
		var WINDOW_DAYS = <?php echo (int) $days; ?>;
		var box = document.getElementById('su-remind');
		if (!box) { return; }

		function today() {
			var n = new Date();
			return Date.UTC(n.getFullYear(), n.getMonth(), n.getDate());
		}
		var DISMISS = 'su-remind-off-' + Math.floor(today() / 86400000);
		try { if (localStorage.getItem(DISMISS) === '1') { return; } } catch (e) { return; }

		var items = [];
		try { items = JSON.parse(localStorage.getItem(STORE) || '[]'); } catch (e) { items = []; }
		if (!items.length) { return; }

		var due = [];
		items.forEach(function (it) {
			var d = it && (it.date || it.d);
			if (!/^\d{4}-\d{2}-\d{2}$/.test(d || '')) { return; }
			var p = d.split('-');
			var left = Math.floor((Date.UTC(+p[0], +p[1] - 1, +p[2]) - today()) / 86400000);
			if (left < 0 || left > WINDOW_DAYS) { return; }
			due.push({ left: left, title: it.title || it.t || '', url: it.url || it.u || '' });
		});
		if (!due.length) { return; }
		due.sort(function (a, b) { return a.left - b.left; });

		document.getElementById('su-remind-title').textContent =
			due.length === 1 ? 'A job you saved closes soon' : due.length + ' jobs you saved close soon';
		var list = document.getElementById('su-remind-list');
		due.slice(0, 4).forEach(function (row) {
			var li = document.createElement('li');
			var tag = document.createElement('span');
			tag.className = 'su-remind-pill';
			tag.textContent = row.left === 0 ? 'Last day today' : (row.left === 1 ? '1 day left' : row.left + ' days left');
			var a = document.createElement('a');
			a.href = row.url; a.textContent = row.title;
			li.appendChild(tag); li.appendChild(a); list.appendChild(li);
		});
		box.hidden = false;

		document.getElementById('su-remind-x').addEventListener('click', function () {
			box.hidden = true;
			try { localStorage.setItem(DISMISS, '1'); } catch (e) {}
		});

		var allow = document.getElementById('su-remind-allow');
		if (allow && 'Notification' in window && Notification.permission === 'default') {
			allow.hidden = false;
			allow.addEventListener('click', function () {
				Notification.requestPermission().then(function (p) {
					if (p === 'granted') {
						new Notification('StudentUp', { body: due[0].title + ' — ' + (due[0].left === 0 ? 'last day today' : due[0].left + ' days left') });
					}
					allow.hidden = true;
				});
			});
		}
	})();
	</script>
	<?php
}
add_action( 'wp_footer', 'studentup_remind_strip', 30 );
