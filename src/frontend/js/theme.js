// Light or dark. No stored choice means the system setting decides (see index.html).
const KEY = "theme";
const darkQuery = window.matchMedia("(prefers-color-scheme: dark)");

export function isDark() {
  const chosen = document.documentElement.getAttribute("data-theme");
  return chosen ? chosen === "dark" : darkQuery.matches;
}

export function setTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  try {
    localStorage.setItem(KEY, theme);
  } catch {
    // The choice then lasts until the page is closed.
  }
  syncThemeColor();
}

function syncThemeColor() {
  const meta = document.querySelector('meta[name="theme-color"]');
  if (meta) meta.setAttribute("content", isDark() ? "#1c2420" : "#faf7f2");
}

export function onSystemChange(callback) {
  darkQuery.addEventListener("change", () => {
    syncThemeColor();
    callback();
  });
}

syncThemeColor();
