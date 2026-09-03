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

const UZ_DAYS = ["Yakshanba", "Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba"];


// ==========================
// EKRANLARNI BOSHQARISH
// ==========================

function showScreen(id) {

  document.querySelectorAll(".screen").forEach((el) => el.classList.add("hidden"));

  document.getElementById(id).classList.remove("hidden");
}

function showError(text) {

  document.getElementById("error-text").textContent = text;

  showScreen("error");
}


// ==========================
// TARMOQ YORDAMCHILARI
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

function escapeHtml(text) {

  const div = document.createElement("div");

  div.textContent = text == null ? "" : String(text);

  return div.innerHTML;
}

function formatMoney(amount) {

  return Number(amount || 0).toLocaleString("ru-RU");
}


// ==========================
// TAB VA ORQAGA TUGMALARI (umumiy)
// ==========================

document.querySelectorAll(".back-btn").forEach((btn) => {

  btn.addEventListener("click", () => showScreen(btn.dataset.back));

});

document.querySelectorAll(".tab-row").forEach((row) => {

  row.querySelectorAll(".tab-btn").forEach((btn) => {

    btn.addEventListener("click", () => {

      row.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));

      btn.classList.add("active");

      const root = row.parentElement;

      root.querySelectorAll(".tab-pane").forEach((pane) => {

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

    if (who.role === "admin") {

      initAdmin();

    } else if (who.role === "teacher") {

      initTeacher();

    } else if (who.role === "parent") {

      initParent();

    } else {

      showError("Siz tizimda ro'yxatdan o'tmagansiz.\nBotda /start yoki /parent yuboring.");
    }

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

      showError("Sizga hali farzand bog'lanmagan.\nBotda /parent buyrug'i orqali bog'lang.");

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
      <div class="avatar">👤</div>
      <div class="child-meta">
        <strong>${escapeHtml(child.student)}</strong>
        <span>${escapeHtml(child.teacher)}</span>
      </div>
    `;

    row.addEventListener("click", () => openChild(child.link_id, true));

    container.appendChild(row);

  });

  showScreen("child-list");
}

async function openChild(linkId, showBack) {

  showScreen("loading");

  try {

    const data = await apiGet("/api/child/" + linkId);

    renderChildCard(data, showBack);

  } catch (e) {

    showError(e.message);
  }
}

function renderChildCard(data, showBack) {

  document.getElementById("student-name").textContent = data.student;
  document.getElementById("student-class").textContent = data.class_name || "-";
  document.getElementById("teacher-name").textContent = data.teacher;
  document.getElementById("department").textContent = data.department;

  renderSchedule(data.schedule, "schedule-list");
  renderPayments(data.payments);

  document.querySelector("#child-card .back-btn").classList.toggle("hidden", !showBack);

  showScreen("child-card");
}

function renderPayments(payments) {

  const container = document.getElementById("payments-list");

  container.innerHTML = "";

  if (!payments || payments.length === 0) {

    container.innerHTML = '<div class="empty-hint">Hali to\'lov tarixi yo\'q</div>';

    return;
  }

  const statusMap = {
    "tasdiqlandi": { text: "✅ To'landi", cls: "paid" },
    "kutilmoqda": { text: "⏳ Kutilmoqda", cls: "pending" },
    "rad_etildi": { text: "❌ Rad etildi", cls: "rejected" }
  };

  payments.slice(0, 12).forEach((p) => {

    const info = statusMap[p.status] || { text: p.status, cls: "pending" };

    const row = document.createElement("div");

    row.className = "payment-row";

    row.innerHTML = `
      <div>
        <div class="payment-month">${escapeHtml(p.month)}</div>
        <div class="payment-amount">${formatMoney(p.amount)} so'm</div>
      </div>
      <span class="badge ${info.cls}">${info.text}</span>
    `;

    container.appendChild(row);

  });
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
      <div class="schedule-main">
        <span class="schedule-day">${isToday ? "🔵 " : ""}${escapeHtml(s.day)}</span>
        <span class="schedule-time">🕐 ${escapeHtml(s.time)}</span>
      </div>
      <div class="schedule-sub">
        <span class="schedule-subject">${escapeHtml(s.subject)}</span>
        <span class="schedule-room">🚪 ${escapeHtml(s.room)} · ${escapeHtml(s.teacher)}</span>
      </div>
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

    const subjectSelect = document.getElementById("ns-subject");
    subjectSelect.innerHTML = me.subjects.map((s) => `<option>${escapeHtml(s)}</option>`).join("");

    const daySelect = document.getElementById("ns-day");
    daySelect.innerHTML = me.days.map((d) => `<option>${escapeHtml(d)}</option>`).join("");

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

  data.slots.forEach((slot) => {

    const row = document.createElement("div");

    row.className = "list-row";

    row.innerHTML = `
      <div>
        <div class="list-row-title">${escapeHtml(slot.day)} ${escapeHtml(slot.time)} - ${escapeHtml(slot.subject)}</div>
        <div class="list-row-sub">🚪 ${escapeHtml(slot.room)}</div>
      </div>
      <span class="list-row-badge">${slot.student_count} ta</span>
    `;

    row.addEventListener("click", () => openTeacherSlotDetail(slot.id));

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

  data.students.forEach((s) => {

    const row = document.createElement("div");

    row.className = "payment-row";

    row.innerHTML = `
      <div>
        <div class="payment-month">${escapeHtml(s.student)}</div>
        <div class="payment-amount">${formatMoney(s.fee)} so'm / oy</div>
      </div>
      <span class="badge ${s.paid ? "paid" : "pending"}">${s.paid ? "✅ To'landi" : "⏳ Kutilmoqda"}</span>
    `;

    container.appendChild(row);

  });
}

document.getElementById("t-new-slot").addEventListener("click", () => {

  document.getElementById("ns-time").value = "";
  document.getElementById("ns-room").value = "";

  showScreen("teacher-new-slot");

});

document.getElementById("ns-save").addEventListener("click", async () => {

  const subject = document.getElementById("ns-subject").value;
  const day = document.getElementById("ns-day").value;
  const time = document.getElementById("ns-time").value.trim();
  const room = document.getElementById("ns-room").value.trim();

  if (!time || !room) {

    if (tg && tg.showAlert) tg.showAlert("Soat va xonani kiriting");

    return;
  }

  try {

    await apiSend("/api/teacher/slots", "POST", { subject, day, time, room });

    await loadTeacherSlots();

    showScreen("teacher-root");

  } catch (e) {

    if (tg && tg.showAlert) tg.showAlert(e.message);

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

  document.getElementById("tsd-title").textContent = data.day + " " + data.time + " - " + data.subject;
  document.getElementById("tsd-meta").textContent = "🚪 Xona: " + data.room;

  const container = document.getElementById("tsd-students");

  container.innerHTML = "";

  if (data.students.length === 0) {

    container.innerHTML = '<div class="empty-hint">Hali o\'quvchi qo\'shilmagan</div>';

  } else {

    data.students.forEach((s) => {

      const row = document.createElement("div");

      row.className = "list-row";

      row.innerHTML = `
        <div>
          <div class="list-row-title">${escapeHtml(s.student)}</div>
          <div class="list-row-sub">${escapeHtml(s.teacher)}</div>
        </div>
        <button class="remove-btn">🗑</button>
      `;

      row.querySelector(".remove-btn").addEventListener("click", async (ev) => {

        ev.stopPropagation();

        await apiSend("/api/teacher/slot_students/" + s.row_id, "DELETE");

        await refreshTeacherSlotDetail();

      });

      container.appendChild(row);

    });
  }
}

let searchDebounce = null;

document.getElementById("tsd-search").addEventListener("input", (e) => {

  clearTimeout(searchDebounce);

  const query = e.target.value.trim();

  if (query.length < 2) {

    document.getElementById("tsd-results").innerHTML = "";

    return;
  }

  searchDebounce = setTimeout(async () => {

    try {

      const data = await apiGet("/api/teacher/search_students?q=" + encodeURIComponent(query));

      const container = document.getElementById("tsd-results");

      container.innerHTML = "";

      data.results.forEach((r) => {

        const row = document.createElement("div");

        row.className = "list-row";

        row.innerHTML = `
          <div class="list-row-title">${escapeHtml(r.student)}</div>
          <span class="list-row-sub">${escapeHtml(r.teacher)}</span>
        `;

        row.addEventListener("click", async () => {

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

  await apiSend("/api/teacher/slots/" + currentSlotId, "DELETE");

  await loadTeacherSlots();

  showScreen("teacher-root");

});


// ==========================================================
// ADMIN / DIREKTOR
// ==========================================================

async function initAdmin() {

  showScreen("admin-root");

  loadLive();
  loadDepartments();
  loadReport();
}

async function loadLive() {

  try {

    const data = await apiGet("/api/admin/live");

    document.getElementById("a-live-time").textContent = "📅 " + data.day + " · 🕐 " + data.now;

    const container = document.getElementById("a-live-list");

    container.innerHTML = "";

    if (data.live.length === 0) {

      container.innerHTML = '<div class="empty-hint">Hozir hech qanday dars yo\'q</div>';

      return;
    }

    data.live.forEach((l) => {

      const card = document.createElement("div");

      card.className = "live-card";

      card.innerHTML = `
        <div class="live-card-title">🚪 ${escapeHtml(l.room)} - ${escapeHtml(l.subject)}</div>
        <div class="live-card-meta">👨‍🏫 ${escapeHtml(l.teacher)} · 🕐 ${escapeHtml(l.time)}</div>
        <div class="live-card-students">👨‍🎓 ${l.students.map(escapeHtml).join(", ") || "o'quvchi yo'q"}</div>
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

      const row = document.createElement("div");

      row.className = "list-row";

      row.innerHTML = `<div class="list-row-title">📂 ${escapeHtml(dept)}</div>`;

      row.addEventListener("click", () => openAdminTeachers(dept));

      container.appendChild(row);

    });

  } catch (e) {}
}

async function openAdminTeachers(dept) {

  document.getElementById("at-dept-name").textContent = "📂 " + dept;

  const data = await apiGet("/api/admin/teachers?dept=" + encodeURIComponent(dept));

  const container = document.getElementById("at-teacher-list");

  container.innerHTML = "";

  data.teachers.forEach((t) => {

    const row = document.createElement("div");

    row.className = "list-row";

    row.innerHTML = `<div class="list-row-title">${t.status === "approved" ? "🔒 " : ""}${escapeHtml(t.name)}</div>`;

    row.addEventListener("click", () => openAdminSlots(t.id, t.name));

    container.appendChild(row);

  });

  showScreen("admin-teachers");
}

async function openAdminSlots(teacherId, name) {

  document.getElementById("as-teacher-name").textContent = "👨‍🏫 " + name;

  const data = await apiGet("/api/admin/teacher/" + teacherId + "/slots");

  const container = document.getElementById("as-slot-list");

  container.innerHTML = "";

  if (data.slots.length === 0) {

    container.innerHTML = '<div class="empty-hint">Hali dars vaqti kiritilmagan</div>';

  } else {

    data.slots.forEach((slot) => {

      const row = document.createElement("div");

      row.className = "list-row";

      row.innerHTML = `
        <div>
          <div class="list-row-title">${escapeHtml(slot.day)} ${escapeHtml(slot.time)} - ${escapeHtml(slot.subject)}</div>
          <div class="list-row-sub">🚪 ${escapeHtml(slot.room)}</div>
        </div>
        <span class="list-row-badge">${slot.student_count} ta</span>
      `;

      row.addEventListener("click", () => openAdminSlotDetail(slot.id));

      container.appendChild(row);

    });
  }

  showScreen("admin-slots");
}

async function openAdminSlotDetail(slotId) {

  const data = await apiGet("/api/admin/slot/" + slotId);

  document.getElementById("asd-title").textContent = data.day + " " + data.time + " - " + data.subject;
  document.getElementById("asd-meta").textContent = "🚪 Xona: " + data.room + " · 👨‍🏫 " + data.teacher;

  const container = document.getElementById("asd-students");

  container.innerHTML = "";

  if (data.students.length === 0) {

    container.innerHTML = '<div class="empty-hint">O\'quvchi yo\'q</div>';

  } else {

    data.students.forEach((s) => {

      const row = document.createElement("div");

      row.className = "list-row";

      row.innerHTML = `
        <div class="list-row-title">${escapeHtml(s.student)}</div>
        <span class="list-row-sub">${escapeHtml(s.teacher)}</span>
      `;

      container.appendChild(row);

    });
  }

  showScreen("admin-slot-detail");
}

async function loadReport() {

  try {

    const data = await apiGet("/api/admin/report");

    document.getElementById("a-report-month").textContent =
      "📅 " + data.month + " · Jami qarz: " + formatMoney(data.total_debt) + " so'm";

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
        <span class="badge ${t.debt > 0 ? "rejected" : "paid"}">${formatMoney(t.debt)} so'm</span>
      `;

      container.appendChild(row);

    });

  } catch (e) {}
}


// ==========================================================
// DEMO REJIM (Telegram tashqarisida ko'rish uchun)
// ==========================================================

function runDemo(role) {

  if (role === "teacher") {

    document.getElementById("t-name").textContent = "Qayumov Qobil";

    document.getElementById("ns-subject").innerHTML =
      ["Mutaxassislik", "Solfedjio", "San'at tarixi"].map((s) => `<option>${s}</option>`).join("");

    document.getElementById("ns-day").innerHTML =
      UZ_DAYS.slice(1).concat(UZ_DAYS[0]).map((d) => `<option>${d}</option>`).join("");

    document.getElementById("t-slots-list").innerHTML = `
      <div class="list-row"><div><div class="list-row-title">Dushanba 15:00 - Mutaxassislik</div><div class="list-row-sub">🚪 12</div></div><span class="list-row-badge">2 ta</span></div>
    `;

    document.getElementById("t-students-list").innerHTML = `
      <div class="payment-row"><div><div class="payment-month">Alisherov Zafar</div><div class="payment-amount">250 000 so'm / oy</div></div><span class="badge paid">✅ To'landi</span></div>
    `;

    showScreen("teacher-root");

    return;
  }

  if (role === "admin") {

    document.getElementById("a-live-time").textContent = "📅 Payshanba · 🕐 14:20";

    document.getElementById("a-live-list").innerHTML = `
      <div class="live-card">
        <div class="live-card-title">🚪 3 - San'at tarixi</div>
        <div class="live-card-meta">👨‍🏫 Karimov B. · 🕐 14:00</div>
        <div class="live-card-students">👨‍🎓 Alisherov Zafar, Aliyev Vali</div>
      </div>
    `;

    document.getElementById("a-dept-list").innerHTML = `<div class="list-row"><div class="list-row-title">📂 Xalq cholg'u</div></div>`;

    document.getElementById("a-report-month").textContent = "📅 2026-09 · Jami qarz: 500 000 so'm";

    document.getElementById("a-report-list").innerHTML = `
      <div class="payment-row"><div><div class="payment-month">Qayumov Qobil</div><div class="payment-amount">Xalq cholg'u · 2/5 qarzdor</div></div><span class="badge rejected">500 000 so'm</span></div>
    `;

    showScreen("admin-root");

    return;
  }

  // parent (standart)

  renderChildCard({
    student: "Alisherov Zafar Javlon o'g'li",
    class_name: "3-sinf",
    teacher: "Qayumov Qobil",
    department: "Xalq cholg'u",
    payments: [
      { month: "2026-09", status: "tasdiqlandi", amount: 250000, date: "" },
      { month: "2026-08", status: "kutilmoqda", amount: 250000, date: "" }
    ],
    schedule: [
      { subject: "Mutaxassislik", day: "Dushanba", time: "15:00", room: "12", teacher: "Qayumov Qobil" },
      { subject: "Solfedjio", day: "Seshanba", time: "16:00", room: "5", teacher: "Rahimova Sh." }
    ]
  }, false);
}

init();
