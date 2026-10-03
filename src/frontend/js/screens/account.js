import { ApiError } from "../api.js";
import { h } from "../dom.js";
import { DEMO_PASSWORD } from "../mock-store.js";
import { t } from "../strings.pl.js";
import { messageOf, messageSlot, notice } from "../ui/feedback.js";
import { field, showFieldErrors, submitButton, whileBusy } from "../ui/forms.js";
import { pageHead } from "../ui/layout.js";

const MIN_PASSWORD = 8;

function accountScreen({ title, lead, form, footer, extra }) {
  return h(
    "div",
    { class: "account" },
    h("span", { class: "account__mark", "aria-hidden": "true" }),
    pageHead({ title, lead }),
    extra,
    h("div", { class: "card account__card" }, form),
    h("p", { class: "account__switch" }, ...footer),
  );
}

// Signs the person in on the screen and goes where they wanted to go.
async function signedIn(ctx, me) {
  await ctx.setMe(me);
  ctx.navigate(ctx.session.takeRememberedPath());
}

export async function login(ctx) {
  const message = messageSlot();
  const email = field({ label: t.account.email, name: "email", type: "email", autocomplete: "email" });
  const password = field({
    label: t.account.password,
    name: "password",
    type: "password",
    autocomplete: "current-password",
  });
  const submit = submitButton(t.account.loginSubmit, { variant: "accent", iconName: "login" });
  const form = h("form", { class: "form", novalidate: true }, message.node, email.node, password.node, submit);

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    message.clear();
    email.setError(email.value.trim() ? "" : t.account.errors.emailMissing);
    password.setError(password.value ? "" : t.account.errors.passwordMissing);
    if (!email.value.trim() || !password.value) return;
    await whileBusy(submit, async () => {
      try {
        const me = await ctx.api.call("login", {
          body: { email: email.value.trim(), password: password.value },
        });
        await signedIn(ctx, me);
      } catch (error) {
        if (error instanceof ApiError && error.status === 422) {
          showFieldErrors(error, { email, password });
        }
        message.error(messageOf(error));
      }
    });
  });

  return accountScreen({
    title: t.account.loginTitle,
    lead: t.account.loginLead,
    form,
    extra: ctx.api.mock && notice({ tone: "accent" }, t.mock.loginHint("anna@example.com", DEMO_PASSWORD)),
    footer: [t.account.toRegister, " ", h("a", { href: "#/register" }, t.account.toRegisterLink)],
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
  const email = field({ label: t.account.email, name: "email", type: "email", autocomplete: "email" });
  const password = field({
    label: t.account.password,
    name: "password",
    type: "password",
    hint: t.account.newPasswordHint,
    autocomplete: "new-password",
    maxlength: 128,
  });
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
    await whileBusy(submit, async () => {
      try {
        const me = await ctx.api.call("register", {
          body: {
            display_name: name.value.trim(),
            email: email.value.trim(),
            password: password.value,
          },
        });
        await signedIn(ctx, me);
      } catch (error) {
        if (error instanceof ApiError && error.status === 422 && showFieldErrors(error, fields)) {
          message.error(messageOf(error));
          return;
        }
        message.error(messageOf(error));
      }
    });
  });

  return accountScreen({
    title: t.account.registerTitle,
    lead: t.account.registerLead,
    form,
    footer: [t.account.toLogin, " ", h("a", { href: "#/login" }, t.account.toLoginLink)],
  });
}
