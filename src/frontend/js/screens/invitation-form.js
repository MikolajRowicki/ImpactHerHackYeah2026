import { ApiError } from "../api.js";
import { h } from "../dom.js";
import { date } from "../format.js";
import { icon } from "../icons.js";
import { t } from "../strings.pl.js";
import { messageOf, messageSlot } from "../ui/feedback.js";
import { choiceGroup, field, showFieldErrors, submitButton, whileBusy } from "../ui/forms.js";
import { button } from "../ui/layout.js";

// The variant parameter picks a demo person, so it must not travel with a shared link.
export function invitationLink(token) {
  const params = new URLSearchParams(location.search);
  params.delete("variant");
  const query = params.toString() ? `?${params}` : "";
  return `${location.origin}${location.pathname}${query}#/invite/${encodeURIComponent(token)}`;
}

async function copyText(text, input) {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    input.select();
    try {
      return document.execCommand("copy");
    } catch {
      return false;
    }
  }
}

function linkResult(invitation) {
  const url = invitationLink(invitation.token);
  const status = h("p", { class: "invite-link__status", role: "status" });
  const input = h("input", {
    class: "field__input invite-link__input",
    id: "invite-link",
    type: "text",
    readonly: true,
  });
  input.value = url;
  input.addEventListener("focus", () => input.select());
  const copy = button(t.group.copy, {
    variant: "accent",
    iconName: "copy",
    async onclick() {
      const ok = await copyText(url, input);
      status.replaceChildren(
        ...(ok ? [icon("check", 18), t.group.copied] : [t.group.copyFailed]),
      );
    },
  });
  return h(
    "div",
    { class: "invite-link" },
    h("label", { class: "field__label", for: "invite-link" }, t.group.linkLabel),
    h("div", { class: "invite-link__row" }, input, copy),
    status,
    h(
      "p",
      { class: "field__hint" },
      h("time", { datetime: invitation.expires_at }, t.group.expires(date(invitation.expires_at))),
    ),
  );
}

// Creates an invitation for one of `roles` and shows the link to share.
export function invitationForm(ctx, roles, { onCreated } = {}) {
  const message = messageSlot();
  const result = h("div", { class: "invite-result" });
  const who =
    roles.length > 1
      ? choiceGroup({
          legend: t.group.whoLegend,
          name: "role",
          options: roles.map((value) => ({ value, label: t.group.roleOptions[value] })),
          value: roles[0],
        })
      : null;
  const email = field({
    label: t.group.email,
    name: "email",
    type: "email",
    hint: t.group.emailHint,
    autocomplete: "off",
  });
  const submit = submitButton(t.group.createLink, { iconName: "link" });
  const form = h("form", { class: "form", novalidate: true }, who?.node, email.node, submit);

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    message.clear();
    email.setError("");
    result.replaceChildren();
    const body = { role: who ? who.value : roles[0] };
    if (email.value.trim()) body.email = email.value.trim();
    await whileBusy(submit, async () => {
      try {
        const invitation = await ctx.api.call("create_invitation", { body });
        result.replaceChildren(linkResult(invitation));
        if (onCreated) await onCreated(invitation);
      } catch (error) {
        if (error instanceof ApiError && error.status === 422) showFieldErrors(error, { email });
        message.error(messageOf(error));
      }
    });
  });

  return h("div", { class: "invite-form stack" }, form, message.node, result);
}
