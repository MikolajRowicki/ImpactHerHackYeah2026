// Small inline line icons on a 24 px grid. They are decoration: a text label always sits
// next to them, so every icon is hidden from assistive technology.
const PATHS = {
  home: ["M3 10.5 12 3l9 7.5", "M5 9.5V20h5v-6h4v6h5V9.5"],
  leaf: [
    "M5 19c0-8 5-14 15-15-1 10-7 15-15 15Z",
    "M5 19c3-4 6-7 10-9",
  ],
  sun: [
    "M12 16a4 4 0 1 0 0-8 4 4 0 0 0 0 8Z",
    "M12 2v2",
    "M12 20v2",
    "m4.9 4.9 1.4 1.4",
    "m17.7 17.7 1.4 1.4",
    "M2 12h2",
    "M20 12h2",
    "m4.9 19.1 1.4-1.4",
    "m17.7 6.3 1.4-1.4",
  ],
  moon: ["M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5Z"],
  cloud: ["M7 18h10a4 4 0 0 0 .5-8 6 6 0 0 0-11.6 1.5A3.3 3.3 0 0 0 7 18Z"],
  heart: [
    "M12 20s-7.5-4.6-9-9.4C2 7.3 4.2 4.5 7.2 4.5c2 0 3.5 1 4.8 2.7 1.3-1.7 2.8-2.7 4.8-2.7 3 0 5.2 2.8 4.2 6.1-1.5 4.8-9 9.4-9 9.4Z",
  ],
  hand: [
    "M7 11V6.5a1.5 1.5 0 0 1 3 0V11",
    "M10 10V5a1.5 1.5 0 0 1 3 0v5",
    "M13 10V6a1.5 1.5 0 0 1 3 0v6",
    "M16 11V9a1.5 1.5 0 0 1 3 0v5a7 7 0 0 1-7 7h-.6a6 6 0 0 1-4.6-2.2L4 15a1.6 1.6 0 0 1 2.4-2.1L7 13.6",
  ],
  chat: ["M4 5h16v11H9l-5 4V5Z", "M8 9.5h8", "M8 12.5h5"],
  tasks: ["M9 6h11", "M9 12h11", "M9 18h11", "m3.5 6 1.2 1.2L7 5", "m3.5 12 1.2 1.2L7 11", "M4 18h2"],
  people: [
    "M9 11a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Z",
    "M2.5 20a6.5 6.5 0 0 1 13 0",
    "M16 4.3a3.5 3.5 0 0 1 0 6.4",
    "M18 14.2a6.5 6.5 0 0 1 3.5 5.8",
  ],
  lifebuoy: [
    "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18Z",
    "M12 16a4 4 0 1 0 0-8 4 4 0 0 0 0 8Z",
    "m5.6 5.6 3.6 3.6",
    "m14.8 14.8 3.6 3.6",
    "m14.8 9.2 3.6-3.6",
    "m5.6 18.4 3.6-3.6",
  ],
  logout: ["M15 4h3a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-3", "M10 16l-4-4 4-4", "M6 12h10"],
  login: ["M9 4H6a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h3", "M14 16l4-4-4-4", "M18 12H8"],
  copy: ["M9 9h11v11H9z", "M5 15H4V4h11v1"],
  check: ["m5 12.5 4.5 4.5L19 7.5"],
  plus: ["M12 5v14", "M5 12h14"],
  close: ["m6 6 12 12", "M18 6 6 18"],
  info: ["M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18Z", "M12 11v5", "M12 7.5h.01"],
  arrow: ["M5 12h14", "m13 6 6 6-6 6"],
  back: ["M19 12H5", "m11 6-6 6 6 6"],
  clock: ["M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18Z", "M12 7v5l3 2"],
  lock: ["M6 11h12v9H6z", "M8.5 11V8a3.5 3.5 0 0 1 7 0v3"],
  mail: ["M3 6h18v12H3z", "m3 7 9 6 9-6"],
  link: [
    "M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1",
    "M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1",
  ],
  wind: ["M3 9h11a3 3 0 1 0-3-3", "M3 13h15a3 3 0 1 1-3 3", "M3 17h6"],
  feather: ["M20 4c-8 0-14 5-14 12v4", "M6 16c5 0 10-3 12-8", "M10 12h5"],
  lotus: [
    "M12 20c-4 0-8-2.5-9-6 3-.5 6 .5 9 3 3-2.5 6-3.5 9-3-1 3.5-5 6-9 6Z",
    "M12 17c-2-2-3-4.5-3-7 1-1.5 2-3 3-4 1 1 2 2.5 3 4 0 2.5-1 5-3 7Z",
  ],
  walk: [
    "M13 5.5a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3Z",
    "m9 21 2.5-6 2.5 2v4",
    "M7 12l2.5-4.5 3.5 1 2 3.5 2.5 1",
    "m11.5 15 1-6.5",
  ],
  sparkle: ["M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8Z", "M19 17l.7 1.8 1.8.7-1.8.7L19 22l-.7-1.8-1.8-.7 1.8-.7Z"],
  calendar: ["M4 6h16v14H4z", "M4 10h16", "M8 3v4", "M16 3v4"],
  user: ["M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8Z", "M4.5 21a7.5 7.5 0 0 1 15 0"],
  door: ["M5 21V4h10v17", "M15 6h4v15", "M3 21h18", "M11.5 12.5h.01"],
};

const SVG = "http://www.w3.org/2000/svg";

export function icon(name, size = 22) {
  const svg = document.createElementNS(SVG, "svg");
  for (const [key, value] of Object.entries({
    viewBox: "0 0 24 24",
    width: size,
    height: size,
    fill: "none",
    stroke: "currentColor",
    "stroke-width": "1.8",
    "stroke-linecap": "round",
    "stroke-linejoin": "round",
    "aria-hidden": "true",
    focusable: "false",
    class: `icon icon--${name}`,
  })) {
    svg.setAttribute(key, String(value));
  }
  for (const d of PATHS[name] || PATHS.sparkle) {
    const path = document.createElementNS(SVG, "path");
    path.setAttribute("d", d);
    svg.append(path);
  }
  return svg;
}

// Self-care kinds from the contract mapped to icons.
export const SELF_CARE_ICONS = {
  breathing: "wind",
  relaxation: "feather",
  meditation: "lotus",
  walk: "walk",
};
