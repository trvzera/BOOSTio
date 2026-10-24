import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync, existsSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const raiz=new URL("../../",import.meta.url);
test("Docker da API inclui os dois manifestos compartilhados de runtime",()=>{
  const docker=readFileSync(new URL("Dockerfile.api",raiz),"utf8");
  for (const nome of ["medidas-fisicas.json","imagens-referencia.json"]) {
    assert.ok(existsSync(new URL("frontend/data/"+nome,raiz)));
    assert.match(docker,new RegExp("COPY[^\\n]*frontend/data/"+nome.replace(".","\\.")+"[^\\n]*\\./frontend/data/"));
  }
});

test("artefatos locais são ignorados, fontes, testes e dados de runtime não",()=>{
  const ignorado=caminho=>spawnSync("git",["check-ignore","--no-index","-q",caminho],
    {cwd:fileURLToPath(raiz)}).status;
  for (const arquivo of ["node_modules/exemplo.js","output/arte.png","backend/.pytest_cache/v/cache",
    "database/banco.db","database/banco.db-wal","database/banco.sqlite3-shm",".env.development",
    ".env.production.local","frontend/.DS_Store","debug.log","playwright-report/index.html"]) {
    assert.equal(ignorado(arquivo),0,arquivo);
  }
  for (const arquivo of [".env.example",".env.sample","package-lock.json","frontend/testes.html",
    "frontend/data/medidas-fisicas.json","frontend/imgs/produtos/fan-1.webp",
    "backend/data/pecas_basicas_medias.json","backend/tests/conftest.py","docs/diagrama-classes.png"]) {
    assert.equal(ignorado(arquivo),1,arquivo);
  }
});
