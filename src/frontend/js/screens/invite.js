import { ApiError } from "../api.js";
import { h } from "../dom.js";
import { date } from "../format.js";
import { icon } from "../icons.js";
import { t } from "../strings.pl.js";
import { messageOf, messageSlot, notice } from "../ui/feedback.js";
import { whileBusy } from "../ui/forms.js";
import { button, linkButton, pageHead, stateScreen } from "../ui/layout.js";

// `#/invite/<token>`: who invites, for which role, until when, and the way to accept.
export async function invite(ctx) {
  const { token } = ctx.params;
  let preview;
  try {
    preview = await ctx.api.call("get_invitation", { params: { token } });
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      return stateScreen({
        iconName: "link",
        title: t.group.goneTitle,
        text: t.group.goneText,
        actions: [linkButton("#/", t.common.backHome, { iconName: "back" })],
      });
    }
    throw error;
  }

  const message = messageSlot();
  const details = h(
    "div",
    { class: "card invitation" },
    h("p", { class: "invitation__label" }, t.group.invitationRole),
    h(
      "p",
      { class: "invitation__role" },
      h("span", { class: "icon-badge" }, icon(preview.role === "woman" ? "heart" : "people")),
      t.common.roles[preview.role],
    ),
    h("p", { class: "muted" }, t.group.roleDescriptions[preview.role]),
    h(
      "p",
      { class: "invitation__expiry" },
      icon("calendar", 18),
      h("time", { datetime: preview.expires_at }, t.group.expires(date(preview.expires_at))),
    ),
  );

  let action;
  if (preview.group_status === "closed") {
    action = notice({ tone: "accent", iconName: "lock" }, t.group.invitationClosed);
  } else if (!ctx.session.me) {
    // Remembered now, so any way of signing in (also the navigation link) comes back here.
    ctx.session.rememberPath(`/invite/${token}`);
    action = h(
      "div",
      { class: "stack" },
      h("p", {}, t.group.signInToAccept),
      h(
        "div",
        { class: "actions" },
        h("a", { class: "button button--accent", href: "#/login" }, t.group.signIn),
        h("a", { class: "button button--ghost", href: "#/register" }, t.group.signUp),
      ),
    );
  } else {
    const accept = button(t.group.accept, {
      variant: "accent",
      iconName: "check",
      async onclick() {
        message.clear();
        await whileBusy(accept, async () => {
          try {
            const me = await ctx.api.call("accept_invitation", { params: { token } });
            // The new group is the one shown, also when the person has other groups.
            await ctx.enterGroup(me.membership.group_id);
            ctx.navigate("/");
          } catch (error) {
            message.error(messageOf(error));
          }
        });
      },
    });
    action = h("div", { class: "actions" }, accept);
  }

  return h(
    "div",
    { class: "invite-screen stack-large" },
    pageHead({
      title: t.group.invitationTitle(preview.invited_by_name),
      eyebrowIcon: "mail",
      lead: t.group.invitationLead,
    }),
    details,
    message.node,
    action,
  );
}
