import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resumirCompatibilidade } from "../js/build/resumo-compatibilidade.js";
import { indicadorBuild } from "../js/build/indicador.js";
import { planejamentoFans, informacoesFans, temFansInclusas } from "../js/build/fans.js";
import { completarMedidas } from "../js/build/medidas-fisicas.js";
import { fichaTecnica } from "../js/build/catalogo.js";

const base = {erros: [], avisos: [], dicas: [], faltam: []};
const diagnostico = {status: "nao_verificado", rotulo: "Compatibilidade não totalmente verificada", naoVerificado: [
  {codigo: "placa_video-medida", mensagem: "Falta confirmar comprimento."},
  {codigo: "gpu-altura", mensagem: "Falta confirmar altura."},
  {codigo: "gpu-espessura", mensagem: "Falta confirmar espessura."},
  {codigo: "fans-tamanho", mensagem: "Faltam tamanhos de fans."},
  {codigo: "fans-posicoes", mensagem: "Faltam posições de fans."},
  {codigo: "suporte-cpu-bios", mensagem: "Confirme a BIOS."},
]};

test("seis verificações aparecem em três assuntos, preservando o diagnóstico e os motivos", () => {
  const entrada = {...base, compatibilidade: diagnostico}, antes = structuredClone(entrada);
  const resumo = resumirCompatibilidade(entrada);
  assert.equal(resumo.verificacoes, 6);
  assert.equal(resumo.grupos.length, 3);
  assert.equal(resumo.grupos.flatMap(g => g.mensagens).length, 6);
  assert.deepEqual(entrada, antes);
  const html = indicadorBuild(entrada, "teste");
  assert.match(html, /build-indicator aviso/);
  assert.match(html, /6 verificações agrupadas por assunto/);
  assert.doesNotMatch(html, /<details[^>]*\bopen\b/);
});
test("uma dúvida não reaparece como dica local quando a regra do servidor já explica o campo", () => {
  const resumo = resumirCompatibilidade({...base, compatibilidade: diagnostico, dicas: [
    "Faltam medidas para confirmar o encaixe da placa de vídeo no gabinete.",
    "Faltam medidas para confirmar o encaixe da altura da placa de vídeo no gabinete.",
    "Confirme a distribuição das fans e do radiador: faltam medidas por posição.",
  ]});
  assert.equal(resumo.grupos.flatMap(g => g.mensagens).length, 6);
  assert.deepEqual(resumo.dicas, []);
});
test("conflitos e avisos sérios permanecem fora das seções recolhidas", () => {
  const entrada = {...base, erros: ["Socket incompatível.", "Socket incompatível."], avisos: ["RAM de modelos diferentes."], faltam: ["Fonte", "Gabinete"], compatibilidade: diagnostico};
  const html = indicadorBuild(entrada, "teste");
  assert.match(html, /build-indicator erro/);
  assert.equal(html.split("Socket incompatível.").length - 1, 1);
  const recolhida = html.indexOf('<details class="compatibility-unknown');
  for (const texto of ["Socket incompatível.", "RAM de modelos diferentes.", "Falta adicionar: Fonte, Gabinete."])
    assert.ok(html.indexOf(texto) < recolhida);
});
test("mensagens desconhecidas e detalhes técnicos continuam disponíveis e escapados", () => {
  const html = indicadorBuild({...base, dicas: ["Uma dica sem categoria."], compatibilidade: {naoVerificado: [{codigo: "nova-regra", mensagem: '<img src=x onerror="alert(1)">'}]}}, "teste");
  assert.ok(html.includes("&lt;img"));
  assert.ok(!html.includes("<img"));
  assert.match(html, /Outras informações/);
  assert.match(html, /Uma dica sem categoria/);
});
test("aviso sério continua destacado mesmo se o servidor repetir o texto como dado pendente", () => {
  const mensagem = "Misturar kits pode afetar a estabilidade.";
  const resultado = {...base, avisos: [mensagem], compatibilidade: {naoVerificado: [{codigo: "ram-perfis", mensagem}]}};
  assert.deepEqual(resumirCompatibilidade(resultado).avisos, [mensagem]);
  const html = indicadorBuild(resultado, "teste");
  assert.ok(html.indexOf('class="warning"') < html.indexOf('<details class="compatibility-unknown'));
});

const manifesto = JSON.parse(readFileSync(new URL("../data/medidas-fisicas.json", import.meta.url)));
const x1 = completarMedidas({categoria: "gabinete", fabricante: "Rise Mode",
  modelo: "Office Rise Mode X1 White, Mini Tower, M-ATX, Sem FANs, Branco - RM-GA-OFX1-FW",
  part_number: "KABUM-516120", link: "https://www.kabum.com.br/produto/516120"}, manifesto);
const fans = [{item: {quantidade: 2}, peca: {quantidade: 1, tamanho_mm: 120}}];
test("referência visual do X1 preserva capacidade publicada e não confirma diâmetro ou distribuição", () => {
  const antes = structuredClone(x1), plano = planejamentoFans(x1);
  assert.equal(plano.quantidade, 2);
  assert.match(plano.posicoes, /lateral.*traseira/);
  assert.equal(plano.dimensoes, "315 × 170 × 350 mm");
  const info = informacoesFans(x1, fans);
  assert.equal(info.capacidade, 3);
  assert.equal(info.tamanhos, null);
  assert.equal(info.distribuicao, null);
  assert.equal(temFansInclusas(x1), false);
  assert.deepEqual(x1, antes);
  assert.ok(fichaTecnica(x1).some(([nome, valor]) => nome.includes("estimativa visual") && valor.includes("não confirma")));
});
test("medidas externas maiores e estimativas não viram capacidade, aprovação ou fans inclusas", () => {
  const gabinete = {...x1, quantidade_max_fans: null, comprimento_mm: 1000, largura_mm: 1000, altura_mm: 1000};
  assert.equal(planejamentoFans(gabinete).quantidade, 2);
  assert.equal(informacoesFans(gabinete, fans).capacidade, null);
  assert.equal(informacoesFans(gabinete, fans).quantidade, null);
  assert.equal(informacoesFans(gabinete, fans).tamanhos, null);
  assert.equal(planejamentoFans({comprimento_mm: 500, largura_mm: 250, altura_mm: 500}), null);
});
test("referência não se transfere para outra revisão e metadados inválidos não geram sugestão", () => {
  assert.equal(completarMedidas({...x1, estimativa_fans: undefined, part_number: "outra-revisao"}, manifesto).estimativa_fans, undefined);
  for (const estimativa of [{...x1.estimativa_fans, quantidade_inicial: true}, {...x1.estimativa_fans, quantidade_inicial: 4}, {...x1.estimativa_fans, quantidade_inicial: 1.5}, {...x1.estimativa_fans, origem: "dimensoes_externas"}, {...x1.estimativa_fans, posicoes_aparentes: []}])
    assert.equal(planejamentoFans({...x1, estimativa_fans: estimativa}), null);
});
