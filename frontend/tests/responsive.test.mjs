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
