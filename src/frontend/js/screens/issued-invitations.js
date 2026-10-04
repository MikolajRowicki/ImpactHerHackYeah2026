import { h } from "../dom.js";
import { date } from "../format.js";
import { icon } from "../icons.js";
import { t } from "../strings.pl.js";
import { messageOf, messageSlot } from "../ui/feedback.js";
import { button, section } from "../ui/layout.js";

// The unused invitations of the group, each with a way to take it back. `reload()` reads the
// list again, so a form on the same screen can refresh it after creating a link.
export function issuedInvitations(ctx) {
  const list = h("ul", { class: "card-list invitation-list" });
  const message = messageSlot();
  const node = section(
    { title: t.group.issuedTitle, id: "issued-title", className: "issued" },
    message.node,
    list,
  );

  async function revoke(invitation) {
    message.clear();
    try {
      await ctx.api.call("revoke_invitation", { params: { token: invitation.token } });
      await reload();
      message.success(t.group.revoked);
    } catch (error) {
      message.error(messageOf(error));
    }
  }

  function row(invitation) {
    const role = t.common.roles[invitation.role];
    return h(
      "li",
      { class: "card member" },
      h("span", { class: "icon-badge" }, icon("link")),
      h(
        "div",
        { class: "member__text" },
        h("p", { class: "member__name" }, role),
        h(
          "p",
          { class: "member__joined" },
          h("time", { datetime: invitation.expires_at }, t.group.issuedExpires(date(invitation.expires_at))),
        ),
      ),
      button(t.group.revoke(role), {
        variant: "danger",
        small: true,
        onclick: () => revoke(invitation),
      }),
    );
  }

  async function reload() {
    const { items } = await ctx.api.call("list_invitations");
    list.replaceChildren(
      ...(items.length
        ? items.map(row)
        : [h("li", { class: "muted issued__empty" }, t.group.issuedEmpty)]),
    );
  }

  return { node, reload };
}
