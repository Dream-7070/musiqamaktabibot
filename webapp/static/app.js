// ==========================================================
// 19-son musiqa maktabi — Mini App
// ==========================================================

const tg = window.Telegram ? window.Telegram.WebApp : null;

if (tg) {
  tg.ready();
  tg.expand();
  try {
    tg.setHeaderColor("#11151F");
    tg.setBackgroundColor("#0B0E14");
  } catch (e) {}
}

const initData = tg ? tg.initData : "";

const UZ_DAYS = ["Yakshanba", "Dushanba", "Seshanba", "Chorshanba",
                 "Payshanba", "Juma", "Shanba"];

const UZ_MONTHS = ["Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun",
                   "Iyul", "Avgust", "Sentabr", "Oktabr", "Noyabr", "Dekabr"];

const TODAY = UZ_DAYS[new Date().getDay()];


// ==========================
// YORDAMCHILAR
// ==========================

const $ = (id) => document.getElementById(id);

function el(html) {
  const t = document.createElement("template");
  t.innerHTML = html.trim();
  return t.content.firstElementChild;
}

function esc(text) {
  const d = document.createElement("div");
  d.textContent = text == null ? "" : String(text);
  return d.innerHTML;
}

function money(n) {
  return Number(n || 0).toLocaleString("ru-RU").replace(/ /g, " ");
}

function shortMoney(n) {
  n = Number(n || 0);
  if (n >= 1000000) return (n / 1000000).toFixed(1).replace(".0", "") + " <small>mln</small>";
  if (n >= 1000)    return Math.round(n / 1000) + " <small>ming</small>";
  return String(n);
}

function monthName(v) {
  const m = /^(\d{4})-(\d{2})$/.exec(v || "");
  if (!m) return v || "—";
  return (UZ_MONTHS[parseInt(m[2], 10) - 1] || m[2]) + " " + m[1];
}

function initials(name) {
  const p = String(name || "").trim().split(/\s+/).filter((x) => /[\p{L}]/u.test(x));
  if (!p.length) return "?";
  return ((p[0][0] || "") + (p.length > 1 ? p[1][0] : "")).toUpperCase();
}

function haptic(kind) {
  if (!tg || !tg.HapticFeedback) return;
  try { tg.HapticFeedback.impactOccurred(kind || "light"); } catch (e) {}
}

function notify(text) {
  if (tg && tg.showAlert) tg.showAlert(text);
  else alert(text);
}


// ==========================
// TARMOQ
// ==========================

async function api(path, method, body) {
  const res = await fetch(path, {
    method: method || "GET",
    headers: {
      "X-Telegram-Init-Data": initData,
      "Content-Type": "application/json"
    },
    body: body ? JSON.stringify(body) : undefined
  });

  if (!res.ok) {
    const b = await res.json().catch(() => ({}));
    throw new Error(b.error || ("Xato: " + res.status));
  }

  return res.json();
}


// ==========================
// EKRAN HOLATI
// ==========================

function showLoading() {
  $("loading").classList.remove("hidden");
  $("error").classList.add("hidden");
  $("app").classList.add("hidden");
  $("nav").classList.add("hidden");
}

function showError(text) {
  $("error-text").textContent = text;
  $("loading").classList.add("hidden");
  $("error").classList.remove("hidden");
  $("app").classList.add("hidden");
  $("nav").classList.add("hidden");
}

function showApp() {
  $("loading").classList.add("hidden");
  $("error").classList.add("hidden");
  $("app").classList.remove("hidden");
  $("nav").classList.remove("hidden");
}

function setHead(badge, title, sub) {
  $("head-badge").textContent = badge;
  $("head-title").textContent = title;
  $("head-sub").textContent = sub || "";
}

function setPane(node) {
  const p = $("panes");
  p.innerHTML = "";
  const box = el('<div class="pane"></div>');
  box.appendChild(node);
  p.appendChild(box);
  window.scrollTo(0, 0);
}


// ==========================
// PASTDAN CHIQUVCHI OYNA
// ==========================

function openSheet(html) {
  $("sheet-body").innerHTML = "";
  $("sheet-body").appendChild(typeof html === "string" ? el(html) : html);
  $("sheet").classList.add("open");
  $("sheet-back").classList.add("open");
}

function closeSheet() {
  $("sheet").classList.remove("open");
  $("sheet-back").classList.remove("open");
}

$("sheet-back").addEventListener("click", closeSheet);


// ==========================
// IKONKALAR
// ==========================

const ICON = {
  user:     '<svg viewBox="0 0 24 24"><circle cx="12" cy="8" r="4"/><path d="M4.5 20a7.5 7.5 0 0115 0"/></svg>',
  calendar: '<svg viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="16" rx="3"/><path d="M8 3v4M16 3v4M3 10h18"/></svg>',
  wallet:   '<svg viewBox="0 0 24 24"><rect x="3" y="6" width="18" height="13" rx="3"/><path d="M3 10h18M16.5 14.5h.01"/></svg>',
  users:    '<svg viewBox="0 0 24 24"><circle cx="9" cy="8" r="3.4"/><path d="M3 19a6 6 0 0112 0M16 5.5a3.4 3.4 0 010 6.6M18 19a6 6 0 00-2-4.4"/></svg>',
  clock:    '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>',
  chart:    '<svg viewBox="0 0 24 24"><path d="M4 19V10M10 19V5M16 19v-6M22 19H2"/></svg>',
  search:   '<svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/></svg>'
};


// ==========================
// NAVIGATSIYA
// ==========================

let NAV = [];
let activeTab = null;

function buildNav(items) {
  NAV = items;
  const nav = $("nav");
  nav.innerHTML = "";

  items.forEach((item, i) => {
    const b = el(
      '<button class="nav-item' + (i === 0 ? " on" : "") + '">' +
      item.icon + esc(item.label) + "</button>"
    );
    b.addEventListener("click", () => selectTab(item.id));
    nav.appendChild(b);
  });

  selectTab(items[0].id);
}

function selectTab(id) {
  if (activeTab !== id) haptic();
  activeTab = id;

  const nav = $("nav");
  NAV.forEach((item, i) => {
    nav.children[i].classList.toggle("on", item.id === id);
  });

  const item = NAV.find((x) => x.id === id);
  if (item) item.render();
}


// ==========================
// BOSHLANISH
// ==========================

const state = {};

async function init() {
  if (!initData) {
    showError("Bu sahifa faqat Telegram ichida ishlaydi.");
    return;
  }

  try {
    const who = await api("/api/whoami");

    if (who.role === "admin")        return initAdmin(who);
    if (who.role === "teacher")      return initTeacher();
    if (who.role === "parent")       return initParent();
    if (who.role === "staff")        return initStaff(who);

    showError("Siz tizimda ro'yxatdan o'tmagansiz.\nBotda /start yuboring.");

  } catch (e) {
    showError(e.message);
  }
}


// ==========================================================
// OTA-ONA
// ==========================================================

async function initParent() {
  const me = await api("/api/me");

  if (!me.children || !me.children.length) {
    showError("Sizga hali farzand bog'lanmagan.\nBotda /start → «Men ota-onaman».");
    return;
  }

  state.children = me.children;
  await loadChild(me.children[0].link_id);

  buildNav([
    { id: "p-child",    label: "Farzandim",  icon: ICON.user,     render: renderParentChild },
    { id: "p-schedule", label: "Jadval",     icon: ICON.calendar, render: renderParentSchedule },
    { id: "p-pay",      label: "To'lovlar",  icon: ICON.wallet,   render: renderParentPayments }
  ]);

  showApp();
}

async function loadChild(linkId) {
  state.child = await api("/api/child/" + linkId);
  state.childLink = linkId;
  setHead(initials(state.child.student), state.child.student, state.child.department);
}

function childSwitcher() {
  if (!state.children || state.children.length < 2) return "";

  return '<div class="chips" style="margin:0 0 18px">' +
    state.children.map((c) =>
      '<span class="chip' + (c.link_id === state.childLink ? " on" : "") + '" ' +
      'data-link="' + c.link_id + '" style="cursor:pointer' +
      (c.link_id === state.childLink
        ? ";background:var(--accent-dim);border-color:rgba(167,139,250,.3);color:var(--accent-2)"
        : "") + '">' + esc(c.student.split(/\s+/)[0]) + "</span>"
    ).join("") + "</div>";
}

function wireSwitcher(node) {
  node.querySelectorAll("[data-link]").forEach((c) => {
    c.addEventListener("click", async () => {
      haptic();
      await loadChild(Number(c.dataset.link));
      selectTab(activeTab);
    });
  });
}

function renderParentChild() {
  const c = state.child;

  const paid = (c.payments || []).filter((p) => p.status === "tasdiqlandi").length;

  const node = el(
    "<div>" + childSwitcher() +
    '<div class="profile">' +
      '<div class="ava">' + esc(initials(c.student)) + "</div>" +
      "<h2>" + esc(c.student) + "</h2>" +
      '<div class="pill-row">' +
        '<span class="pill-out strong">' + esc(c.class_name || "—") + "</span>" +
        '<span class="pill-out">' + esc(c.department || "—") + "</span>" +
      "</div>" +
    "</div>" +

    '<div class="stats">' +
      '<div class="stat"><div class="stat-label">Darslar</div>' +
        '<div class="stat-value">' + (c.schedule || []).length + ' <small>/hafta</small></div></div>' +
      '<div class="stat live"><div class="stat-label">To\'langan</div>' +
        '<div class="stat-value">' + paid + " <small>oy</small></div></div>" +
      '<div class="stat accent"><div class="stat-label">Oylik</div>' +
        '<div class="stat-value">' +
          (c.privileged ? "Imtiyozli" : shortMoney(c.monthly_fee)) + "</div></div>" +
    "</div>" +

    '<div class="sec"><h3>Ma\'lumot</h3><span class="rule"></span></div>' +
    '<div class="row"><div class="row-ava">' + esc(initials(c.teacher)) + "</div>" +
      '<div class="row-main"><div class="row-title">' + esc(c.teacher) + "</div>" +
      '<div class="row-sub">Mutaxassislik o\'qituvchisi</div></div></div>' +
    "</div>"
  );

  wireSwitcher(node);
  setPane(node);
}

function renderParentSchedule() {
  const c = state.child;
  const list = c.schedule || [];

  let html = "<div>" + childSwitcher() +
    '<div class="sec"><h3>Haftalik jadval</h3><span class="rule"></span></div>';

  if (!list.length) {
    html += '<div class="empty">Hali dars jadvali kiritilmagan</div>';
  } else {
    html += list.map(slotCardHtml).join("");
  }

  const node = el(html + "</div>");
  wireSwitcher(node);
  setPane(node);
}

// 1 kishilik / guruhli mashg'ulot belgisi
function typeIcon(t) { return t === "guruh" ? "👥" : "👤"; }

// darsga biriktirilgan jo'rnavozlar satri
function cmLine(list) {
  if (!list || !list.length) return "";
  return '<div class="lc-sub">🎹 ' + esc(list.join(", ")) + "</div>";
}

function slotCardHtml(s) {
  const isToday = s.day === TODAY;
  return '<div class="slot-card' + (isToday ? " today" : "") + '">' +
    '<div class="lc-top">' +
      '<span class="lc-day">' + esc(s.day) +
        (isToday ? '<span class="tag-today">BUGUN</span>' : "") + "</span>" +
      '<span class="lc-time">' + esc(s.time) + "</span>" +
    "</div>" +
    '<div class="lc-title">' + esc(s.subject) + "</div>" +
    '<div class="lc-sub">' + esc(s.room) + "-xona · " + esc(s.teacher) + "</div>" +
    cmLine(s.concertmasters) +
  "</div>";
}

function renderParentPayments() {
  const c = state.child;
  const list = c.payments || [];

  const STATUS = {
    tasdiqlandi: ["To'landi", "ok"],
    kutilmoqda:  ["Kutilmoqda", "pending"],
    rad_etildi:  ["Rad etildi", "bad"]
  };

  let html = "<div>" + childSwitcher() +
    '<div class="sec"><h3>To\'lov tarixi</h3><span class="rule"></span></div>';

  if (!list.length) {
    html += '<div class="empty">Hali to\'lov tarixi yo\'q</div>';
  } else {
    html += list.slice(0, 14).map((p) => {
      const st = STATUS[p.status] || [p.status, "dim"];
      return '<div class="row"><div class="row-main">' +
        '<div class="row-title">' + esc(monthName(p.month)) + "</div>" +
        '<div class="row-sub">' + money(p.amount) + " so'm</div></div>" +
        '<span class="pill ' + st[1] + '">' + esc(st[0]) + "</span></div>";
    }).join("");
  }

  const node = el(html + "</div>");
  wireSwitcher(node);
  setPane(node);
}


// ==========================================================
// O'QITUVCHI
// ==========================================================

async function initTeacher() {
  state.teacher = await api("/api/teacher/me");

  setHead(initials(state.teacher.teacher), state.teacher.teacher, state.teacher.department);

  buildNav([
    { id: "t-slots",    label: "Jadvalim",    icon: ICON.calendar, render: renderTeacherSlots },
    { id: "t-students", label: "O'quvchilar", icon: ICON.users,    render: renderTeacherStudents }
  ]);

  showApp();
}

async function renderTeacherSlots() {
  const data = await api("/api/teacher/slots");

  const today = data.slots.filter((s) => s.day === TODAY).length;
  const total = data.slots.reduce((a, s) => a + s.student_count, 0);

  let html =
    '<div class="stats">' +
      '<div class="stat"><div class="stat-label">Dars vaqti</div>' +
        '<div class="stat-value">' + data.slots.length + "</div></div>" +
      '<div class="stat accent"><div class="stat-label">Bugun</div>' +
        '<div class="stat-value">' + today + "</div></div>" +
      '<div class="stat live"><div class="stat-label">O\'quvchi</div>' +
        '<div class="stat-value">' + total + "</div></div>" +
    "</div>" +
    '<div class="sec"><h3>Haftalik jadval</h3><span class="rule"></span></div>';

  if (!data.slots.length) {
    html += '<div class="empty">Hali dars vaqti kiritilmagan.<br>Pastdagi ＋ tugmasi orqali qo\'shing.</div>';
  } else {
    html += data.slots.map((s) => {
      const isToday = s.day === TODAY;
      return '<div class="slot-card tappable' + (isToday ? " today" : "") +
        '" data-slot="' + s.id + '">' +
        '<div class="lc-top"><span class="lc-day">' + esc(s.day) +
          (isToday ? '<span class="tag-today">BUGUN</span>' : "") + "</span>" +
          '<span class="lc-time">' + esc(s.time) + "</span></div>" +
        '<div class="lc-title">' + typeIcon(s.lesson_type) + " " + esc(s.subject) + "</div>" +
        '<div class="lc-sub">' + esc(s.room) + "-xona · " + s.student_count + " ta o'quvchi</div>" +
        cmLine(s.concertmasters) +
      "</div>";
    }).join("");
  }

  // jo'rnavozlik - o'qituvchi o'zi biriktirilgan darslar

  const cm = await api("/api/teacher/concertmaster");

  html += '<div class="sec"><h3>🎹 Jo\'rnavozligim</h3><span class="rule"></span></div>';

  html += cm.slots.length
    ? cm.slots.map((s) =>
        '<div class="row"><div class="row-main">' +
        '<div class="row-title">' + esc(s.day) + " " + esc(s.time) + " · " + esc(s.subject) + "</div>" +
        '<div class="row-sub">' + esc(s.owner) + " · " + esc(s.room) + "-xona</div></div>" +
        '<button class="back" data-leave="' + s.id + '" style="color:var(--bad)">✕</button></div>'
      ).join("")
    : '<div class="empty" style="padding:18px">Hech qaysi darsga biriktirilmagansiz</div>';

  html += '<button class="btn ghost" id="cm-join" style="margin-top:12px">' +
    "＋ Darsga jo\'rnavoz bo\'lib biriktirilish</button>";

  const node = el("<div>" + html + "</div>");

  node.querySelectorAll("[data-slot]").forEach((c) => {
    c.addEventListener("click", () => { haptic(); openSlotSheet(Number(c.dataset.slot)); });
  });

  node.querySelectorAll("[data-leave]").forEach((b) => {
    b.addEventListener("click", async () => {
      haptic("medium");
      await api("/api/teacher/concertmaster", "DELETE", { slot_id: Number(b.dataset.leave) });
      renderTeacherSlots();
    });
  });

  node.querySelector("#cm-join").addEventListener("click", () => {
    haptic();
    openJoinConcertmasterSheet();
  });

  setPane(node);
  mountFab(openNewSlotSheet);
}

// Jo'rnavozning o'zi tanlaydi: o'qituvchini qidiradi ->
// uning dars vaqtlarini ko'radi -> keraklisiga biriktiriladi.

function openJoinConcertmasterSheet() {
  const body = el(
    "<div>" +
      "<h3>Jo\'rnavozlik</h3>" +
      '<p class="sheet-sub">Dars egasini qidiring, so\'ng dars vaqtini tanlang</p>' +
      '<input class="input" id="jc-search" placeholder="O\'qituvchi ism-familiyasi...">' +
      "<div id='jc-results' style='margin-top:12px'></div>" +
    "</div>"
  );

  const box = body.querySelector("#jc-results");

  async function showSlots(name) {
    const d = await api("/api/teacher/teacher_slots?teacher=" + encodeURIComponent(name));
    box.innerHTML = '<div class="sec"><h3>' + esc(name) + "</h3><span class=\"rule\"></span></div>" +
      (d.slots.length
        ? d.slots.map((s) =>
            '<div class="row tappable" data-join="' + s.id + '">' +
            '<div class="row-main"><div class="row-title">' +
              typeIcon(s.lesson_type) + " " + esc(s.day) + " " + esc(s.time) + " · " + esc(s.subject) + "</div>" +
            '<div class="row-sub">' + esc(s.room) + "-xona</div></div>" +
            '<span class="pill ' + (s.joined ? "ok" : "") + '">' +
              (s.joined ? "\u2713" : "+") + "</span></div>").join("")
        : '<div class="empty" style="padding:18px">Bu o\'qituvchi hali dars vaqti kiritmagan</div>');

    box.querySelectorAll("[data-join]").forEach((n) => {
      n.addEventListener("click", async () => {
        try {
          haptic("medium");
          await api("/api/teacher/concertmaster", "POST", { slot_id: Number(n.dataset.join) });
          closeSheet();
          renderTeacherSlots();
        } catch (e) { notify(e.message); }
      });
    });
  }

  let timer = null;

  body.querySelector("#jc-search").addEventListener("input", (e) => {
    clearTimeout(timer);
    const q = e.target.value.trim();
    if (q.length < 3) { box.innerHTML = ""; return; }
    timer = setTimeout(async () => {
      const r = await api("/api/teacher/search_teachers?q=" + encodeURIComponent(q));
      box.innerHTML = r.teachers.length
        ? r.teachers.map((x) =>
            '<div class="row tappable" data-owner="' + esc(x.name) + '">' +
            '<div class="row-main"><div class="row-title">' + esc(x.name) + "</div>" +
            '<div class="row-sub">' + esc(x.department) + "</div></div>" +
            '<span class="pill">›</span></div>').join("")
        : '<div class="empty" style="padding:14px">Topilmadi</div>';
      box.querySelectorAll("[data-owner]").forEach((n) => {
        n.addEventListener("click", () => { haptic(); showSlots(n.dataset.owner); });
      });
    }, 300);
  });

  openSheet(body);
}

async function renderTeacherStudents() {
  removeFab();

  const data = await api("/api/teacher/students");

  const paid = data.students.filter((s) => s.paid).length;
  const debt = data.students.filter((s) => !s.paid).reduce((a, s) => a + (s.fee || 0), 0);
  const free = data.students.filter((s) => s.privileged).length;

  let html =
    '<div class="stats">' +
      '<div class="stat"><div class="stat-label">Jami</div>' +
        '<div class="stat-value">' + data.students.length + "</div></div>" +
      '<div class="stat live"><div class="stat-label">To\'lagan</div>' +
        '<div class="stat-value">' + paid + "</div></div>" +
      '<div class="stat bad"><div class="stat-label">Qarz</div>' +
        '<div class="stat-value">' + shortMoney(debt) + "</div></div>" +
    "</div>" +
    (free ? '<div class="sheet-sub" style="margin-top:10px">🎖 ' + free +
       " ta imtiyozli o'quvchi (badal to'lamaydi)</div>" : "") +
    '<div class="sec"><h3>' + esc(monthName(data.month)) + '</h3><span class="rule"></span></div>';

  if (!data.students.length) {
    html += '<div class="empty">Hali o\'quvchi yo\'q</div>';
  } else {
    html += data.students.map((s) =>
      '<div class="row"><div class="row-ava">' + esc(initials(s.student)) + "</div>" +
      '<div class="row-main"><div class="row-title">' + esc(s.student) + "</div>" +
      '<div class="row-sub">' + (s.privileged
          ? "🎖 Imtiyozli — badal to'lamaydi"
          : (s.fee ? money(s.fee) + " so'm / oy" : "badal kiritilmagan")) + "</div></div>" +
      '<span class="pill ' + (s.privileged || s.paid ? "ok" : "pending") + '">' +
        (s.privileged ? "Imtiyozli" : (s.paid ? "To'landi" : "Kutilmoqda")) + "</span></div>"
    ).join("");
  }

  setPane(el("<div>" + html + "</div>"));
}

// ---- O'qituvchi: vaqt tafsiloti ----

async function openSlotSheet(slotId) {
  const d = await api("/api/teacher/slots/" + slotId);

  const students = d.students.length
    ? d.students.map((s) =>
        '<div class="row" style="margin-bottom:8px"><div class="row-main">' +
        '<div class="row-title">' + esc(s.student) + "</div>" +
        '<div class="row-sub">' + esc(s.teacher) + "</div></div>" +
        '<button class="back" data-rm="' + s.row_id + '" style="color:var(--bad)">✕</button></div>'
      ).join("")
    : '<div class="empty" style="padding:18px">Hali o\'quvchi qo\'shilmagan</div>';

  const cms = d.concertmasters || [];

  const cmHtml = cms.length
    ? cms.map((n) =>
        '<div class="row" style="margin-bottom:8px"><div class="row-main">' +
        '<div class="row-title">🎹 ' + esc(n) + "</div></div>" +
        '<button class="back" data-rmcm="' + esc(n) + '" style="color:var(--bad)">✕</button></div>'
      ).join("")
    : '<div class="empty" style="padding:14px">Jo\'rnavoz biriktirilmagan</div>';

  const body = el(
    "<div>" +
      "<h3>" + typeIcon(d.lesson_type) + " " + esc(d.subject) + "</h3>" +
      '<p class="sheet-sub">' + esc(d.day) + " · " + esc(d.time) + " · " + esc(d.room) + "-xona · " +
        (d.lesson_type === "guruh" ? "guruhli" : "yakka tartibdagi") + " mashg\'ulot</p>" +
      '<div class="sec"><h3>Jo\'rnavozlar</h3><span class="rule"></span></div>' +
      "<div id='sl-cms'>" + cmHtml + "</div>" +
      '<p class="sheet-sub">Jo\'rnavozlar bu darsga o\'zlari biriktiriladi. ' +
        "Keraksizini shu yerdan olib tashlashingiz mumkin.</p>" +
      '<div class="sec"><h3>O\'quvchilar</h3><span class="rule"></span></div>' +
      "<div id='sl-students'>" + students + "</div>" +
      '<label class="label">O\'quvchi qo\'shish</label>' +
      '<input class="input" id="sl-search" placeholder="Ism-familiyani yozing...">' +
      "<div id='sl-results' style='margin-top:9px'></div>" +
      '<button class="btn danger" id="sl-del">Bu dars vaqtini o\'chirish</button>' +
    "</div>"
  );

  body.querySelectorAll("[data-rm]").forEach((b) => {
    b.addEventListener("click", async () => {
      haptic("medium");
      await api("/api/teacher/slot_students/" + b.dataset.rm, "DELETE");
      openSlotSheet(slotId);
      renderTeacherSlots();
    });
  });

  body.querySelectorAll("[data-rmcm]").forEach((b) => {
    b.addEventListener("click", async () => {
      haptic("medium");
      await api("/api/teacher/slots/" + slotId + "/concertmasters", "DELETE",
        { teacher: b.dataset.rmcm });
      openSlotSheet(slotId);
      renderTeacherSlots();
    });
  });


  let timer = null;

  body.querySelector("#sl-search").addEventListener("input", (e) => {
    clearTimeout(timer);
    const q = e.target.value.trim();
    const box = body.querySelector("#sl-results");

    if (q.length < 2) { box.innerHTML = ""; return; }

    timer = setTimeout(async () => {
      const r = await api("/api/teacher/search_students?q=" + encodeURIComponent(q));

      if (!r.results.length) {
        box.innerHTML = '<div class="empty" style="padding:14px">Topilmadi</div>';
        return;
      }

      box.innerHTML = r.results.map((x, i) =>
        '<div class="row tappable" data-i="' + i + '" style="margin-bottom:8px">' +
        '<div class="row-main"><div class="row-title">' + esc(x.student) + "</div>" +
        '<div class="row-sub">' + esc(x.teacher) + '</div></div>' +
        '<span class="pill dim">＋</span></div>'
      ).join("");

      box.querySelectorAll("[data-i]").forEach((rowEl) => {
        rowEl.addEventListener("click", async () => {
          haptic();
          await api("/api/teacher/slots/" + slotId + "/students", "POST",
                    r.results[Number(rowEl.dataset.i)]);
          openSlotSheet(slotId);
          renderTeacherSlots();
        });
      });
    }, 300);
  });

  body.querySelector("#sl-del").addEventListener("click", async () => {
    haptic("medium");
    await api("/api/teacher/slots/" + slotId, "DELETE");
    closeSheet();
    renderTeacherSlots();
  });

  openSheet(body);
}

// O'qituvchi o'z yo'nalishidagi fanni qo'shadi -
// masalan Tasviriy san'atda "Rang tasvir", "Qalam tasvir".
// Mashg'ulot turi keyin dars jadvalida ko'rsatiladi.

// O'zi qo'shgan fanlar ro'yxati - nomini, mashg'ulot turini
// o'zgartirish yoki fanni o'chirish.

async function openSubjectsSheet() {
  const d = await api("/api/teacher/subjects");

  const body = el(
    "<div>" +
      "<h3>Fanlarim</h3>" +
      '<p class="sheet-sub">Umumiy fanlardan tashqari o\'zingiz qo\'shganlari</p>' +
      (d.subjects.length
        ? d.subjects.map((s) =>
            '<div class="row tappable" data-subj="' + s.id + '">' +
            '<div class="row-main"><div class="row-title">' +
              typeIcon(s.lesson_type) + " " + esc(s.name) + "</div>" +
            '<div class="row-sub">' +
              (s.lesson_type === "guruh" ? "guruhli" : "yakka tartibdagi") +
              " · " + s.used + " ta dars vaqti</div></div>" +
            '<span class="pill">›</span></div>').join("")
        : '<div class="empty" style="padding:18px">Hali fan qo\'shmagansiz</div>') +
      '<button class="btn" id="sj-new" style="margin-top:16px">＋ Yangi fan</button>' +
    "</div>"
  );

  body.querySelectorAll("[data-subj]").forEach((n) => {
    n.addEventListener("click", () => {
      haptic();
      const s = d.subjects.find((x) => x.id === Number(n.dataset.subj));
      openEditSubjectSheet(s);
    });
  });

  body.querySelector("#sj-new").addEventListener("click", () => {
    haptic();
    openNewSubjectSheet();
  });

  openSheet(body);
}


function openEditSubjectSheet(s) {
  const body = el(
    "<div>" +
      "<h3>Fanni tahrirlash</h3>" +
      (s.used
        ? '<p class="sheet-sub">Nomini o\'zgartirsangiz, shu fandagi ' + s.used +
            " ta dars vaqti ham yangilanadi</p>"
        : '<p class="sheet-sub">Bu fan bo\'yicha hali dars vaqti tuzilmagan</p>') +
      '<label class="label">Fan nomi</label>' +
      '<input class="input" id="es-name" value="' + esc(s.name) + '">' +
      '<label class="label">Mashg\'ulot turi</label>' +
      '<select class="select" id="es-type">' +
        '<option value="yakka"' + (s.lesson_type === "yakka" ? " selected" : "") +
          '>👤 Yakka tartibdagi</option>' +
        '<option value="guruh"' + (s.lesson_type === "guruh" ? " selected" : "") +
          '>👥 Guruhli</option></select>' +
      '<button class="btn" id="es-save" style="margin-top:20px">Saqlash</button>' +
      '<button class="btn danger" id="es-del">Fanni o\'chirish</button>' +
    "</div>"
  );

  body.querySelector("#es-save").addEventListener("click", async () => {
    try {
      haptic("medium");
      await api("/api/teacher/subjects/" + s.id, "PATCH", {
        name: body.querySelector("#es-name").value.trim(),
        lesson_type: body.querySelector("#es-type").value
      });
      state.teacher = await api("/api/teacher/me");
      closeSheet();
      openSubjectsSheet();
    } catch (e) { notify(e.message); }
  });

  body.querySelector("#es-del").addEventListener("click", async () => {
    try {
      haptic("medium");
      await api("/api/teacher/subjects/" + s.id, "DELETE");
      state.teacher = await api("/api/teacher/me");
      closeSheet();
      openSubjectsSheet();
    } catch (e) { notify(e.message); }
  });

  openSheet(body);
}


function openNewSubjectSheet() {
  const body = el(
    "<div>" +
      "<h3>Yangi fan</h3>" +
      '<p class="sheet-sub">Faqat sizning ro\'yxatingizga qo\'shiladi</p>' +
      '<label class="label">Fan nomi</label>' +
      '<input class="input" id="nsj-name" placeholder="Masalan: Rang tasvir">' +
      '<label class="label">Mashg\'ulot turi</label>' +
      '<select class="select" id="nsj-type">' +
        '<option value="yakka">👤 Yakka tartibdagi</option>' +
        '<option value="guruh">👥 Guruhli</option></select>' +
      '<button class="btn" id="nsj-save" style="margin-top:20px">Saqlash</button>' +
    "</div>"
  );

  body.querySelector("#nsj-save").addEventListener("click", async () => {
    const name = body.querySelector("#nsj-name").value.trim();
    if (name.length < 2) { notify("Fan nomini kiriting"); return; }
    try {
      haptic("medium");
      await api("/api/teacher/subjects", "POST",
        { name: name, lesson_type: body.querySelector("#nsj-type").value });
      state.teacher = await api("/api/teacher/me");
      closeSheet();
      openSubjectsSheet();
    } catch (e) { notify(e.message); }
  });

  openSheet(body);
}

function openNewSlotSheet() {
  const t = state.teacher;

  const body = el(
    "<div>" +
      "<h3>Yangi dars vaqti</h3>" +
      '<p class="sheet-sub">Kun, soat va xonani belgilang</p>' +
      '<label class="label">Fan</label>' +
      '<select class="select" id="ns-subject">' +
        t.subjects.map((s) => '<option value="' + esc(s) + '">' +
          typeIcon((t.subject_types || {})[s]) + " " + esc(s) + "</option>").join("") + "</select>" +
      '<button class="btn ghost" id="ns-newsubj" style="margin-top:10px">' +
        "📚 Fanlarim</button>" +
      '<label class="label">Hafta kuni</label>' +
      '<select class="select" id="ns-day">' +
        t.days.map((d) => "<option>" + esc(d) + "</option>").join("") + "</select>" +
      '<div class="grid-2">' +
        "<div><label class='label'>Soat</label>" +
          '<input class="input" id="ns-time" placeholder="15:00"></div>' +
        "<div><label class='label'>Xona</label>" +
          '<input class="input" id="ns-room" placeholder="12"></div>' +
      "</div>" +
      '<button class="btn" id="ns-save" style="margin-top:20px">Saqlash</button>' +
    "</div>"
  );

  body.querySelector("#ns-newsubj").addEventListener("click", () => {
    haptic();
    openSubjectsSheet();
  });

  body.querySelector("#ns-save").addEventListener("click", async () => {
    const payload = {
      subject: body.querySelector("#ns-subject").value,
      day:     body.querySelector("#ns-day").value,
      time:    body.querySelector("#ns-time").value.trim(),
      room:    body.querySelector("#ns-room").value.trim()
    };

    if (!payload.time || !payload.room) { notify("Soat va xonani kiriting"); return; }

    try {
      haptic("medium");
      await api("/api/teacher/slots", "POST", payload);
      closeSheet();
      renderTeacherSlots();
    } catch (e) { notify(e.message); }
  });

  openSheet(body);
}

// ---- FAB ----

function mountFab(onClick) {
  removeFab();
  const b = el('<button class="fab" id="fab">＋</button>');
  b.addEventListener("click", () => { haptic("medium"); onClick(); });
  document.body.appendChild(b);
}

function removeFab() {
  const f = $("fab");
  if (f) f.remove();
}


// ==========================================================
// DIREKTOR / ADMIN
// ==========================================================

function initAdmin(who) {
  setHead("🏫", who.staff === "direktor" ? "Direktor paneli" : "Boshqaruv paneli",
          TODAY + " · 19-son musiqa maktabi");

  buildNav([
    { id: "a-live",   label: "Hozir",     icon: ICON.clock,    render: renderLive },
    { id: "a-sched",  label: "Jadvallar", icon: ICON.calendar, render: renderDepts },
    { id: "a-report", label: "Hisobot",   icon: ICON.chart,    render: renderReport },
    { id: "a-search", label: "Qidiruv",   icon: ICON.search,   render: renderSearch }
  ]);

  showApp();
}

function initStaff(who) {
  const names = { buxgalter: "Buxgalter", yordamchi: "Yordamchi" };
  setHead("👤", names[who.staff] || "Panel", "19-son musiqa maktabi");
  $("nav").classList.add("hidden");
  $("loading").classList.add("hidden");
  $("app").classList.remove("hidden");
  setPane(el('<div class="empty">Sizning rolingiz uchun Mini App hali tayyor emas.<br>' +
             "Botdagi tugmalardan foydalaning.</div>"));
}

async function renderLive() {
  removeFab();

  const d = await api("/api/admin/live");
  const r = await api("/api/admin/report").catch(() => null);

  let html =
    '<div class="stats">' +
      '<div class="stat live"><div class="stat-label">Hozir dars</div>' +
        '<div class="stat-value">' + d.live.length + " <small>xona</small></div></div>" +
      '<div class="stat bad"><div class="stat-label">Qarzdor</div>' +
        '<div class="stat-value">' + (r ? r.total_unpaid : "—") + "</div></div>" +
      '<div class="stat accent"><div class="stat-label">Jami qarz</div>' +
        '<div class="stat-value">' + (r ? shortMoney(r.total_debt) : "—") + "</div></div>" +
    "</div>" +
    '<div class="sec"><span class="dot-live"></span>' +
      "<h3>" + esc(d.day) + " · " + esc(d.now) + '</h3><span class="rule"></span></div>';

  if (!d.live.length) {
    html += '<div class="empty">Hozir dars ketayotgan xona yo\'q</div>';
  } else {
    html += d.live.map((l) =>
      '<div class="live-card">' +
        '<div class="lc-top"><span class="lc-room">' + esc(l.room) + "-xona</span>" +
        '<span class="lc-time">' + esc(l.time) + "</span></div>" +
        '<div class="lc-sub">' + esc(l.subject) + " · " + esc(l.teacher) + "</div>" +
        (l.students.length
          ? '<div class="chips">' + l.students.map((s) => '<span class="chip">' + esc(s) + "</span>").join("") + "</div>"
          : "") +
      "</div>"
    ).join("");
  }

  setPane(el("<div>" + html + "</div>"));
}

// ---- Jadvallar: bo'lim → o'qituvchi → vaqtlar ----

async function renderDepts() {
  removeFab();

  const d = await api("/api/admin/departments");

  const node = el("<div>" +
    '<div class="sec"><h3>Bo\'limlar</h3><span class="rule"></span></div>' +
    d.departments.map((x, i) =>
      '<div class="row tappable" data-d="' + i + '">' +
      '<div class="row-main"><div class="row-title">' + esc(x) + "</div></div>" +
      '<span class="chevron">›</span></div>'
    ).join("") + "</div>");

  node.querySelectorAll("[data-d]").forEach((r) => {
    r.addEventListener("click", () => {
      haptic();
      openTeachers(d.departments[Number(r.dataset.d)]);
    });
  });

  setPane(node);
}

async function openTeachers(dept) {
  const d = await api("/api/admin/teachers?dept=" + encodeURIComponent(dept));

  let html =
    '<div class="subhead"><button class="back" id="bk">‹</button>' +
    '<div class="subhead-text"><h2>' + esc(dept) + "</h2>" +
    "<p>" + d.teachers.length + " ta o'qituvchi</p></div></div>";

  html += d.teachers.length
    ? d.teachers.map((t, i) =>
        '<div class="row tappable" data-t="' + i + '">' +
        '<div class="row-ava">' + esc(initials(t.name)) + "</div>" +
        '<div class="row-main"><div class="row-title">' + esc(t.name) + "</div>" +
        (t.status === "approved" ? '<div class="row-sub">ro\'yxatdan o\'tgan</div>' : "") +
        '</div><span class="chevron">›</span></div>'
      ).join("")
    : '<div class="empty">Bu bo\'limda o\'qituvchi yo\'q</div>';

  const node = el("<div>" + html + "</div>");

  node.querySelector("#bk").addEventListener("click", () => { haptic(); renderDepts(); });

  node.querySelectorAll("[data-t]").forEach((r) => {
    r.addEventListener("click", () => {
      haptic();
      const t = d.teachers[Number(r.dataset.t)];
      openTeacherSlots(t.id, t.name, dept);
    });
  });

  setPane(node);
}

async function openTeacherSlots(id, name, dept) {
  const d = await api("/api/admin/teacher/" + id + "/slots");

  let html =
    '<div class="subhead"><button class="back" id="bk">‹</button>' +
    '<div class="subhead-text"><h2>' + esc(name) + "</h2>" +
    "<p>" + esc(dept) + "</p></div></div>";

  html += d.slots.length
    ? d.slots.map((s) => {
        const isToday = s.day === TODAY;
        return '<div class="slot-card tappable' + (isToday ? " today" : "") +
          '" data-s="' + s.id + '">' +
          '<div class="lc-top"><span class="lc-day">' + esc(s.day) +
            (isToday ? '<span class="tag-today">BUGUN</span>' : "") + "</span>" +
            '<span class="lc-time">' + esc(s.time) + "</span></div>" +
          '<div class="lc-title">' + esc(s.subject) + "</div>" +
          '<div class="lc-sub">' + esc(s.room) + "-xona · " + s.student_count + " ta o'quvchi</div>" +
        "</div>";
      }).join("")
    : '<div class="empty">Hali dars vaqti kiritilmagan</div>';

  const node = el("<div>" + html + "</div>");

  node.querySelector("#bk").addEventListener("click", () => { haptic(); openTeachers(dept); });

  node.querySelectorAll("[data-s]").forEach((c) => {
    c.addEventListener("click", async () => {
      haptic();
      const s = await api("/api/admin/slot/" + c.dataset.s);
      openSheet(
        "<div><h3>" + typeIcon(s.lesson_type) + " " + esc(s.subject) + "</h3>" +
        '<p class="sheet-sub">' + esc(s.day) + " · " + esc(s.time) + " · " +
          esc(s.room) + "-xona · " + esc(s.teacher) + "</p>" +
        ((s.concertmasters || []).length
          ? '<p class="sheet-sub">🎹 ' + esc(s.concertmasters.join(", ")) + "</p>" : "") +
        '<div class="sec"><h3>O\'quvchilar</h3><span class="rule"></span></div>' +
        (s.students.length
          ? s.students.map((x) =>
              '<div class="row" style="margin-bottom:8px"><div class="row-main">' +
              '<div class="row-title">' + esc(x.student) + "</div>" +
              '<div class="row-sub">' + esc(x.teacher) + "</div></div></div>").join("")
          : '<div class="empty" style="padding:18px">O\'quvchi biriktirilmagan</div>') +
        "</div>"
      );
    });
  });

  setPane(node);
}

// ---- Hisobot ----

async function renderReport() {
  removeFab();

  const d = await api("/api/admin/report");

  let html =
    '<div class="stats">' +
      '<div class="stat bad"><div class="stat-label">Jami qarz</div>' +
        '<div class="stat-value">' + shortMoney(d.total_debt) + "</div></div>" +
      '<div class="stat"><div class="stat-label">Qarzdor</div>' +
        '<div class="stat-value">' + d.total_unpaid + "</div></div>" +
      '<div class="stat accent"><div class="stat-label">O\'qituvchi</div>' +
        '<div class="stat-value">' + d.teachers.length + "</div></div>" +
    "</div>" +
    '<div class="sec"><h3>' + esc(monthName(d.month)) + '</h3><span class="rule"></span></div>';

  html += d.teachers.length
    ? d.teachers.map((t, i) =>
        '<div class="row tappable" data-r="' + i + '">' +
        '<div class="row-ava">' + esc(initials(t.teacher)) + "</div>" +
        '<div class="row-main"><div class="row-title">' + esc(t.teacher) + "</div>" +
        '<div class="row-sub">' + esc(t.department) + " · " + t.unpaid + "/" + t.total + " qarzdor</div></div>" +
        '<div class="row-right"><div class="amount ' + (t.debt > 0 ? "bad" : "ok") + '">' +
          money(t.debt) + "</div></div></div>"
      ).join("")
    : '<div class="empty">Ma\'lumot yo\'q</div>';

  const node = el("<div>" + html + "</div>");

  node.querySelectorAll("[data-r]").forEach((r) => {
    r.addEventListener("click", () => {
      haptic();
      const t = d.teachers[Number(r.dataset.r)];
      openSheet(
        "<div><h3>" + esc(t.teacher) + "</h3>" +
        '<p class="sheet-sub">' + esc(t.department) + " · " + esc(monthName(d.month)) + "</p>" +
        '<div class="kv"><span>Jami o\'quvchi</span><span>' + t.total + " ta</span></div>" +
        '<div class="kv"><span>To\'lagan</span><span style="color:var(--live)">' +
          (t.total - t.unpaid) + " ta</span></div>" +
        '<div class="kv"><span>Qarzdor</span><span style="color:var(--bad)">' + t.unpaid + " ta</span></div>" +
        '<div class="kv"><span>Jami qarz</span><span>' + money(t.debt) + " so'm</span></div></div>"
      );
    });
  });

  setPane(node);
}

// ---- Qidiruv ----

function renderSearch() {
  removeFab();

  const node = el("<div>" +
    '<label class="label">O\'quvchi yoki o\'qituvchi</label>' +
    '<input class="input" id="q" placeholder="Ism-familiyani yozing..." autocomplete="off">' +
    '<div id="q-res" style="margin-top:16px"></div></div>');

  let timer = null;

  node.querySelector("#q").addEventListener("input", (e) => {
    clearTimeout(timer);
    const q = e.target.value.trim();
    const box = node.querySelector("#q-res");

    if (q.length < 2) { box.innerHTML = ""; return; }

    timer = setTimeout(async () => {
      const d = await api("/api/admin/search?q=" + encodeURIComponent(q));

      let out = "";

      if (d.teachers.length) {
        out += '<div class="sec"><h3>O\'qituvchilar</h3><span class="rule"></span></div>' +
          d.teachers.map((t) =>
            '<div class="row"><div class="row-ava">' + esc(initials(t.name)) + "</div>" +
            '<div class="row-main"><div class="row-title">' + esc(t.name) + "</div>" +
            '<div class="row-sub">' + esc(t.department) + "</div></div></div>"
          ).join("");
      }

      if (d.students.length) {
        out += '<div class="sec"><h3>O\'quvchilar</h3><span class="rule"></span></div>' +
          d.students.map((s) =>
            '<div class="row"><div class="row-ava">' + esc(initials(s.student)) + "</div>" +
            '<div class="row-main"><div class="row-title">' + esc(s.student) + "</div>" +
            '<div class="row-sub">' + esc(s.teacher) + "</div></div></div>"
          ).join("");
      }

      box.innerHTML = out || '<div class="empty">Topilmadi</div>';
    }, 300);
  });

  setPane(node);
}


init();
