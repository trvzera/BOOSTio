import { categorias, nomePeca } from "./catalogo.js";
import { categoriasMultiplas, itensCategoria, normalizarBuild } from "./estado.js";

// JSON: {formato:"boostio-build",versao:1,build:{...}} ou build legado.
// CSV v1 (vírgula, CRLF): boostio-build,1 / metadados,<JSON sem componentes>
// / categoria,id,proprio,quantidade,nome / uma linha por modelo.
// Células perigosas e apóstrofos iniciais recebem um apóstrofo reversível.
const FORMATO = "boostio-build", VERSAO = 1, LIMITE_BYTES = 1024 * 1024;
const CABECALHO = ["categoria","id","proprio","quantidade","nome"];
const categoriasValidas = new Set(categorias.map(c => c.id));
const MAX_LINHAS = 3 + categorias.reduce((n,c) => n + (categoriasMultiplas.has(c.id) ? 64 : 1),0);
const transientes = new Set(["preco","consumo","watts","consumo_energia"]);
const tem = (obj,chave) => Object.hasOwn(obj,chave);
const objeto = valor => valor !== null && typeof valor === "object" && !Array.isArray(valor);
const falhar = mensagem => { throw new Error(mensagem); };

function limitarTexto(texto) {
  if (typeof texto !== "string") falhar("O arquivo deve ser um texto JSON ou CSV.");
  if (texto.length > LIMITE_BYTES || new TextEncoder().encode(texto).length > LIMITE_BYTES)
    falhar("O arquivo excede o limite de 1 MB (1048576 bytes UTF-8).");
  return texto;
}

function lerJson(texto) {
  try { return JSON.parse(texto); }
  catch { falhar("JSON inválido ou incompleto."); }
}

// Evita coerções, perda silenciosa na serialização e chaves de protótipo.
function validarJson(valor,ancestrais = new Set(),nivel = 0) {
  if (nivel > 64) falhar("Payload com profundidade excessiva.");
  if (valor === null || typeof valor === "boolean") return;
  if (typeof valor === "string") {
    if (valor.includes("\0")) falhar("Texto com caractere nulo inválido.");
    return;
  }
  if (typeof valor === "number" && Number.isFinite(valor)) return;
  if (typeof valor !== "object") falhar("Payload contém um valor JSON inválido.");
  if (ancestrais.has(valor)) falhar("Payload circular inválido.");
  if (!Array.isArray(valor) && ![Object.prototype,null].includes(Object.getPrototypeOf(valor)))
    falhar("Payload deve conter somente objetos JSON.");
  ancestrais.add(valor);
  if (Array.isArray(valor)) {
    for (const item of valor) validarJson(item,ancestrais,nivel + 1);
  } else {
    for (const [chave,item] of Object.entries(valor)) {
      if (["__proto__","constructor","prototype"].includes(chave)) falhar("Chave de metadado inválida.");
      validarJson(item,ancestrais,nivel + 1);
    }
  }
  ancestrais.delete(valor);
}

function validarNumero(valor,campo,maximo,minimo = 0,inclusivo = true) {
  if (valor !== null && (typeof valor !== "number" || !Number.isFinite(valor) ||
      (inclusivo ? valor < minimo : valor <= minimo) || valor > maximo))
    falhar("Valor inválido para " + campo + ".");
}

function validarMetadados(build) {
  for (const [campo,maximo] of [["id",100],["titulo",100],["descricao",300]]) {
    if (tem(build,campo) && (typeof build[campo] !== "string" || build[campo].length > maximo))
      falhar("Metadado inválido: " + campo + ".");
  }
  if (tem(build,"visibilidade") && !["publico","privado"].includes(build.visibilidade))
    falhar("Visibilidade inválida.");
  for (const campo of ["travada","incluirPerifericos","incluirRede"]) {
    if (tem(build,campo) && typeof build[campo] !== "boolean") falhar("Metadado inválido: " + campo + ".");
  }
  if (tem(build,"criadoEm") && (!["string","number"].includes(typeof build.criadoEm) ||
      build.criadoEm === "" || !Number.isFinite(new Date(build.criadoEm).getTime())))
    falhar("Data de criação inválida.");
  if (tem(build,"orcamento")) validarNumero(build.orcamento,"orcamento",1000000);
  if (tem(build,"rede")) {
    const rede = build.rede;
    if (!objeto(rede)) falhar("Rede inválida.");
    const campos = ["tipo","possuiAcessorio","velocidadeMbps","comprimentoCaboM","custoPrevisto"];
    if (Object.keys(rede).some(c => !campos.includes(c))) falhar("Campo de rede inválido.");
    if (tem(rede,"tipo") && !["indefinido","cabo","wifi"].includes(rede.tipo)) falhar("Tipo de rede inválido.");
    if (tem(rede,"possuiAcessorio") && rede.possuiAcessorio !== null && typeof rede.possuiAcessorio !== "boolean")
      falhar("possuiAcessorio deve ser booleano ou null.");
    for (const [campo,maximo] of [["velocidadeMbps",100000],["comprimentoCaboM",1000],["custoPrevisto",100000]]) {
      if (tem(rede,campo)) validarNumero(rede[campo],"rede." + campo,maximo,0,false);
    }
  }
}

function prepararBuild(valor,catalogo) {
  validarJson(valor);
  if (!objeto(valor) || !tem(valor,"componentes") || !objeto(valor.componentes))
    falhar("Build inválida: componentes deve ser um objeto.");
  validarMetadados(valor);
  if (catalogo !== undefined && !Array.isArray(catalogo)) falhar("Catálogo inválido.");
  const conhecidos = catalogo === undefined ? null : new Set(catalogo.map(p => JSON.stringify([p?.categoria,p?.id])));
  for (const [categoria,selecao] of Object.entries(valor.componentes)) {
    if (!categoriasValidas.has(categoria)) falhar("Categoria inválida: " + categoria + ".");
    const multipla = categoriasMultiplas.has(categoria);
    if (!multipla && Array.isArray(selecao)) falhar("A categoria " + categoria + " aceita somente um modelo.");
    const itens = Array.isArray(selecao) ? selecao : [selecao];
    if (itens.length > 64) falhar("Limite de 64 modelos por categoria.");
    const totais = new Map();
    for (const item of itens) {
      if (!objeto(item) || Object.keys(item).some(c => !["id","proprio","quantidade"].includes(c) && !transientes.has(c)))
        falhar("Componente inválido em " + categoria + ".");
      if (tem(item,"id") === tem(item,"proprio")) falhar("Informe exatamente um id ou proprio por componente.");
      const campo = tem(item,"id") ? "id" : "proprio", identidade = item[campo];
      if (typeof identidade !== "string" || !identidade.trim() || identidade.length > 120)
        falhar("Identificação de componente inválida.");
      const quantidade = tem(item,"quantidade") ? item.quantidade : 1;
      if (!Number.isInteger(quantidade) || quantidade < 1 || quantidade > (multipla ? 64 : 1))
        falhar("Quantidade inválida em " + categoria + ".");
      const chave = JSON.stringify([campo,identidade]), total = (totais.get(chave) || 0) + quantidade;
      if (total > 64) falhar("Quantidade acumulada excede 64 unidades por modelo.");
      totais.set(chave,total);
      if (campo === "id" && conhecidos && !conhecidos.has(JSON.stringify([categoria,identidade])))
        falhar("ID desconhecido para a categoria " + categoria + ": " + identidade + ".");
    }
  }
  const metadados = Object.fromEntries(Object.entries(valor).filter(([chave]) => !transientes.has(chave)));
  // Preserva extensões JSON, inclusive rede/orcamento em builds de versões antigas.
  return {...metadados,...normalizarBuild(valor)};
}

function codificarCelula(valor) {
  let texto = String(valor);
  if (/^(?:'|[\t\r\n]|[\s\uFEFF]*[=+\-@])/u.test(texto)) texto = "'" + texto;
  return '"' + texto.replaceAll('"','""') + '"';
}

function decodificarCelula(texto) { return texto.startsWith("'") ? texto.slice(1) : texto; }

function lerCsv(texto) {
  const linhas = [];
  let linha = [], campo = "", estado = "inicio";
  const guardarCampo = () => {
    linha.push(decodificarCelula(campo)); campo = ""; estado = "inicio";
    if (linha.length > CABECALHO.length) falhar("CSV com colunas em excesso.");
  };
  const guardarLinha = () => {
    guardarCampo(); linhas.push(linha); linha = [];
    if (linhas.length > MAX_LINHAS) falhar("CSV excede o limite de modelos.");
  };
  for (let i = 0; i < texto.length; i++) {
    const char = texto[i];
    if (estado === "aspas") {
      if (char === '"') {
        if (texto[i + 1] === '"') { campo += '"'; i++; }
        else estado = "fechado";
      } else campo += char;
    } else if (char === ",") guardarCampo();
    else if (char === "\r" || char === "\n") {
      guardarLinha();
      if (char === "\r" && texto[i + 1] === "\n") i++;
    } else if (char === '"' && estado === "inicio") estado = "aspas";
    else {
      if (char === '"' || estado === "fechado") falhar("Aspas inválidas no CSV.");
      campo += char; estado = "texto";
    }
  }
  if (estado === "aspas") falhar("Aspas não fechadas no CSV.");
  if (estado !== "inicio" || campo || linha.length) guardarLinha();
  return linhas;
}

function buildCsv(texto) {
  const linhas = lerCsv(texto), [formato,metadados,cabecalho] = linhas;
  if (formato?.length !== 2 || formato[0] !== FORMATO || formato[1] !== String(VERSAO))
    falhar("Formato ou versão CSV não suportado.");
  if (metadados?.length !== 2 || metadados[0] !== "metadados") falhar("Metadados CSV ausentes ou inválidos.");
  if (!cabecalho || cabecalho.length !== CABECALHO.length || cabecalho.some((c,i) => c !== CABECALHO[i]))
    falhar("Cabeçalho CSV inválido.");
  const dados = lerJson(metadados[1]);
  if (!objeto(dados) || tem(dados,"componentes")) falhar("Metadados CSV inválidos.");
  const componentes = {};
  for (const linha of linhas.slice(3)) {
    if (linha.length !== CABECALHO.length) falhar("Linha CSV com número de colunas inválido.");
    const [categoria,id,proprio,quantidade] = linha;
    if (!categoriasValidas.has(categoria)) falhar("Categoria inválida: " + categoria + ".");
    if (Boolean(id) === Boolean(proprio)) falhar("Informe exatamente um id ou proprio por componente.");
    if (!/^[1-9]\d?$/.test(quantidade)) falhar("Quantidade CSV inválida.");
    const item = {...(id ? {id} : {proprio}),quantidade:Number(quantidade)};
    if (categoriasMultiplas.has(categoria)) (componentes[categoria] ??= []).push(item);
    else {
      if (tem(componentes,categoria)) falhar("Categoria repetida no CSV: " + categoria + ".");
      componentes[categoria] = item;
    }
  }
  return {...dados,componentes};
}

/** Exporta um envelope JSON v1; não altera a build nem acessa storage. */
export function exportarJson(build) {
  return limitarTexto(JSON.stringify({formato:FORMATO,versao:VERSAO,build:prepararBuild(build)},null,2));
}

/** Exporta CSV v1. A coluna nome é informativa; id/proprio são a identidade. */
export function exportarCsv(build,catalogo) {
  const {componentes,...metadados} = prepararBuild(build,catalogo);
  const linhas = [[FORMATO,VERSAO],["metadados",JSON.stringify(metadados)],CABECALHO];
  for (const {id:categoria} of categorias) {
    for (const item of itensCategoria({componentes},categoria)) {
      const peca = catalogo?.find(p => p?.id === item.id && p?.categoria === categoria);
      linhas.push([categoria,item.id || "",item.proprio || "",item.quantidade,item.proprio || nomePeca(peca)]);
    }
  }
  return limitarTexto(linhas.map(linha => linha.map(codificarCelula).join(",")).join("\r\n") + "\r\n");
}

/** Importa .json/.csv (até 1 MiB UTF-8) como cópia privada, destrancada e sem totais. */
export function importarBuild(texto,extensao,catalogo) {
  limitarTexto(texto);
  texto = texto.replace(/^\uFEFF/,"");
  if (!texto.trim()) falhar("Arquivo vazio.");
  const tipo = typeof extensao === "string" ? extensao.trim().toLowerCase().replace(/^\./,"") : "";
  let dados;
  if (tipo === "json") {
    dados = lerJson(texto);
    if (objeto(dados) && (tem(dados,"formato") || tem(dados,"build"))) {
      if (dados.formato !== FORMATO || dados.versao !== VERSAO ||
          Object.keys(dados).some(c => !["formato","versao","build"].includes(c)))
        falhar("Formato ou versão JSON não suportado.");
      dados = dados.build;
    }
  } else if (tipo === "csv") dados = buildCsv(texto);
  else falhar("Extensão não suportada. Use JSON ou CSV.");
  return {...prepararBuild(dados,catalogo),id:crypto.randomUUID(),visibilidade:"privado",travada:false};
}
