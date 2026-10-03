import { pageHead } from "../ui/layout.js";

export async function login() {
  return pageHead({ title: "Zaloguj się" });
}

export async function register() {
  return pageHead({ title: "Załóż konto" });
}
