import { ApiError } from "../api.js";
import { h } from "../dom.js";
import { DEMO_PASSWORD } from "../mock-store.js";
import { t } from "../strings.pl.js";
import { messageOf, messageSlot, notice } from "../ui/feedback.js";
import { field, showFieldErrors, submitButton, whileBusy } from "../ui/forms.js";
import { button, linkButton, pageHead, stateScreen } from "../ui/layout.js";

const MIN_PASSWORD = 8;

function accountScreen({ title, lead, form, footer = [], extra }) {
  return h(
    "div",
    { class: "account" },
    h("span", { class: "account__mark", "aria-hidden": "true" }),
    pageHead({ title, lead }),
    extra,
    h("div", { class: "card account__card" }, form),
    footer.length > 0 && h("p", { class: "account__switch" }, ...footer),
  );
}

// Signs the person in on the screen and goes where they wanted to go. Without a group only an
// invitation can be opened, so other remembered addresses lead to the start instead.
async function signedIn(ctx) {
  await ctx.reloadSession();
  const noGroup = ctx.session.memberships.length === 0;
  ctx.navigate(ctx.session.takeRememberedPath({ invitationsOnly: noGroup }));
}

// In mock mode the "e-mail" is in the demo outbox, so its link can be opened right here.
async function demoMail(ctx, kind, email) {
  if (!ctx.api.mock) return null;
  const letter = await ctx.api.lastMail(kind, email);
  if (!letter) return null;
  const path = kind === "activate" ? "activate" : "reset";
  return notice(
    { tone: "accent", iconName: "mail" },
    h("a", { href: `#/${path}/${letter.token}` }, t.account.demoMail),
  );
}

function emailField() {
  return field({ label: t.account.email, name: "email", type: "email", autocomplete: "email" });
}

function newPasswordField(label = t.account.password, name = "password") {
  return field({
    label,
    name,
    type: "password",
    hint: t.account.newPasswordHint,
    autocomplete: "new-password",
    maxlength: 128,
  });
}

// "Send the activation link again" for an address. The answer never says if the account exists.
function resendButton(ctx, readEmail, message) {
  const control = button(t.account.resendActivation, { variant: "quiet", iconName: "mail" });
  control.addEventListener("click", () =>
    whileBusy(control, async () => {
      const email = readEmail().trim();
      try {
        await ctx.api.call("resend_activation", { body: { email } });
        message.success(t.account.resendSent);
        const demo = await demoMail(ctx, "activate", email);
        if (demo) message.node.append(demo);
      } catch (error) {
        message.error(messageOf(error));
      }
    }),
  );
  return control;
}

export async function login(ctx) {
  const message = messageSlot();
  const resendSlot = messageSlot();
  const email = emailField();
  const password = field({
    label: t.account.password,
    name: "password",
    type: "password",
    autocomplete: "current-password",
  });
  const resend = h("div", { class: "account__resend", hidden: true }, resendButton(ctx, () => email.value, resendSlot), resendSlot.node);
  const submit = submitButton(t.account.loginSubmit, { variant: "accent", iconName: "login" });
  const form = h(
    "form",
    { class: "form", novalidate: true },
    message.node,
    email.node,
    password.node,
    submit,
    resend,
  );

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    message.clear();
    email.setError(email.value.trim() ? "" : t.account.errors.emailMissing);
    password.setError(password.value ? "" : t.account.errors.passwordMissing);
    if (!email.value.trim() || !password.value) return;
    await whileBusy(submit, async () => {
      try {
        await ctx.api.call("login", {
          body: { email: email.value.trim(), password: password.value },
        });
        await signedIn(ctx);
      } catch (error) {
        if (error instanceof ApiError && error.status === 422) {
          showFieldErrors(error, { email, password });
        }
        // A 401 may also mean "not activated yet"; the message says both, so offer a new link.
        if (error instanceof ApiError && error.status === 401) resend.hidden = false;
        message.error(messageOf(error));
      }
    });
  });

  return accountScreen({
    title: t.account.loginTitle,
    lead: t.account.loginLead,
    form,
    extra:
      ctx.api.mock && notice({ tone: "accent" }, t.mock.loginHint("anna@example.com", DEMO_PASSWORD)),
    footer: [
      h("a", { href: "#/forgot" }, t.account.forgotLink),
      h("br"),
      t.account.toRegister,
      " ",
      h("a", { href: "#/register" }, t.account.toRegisterLink),
    ],
  });
}

export async function register(ctx) {
  const message = messageSlot();
  const name = field({
    label: t.account.name,
    name: "display_name",
    hint: t.account.nameHint,
    autocomplete: "given-name",
    maxlength: 60,
  });
  const email = emailField();
  const password = newPasswordField();
  const fields = { display_name: name, email, password };
  const submit = submitButton(t.account.registerSubmit, { variant: "accent" });
  const form = h(
    "form",
    { class: "form", novalidate: true },
    message.node,
    name.node,
    email.node,
    password.node,
    submit,
  );
  const node = accountScreen({
    title: t.account.registerTitle,
    lead: t.account.registerLead,
    form,
    footer: [t.account.toLogin, " ", h("a", { href: "#/login" }, t.account.toLoginLink)],
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    message.clear();
    const problems = {
      display_name: name.value.trim() ? "" : t.account.errors.nameMissing,
      email: email.value.trim() ? "" : t.account.errors.emailMissing,
      password: password.value.length >= MIN_PASSWORD ? "" : t.account.errors.passwordShort,
    };
    for (const [key, text] of Object.entries(problems)) fields[key].setError(text);
    const first = Object.keys(problems).find((key) => problems[key]);
    if (first) {
      fields[first].input.focus();
      return;
    }
    const address = email.value.trim();
    await whileBusy(submit, async () => {
      try {
        // Sign-up confirms the address first, so there is no session yet.
        await ctx.api.call("signup", {
          body: { display_name: name.value.trim(), email: address, password: password.value },
        });
      } catch (error) {
        if (error instanceof ApiError && error.status === 422) showFieldErrors(error, fields);
        message.error(messageOf(error));
        return;
      }
      const resendMessage = messageSlot();
      const done = stateScreen({
        iconName: "mail",
        title: t.account.checkMailTitle,
        text: t.account.checkMailText,
        actions: [resendButton(ctx, () => address, resendMessage), linkButton("#/login", t.account.toLoginLink, { variant: "ghost" })],
      });
      done.append(resendMessage.node);
      const demo = await demoMail(ctx, "activate", address);
      if (demo) done.append(demo);
      node.replaceWith(done);
      focusHeading(done);
    });
  });

  return node;
}

function focusHeading(node) {
  const heading = node.querySelector("h1");
  heading.setAttribute("tabindex", "-1");
  heading.focus();
}

// `#/activate/<token>`, opened from the sign-up e-mail.
export async function activate(ctx) {
  try {
    await ctx.api.call("activate_account", { body: { token: ctx.params.token } });
  } catch (error) {
    if (!(error instanceof ApiError && [404, 422].includes(error.status))) throw error;
    const message = messageSlot();
    const email = emailField();
    const screen = stateScreen({ iconName: "link", title: t.account.linkGoneTitle, text: messageOf(error) });
    screen.append(
      h(
        "div",
        { class: "card account__card account__again" },
        email.node,
        resendButton(ctx, () => email.value, message),
        message.node,
      ),
    );
    return screen;
  }
  return stateScreen({
    iconName: "check",
    title: t.account.activatedTitle,
    text: t.account.activatedText,
    actions: [linkButton("#/login", t.account.toLoginLink, { variant: "accent", iconName: "login" })],
  });
}

// `#/forgot`: ask for a reset link. The answer is the same for every address.
export async function forgot(ctx) {
  const message = messageSlot();
  const email = emailField();
  const submit = submitButton(t.account.forgotSubmit, { variant: "accent", iconName: "mail" });
  const form = h("form", { class: "form", novalidate: true }, message.node, email.node, submit);

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    message.clear();
    const address = email.value.trim();
    email.setError(address ? "" : t.account.errors.emailMissing);
    if (!address) return;
    await whileBusy(submit, async () => {
      try {
        await ctx.api.call("request_password_reset", { body: { email: address } });
      } catch (error) {
        if (error instanceof ApiError && error.status === 422) showFieldErrors(error, { email });
        message.error(messageOf(error));
        return;
      }
      message.success(t.account.forgotSent);
      const demo = await demoMail(ctx, "reset", address);
      if (demo) message.node.append(demo);
    });
  });

  return accountScreen({
    title: t.account.forgotTitle,
    lead: t.account.forgotLead,
    form,
    footer: [h("a", { href: "#/login" }, t.account.toLoginLink)],
  });
}

// `#/reset/<token>`, opened from the reset e-mail.
export async function reset(ctx) {
  const message = messageSlot();
  const password = newPasswordField(t.account.newPassword);
  const submit = submitButton(t.account.resetSubmit, { variant: "accent", iconName: "lock" });
  const form = h("form", { class: "form", novalidate: true }, message.node, password.node, submit);
  const node = accountScreen({ title: t.account.resetTitle, lead: t.account.resetLead, form });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    message.clear();
    const short = password.value.length < MIN_PASSWORD;
    password.setError(short ? t.account.errors.passwordShort : "");
    if (short) return;
    await whileBusy(submit, async () => {
      try {
        await ctx.api.call("confirm_password_reset", {
          body: { token: ctx.params.token, password: password.value },
        });
      } catch (error) {
        if (error instanceof ApiError && error.status === 422) showFieldErrors(error, { password });
        message.error(messageOf(error));
        if (error instanceof ApiError && error.status === 404) {
          message.node.append(linkButton("#/forgot", t.account.askNewLink, { variant: "ghost" }));
        }
        return;
      }
      const done = stateScreen({
        iconName: "check",
        title: t.account.resetDoneTitle,
        text: t.account.resetDoneText,
        actions: [linkButton("#/login", t.account.toLoginLink, { variant: "accent", iconName: "login" })],
      });
      node.replaceWith(done);
      focusHeading(done);
    });
  });

  return node;
}

// `#/account`: the signed-in person changes their password.
export async function account(ctx) {
  const message = messageSlot();
  const current = field({
    label: t.account.currentPassword,
    name: "current_password",
    type: "password",
    autocomplete: "current-password",
  });
  const next = newPasswordField(t.account.newPassword, "new_password");
  const submit = submitButton(t.account.changeSubmit, { iconName: "lock" });
  const form = h("form", { class: "form", novalidate: true }, message.node, current.node, next.node, submit);

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    message.clear();
    current.setError(current.value ? "" : t.account.errors.passwordMissing);
    const short = next.value.length < MIN_PASSWORD;
    next.setError(short ? t.account.errors.passwordShort : "");
    if (!current.value || short) return;
    await whileBusy(submit, async () => {
      try {
        await ctx.api.call("change_password", {
          body: { current_password: current.value, new_password: next.value },
        });
      } catch (error) {
        if (error instanceof ApiError && error.status === 422) {
          showFieldErrors(error, { current_password: current, new_password: next });
        }
        message.error(messageOf(error));
        return;
      }
      current.input.value = "";
      next.input.value = "";
      message.success(t.account.changed);
    });
  });

  return h(
    "div",
    { class: "account" },
    pageHead({
      title: t.account.accountTitle,
      eyebrowIcon: "user",
      lead: t.account.accountLead(ctx.session.me.email),
    }),
    h(
      "section",
      { class: "card account__card", "aria-labelledby": "change-title" },
      h("h2", { id: "change-title", class: "card__title" }, t.account.changeTitle),
      form,
    ),
  );
}
