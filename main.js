(() => {
  const root = document.documentElement;
  const savedTheme = localStorage.getItem("smartcampus-theme");
  if (savedTheme) root.dataset.theme = savedTheme;

  const themeButton = document.getElementById("theme-toggle");
  themeButton?.addEventListener("click", () => {
    const next = root.dataset.theme === "dark" ? "light" : "dark";
    root.dataset.theme = next;
    localStorage.setItem("smartcampus-theme", next);
  });

  const sidebar = document.getElementById("sidebar");
  const overlay = document.getElementById("sidebar-overlay");
  const closeSidebar = () => { sidebar?.classList.remove("open"); overlay?.classList.remove("visible"); };
  document.getElementById("menu-toggle")?.addEventListener("click", () => { sidebar?.classList.add("open"); overlay?.classList.add("visible"); });
  overlay?.addEventListener("click", closeSidebar);

  document.querySelectorAll(".toast-close").forEach((button) => button.addEventListener("click", () => button.parentElement.remove()));
  window.setTimeout(() => document.querySelectorAll(".toast").forEach((toast) => toast.classList.add("fade-out")), 4500);

  const dialog = document.getElementById("confirm-dialog");
  let pendingForm;
  document.querySelectorAll(".confirm-form").forEach((form) => {
    form.addEventListener("submit", (event) => {
      if (!dialog || form.dataset.confirmed) return;
      event.preventDefault();
      pendingForm = form;
      document.getElementById("confirm-copy").textContent = form.dataset.confirm || "This action cannot be undone.";
      dialog.showModal();
    });
  });
  dialog?.addEventListener("close", () => {
    if (dialog.returnValue === "confirm" && pendingForm) {
      pendingForm.dataset.confirmed = "true";
      pendingForm.requestSubmit();
    }
    pendingForm = undefined;
  });
})();
