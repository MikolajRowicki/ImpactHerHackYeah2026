# Account security: new screens and operations

Status: planned. The operations below arrive in the contract in the first commit group of the
change `full-backend` (branch `change/full-backend`). This file is updated to `ready` with the
commit when they are in.

## What changes for you

Sign-up now confirms the e-mail address. Use the new operations instead of `register`. The old
`register` and `login` keep working as they are in the contract, but `register` is switched off in
production (`ALLOW_LEGACY_REGISTER` off), so do not build the real flow on it.

| Operation | Use it for |
|---|---|
| `signup` | the sign-up form; answers 202 and no session, show "check your e-mail" |
| `activate_account` | the screen opened from the e-mail link |
| `resend_activation` | a "send the link again" action on the "check your e-mail" screen and on the sign-in screen |
| `request_password_reset` | the "forgot password" form |
| `confirm_password_reset` | the screen opened from the reset e-mail link |
| `change_password` | a form for a signed-in person |

## Screens to add

- `#/activate/<token>`: call `activate_account` with the token, then show success and a link to
  sign in, or the `token_invalid` message with a way to ask for a new link.
- `#/reset/<token>`: a form with a new password; call `confirm_password_reset`; on
  `token_invalid` offer a new reset.
- The answers of `signup`, `resend_activation` and `request_password_reset` are identical for known
  and unknown addresses on purpose. Never write text that implies whether an account exists.
- A sign-in that fails with 401 may mean "wrong data" or "account not activated yet". The Polish
  message in the response names both; show it as it is and offer "send the activation link again".

## Details

- Activation links live 3 days, reset links 1 hour; both work once.
- Too many requests for the same address are silently ignored by the server and look like success.
  Do not promise "e-mail sent"; say "if the address is right, you will get a message".
- Passwords are 8 to 128 characters, as in `register`.
