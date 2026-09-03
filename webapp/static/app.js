// ==========================
// webapp/static/app.js
// MINI APP - FRONTEND MANTIQI
// ==========================

const tg = window.Telegram ? window.Telegram.WebApp : null;

if (tg) {
  tg.ready();
  tg.expand();
}

const initData = tg ? tg.initData : "";

const UZ_DAYS = [
  "Yakshanba", "Dushanba", "Seshanba", "Chorshanba",
  "Payshanba", "Juma", "Shanba"
];

const UZ_MONTHS = [
  "Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun",
  "Iyul", "Avgust", "Sentabr", "Oktabr", "Noyabr", "Dekabr"
];


// ==========================
// YORDAMCHILAR
// ==========================

function showScreen(id) {

  document.querySelectorAll(".screen").forEach((el) => el.classList.add("hidden"));

  const el = document.getElementById(id);

  if (el) {
    el.classList.remove("hidden");
    window.scrollTo(0, 0);
  }
}

function showError(text) {

  document.getElementById("error-text").textContent = text;

  showScreen("error");
}

function escapeHtml(text) {

  const div = document.createElement("div");

  div.textContent = text == null ? "" : String(text);

  return div.innerHTML;
}

function formatMoney(amount) {

  return Number(amount || 0).toLocaleString("ru-RU").replace(/ /g, " ");
}

/** "2026-09" -> "Sentabr 2026" */
function formatMonth(value) {

  const match = /^(\d{4})-(\d{2})$/.exec(value || "");

  if (!match) return value || "—";

  const monthIndex = parseInt(match[2], 10) - 1;

  return (UZ_MONTHS[monthIndex] || match[2]) + " " + match[1];
}

/** "Alisherov Zafar" -> "AZ" */
function initials(name) {

  const parts = String(name || "")
    .trim()
    .split(/\s+/)
    .filter((p) => /[\p{L}]/u.test(p));

  if (parts.length === 0) return "?";

  const first = parts[0][0] || "";
  const second = parts.length > 1 ? parts[1][0] : "";

  return (first + second).toUpperCase();
}


// ==========================
// TARMOQ
// ==========================

async function apiGet(path) {

  const res = await fetch(path, {
    headers: { "X-Telegram-Init-Data": initData }
  });

  return handleResponse(res);
}

async function apiSend(path, method, body) {

  const res = await fetch(path, {
    method,
    headers: {
      "X-Telegram-Init-Data": initData,
      "Content-Type": "application/json"
    },
    body: body ? JSON.stringify(body) : undefined
  });

  return handleResponse(res);
}

async function handleResponse(res) {

  if (!res.ok) {

    const body = await res.json().catch(() => ({}));

    throw new Error(body.error || ("Xato: " + res.status));
  }

  return res.json();
}

function notify(text) {

  if (tg && tg.showAlert) tg.showAlert(text);
  else alert(text);
}

function haptic() {

  if (tg && tg.HapticFeedback) {
    try { tg.HapticFeedback.impactOccurred("light"); } catch (e) {}
  }
}


// ==========================
// TAB / ORQAGA
// ==========================

document.querySelectorAll(".back-btn").forEach((btn) => {

  btn.addEventListener("click", () => showScreen(btn.dataset.back));

});

document.querySelectorAll(".tab-row").forEach((row) => {

  row.querySelectorAll(".tab-btn").forEach((btn) => {

    btn.addEventListener("click", () => {

      haptic();

      row.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));

      btn.classList.add("active");

      row.parentElement.querySelectorAll(".tab-pane").forEach((pane) => {

        pane.classList.toggle("hidden", pane.id !== btn.dataset.tab);

      });

    });

  });

});


// ==========================
// BOSHLANISH - ROL ANIQLASH
// ==========================

const params = new URLSearchParams(location.search);

const demoRole = params.get("demo") === "1" ? (params.get("role") || "parent") : null;


async function init() {

  if (demoRole) {
    runDemo(demoRole);
    return;
  }

  if (!initData) {
    showError("Bu sahifa faqat Telegram ichida ishlaydi.");
    return;
  }

  try {

    const who = await apiGet("/api/whoami");

    if (who.role === "admin")        initAdmin();
    else if (who.role === "teacher") initTeacher();
    else if (who.role === "parent")  initParent();
    else showError("Siz tizimda ro'yxatdan o'tmagansiz.\nBotda /start yoki /parent yuboring.");

  } catch (e) {

    showError(e.message);
  }
}


// ==========================================================
// OTA-ONA
// ==========================================================

async function initParent() {

  try {

    const me = await apiGet("/api/me");

    if (!me.children || me.children.length === 0) {
      showError("Sizga hali farzand bog'lanmagan.\nBotda /parent orqali ITV raqamini kiriting.");
      return;
    }

    if (me.children.length === 1) {
      openChild(me.children[0].link_id, false);
      return;
    }

    renderChildList(me.children);

  } catch (e) {

    showError(e.message);
  }
}

function renderChildList(children) {

  const container = document.getElementById("child-list-items");

  container.innerHTML = "";

  children.forEach((child) => {

    const row = document.createElement("div");

    row.className = "child-row";

    row.innerHTML = `
      <div class="child-avatar">${escapeHtml(initials(child.student))}</div>
      <div class="child-meta">
        <strong>${escapeHtml(child.student)}</strong>
        <span>${escapeHtml(child.teacher)}</span>
      </div>
    `;

    row.addEventListener("click", () => { haptic(); openChild(child.link_id, true); });

    container.appendChild(row);

  });

  showScreen("child-list");
}

async function openChild(linkId, showBack) {

  showScreen("loading");

  try {

    renderChildCard(await apiGet("/api/child/" + linkId), showBack);

  } catch (e) {

    showError(e.message);
  }
}

function renderChildCard(data, showBack) {

  document.getElementById("student-initials").textContent = initials(data.student);
  document.getElementById("student-name").textContent = data.student;
  document.getElementById("student-class").textContent = data.class_name || "—";
  document.getElementById("department").textContent = data.department || "—";
  document.getElementById("teacher-name").textContent = data.teacher;

  document.getElementById("monthly-fee").textContent =
    data.monthly_fee ? formatMoney(data.monthly_fee) + " so'm" : "—";

  renderSchedule(data.schedule, "schedule-list");
  renderPayments(data.payments);

  document.querySelector("#child-card .back-btn").classList.toggle("hidden", !showBack);

  showScreen("child-card");
}

function renderSchedule(schedule, containerId) {

  const container = document.getElementById(containerId);

  container.innerHTML = "";

  if (!schedule || schedule.length === 0) {
    container.innerHTML = '<div class="empty-hint">Hali dars jadvali kiritilmagan</div>';
    return;
  }

  const today = UZ_DAYS[new Date().getDay()];

  schedule.forEach((s) => {

    const isToday = s.day === today;

    const row = document.createElement("div");

    row.className = "schedule-row" + (isToday ? " today" : "");

    row.innerHTML = `
      <div class="schedule-top">
        <span class="schedule-day">
          ${escapeHtml(s.day)}${isToday ? '<span class="today-tag">BUGUN</span>' : ""}
        </span>
        <span class="schedule-time">${escapeHtml(s.time)}</span>
      </div>
      <div class="schedule-subject">${escapeHtml(s.subject)}</div>
      <div class="schedule-meta">${escapeHtml(s.room)}-xona · ${escapeHtml(s.teacher)}</div>
    `;

    container.appendChild(row);

  });
}

const PAYMENT_STATUS = {
  "tasdiqlandi": { text: "To'landi",   cls: "paid" },
  "kutilmoqda":  { text: "Kutilmoqda", cls: "pending" },
  "rad_etildi":  { text: "Rad etildi", cls: "rejected" }
};

function renderPayments(payments) {

  const container = document.getElementById("payments-list");

  container.innerHTML = "";

  if (!payments || payments.length === 0) {
    container.innerHTML = '<div class="empty-hint">Hali to\'lov tarixi yo\'q</div>';
    return;
  }

  payments.slice(0, 12).forEach((p) => {

    const info = PAYMENT_STATUS[p.status] || { text: p.status, cls: "pending" };

    const row = document.createElement("div");

    row.className = "payment-row";

    row.innerHTML = `
      <div>
        <div class="payment-month">${escapeHtml(formatMonth(p.month))}</div>
        <div class="payment-amount">${formatMoney(p.amount)} so'm</div>
      </div>
      <span class="badge ${info.cls}">${escapeHtml(info.text)}</span>
    `;

    container.appendChild(row);

  });
}


// ==========================================================
// O'QITUVCHI
// ==========================================================

async function initTeacher() {

  try {

    const me = await apiGet("/api/teacher/me");

    document.getElementById("t-name").textContent = me.teacher;

    document.getElementById("ns-subject").innerHTML =
      me.subjects.map((s) => `<option>${escapeHtml(s)}</option>`).join("");

    document.getElementById("ns-day").innerHTML =
      me.days.map((d) => `<option>${escapeHtml(d)}</option>`).join("");

    await loadTeacherSlots();
    await loadTeacherStudents();

    showScreen("teacher-root");

  } catch (e) {

    showError(e.message);
  }
}

async function loadTeacherSlots() {

  const data = await apiGet("/api/teacher/slots");

  const container = document.getElementById("t-slots-list");

  container.innerHTML = "";

  if (data.slots.length === 0) {
    container.innerHTML = '<div class="empty-hint">Hali dars vaqti kiritilmagan</div>';
    return;
  }

  const today = UZ_DAYS[new Date().getDay()];

  data.slots.forEach((slot) => {

    const isToday = slot.day === today;

    const row = document.createElement("div");

    row.className = "schedule-row" + (isToday ? " today" : "");
    row.style.cursor = "pointer";

    row.innerHTML = `
      <div class="schedule-top">
        <span class="schedule-day">
          ${escapeHtml(slot.day)}${isToday ? '<span class="today-tag">BUGUN</span>' : ""}
        </span>
        <span class="schedule-time">${escapeHtml(slot.time)}</span>
      </div>
      <div class="schedule-subject">${escapeHtml(slot.subject)}</div>
      <div class="schedule-meta">${escapeHtml(slot.room)}-xona · ${slot.student_count} ta o'quvchi</div>
    `;

    row.addEventListener("click", () => { haptic(); openTeacherSlotDetail(slot.id); });

    container.appendChild(row);

  });
}

async function loadTeacherStudents() {

  const data = await apiGet("/api/teacher/students");

  const container = document.getElementById("t-students-list");

  container.innerHTML = "";

  if (data.students.length === 0) {
    container.innerHTML = '<div class="empty-hint">Hali o\'quvchi yo\'q</div>';
    return;
  }

  const header = document.createElement("p");
  header.className = "muted";
  header.style.marginBottom = "4px";
  header.textContent = formatMonth(data.month) + " uchun to'lov holati";
  container.appendChild(header);

  data.students.forEach((s) => {

    const row = document.createElement("div");

    row.className = "payment-row";

    row.innerHTML = `
      <div>
        <div class="payment-month">${escapeHtml(s.student)}</div>
        <div class="payment-amount">${s.fee ? formatMoney(s.fee) + " so'm / oy" : "badal kiritilmagan"}</div>
      </div>
      <span class="badge ${s.paid ? "paid" : "pending"}">${s.paid ? "To'landi" : "Kutilmoqda"}</span>
    `;

    container.appendChild(row);

  });
}

document.getElementById("t-new-slot").addEventListener("click", () => {

  haptic();

  document.getElementById("ns-time").value = "";
  document.getElementById("ns-room").value = "";

  showScreen("teacher-new-slot");

});

document.getElementById("ns-save").addEventListener("click", async () => {

  const payload = {
    subject: document.getElementById("ns-subject").value,
    day:     document.getElementById("ns-day").value,
    time:    document.getElementById("ns-time").value.trim(),
    room:    document.getElementById("ns-room").value.trim()
  };

  if (!payload.time || !payload.room) {
    notify("Soat va xonani kiriting");
    return;
  }

  try {

    await apiSend("/api/teacher/slots", "POST", payload);

    await loadTeacherSlots();

    showScreen("teacher-root");

  } catch (e) {

    notify(e.message);
  }

});

let currentSlotId = null;

async function openTeacherSlotDetail(slotId) {

  currentSlotId = slotId;

  document.getElementById("tsd-search").value = "";
  document.getElementById("tsd-results").innerHTML = "";

  await refreshTeacherSlotDetail();

  showScreen("teacher-slot-detail");
}

async function refreshTeacherSlotDetail() {

  const data = await apiGet("/api/teacher/slots/" + currentSlotId);

  document.getElementById("tsd-title").textContent = data.subject;

  document.getElementById("tsd-meta").textContent =
    data.day + " · " + data.time + " · " + data.room + "-xona";

  const container = document.getElementById("tsd-students");

  container.innerHTML = "";

  if (data.students.length === 0) {

    container.innerHTML = '<div class="empty-hint">Hali o\'quvchi qo\'shilmagan</div>';

    return;
  }

  data.students.forEach((s) => {

    const row = document.createElement("div");

    row.className = "list-row";

    row.innerHTML = `
      <div>
        <div class="list-row-title">${escapeHtml(s.student)}</div>
        <div class="list-row-sub">${escapeHtml(s.teacher)}</div>
      </div>
      <button class="remove-btn" title="O'chirish">✕</button>
    `;

    row.querySelector(".remove-btn").addEventListener("click", async (ev) => {

      ev.stopPropagation();

      haptic();

      await apiSend("/api/teacher/slot_students/" + s.row_id, "DELETE");

      await refreshTeacherSlotDetail();

    });

    container.appendChild(row);

  });
}

let searchDebounce = null;

document.getElementById("tsd-search").addEventListener("input", (e) => {

  clearTimeout(searchDebounce);

  const query = e.target.value.trim();

  const container = document.getElementById("tsd-results");

  if (query.length < 2) {
    container.innerHTML = "";
    return;
  }

  searchDebounce = setTimeout(async () => {

    try {

      const data = await apiGet("/api/teacher/search_students?q=" + encodeURIComponent(query));

      container.innerHTML = "";

      if (data.results.length === 0) {
        container.innerHTML = '<div class="empty-hint">Topilmadi</div>';
        return;
      }

      data.results.forEach((r) => {

        const row = document.createElement("div");

        row.className = "list-row";

        row.innerHTML = `
          <div>
            <div class="list-row-title">${escapeHtml(r.student)}</div>
            <div class="list-row-sub">${escapeHtml(r.teacher)}</div>
          </div>
          <span class="list-row-badge">＋</span>
        `;

        row.addEventListener("click", async () => {

          haptic();

          await apiSend("/api/teacher/slots/" + currentSlotId + "/students", "POST", r);

          document.getElementById("tsd-search").value = "";

          container.innerHTML = "";

          await refreshTeacherSlotDetail();

        });

        container.appendChild(row);

      });

    } catch (e) {}

  }, 300);

});

document.getElementById("tsd-delete").addEventListener("click", async () => {

  haptic();

  await apiSend("/api/teacher/slots/" + currentSlotId, "DELETE");

  await loadTeacherSlots();

  showScreen("teacher-root");

});


// ==========================================================
// DIREKTOR
// ==========================================================

function initAdmin() {

  showScreen("admin-root");

  loadLive();
  loadDepartments();
  loadReport();
}

async function loadLive() {

  try {

    const data = await apiGet("/api/admin/live");

    document.getElementById("a-live-time").textContent =
      data.day + " · " + data.now;

    const container = document.getElementById("a-live-list");

    container.innerHTML = "";

    if (data.live.length === 0) {
      container.innerHTML = '<div class="empty-hint">Hozir dars ketayotgan xona yo\'q</div>';
      return;
    }

    data.live.forEach((l) => {

      const card = document.createElement("div");

      card.className = "live-card";

      card.innerHTML = `
        <div class="live-card-top">
          <span class="live-room">${escapeHtml(l.room)}-xona</span>
          <span class="live-time">${escapeHtml(l.time)}</span>
        </div>
        <div class="live-subject">${escapeHtml(l.subject)} · ${escapeHtml(l.teacher)}</div>
        <div class="live-students">${
          l.students.length
            ? l.students.map(escapeHtml).join(", ")
            : "<span style='opacity:.6'>o'quvchi biriktirilmagan</span>"
        }</div>
      `;

      container.appendChild(card);

    });

  } catch (e) {}
}

async function loadDepartments() {

  try {

    const data = await apiGet("/api/admin/departments");

    const container = document.getElementById("a-dept-list");

    container.innerHTML = "";

    data.departments.forEach((dept) => {

      container.appendChild(
        clickableRow(dept, null, () => openAdminTeachers(dept))
      );

    });

  } catch (e) {}
}

function clickableRow(title, sub, onClick) {

  const row = document.createElement("div");

  row.className = "list-row";

  row.innerHTML = `
    <div>
      <div class="list-row-title">${escapeHtml(title)}</div>
      ${sub ? `<div class="list-row-sub">${escapeHtml(sub)}</div>` : ""}
    </div>
    <span class="chevron">›</span>
  `;

  row.addEventListener("click", () => { haptic(); onClick(); });

  return row;
}

async function openAdminTeachers(dept) {

  document.getElementById("at-dept-name").textContent = dept;

  const data = await apiGet("/api/admin/teachers?dept=" + encodeURIComponent(dept));

  const container = document.getElementById("at-teacher-list");

  container.innerHTML = "";

  if (data.teachers.length === 0) {
    container.innerHTML = '<div class="empty-hint">Bu bo\'limda o\'qituvchi yo\'q</div>';
  }

  data.teachers.forEach((t) => {

    container.appendChild(
      clickableRow(
        t.name,
        t.status === "approved" ? "ro'yxatdan o'tgan" : null,
        () => openAdminSlots(t.id, t.name)
      )
    );

  });

  showScreen("admin-teachers");
}

async function openAdminSlots(teacherId, name) {

  document.getElementById("as-teacher-name").textContent = name;

  const data = await apiGet("/api/admin/teacher/" + teacherId + "/slots");

  const container = document.getElementById("as-slot-list");

  container.innerHTML = "";

  if (data.slots.length === 0) {

    container.innerHTML = '<div class="empty-hint">Hali dars vaqti kiritilmagan</div>';

  } else {

    data.slots.forEach((slot) => {

      container.appendChild(
        clickableRow(
          slot.day + " · " + slot.time + " · " + slot.subject,
          slot.room + "-xona · " + slot.student_count + " ta o'quvchi",
          () => openAdminSlotDetail(slot.id)
        )
      );

    });
  }

  showScreen("admin-slots");
}

async function openAdminSlotDetail(slotId) {

  const data = await apiGet("/api/admin/slot/" + slotId);

  document.getElementById("asd-title").textContent = data.subject;

  document.getElementById("asd-meta").textContent =
    data.day + " · " + data.time + " · " + data.room + "-xona · " + data.teacher;

  const container = document.getElementById("asd-students");

  container.innerHTML = "";

  if (data.students.length === 0) {

    container.innerHTML = '<div class="empty-hint">O\'quvchi biriktirilmagan</div>';

  } else {

    data.students.forEach((s) => {

      const row = document.createElement("div");

      row.className = "list-row";

      row.style.cursor = "default";

      row.innerHTML = `
        <div>
          <div class="list-row-title">${escapeHtml(s.student)}</div>
          <div class="list-row-sub">${escapeHtml(s.teacher)}</div>
        </div>
      `;

      container.appendChild(row);

    });
  }

  showScreen("admin-slot-detail");
}

async function loadReport() {

  try {

    const data = await apiGet("/api/admin/report");

    document.getElementById("a-stat-debt").textContent = formatMoney(data.total_debt);
    document.getElementById("a-stat-unpaid").textContent = data.total_unpaid;

    document.getElementById("a-report-month").textContent =
      formatMonth(data.month) + " · o'qituvchilar bo'yicha";

    const container = document.getElementById("a-report-list");

    container.innerHTML = "";

    if (data.teachers.length === 0) {
      container.innerHTML = '<div class="empty-hint">Ma\'lumot yo\'q</div>';
      return;
    }

    data.teachers.forEach((t) => {

      const row = document.createElement("div");

      row.className = "payment-row";

      row.innerHTML = `
        <div>
          <div class="payment-month">${escapeHtml(t.teacher)}</div>
          <div class="payment-amount">${escapeHtml(t.department)} · ${t.unpaid}/${t.total} qarzdor</div>
        </div>
        <span class="badge ${t.debt > 0 ? "rejected" : "paid"}">${formatMoney(t.debt)}</span>
      `;

      container.appendChild(row);

    });

  } catch (e) {}
}


// ==========================================================
// DEMO (Telegram tashqarisida ko'rish uchun)
// ==========================================================

function runDemo(role) {

  if (role === "teacher") {

    document.getElementById("t-name").textContent = "Qayumov Qobil";

    document.getElementById("ns-subject").innerHTML =
      ["Mutaxassislik", "Solfedjio", "San'at tarixi"].map((s) => `<option>${s}</option>`).join("");

    document.getElementById("ns-day").innerHTML =
      UZ_DAYS.slice(1).concat(UZ_DAYS[0]).map((d) => `<option>${d}</option>`).join("");

    const today = UZ_DAYS[new Date().getDay()];

    document.getElementById("t-slots-list").innerHTML = [
      { day: "Dushanba", time: "15:00", subject: "Mutaxassislik", room: "12", n: 2 },
      { day: today, time: "16:30", subject: "Ansambl", room: "7", n: 5 }
    ].map((s) => `
      <div class="schedule-row${s.day === today ? " today" : ""}">
        <div class="schedule-top">
          <span class="schedule-day">${s.day}${s.day === today ? '<span class="today-tag">BUGUN</span>' : ""}</span>
          <span class="schedule-time">${s.time}</span>
        </div>
        <div class="schedule-subject">${s.subject}</div>
        <div class="schedule-meta">${s.room}-xona · ${s.n} ta o'quvchi</div>
      </div>`).join("");

    document.getElementById("t-students-list").innerHTML = `
      <p class="muted" style="margin-bottom:4px">Sentabr 2026 uchun to'lov holati</p>
      <div class="payment-row"><div><div class="payment-month">Alisherov Zafar</div><div class="payment-amount">250 000 so'm / oy</div></div><span class="badge paid">To'landi</span></div>
      <div class="payment-row"><div><div class="payment-month">Mansurov Abbosxo'ja</div><div class="payment-amount">250 000 so'm / oy</div></div><span class="badge pending">Kutilmoqda</span></div>
    `;

    showScreen("teacher-root");

    return;
  }

  if (role === "admin") {

    document.getElementById("a-live-time").textContent =
      UZ_DAYS[new Date().getDay()] + " · 14:20";

    document.getElementById("a-live-list").innerHTML = `
      <div class="live-card">
        <div class="live-card-top">
          <span class="live-room">3-xona</span>
          <span class="live-time">14:00</span>
        </div>
        <div class="live-subject">San'at tarixi · Karimov B.</div>
        <div class="live-students">Alisherov Zafar, Aliyev Vali, Sodiqova Nilufar</div>
      </div>
      <div class="live-card">
        <div class="live-card-top">
          <span class="live-room">12-xona</span>
          <span class="live-time">14:15</span>
        </div>
        <div class="live-subject">Mutaxassislik · Qayumov Qobil</div>
        <div class="live-students">Mansurov Abbosxo'ja</div>
      </div>
    `;

    document.getElementById("a-dept-list").innerHTML =
      ["Xalq cholg'u", "Fortepiano", "Folklor"].map((d) => `
        <div class="list-row">
          <div><div class="list-row-title">${d}</div></div>
          <span class="chevron">›</span>
        </div>`).join("");

    document.getElementById("a-stat-debt").textContent = "1 250 000";
    document.getElementById("a-stat-unpaid").textContent = "5";

    document.getElementById("a-report-month").textContent = "Sentabr 2026 · o'qituvchilar bo'yicha";

    document.getElementById("a-report-list").innerHTML = `
      <div class="payment-row"><div><div class="payment-month">Qayumov Qobil</div><div class="payment-amount">Xalq cholg'u · 3/5 qarzdor</div></div><span class="badge rejected">750 000</span></div>
      <div class="payment-row"><div><div class="payment-month">Isroilova Dilshoda</div><div class="payment-amount">Fortepiano · 2/4 qarzdor</div></div><span class="badge rejected">500 000</span></div>
      <div class="payment-row"><div><div class="payment-month">Jo'rayev Uchqun</div><div class="payment-amount">Xalq cholg'u · 0/10 qarzdor</div></div><span class="badge paid">0</span></div>
    `;

    showScreen("admin-root");

    return;
  }

  const today = UZ_DAYS[new Date().getDay()];

  renderChildCard({
    student: "Alisherov Zafar Javlon o'g'li",
    class_name: "3-sinf",
    teacher: "Qayumov Qobil",
    department: "Xalq cholg'u",
    monthly_fee: 250000,
    payments: [
      { month: "2026-09", status: "tasdiqlandi", amount: 250000 },
      { month: "2026-08", status: "kutilmoqda",  amount: 250000 },
      { month: "2026-07", status: "rad_etildi",  amount: 250000 }
    ],
    schedule: [
      { subject: "Mutaxassislik", day: "Dushanba", time: "15:00", room: "12", teacher: "Qayumov Qobil" },
      { subject: "Solfedjio",     day: "Seshanba", time: "16:00", room: "5",  teacher: "Rahimova Sh." },
      { subject: "San'at tarixi", day: today,      time: "14:00", room: "3",  teacher: "Karimov B." },
      { subject: "Tanlangan fan", day: "Juma",     time: "15:00", room: "8",  teacher: "Ismoilova N." }
    ]
  }, false);
}

init();
