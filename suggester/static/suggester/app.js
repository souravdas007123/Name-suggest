(function () {
  var KEY = "naamastro.shortlist";

  // ---- localStorage safe wrappers (private mode mein error aa sakta hai) ----
  function load() {
    try { return JSON.parse(localStorage.getItem(KEY)) || []; } catch (e) { return []; }
  }
  function save(list) {
    try { localStorage.setItem(KEY, JSON.stringify(list)); } catch (e) { /* ignore */ }
  }

  // 1) Form submit: button disable + progress bar (search mein kuch seconds lagte hain)
  var form = document.getElementById("search-form");
  if (form) {
    form.addEventListener("submit", function () {
      var btn = form.querySelector("button[type=submit]");
      var panel = form.closest(".panel");
      if (panel) panel.classList.add("is-loading");
      if (btn) {
        btn.disabled = true;
        btn.textContent = "Domain check ho raha hai...";
      }
    });
  }

  // 2) Result: sirf wahi naam dikhao jinka primary (.com) domain khaali hai
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

  // 3) Copy buttons (naam aur share link)
  document.querySelectorAll("[data-copy]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var text = btn.getAttribute("data-copy");
      var done = function () {
        var old = btn.textContent;
        btn.textContent = "Copy ho gaya";
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

  // 5) Shortlist (sirf is browser mein save hoti hai)
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
      rm.textContent = "Hatayein";
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
  renderShortlist();
})();
