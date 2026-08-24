// Capstone progress dashboard — static, client-side only.
// Reads docs/data/calendar.json (the 16-week schedule) and
// docs/hours-log.csv (hand-maintained hours log) and renders current
// status. No backend, no automation — refresh the page after pushing an
// updated hours-log.csv to see new numbers.

async function loadCalendar() {
  const res = await fetch("data/calendar.json");
  return res.json();
}

async function loadHoursLog() {
  const res = await fetch("hours-log.csv");
  const text = await res.text();
  return parseCsv(text);
}

function parseCsv(text) {
  const lines = text.trim().split("\n").filter((l) => l.trim().length > 0);
  if (lines.length === 0) return [];
  const header = lines[0].split(",").map((h) => h.trim());
  const rows = [];
  for (let i = 1; i < lines.length; i++) {
    // Simple split is fine here — this file has no quoted commas by design.
    const cells = lines[i].split(",");
    const row = {};
    header.forEach((key, idx) => {
      row[key] = (cells[idx] ?? "").trim();
    });
    rows.push(row);
  }
  return rows;
}

function findCurrentWeek(calendar, today) {
  for (const w of calendar.weeks) {
    const start = new Date(w.start + "T00:00:00");
    const end = new Date(w.end + "T23:59:59");
    if (today >= start && today <= end) return w;
  }
  return null;
}

function hoursInRange(hoursLog, start, end) {
  let total = 0;
  for (const row of hoursLog) {
    if (!row.date || !row.actual_hours) continue;
    const d = new Date(row.date + "T12:00:00");
    if (d >= start && d <= end) {
      total += parseFloat(row.actual_hours) || 0;
    }
  }
  return total;
}

function totalHours(hoursLog) {
  return hoursLog.reduce((sum, row) => sum + (parseFloat(row.actual_hours) || 0), 0);
}

function renderCurrentWeek(week, today, calendar) {
  const el = document.getElementById("currentWeekBody");
  if (!week) {
    const firstStart = new Date(calendar.weeks[0].start + "T00:00:00");
    const lastEnd = new Date(calendar.weeks[calendar.weeks.length - 1].end + "T23:59:59");
    if (today < firstStart) {
      el.innerHTML = `<p class="meta-line">The semester hasn't started yet — Week 1 begins ${firstStart.toLocaleDateString()}.</p>`;
    } else if (today > lastEnd) {
      el.innerHTML = `<p class="meta-line">All 16 weeks are complete. 🎉</p>`;
    } else {
      el.innerHTML = `<p class="meta-line">No matching week found.</p>`;
    }
    return;
  }
  const due = new Date(week.due);
  const daysLeft = Math.ceil((due - today) / (1000 * 60 * 60 * 24));
  el.innerHTML = `
    <p class="meta-line">Week ${week.week} · ${week.hat}</p>
    <p class="milestone-title">${escapeHtml(week.milestone)}</p>
    <p class="meta-line">Due ${due.toLocaleString()} (${daysLeft >= 0 ? `${daysLeft} day${daysLeft === 1 ? "" : "s"} left` : "overdue"})</p>
    ${week.notes ? `<p class="meta-line">${escapeHtml(week.notes)}</p>` : ""}
  `;
}

function renderWeekHours(week, hoursLog, target) {
  const el = document.getElementById("weekHoursBody");
  if (!week) {
    el.innerHTML = `<p class="meta-line">No active week.</p>`;
    return;
  }
  const start = new Date(week.start + "T00:00:00");
  const end = new Date(week.end + "T23:59:59");
  const hours = hoursInRange(hoursLog, start, end);
  const pct = Math.min(100, (hours / target) * 100);
  const over = hours > target;
  const badge = over
    ? `<span class="badge badge-warn">+${(hours - target).toFixed(1)}h overtime</span>`
    : hours >= target
    ? `<span class="badge badge-good">on target</span>`
    : "";
  el.innerHTML = `
    <p class="meta-line">${hours.toFixed(1)} / ${target} hrs${badge}</p>
    <div class="progress-track"><div class="progress-fill ${over ? "over" : hours >= target ? "good" : ""}" style="width:${pct}%"></div></div>
  `;
}

function renderTotalHours(week, hoursLog, totalTarget) {
  const el = document.getElementById("totalHoursBody");
  const hours = totalHours(hoursLog);
  const pct = Math.min(100, (hours / totalTarget) * 100);
  const paceTarget = week ? week.cumulativeHours : totalTarget;
  const onPace = hours >= paceTarget;
  el.innerHTML = `
    <p class="meta-line">${hours.toFixed(1)} / ${totalTarget} hrs total
      ${week ? `<span class="badge ${onPace ? "badge-good" : "badge-bad"}">${onPace ? "on pace" : "behind pace"} for week ${week.week} (target ${paceTarget})</span>` : ""}
    </p>
    <div class="progress-track"><div class="progress-fill" style="width:${pct}%"></div></div>
  `;
}

function renderUpcoming(calendar, week) {
  const el = document.getElementById("upcomingBody");
  if (!week) {
    el.innerHTML = `<p class="meta-line">Nothing to show.</p>`;
    return;
  }
  const upcoming = calendar.weeks.filter((w) => w.week > week.week).slice(0, 2);
  if (upcoming.length === 0) {
    el.innerHTML = `<p class="meta-line">This is the last week.</p>`;
    return;
  }
  el.innerHTML = upcoming
    .map(
      (w) => `
        <div class="upcoming-item">
          <div class="upcoming-week">Week ${w.week} · ${new Date(w.start + "T00:00:00").toLocaleDateString()}</div>
          <div>${escapeHtml(w.milestone)}</div>
        </div>`
    )
    .join("");
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

async function main() {
  const today = new Date();
  document.getElementById("todayLine").textContent = today.toLocaleString();

  const [calendar, hoursLog] = await Promise.all([loadCalendar(), loadHoursLog()]);
  const week = findCurrentWeek(calendar, today);

  renderCurrentWeek(week, today, calendar);
  renderWeekHours(week, hoursLog, calendar.weeklyHourTarget);
  renderTotalHours(week, hoursLog, calendar.totalHourTarget);
  renderUpcoming(calendar, week);
}

main().catch((err) => {
  document.querySelector("main").innerHTML = `<p class="meta-line">Failed to load dashboard data: ${err.message}</p>`;
});
