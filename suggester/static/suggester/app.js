(function () {
  var KEY = "naamastro.shortlist";

  // ---- localStorage safe wrappers (these can throw in private mode) ----
  function load() {
    try { return JSON.parse(localStorage.getItem(KEY)) || []; } catch (e) { return []; }
  }
  function save(list) {
    try { localStorage.setItem(KEY, JSON.stringify(list)); } catch (e) { /* ignore */ }
  }

  // 1) Form submit: disable the button and show a progress bar (the search takes a few seconds)
  var form = document.getElementById("search-form");
  if (form) {
    form.addEventListener("submit", function () {
      var btn = form.querySelector("button[type=submit]");
      var panel = form.closest(".panel");
      if (panel) panel.classList.add("is-loading");
      if (btn) {
        btn.disabled = true;
        btn.textContent = "Checking domains...";
      }
    });
  }

  // 2) Result: show only names whose primary (.com) domain is free
  var toggle = document.getElementById("only-available");
  var rows = document.querySelectorAll("[data-primary]");
  var countEl = document.getElementById("shown-count");
  if (toggle && rows.length) {
    toggle.addEventListener("change", function () {
      var shown = 0;
      rows.forEach(function (row) {
        var hide = toggle.checked && row.dataset.primary !== "available";
        row.hidden = hide;
        if (!hide) shown++;
      });
      if (countEl) countEl.textContent = shown;
    });
  }

  // 3) Copy buttons (name and share link)
  document.querySelectorAll("[data-copy]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var text = btn.getAttribute("data-copy");
      var done = function () {
        var old = btn.textContent;
        btn.textContent = "Copied";
        btn.classList.add("done");
        setTimeout(function () { btn.textContent = old; btn.classList.remove("done"); }, 1600);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done);
      }
    });
  });

  // 4) Print / PDF save
  document.querySelectorAll("[data-print]").forEach(function (btn) {
    btn.addEventListener("click", function () { window.print(); });
  });

  // 5) Shortlist (saved in this browser only)
  var panel = document.getElementById("shortlist");
  var listEl = document.getElementById("shortlist-list");

  function renderShortlist() {
    var items = load();
    if (!panel || !listEl) return;
    listEl.textContent = "";
    items.forEach(function (it) {
      var li = document.createElement("li");
      var ring = document.createElement("span");
      ring.className = "ring sm";
      ring.textContent = it.number;
      var box = document.createElement("div");
      var nm = document.createElement("strong");
      nm.textContent = it.name;
      var dm = document.createElement("span");
      dm.className = "small";
      dm.textContent = it.domain;
      box.appendChild(nm);
      box.appendChild(dm);
      var rm = document.createElement("button");
      rm.type = "button";
      rm.className = "copy";
      rm.textContent = "Remove";
      rm.addEventListener("click", function () { toggleFav(it); });
      li.appendChild(ring);
      li.appendChild(box);
      li.appendChild(rm);
      listEl.appendChild(li);
    });
    panel.hidden = items.length === 0;
    document.querySelectorAll("[data-fav]").forEach(function (b) {
      var on = items.some(function (it) { return it.name === b.dataset.name; });
      b.setAttribute("aria-pressed", on ? "true" : "false");
      b.innerHTML = on ? "&#9733;" : "&#9734;";
    });
  }

  function toggleFav(item) {
    var items = load();
    var idx = items.findIndex(function (it) { return it.name === item.name; });
    if (idx >= 0) items.splice(idx, 1); else items.push(item);
    save(items);
    renderShortlist();
  }

  document.querySelectorAll("[data-fav]").forEach(function (b) {
    b.addEventListener("click", function () {
      toggleFav({ name: b.dataset.name, domain: b.dataset.domain, number: b.dataset.number });
    });
  });
  // 6) Conflict check: on demand, one name at a time (keeps the main search fast)
  var RISK_LABELS = {
    high: "Possible well-known brand",
    medium: "Existing website found",
    low: "Similar domains registered",
    none: "No conflict signals found"
  };
  var CHECK_LABEL = "Check for existing businesses";

  function node(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text) n.textContent = text;
    return n;
  }
  function link(href, text) {
    var a = node("a", "", text);
    a.href = href;
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    return a;
  }
  function line(prefix, items) {
    var p = node("p", "", prefix + " ");
    items.forEach(function (a, i) {
      if (i) p.appendChild(document.createTextNode(", "));
      p.appendChild(a);
    });
    return p;
  }

  function showConflict(row, d) {
    var slot = row.querySelector(".risk-slot");
    var out = row.querySelector(".conflict-result");
    var btn = row.querySelector("[data-conflict]");
    slot.textContent = "";
    slot.appendChild(node("span", "risk risk-" + d.level, RISK_LABELS[d.level] || RISK_LABELS.none));
    out.textContent = "";
    if (d.wikipedia && /^https:\/\//.test(d.wikipedia.url)) {
      out.appendChild(line("Wikipedia has a page called", [link(d.wikipedia.url, d.wikipedia.title)]));
    }
    if (d.live_sites && d.live_sites.length) {
      out.appendChild(line("A website responds at", d.live_sites.map(function (x) { return link("https://" + x, x); })));
    }
    var quiet = (d.registered || []).filter(function (x) { return (d.live_sites || []).indexOf(x) < 0; });
    if (quiet.length) {
      out.appendChild(node("p", "", "Registered, but no website responded: " + quiet.join(", ")));
    }
    if (d.level === "none") {
      out.appendChild(node("p", "", "We found no existing website or Wikipedia page with this name."));
    }
    out.appendChild(node("p", "", "These are signals only, not proof. Always search trademarks too."));
    if (btn) { btn.textContent = "Checked"; btn.disabled = true; }
  }

  function runConflict(row) {
    var url = row.dataset.conflictUrl;
    var state = row.dataset.conflictState;
    if (!url || state === "done" || state === "loading") return Promise.resolve();
    row.dataset.conflictState = "loading";
    var btn = row.querySelector("[data-conflict]");
    var out = row.querySelector(".conflict-result");
    if (btn) { btn.disabled = true; btn.textContent = "Checking..."; }
    return fetch(url, { headers: { "Accept": "application/json" } })
      .then(function (r) { if (!r.ok) throw new Error("status " + r.status); return r.json(); })
      .then(function (d) { row.dataset.conflictState = "done"; showConflict(row, d); })
      .catch(function () {
        row.dataset.conflictState = "";
        var slot = row.querySelector(".risk-slot");
        if (slot) {
          slot.textContent = "";
          slot.appendChild(node("span", "risk risk-none", "Could not check. Open this row to retry."));
        }
        if (out) out.textContent = "Could not check right now. Try again.";
        if (btn) { btn.disabled = false; btn.textContent = CHECK_LABEL; }
      });
  }

  document.querySelectorAll("[data-conflict]").forEach(function (b) {
    b.addEventListener("click", function () { runConflict(b.closest("[data-conflict-url]")); });
  });

  var checkAll = document.getElementById("check-all");
  if (checkAll) {
    var ALL_LABEL = checkAll.textContent;
    checkAll.addEventListener("click", function () {
      var pending = Array.prototype.filter.call(
        document.querySelectorAll("[data-conflict-url]"),
        function (r) { return r.dataset.conflictState !== "done" && !r.hidden; }
      );
      var total = pending.length, finished = 0, i = 0;
      if (!total) return;
      checkAll.disabled = true;
      checkAll.textContent = "Checked 0 of " + total;
      function next() {
        if (i >= total) return Promise.resolve();
        return runConflict(pending[i++]).then(function () {
          finished++;
          checkAll.textContent = "Checked " + finished + " of " + total;
          return next();
        });
      }
      Promise.all([next(), next()]).then(function () {
        checkAll.disabled = false;
        checkAll.textContent = ALL_LABEL;
      });
    });
  }

  renderShortlist();
})();
