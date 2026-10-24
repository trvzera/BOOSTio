import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { fichaTecnica, destaquesFichaTecnica, gruposFichaTecnica } from "../js/build/catalogo.js";

test("destaques da CPU priorizam socket, vídeo integrado, cooler e consumo", () => {
  const peca = {categoria:"processador",modelo:"CPU",soquete:"AM4",nucleo:6,thread:12,
    videointegrado:false,cooler:true,consumo_energia:65};
  const campos = Object.fromEntries(destaquesFichaTecnica(peca));
  assert.equal(campos.Socket,"AM4");
  assert.equal(campos["Vídeo integrado"],"Não");
  assert.equal(campos["Cooler incluso"],"Sim");
  assert.equal(campos["Consumo estimado (W)"],"65");
  assert.equal(destaquesFichaTecnica({...peca,consumo_energia:0}).at(-1)[1],"0");
});

test("slots desconhecidos são explícitos, sem quantidade ou compatibilidade inventada", () => {
  const campos = Object.fromEntries(destaquesFichaTecnica({categoria:"placa_mae",socket:"AM5",tipo_memoria:"DDR5",quantidade_slots_ram:4}));
  assert.equal(campos["Slots de RAM"],"4");
  assert.equal(campos["Slots M.2"],"Não informado");
  assert.equal(campos["Portas SATA"],"Não informado");
  assert.equal(campos["RAM máxima (GB)"],"Não informado");
});

test("grupos preservam todos os campos técnicos sem misturar preço ou ofertas", () => {
  const peca = {categoria:"gabinete",id:"gabinete:1",fabricante:"Teste",modelo:"Case",part_number:"PN-1",preco:500,
    imagem:"foto.webp",ofertas:[{preco:500}],esgotado:false,fans_inclusos:0,quantidade_max_fans:7,
    consumo_energia:0,comprimento_mm:400,painel_vidro:true,detalhe_adicional:"Disponível",
    fonte_medidas:"https://example.test/ficha",ficha_tecnica_verificada_em:"2026-10-23"};
  const antes = structuredClone(peca);
  const grupos = gruposFichaTecnica(peca);
  assert.deepEqual(peca,antes);
  const linhas = grupos.flatMap(grupo => grupo.campos);
  for (const linha of fichaTecnica(peca)) assert.ok(linhas.some(item => JSON.stringify(item) === JSON.stringify(linha)));
  assert.equal(linhas.length,fichaTecnica(peca).length + 1);
  assert.equal(Object.fromEntries(linhas)["Referência do catálogo / part number"],"PN-1");
  assert.equal(Object.fromEntries(grupos.find(grupo=>grupo.titulo==="Compatibilidade e instalação").campos)["Ventoinhas inclusas"],"0");
  assert.equal(Object.fromEntries(grupos.find(grupo=>grupo.titulo==="Origem das informações").campos)["Ficha consultada em"],"23/10/2026");
  assert.ok(!linhas.some(([rotulo])=>["id","preco","esgotado","ofertas","imagem"].includes(rotulo)));
});

test("agrupamento mantém a correção de dimensões legadas e não exibe grupos vazios", () => {
  const peca = {modelo_ficha_tecnica:"Exato",dimensoes:999,comprimento_mm:120,largura_mm:80,altura_mm:150,consumo_energia:null,modelo:"Cooler"};
  const grupos = gruposFichaTecnica(peca);
  assert.ok(grupos.every(grupo=>grupo.campos.length));
  assert.ok(!grupos.flatMap(grupo=>grupo.campos).some(([rotulo])=>rotulo==="Dimensão informada (mm)"));
  assert.ok(!grupos.some(grupo=>grupo.titulo==="Desempenho e consumo"));
});

test("rede recebe rótulos legíveis e dados opcionais não são transformados em valores", () => {
  const campos = Object.fromEntries(gruposFichaTecnica({categoria:"adaptador_wifi",padrao_wifi:"Wi-Fi 6",velocidade_mbps:1200,bluetooth:false,interface:"PCIe",observacoes_medidas:""}).flatMap(grupo=>grupo.campos));
  assert.equal(campos["Padrão Wi-Fi"],"Wi-Fi 6");
  assert.equal(campos["Velocidade de rede (Mbps)"],"1200");
  assert.equal(campos.Bluetooth,"Não");
  assert.ok(!Object.hasOwn(campos,"Condições e folgas a confirmar"));
  assert.equal(Object.fromEntries(destaquesFichaTecnica({categoria:"cabo_rede",comprimento_m:2,conector:"RJ45"}))["Comprimento do cabo (m)"],"2");
});

test("página usa destaques por categoria e seções acessíveis, escapando valores", async () => {
  const pagina = await readFile(new URL("../js/pages/peca.js",import.meta.url),"utf8");
  assert.match(pagina,/destaquesFichaTecnica\(peca\)/);
  assert.match(pagina,/gruposFichaTecnica\(peca\)/);
  assert.match(pagina,/aria-labelledby="spec-group-/);
  assert.match(pagina,/h\(grupo\.titulo\)/);
  assert.match(pagina,/h\(rotulo\)/);
  assert.match(pagina,/h\(valor\)/);
  assert.doesNotMatch(pagina,/detalhes\.slice\(3,7\)/);
});
