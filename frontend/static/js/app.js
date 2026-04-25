const PRAYERS = ["fajr", "dhuhr", "asr", "maghrib", "isha"];
const LABELS = { fajr: "Fajr", shuruq: "Shuruq", dhuhr: "Dhuhr", asr: "Asr", maghrib: "Maghrib", isha: "Isha" };
const TILE_ORDER = ["fajr", "shuruq", "dhuhr", "asr", "maghrib", "isha"];

const fieldEl = (name) => document.querySelector(`[data-field="${name}"]`);

function parseHHMMToToday(hhmm) {
  const [h, m] = hhmm.split(":").map(Number);
  const d = new Date();
  d.setHours(h, m, 0, 0);
  return d;
}

function fmtCountdown(ms) {
  if (ms < 0) return "now";
  const mins = Math.floor(ms / 60000);
  const h = Math.floor(mins / 60);
  const m = mins % 60;
  if (h > 0) return `in ${h}h ${m}m`;
  if (m > 0) return `in ${m}m`;
  return `in <1m`;
}

function fmtDuration(ms) {
  if (ms <= 0) return "now";
  const mins = Math.floor(ms / 60000);
  const h = Math.floor(mins / 60);
  const m = mins % 60;
  if (h > 0) return `${h}h ${m}m`;
  if (m > 0) return `${m}m`;
  return "<1m";
}

function fmtMinutes(min) {
  if (min == null) return "—";
  if (min <= 0) return "now";
  return `${min}'`;
}

function renderClock() {
  const now = new Date();
  fieldEl("clock-time").textContent = now.toTimeString().slice(0, 5);
  fieldEl("clock-day").textContent = now.toLocaleDateString("en-GB", { weekday: "long" });
  fieldEl("clock-cal").textContent = now.toLocaleDateString("en-GB", {
    day: "numeric", month: "long", year: "numeric",
  });
}

async function fetchJSON(url) {
  const r = await fetch(url, { cache: "no-store" });
  if (!r.ok) throw new Error(`${url}: ${r.status}`);
  return r.json();
}

function findNextPrayer(adhan) {
  const now = new Date();
  for (const name of PRAYERS) {
    const t = parseHHMMToToday(adhan[name]);
    if (t > now) return { name, time: adhan[name], at: t };
  }
  const t = parseHHMMToToday(adhan.fajr);
  t.setDate(t.getDate() + 1);
  return { name: "fajr", time: adhan.fajr, at: t, tomorrow: true };
}

async function refreshPrayer() {
  try {
    const data = await fetchJSON("/api/prayer");
    if (data.error) throw new Error(data.error);
    const adhan = data.adhan;
    const iqama = data.iqama || {};
    const next = findNextPrayer(adhan);

    fieldEl("next-eyebrow").textContent = next.tomorrow ? "Next prayer · tomorrow" : "Next prayer";
    fieldEl("next-countdown").textContent = fmtDuration(next.at - new Date());
    fieldEl("next-detail").textContent = `${LABELS[next.name]} at ${next.time}`;

    const list = fieldEl("list");
    list.innerHTML = "";
    for (const name of TILE_ORDER) {
      const li = document.createElement("li");
      if (name === next.name && !next.tomorrow) li.classList.add("current");
      const iqamaHTML = iqama[name] ? `<span class="iqama">iqama ${iqama[name]}</span>` : "";
      li.innerHTML = `<span class="name">${LABELS[name]}</span><span class="adhan">${adhan[name]}</span>${iqamaHTML}`;
      list.appendChild(li);
    }

    const jumuaEl = fieldEl("jumua");
    if (Array.isArray(data.jumua) && data.jumua.length) {
      jumuaEl.textContent = "Jumua: " + data.jumua.join(" · ");
    } else {
      jumuaEl.textContent = "";
    }
  } catch (e) {
    fieldEl("next-name").textContent = "prayer err";
    fieldEl("next-countdown").textContent = String(e.message || e);
  }
}

async function refreshWeather() {
  try {
    const data = await fetchJSON("/api/weather");
    if (data.error) throw new Error(data.error);
    const c = data.current || {};
    fieldEl("icon").textContent = c.icon || "•";
    fieldEl("temp").textContent = c.temp != null ? `${Math.round(c.temp)}°` : "—";
    fieldEl("desc").textContent = c.description || "—";
    fieldEl("wind").textContent = c.wind != null ? `wind ${Math.round(c.wind)} km/h` : "";
    fieldEl("humidity").textContent = c.humidity != null ? `${c.humidity}% humidity` : "";
  } catch (e) {
    fieldEl("desc").textContent = "weather err";
  }
}

async function refreshTransit() {
  try {
    const data = await fetchJSON("/api/transit");
    const container = fieldEl("stops");
    container.innerHTML = "";
    for (const entry of data) {
      const stop = document.createElement("div");
      stop.className = "transit-stop";
      const name = document.createElement("div");
      name.className = "transit-stop-name";
      name.textContent = entry.stop;
      stop.appendChild(name);

      if (entry.error) {
        const empty = document.createElement("div");
        empty.className = "transit-empty";
        empty.textContent = entry.error;
        stop.appendChild(empty);
      } else if (!entry.departures.length) {
        const empty = document.createElement("div");
        empty.className = "transit-empty";
        empty.textContent = "—";
        stop.appendChild(empty);
      } else {
        for (const d of entry.departures.slice(0, 2)) {
          const row = document.createElement("div");
          row.className = "transit-row";
          if (d.cancelled) row.classList.add("cancelled");
          else if (d.delay_seconds && d.delay_seconds > 60) row.classList.add("delayed");
          row.innerHTML = `
            <span class="line">${d.line}</span>
            <span class="ziel">${d.direction}</span>
            <span class="abfahrt">${fmtMinutes(d.in_minutes)}</span>
          `;
          stop.appendChild(row);
        }
      }
      container.appendChild(stop);
    }
  } catch (e) {
    const c = fieldEl("stops");
    c.innerHTML = `<div class="transit-empty">${e.message || e}</div>`;
  }
}

function tick() {
  renderClock();
}

function boot() {
  renderClock();
  refreshPrayer();
  refreshWeather();
  refreshTransit();
  setInterval(tick, 1000);
  setInterval(refreshPrayer, 60 * 1000);
  setInterval(refreshWeather, 5 * 60 * 1000);
  setInterval(refreshTransit, 30 * 1000);
}

boot();
