// Toast notifications
function toast(message, type) {
  const t = document.getElementById("toast");
  if (!t) return;
  t.textContent = message;
  t.className = "toast show";
  if (type === "err")       t.classList.add("toast-err");
  else if (type === "warn") t.classList.add("toast-warn");
  setTimeout(() => {
    t.className = "toast";
  }, 2800);
}

// Disable button while busy
function busyButton(btn, busy) {
  if (!btn) return;
  if (busy) {
    btn.dataset.original = btn.textContent;
    btn.textContent = "Working...";
    btn.disabled = true;
  } else {
    btn.textContent = btn.dataset.original || btn.textContent;
    btn.disabled = false;
  }
}
