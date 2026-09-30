<?php
/**
 * v156 — personalised picks + calendar reminders.
 *
 * Two things students ask for that no login can be justified for:
 *
 *   1. "show me only what I can apply for"  -> a profile (qualification +
 *      state) kept in the reader's own browser, used to rank the openings the
 *      page already lists. No account, no cookie, nothing sent to the server.
 *   2. "remind me before the last date"     -> a one-click .ics download that
 *      drops the deadline into the phone/Google calendar with an alarm one day
 *      before. The file is generated in the browser from the post's own meta.
 *
 * @package StudentUp
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Homepage strip: reader picks a profile, JS ranks the visible cards.
 */
function studentup_personal_picks() {
	if ( '1' !== studentup_opt( 'personal_picks', '1' ) ) {
		return;
	}
	?>
	<section class="su-you" id="su-you" aria-labelledby="su-you-title">
		<h2 id="su-you-title"><?php echo studentup_ui_icon( 'star', 17 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> <?php esc_html_e( 'Your 5 today', 'studentup' ); ?></h2>
		<p class="su-you-sub"><?php esc_html_e( 'Set your qualification and state once. The list is built on this device - no login, nothing sent to a server.', 'studentup' ); ?></p>
		<div class="su-you-form">
			<div>
				<label for="su-you-qual"><?php esc_html_e( 'Qualification', 'studentup' ); ?></label>
				<select id="su-you-qual">
					<option value="10th">10th</option>
					<option value="inter">Inter</option>
					<option value="iti">ITI</option>
					<option value="diploma">Diploma</option>
					<option value="degree" selected>Degree</option>
					<option value="pg">PG</option>
				</select>
			</div>
			<div>
				<label for="su-you-state"><?php esc_html_e( 'State', 'studentup' ); ?></label>
				<select id="su-you-state">
					<option value="ts" selected>Telangana</option>
					<option value="ap">Andhra Pradesh</option>
					<option value="central">Central / All India</option>
				</select>
			</div>
			<div>
				<button type="button" id="su-you-go"><?php esc_html_e( 'Build my list', 'studentup' ); ?></button>
			</div>
		</div>
		<ul class="su-you-list" id="su-you-list"></ul>
		<button type="button" class="su-you-reset" id="su-you-reset" hidden><?php esc_html_e( 'Reset my choices', 'studentup' ); ?></button>
	</section>
	<script>
	(function () {
		var KEY = 'studentup-profile-v1';
		var list = document.getElementById('su-you-list');
		var reset = document.getElementById('su-you-reset');
		if (!list) { return; }

		function today() {
			var n = new Date();
			return Math.floor(Date.UTC(n.getFullYear(), n.getMonth(), n.getDate()) / 86400000);
		}
		function daysLeft(d) {
			if (!/^\d{4}-\d{2}-\d{2}$/.test(d || '')) { return null; }
			var p = d.split('-');
			return Math.floor(Date.UTC(+p[0], +p[1] - 1, +p[2]) / 86400000) - today();
		}
		function build(profile) {
			var rows = [];
			Array.prototype.forEach.call(document.querySelectorAll('[data-su-card]'), function (c) {
				var link = c.querySelector('a[href]');
				if (!link) { return; }
				var left = daysLeft(c.getAttribute('data-last'));
				if (left !== null && left < 0) { return; }
				var quals = (c.getAttribute('data-qual') || '').split(/\s+/);
				var states = (c.getAttribute('data-state') || '').split(/\s+/);
				var score = 0, why = [];
				if (quals.indexOf(profile.q) > -1) { score += 3; why.push('your qualification'); }
				if (states.indexOf(profile.s) > -1) { score += 2; why.push('your state'); }
				else if (states.indexOf('central') > -1) { score += 1; why.push('all-India'); }
				if (left !== null && left <= 7) { score += 2; why.push(left === 0 ? 'last day today' : left + 'd left'); }
				if (score <= 1) { return; }
				rows.push({ s: score, t: link.textContent.trim(), h: link.getAttribute('href'),
					w: why.slice(0, 2).join(' · '), l: left === null ? 999 : left });
			});
			rows.sort(function (a, b) { return (b.s - a.s) || (a.l - b.l); });
			list.innerHTML = '';
			if (!rows.length) {
				var none = document.createElement('li');
				none.textContent = 'Nothing matches that combination today.';
				list.appendChild(none);
				return;
			}
			rows.slice(0, 5).forEach(function (r, i) {
				var li = document.createElement('li');
				var rank = document.createElement('span'); rank.className = 'su-you-rank'; rank.textContent = i + 1;
				var a = document.createElement('a'); a.href = r.h; a.textContent = r.t;
				var w = document.createElement('span'); w.className = 'su-you-why'; w.textContent = r.w;
				li.appendChild(rank); li.appendChild(a); li.appendChild(w); list.appendChild(li);
			});
		}
		document.getElementById('su-you-go').addEventListener('click', function () {
			var p = { q: document.getElementById('su-you-qual').value, s: document.getElementById('su-you-state').value };
			try { localStorage.setItem(KEY, JSON.stringify(p)); } catch (e) {}
			build(p); reset.hidden = false;
		});
		reset.addEventListener('click', function () {
			try { localStorage.removeItem(KEY); } catch (e) {}
			list.innerHTML = ''; reset.hidden = true;
		});
		var saved = null;
		try { saved = JSON.parse(localStorage.getItem(KEY) || 'null'); } catch (e) {}
		if (saved && saved.q && saved.s) {
			document.getElementById('su-you-qual').value = saved.q;
			document.getElementById('su-you-state').value = saved.s;
			build(saved); reset.hidden = false;
		}
	})();
	</script>
	<?php
}

/**
 * Single post: add the last date to the reader's calendar (.ics, built in the browser).
 */
function studentup_calendar_button() {
	if ( ! is_single() || '1' !== studentup_opt( 'calendar_button', '1' ) ) {
		return;
	}
	$last = trim( (string) get_post_meta( get_the_ID(), 'studentup_last_date', true ) );
	if ( ! preg_match( '/^20\d{2}-\d{2}-\d{2}$/', $last ) ) {
		return; // No real last date -> no button. Nothing is guessed.
	}
	?>
	<p class="su-cal-add">
		<button type="button" class="su-cal-btn" id="su-cal-btn"
			data-date="<?php echo esc_attr( $last ); ?>"
			data-title="<?php echo esc_attr( get_the_title() ); ?>"
			data-url="<?php echo esc_url( get_permalink() ); ?>">
			<?php echo studentup_ui_icon( 'calendar', 15 ); // phpcs:ignore WordPress.Security.EscapeOutput -- trusted SVG ?> <?php esc_html_e( 'Add last date to my calendar', 'studentup' ); ?>
		</button>
		<span class="su-cal-hint"><?php esc_html_e( 'Downloads a calendar file with an alarm one day before.', 'studentup' ); ?></span>
	</p>
	<script>
	(function () {
		var b = document.getElementById('su-cal-btn');
		if (!b) { return; }
		b.addEventListener('click', function () {
			var d = b.getAttribute('data-date').replace(/-/g, '');
			var title = b.getAttribute('data-title');
			var url = b.getAttribute('data-url');
			var stamp = new Date().toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z';
			function esc(s) { return String(s).replace(/([,;\\])/g, '\\$1').replace(/\n/g, '\\n'); }
			var ics = [
				'BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//StudentUp//EN', 'CALSCALE:GREGORIAN',
				'BEGIN:VEVENT',
				'UID:' + d + '-' + Math.random().toString(36).slice(2) + '@studentup',
				'DTSTAMP:' + stamp,
				'DTSTART;VALUE=DATE:' + d,
				'DTEND;VALUE=DATE:' + d,
				'SUMMARY:' + esc('Last date: ' + title),
				'DESCRIPTION:' + esc(url),
				'BEGIN:VALARM', 'TRIGGER:-P1D', 'ACTION:DISPLAY',
				'DESCRIPTION:' + esc('Tomorrow is the last date: ' + title),
				'END:VALARM',
				'END:VEVENT', 'END:VCALENDAR'
			].join('\r\n');
			var blob = new Blob([ics], { type: 'text/calendar;charset=utf-8' });
			var a = document.createElement('a');
			a.href = URL.createObjectURL(blob);
			a.download = 'last-date.ics';
			document.body.appendChild(a); a.click();
			setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 500);
		});
	})();
	</script>
	<?php
}
