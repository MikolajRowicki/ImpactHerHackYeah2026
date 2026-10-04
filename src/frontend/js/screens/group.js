import { h } from "../dom.js";
import { date } from "../format.js";
import { icon } from "../icons.js";
import { t } from "../strings.pl.js";
import { confirmDialog } from "../ui/dialog.js";
import { messageOf, messageSlot, notice } from "../ui/feedback.js";
import { button, pageHead, section } from "../ui/layout.js";
import { invitationForm } from "./invitation-form.js";
import { issuedInvitations } from "./issued-invitations.js";

// A member id is a membership id, not a person id, so "me" is found by role and name.
// The mother is unique in her group, which is what keeps her own remove control away.
function isMe(ctx, member) {
  if (member.role !== ctx.session.role) return false;
  return member.role === "woman" || member.display_name === ctx.session.me.display_name;
}

function memberRow(member, { canRemove, onRemove, mine }) {
  return h(
    "li",
    { class: "card member" },
    h("span", { class: "icon-badge" }, icon(member.role === "woman" ? "heart" : "user")),
    h(
      "div",
      { class: "member__text" },
      h(
        "p",
        { class: "member__name" },
        member.display_name,
        mine && h("span", { class: "chip chip--plain" }, t.group.you),
      ),
      h("p", { class: "member__role" }, t.common.roles[member.role]),
      h("p", { class: "member__joined" }, t.group.joined(date(member.joined_at))),
    ),
    canRemove &&
      !mine &&
      button(t.group.remove(member.display_name), {
        variant: "danger",
        small: true,
        onclick: () => onRemove(member),
      }),
  );
}

export async function group(ctx) {
  const membership = ctx.session.me.membership;
  const isMother = membership.role === "woman";
  const status = membership.group_status;
  const { items } = await ctx.api.call("list_members");
  const message = messageSlot();

  async function onRemove(member) {
    const ok = await confirmDialog({
      title: t.group.removeTitle(member.display_name),
      text: t.group.removeText,
      confirmLabel: t.group.removeConfirm,
      danger: true,
    });
    if (!ok) return;
    try {
      await ctx.api.call("remove_member", { params: { member_id: member.id } });
      await ctx.refresh();
    } catch (error) {
      message.error(messageOf(error));
    }
  }

  async function onClose() {
    const ok = await confirmDialog({
      title: t.group.closeDialogTitle,
      text: t.group.closeDialogText,
      confirmLabel: t.group.closeButton,
      danger: true,
    });
    if (!ok) return;
    try {
      await ctx.api.call("close_group");
      await ctx.reloadSession();
      await ctx.refresh();
    } catch (error) {
      message.error(messageOf(error));
    }
  }

  async function onLeave() {
    const closedMother = isMother;
    const ok = await confirmDialog({
      title: closedMother ? t.group.deleteClosedDialogTitle : t.group.leaveDialogTitle,
      text: closedMother ? t.group.deleteClosedDialogText : t.group.leaveDialogText,
      confirmLabel: closedMother ? t.group.deleteClosedButton : t.group.leaveConfirm,
      danger: true,
    });
    if (!ok) return;
    try {
      await ctx.api.call("leave_group");
      // Another group of the person is selected, or the panel is shown when none is left.
      await ctx.reloadSession();
      ctx.navigate("/");
    } catch (error) {
      message.error(messageOf(error));
    }
  }

  const canRemove = isMother && status !== "closed";
  const managesInvitations =
    (status === "active" && isMother) || (status === "pending" && membership.role === "partner");
  const issued = managesInvitations ? issuedInvitations(ctx) : null;
  // Two loved ones with the same name and role cannot be told apart, so neither gets the chip.
  const mine = items.filter((member) => isMe(ctx, member));
  const parts = [
    pageHead({
      title: isMother ? t.group.title : t.group.lovedTitle,
      eyebrow: t.common.roles[membership.role],
      eyebrowIcon: "people",
      lead: t.group.activeLead,
    }),
    status === "closed" &&
      notice({ tone: "accent", iconName: "lock" }, h("strong", {}, t.group.closedTitle), t.group.closedText),
    status === "pending" && notice({ iconName: "clock" }, t.group.pendingNote),
    message.node,
    section(
      { title: t.group.membersTitle, id: "members-title" },
      h(
        "ul",
        { class: "card-list member-list" },
        ...items.map((member) =>
          memberRow(member, { canRemove, onRemove, mine: mine.length === 1 && mine[0] === member }),
        ),
      ),
    ),
  ];

  if (status === "active" && isMother) {
    parts.push(
      section(
        { title: t.group.inviteTitle, id: "invite-title" },
        h(
          "div",
          { class: "card" },
          invitationForm(ctx, ["partner", "supporter"], { onCreated: issued.reload }),
        ),
      ),
      issued.node,
      section(
        { title: t.group.closeTitle, id: "close-title" },
        h(
          "div",
          { class: "card card--soft" },
          h("p", {}, t.group.closeText),
          button(t.group.closeButton, { variant: "danger", iconName: "lock", onclick: onClose }),
        ),
      ),
    );
  }
  if (status === "pending" && membership.role === "partner") {
    parts.push(
      section(
        { title: t.group.inviteMotherTitle, id: "invite-title" },
        h(
          "div",
          { class: "card" },
          h("p", {}, t.group.inviteMotherText),
          invitationForm(ctx, ["woman"], { onCreated: issued.reload }),
        ),
      ),
      issued.node,
    );
  }
  // The mother leaves only a closed group, which deletes it; an active one she closes instead.
  if (!isMother || status === "closed") {
    parts.push(
      section(
        { title: isMother ? t.group.deleteClosedTitle : t.group.leaveTitle, id: "leave-title" },
        h(
          "div",
          { class: "card card--soft" },
          h("p", {}, isMother ? t.group.deleteClosedText : t.group.leaveText),
          button(isMother ? t.group.deleteClosedButton : t.group.leaveButton, {
            variant: "danger",
            iconName: "logout",
            onclick: onLeave,
          }),
        ),
      ),
    );
  }
  if (issued) await issued.reload();
  return h("div", { class: "group" }, ...parts);
}
