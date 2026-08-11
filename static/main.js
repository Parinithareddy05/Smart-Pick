// ── Theme toggle ────────────────────────────────────────────────────────────────
function applyTheme(dark) {
  if (dark) {
    document.body.classList.add("dark");
  } else {
    document.body.classList.remove("dark");
  }
  const btn = document.getElementById("theme-toggle");
  if (btn) {
    btn.querySelector(".icon").textContent = dark ? "☀️" : "🌙";
    btn.querySelector(".label").textContent = dark ? "Light" : "Dark";
  }
}

function toggleTheme() {
  const isDark = document.body.classList.contains("dark");
  const newDark = !isDark;
  localStorage.setItem("theme", newDark ? "dark" : "light");
  applyTheme(newDark);
}

// Apply saved theme on load (before paint)
(function () {
  const saved = localStorage.getItem("theme");
  if (saved === "dark") {
    document.body.classList.add("dark");
  }
})();

document.addEventListener("DOMContentLoaded", () => {
  const saved = localStorage.getItem("theme");
  applyTheme(saved === "dark");

  // Persona card radio sync
  document.querySelectorAll(".persona-card input[type=radio]").forEach(radio => {
    radio.addEventListener("change", () => {
      if (radio.checked) radio.nextElementSibling.classList.add("selected");
    });
  });

  // Loading overlay for compare form
  const form = document.getElementById("compare-form");
  const overlay = document.getElementById("loading-overlay");
  const btn = document.getElementById("compare-btn");
  if (form && overlay) {
    const msgs = [
      "Searching Amazon...",
      "Searching Flipkart...",
      "Matching exact products...",
      "Fetching price history...",
      "Running AI ranking framework...",
      "Almost done..."
    ];
    let msgIdx = 0;
    form.addEventListener("submit", function () {
      overlay.style.display = "flex";
      if (btn) btn.disabled = true;
      const msgEl = document.getElementById("loading-msg");
      const interval = setInterval(() => {
        if (msgIdx < msgs.length && msgEl) {
          msgEl.textContent = msgs[msgIdx++];
        } else {
          clearInterval(interval);
        }
      }, 5000);
    });
  }
});
