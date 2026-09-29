import test from "node:test";
import assert from "node:assert/strict";
import { readFile, readdir, access } from "node:fs/promises";

const frontend = new URL("../", import.meta.url);

test("todas as páginas usam viewport móvel e o stylesheet compartilhado", async () => {
  const pages = await readdir(new URL("pages/", frontend));
  for (const page of pages.filter(name => name.endsWith(".html"))) {
    const html = await readFile(new URL("pages/" + page, frontend), "utf8");
    assert.match(html, /<meta\s+name="viewport"\s+content="width=device-width,\s*initial-scale=1\.0"/i, page);
    assert.match(html, /href="\.\.\/styles\/style\.css"/, page);
  }
});

test("as regras responsivas vêm depois do sistema visual, sem sobrescrita da cascata", async () => {
  const stylesheet = new URL("styles/style.css", frontend);
  const css = await readFile(stylesheet, "utf8");
  const imports = [...css.matchAll(/@import\s+"([^"]+)";/g)].map(match => match[1]);
  const ui = imports.indexOf("./componentes/ui-system.css");
  const shared = imports.indexOf("./responsividades/r-site.css");
  assert.ok(ui >= 0 && shared > ui);
  for (const [index, file] of imports.entries()) {
    await access(new URL(file, stylesheet));
    if (file.startsWith("./responsividades/") && file !== "./responsividades/r-site.css") {
      assert.ok(index > shared, file);
    }
  }
});

test("menu hamburger permanece fixo no canto inferior direito, inclusive no formulário", async () => {
  const menu = await readFile(new URL("styles/componentes/site-menu.css", frontend), "utf8");
  const formulario = await readFile(new URL("styles/responsividades/r-forms.css", frontend), "utf8");
  assert.match(menu, /\.site-menu\s*\{[^}]*position:\s*fixed;[^}]*right:[^;]+;[^}]*bottom:/s);
  assert.doesNotMatch(formulario, /\.form-page\s+\.site-menu\s*\{[^}]*\b(?:top|bottom)\s*:/s);
  assert.match(formulario, /\.form-page\s+\.site-menu-panel\s*\{\s*bottom:\s*52px;/);
});

test("todos os links e botões do HTML têm aria-label", async () => {
  const paginas = await readdir(new URL("pages/", frontend));
  for (const arquivo of [...paginas.filter(nome => nome.endsWith(".html")).map(nome => "pages/" + nome), "testes.html"]) {
    const html = await readFile(new URL(arquivo, frontend), "utf8");
    for (const tag of html.matchAll(/<(?:a|button)\b[^>]*>/gs)) {
      assert.match(tag[0], /\baria-label="[^"]+"/, `${arquivo}: ${tag[0]}`);
    }
  }
});

test("templates JavaScript também identificam links e botões", async () => {
  for (const pasta of ["js/", "js/pages/", "js/components/", "js/build/"]) {
    const arquivos = await readdir(new URL(pasta, frontend));
    for (const arquivo of arquivos.filter(nome => nome.endsWith(".js"))) {
      const codigo = await readFile(new URL(pasta + arquivo, frontend), "utf8");
      for (const tag of codigo.matchAll(/<(?:a|button)\b[^>]*>/gs)) {
        assert.match(tag[0], /\baria-label=/, `${pasta + arquivo}: ${tag[0]}`);
      }
    }
  }
});

test("tamanhos de fonte não usam px", async () => {
  const pastas = await readdir(new URL("styles/", frontend), { withFileTypes: true });
  for (const pasta of pastas.filter(item => item.isDirectory())) {
    const arquivos = await readdir(new URL("styles/" + pasta.name + "/", frontend));
    for (const arquivo of arquivos.filter(nome => nome.endsWith(".css"))) {
      const css = await readFile(new URL("styles/" + pasta.name + "/" + arquivo, frontend), "utf8");
      assert.doesNotMatch(css, /(?:font-size|font)\s*:[^;{}]*\b\d+(?:\.\d+)?px\b/i, arquivo);
    }
  }
});
