(function () {
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

  // 3) Copy button
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
})();
