import { t } from "../strings.pl.js";
import { linkButton, stateScreen } from "../ui/layout.js";

export function notFound() {
  return stateScreen({
    iconName: "door",
    title: t.shell.notFoundTitle,
    text: t.shell.notFoundText,
    actions: [linkButton("#/", t.shell.notFoundBack, { iconName: "back" })],
  });
}

// Shown instead of an error when the role or the group state does not open this place.
export function notAllowed(reason) {
  return stateScreen({
    iconName: "leaf",
    title: t.shell.notAllowedTitle,
    text: t.shell.notAllowed[reason] || t.shell.notAllowed.noGroup,
    actions: [linkButton("#/", t.common.backHome, { iconName: "back" })],
  });
}
