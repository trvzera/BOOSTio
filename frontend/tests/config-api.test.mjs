import test from "node:test";
import assert from "node:assert/strict";
import { resolverApiUrl } from "../js/config.js";

test("mantém localhost e 127.0.0.1 separados em desenvolvimento", () => {
  for (const host of ["localhost", "127.0.0.1"]) {
    assert.equal(resolverApiUrl("", new URL(`http://${host}:5500/frontend`)), `http://${host}:5000`);
  }
});
test("site publicado não aponta para o computador do visitante", () => {
  assert.equal(resolverApiUrl("", new URL("https://www.example.com/pages/login.html")), "https://www.example.com");
});
test("aceita API pública separada e prefixo no mesmo domínio", () => {
  const pagina = new URL("https://www.example.com");
  assert.equal(resolverApiUrl("https://api.example.com/", pagina), "https://api.example.com");
  assert.equal(resolverApiUrl("/api", pagina), "https://www.example.com/api");
});
test("rejeita HTTP em página HTTPS e URL com credenciais", () => {
  const pagina = new URL("https://www.example.com");
  for (const url of ["http://api.example.com", "https://user:senha@api.example.com", "javascript:alert(1)"]) {
    assert.throws(() => resolverApiUrl(url, pagina));
  }
});
