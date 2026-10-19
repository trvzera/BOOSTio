import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { exportarJson, exportarCsv, importarBuild } from "../js/build/arquivos.js";
import { categorias } from "../js/build/catalogo.js";
import { categoriasMultiplas, normalizarBuild } from "../js/build/estado.js";
import { avaliarBuild } from "../js/build/compatibilidade.js";

const catalogo = JSON.parse(readFileSync(new URL("../data/catalogo-demo.json",import.meta.url)));
const rede = {tipo:"cabo",possuiAcessorio:false,velocidadeMbps:500.5,comprimentoCaboM:12.75,custoPrevisto:null};
const base = (alteracoes = {}) => ({
  ...normalizarBuild({
    id:"build-original",titulo:'Configuração do João, "2026"',descricao:'Linha 1\r\nLinha 2\nCom "aspas", vírgula e ação 🎮',
    criadoEm:"2026-10-19T12:00:00.000Z",visibilidade:"publico",travada:true,incluirPerifericos:false,
    componentes:Object.fromEntries(categorias.filter(({id}) => catalogo.some(p => p.categoria === id)).map(({id:categoria}) => {
      const pecas = catalogo.filter(p => p.categoria === categoria);
      return [categoria,categoriasMultiplas.has(categoria) ? [
        {id:pecas[0].id,quantidade:2},{id:pecas[1].id,quantidade:3},
        {proprio:'Meu modelo de ' + categoria + ', "especial"\r\nsegunda linha',quantidade:1},
      ] : categoria === "mouse" ? {proprio:"Meu mouse",quantidade:1} : {id:pecas[0].id,quantidade:1}];
    })),
  }),rede:{...rede},orcamento:6500.75,...alteracoes,
});
const gravarCelula = valor => '"' + String(valor).replaceAll('"','""') + '"';
// Escrita independente do exportador: testa também arquivos editados externamente.
const csv = (linhas = [],metadados = {},fim = "\r\n") => [
  ["boostio-build","1"],["metadados",JSON.stringify(metadados)],
  ["categoria","id","proprio","quantidade","nome"],...linhas,
].map(l => l.map(gravarCelula).join(",")).join(fim) + fim;
const json = componentes => JSON.stringify({componentes});
const semIdentidade = build => {
  const {id,...dados} = build;
  return dados;
};
const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const formatos = [["json",exportarJson],["csv",b => exportarCsv(b,catalogo)]];

for (const [extensao,exportar] of formatos) {
  test(extensao + ": roundtrip de todas as categorias, modelos, próprios e metadados",() => {
    const build = base(), antes = structuredClone(build), texto = exportar(build);
    assert.equal(typeof texto,"string");
    const copia = importarBuild(texto,"." + extensao.toUpperCase(),catalogo);
    assert.deepEqual(semIdentidade(copia),semIdentidade({...build,visibilidade:"privado",travada:false}));
    assert.match(copia.id,uuid);
    assert.notEqual(copia.id,build.id);
    assert.notEqual(importarBuild(texto,extensao,catalogo).id,copia.id);
    assert.equal(copia.incluirPerifericos,false);
    assert.deepEqual(build,antes);
    for (const categoria of categoriasMultiplas) assert.equal(copia.componentes[categoria].length,3);
  });

  test(extensao + ": rede cabo/wifi/indefinida, booleanos/null, decimais e orçamento zero/null",() => {
    for (const tipo of ["cabo","wifi","indefinido"]) {
      for (const possuiAcessorio of [null,true,false]) {
        for (const orcamento of [null,0,1000000,123.45]) {
          const build = base({rede:{...rede,tipo,possuiAcessorio},orcamento});
          const copia = importarBuild(exportar(build),extensao,catalogo);
          assert.deepEqual(copia.rede,build.rede);
          assert.equal(copia.orcamento,orcamento);
        }
      }
    }
    const build = base({rede:{tipo:"indefinido",possuiAcessorio:null,velocidadeMbps:null,comprimentoCaboM:null,custoPrevisto:null}});
    assert.deepEqual(importarBuild(exportar(build),extensao,catalogo).rede,build.rede);
  });

  test(extensao + ": preserva extensões JSON sem alterar objetos compartilhados",() => {
    const build = base({planejamentoFuturo:{etapas:["revisar",{ativo:true,valor:null}],nota:"=texto"}});
    const copia = importarBuild(exportar(build),extensao,catalogo);
    assert.deepEqual(copia.planejamentoFuturo,build.planejamentoFuturo);
    copia.planejamentoFuturo.etapas.push("nova");
    assert.equal(build.planejamentoFuturo.etapas.length,2);
  });

  test(extensao + ": importa build vazia e aceita BOM UTF-8",() => {
    const build = base({componentes:{},titulo:"Sem componentes"});
    assert.deepEqual(importarBuild("\uFEFF" + exportar(build),extensao,catalogo).componentes,{});
  });

  test(extensao + ": não acessa storage nem mesmo ao rejeitar um arquivo",() => {
    const anteriores = ["localStorage","sessionStorage"].map(chave => [chave,Object.getOwnPropertyDescriptor(globalThis,chave)]);
    try {
      for (const [chave] of anteriores) Object.defineProperty(globalThis,chave,{configurable:true,get() { throw new Error("Acesso indevido a storage"); }});
      importarBuild(exportar(base()),extensao,catalogo);
      assert.throws(() => importarBuild("inválido",extensao,catalogo));
    } finally {
      for (const [chave,descriptor] of anteriores) {
        if (descriptor) Object.defineProperty(globalThis,chave,descriptor);
        else delete globalThis[chave];
      }
    }
  });

  test(extensao + ": ignora totais e custos de componentes importados; avaliação usa catálogo",() => {
    const peca = catalogo.find(p => p.categoria === "processador");
    const build = base({componentes:{processador:{id:peca.id,quantidade:1,preco:999999,consumo:999999,consumo_energia:999999}},rede:{...rede,possuiAcessorio:true},preco:999999,consumo:999999,watts:999999});
    // JSON legado permite verificar os campos transitórios antes de qualquer exportação.
    const texto = extensao === "json" ? JSON.stringify(build) : csv([
      ["processador",peca.id,"","1","Preço e consumo devem vir do catálogo"],
    ],{...build,componentes:undefined});
    const copia = importarBuild(texto,extensao,catalogo);
    for (const campo of ["preco","consumo","watts","consumo_energia"]) assert.equal(Object.hasOwn(copia,campo),false);
    assert.deepEqual(copia.componentes.processador,{id:peca.id,quantidade:1});
    const resultado = avaliarBuild(copia,catalogo);
    assert.equal(resultado.preco,peca.preco);
    assert.equal(resultado.watts,Math.round(peca.consumo_energia || 0));
    assert.equal(exportar(build).includes("999999"),false);
  });
}

test("JSON exportado tem envelope e versão explícitos e preserva o estado de origem",() => {
  const build = base(), dados = JSON.parse(exportarJson(build));
  assert.deepEqual(Object.keys(dados),["formato","versao","build"]);
  assert.equal(dados.formato,"boostio-build");
  assert.equal(dados.versao,1);
  assert.deepEqual(dados.build,build);
});

test("JSON legado migra objetos id/proprio de todas as categorias múltiplas para arrays",() => {
  for (const campo of ["id","proprio"]) {
    const componentes = Object.fromEntries([...categoriasMultiplas].map(categoria => [categoria,{
      [campo]:campo === "id" ? catalogo.find(p => p.categoria === categoria).id : "Meu " + categoria,quantidade:2,
    }]));
    const copia = importarBuild(json(componentes),"json",catalogo);
    for (const categoria of categoriasMultiplas) assert.deepEqual(copia.componentes[categoria],[componentes[categoria]]);
  }
});

test("JSON legado sem quantidade usa 1 e infere periféricos; listas vazias são normalizadas",() => {
  const copia = importarBuild(json({mouse:{proprio:"Mouse"},ssd:[]}),"json",catalogo);
  assert.equal(copia.incluirPerifericos,true);
  assert.deepEqual(copia.componentes.mouse,{proprio:"Mouse",quantidade:1});
  assert.equal(copia.componentes.ssd,undefined);
});

test("modelos repetidos são agrupados sem perder unidades, inclusive peças próprias",() => {
  const componentes = {fan:[{proprio:"Minha fan",quantidade:30},{proprio:"Minha fan",quantidade:34}]};
  assert.deepEqual(importarBuild(json(componentes),"json").componentes.fan,[{proprio:"Minha fan",quantidade:64}]);
  assert.deepEqual(importarBuild(csv([["fan","","Minha fan","30",""],["fan","","Minha fan","34",""]]),"csv").componentes.fan,[{proprio:"Minha fan",quantidade:64}]);
});

test("CSV inclui metadados JSON, id/proprio/quantidade e nomes informativos do catálogo",() => {
  const peca = catalogo.find(p => p.categoria === "processador"), texto = exportarCsv(base(),catalogo);
  assert.ok(texto.startsWith('"boostio-build","1"\r\n"metadados",'));
  assert.ok(texto.includes('"categoria","id","proprio","quantidade","nome"\r\n'));
  assert.ok(texto.includes(gravarCelula([peca.fabricante,peca.modelo].filter(Boolean).join(" "))));
  assert.equal(texto.endsWith("\r\n"),true);
});

test("CSV aceita campos sem aspas, CRLF/LF/CR, EOF sem newline e newlines dentro de aspas",() => {
  for (const fim of ["\r\n","\n","\r"]) {
    const texto = ['boostio-build,1','metadados,{}','categoria,id,proprio,quantidade,nome',
      'fan,,"Modelo com ""aspas"", vírgula\r\noutra\nlinha",2,informativo'].join(fim);
    const copia = importarBuild(texto,"csv");
    assert.deepEqual(copia.componentes.fan,[{proprio:'Modelo com "aspas", vírgula\r\noutra\nlinha',quantidade:2}]);
    assert.deepEqual(importarBuild(texto + fim,"csv").componentes,copia.componentes);
  }
});

test("CSV protege fórmulas e apóstrofos em IDs, próprios e nomes, com roundtrip reversível",() => {
  const perigosos = ['=HYPERLINK("https://example.invalid")',"+SUM(1,2)","-2+3","@SUM(1)","\t=1","\r=1","\n=1","  =1","\uFEFF+1","'texto","''=1","  texto normal"];
  for (const proprio of perigosos) {
    const build = base({titulo:proprio,descricao:proprio,componentes:{fan:[{proprio,quantidade:1}]}});
    const texto = exportarCsv(build,[]);
    const seguro = /^(?:'|[\t\r\n]|[\s\uFEFF]*[=+\-@])/u.test(proprio) ? "'" + proprio : proprio;
    assert.ok(texto.includes(gravarCelula(seguro)),JSON.stringify(proprio));
    const copia = importarBuild(texto,"csv",[]);
    assert.equal(copia.componentes.fan[0].proprio,proprio);
    assert.equal(copia.titulo,proprio);
    assert.equal(copia.descricao,proprio);
    const peca = {id:proprio,categoria:"fan",fabricante:"",modelo:proprio};
    const comId = exportarCsv(base({componentes:{fan:[{id:proprio,quantidade:1}]}}),[peca]);
    assert.ok(comId.includes(["fan",seguro,"",1,seguro].map(gravarCelula).join(",")));
    assert.equal(importarBuild(comId,"csv",[peca]).componentes.fan[0].id,proprio);
  }
});

test("ID deve existir na categoria fornecida; sem catálogo não há validação de existência",() => {
  const id = catalogo.find(p => p.categoria === "processador").id;
  for (const [componentes,linha] of [
    [{fan:[{id:"inexistente",quantidade:1}]},["fan","inexistente","","1",""]],
    [{fan:[{id,quantidade:1}]},["fan",id,"","1",""]],
  ]) {
    for (const [texto,extensao] of [[json(componentes),"json"],[csv([linha]),"csv"]]) {
      assert.throws(() => importarBuild(texto,extensao,catalogo),/ID desconhecido/);
      assert.throws(() => importarBuild(texto,extensao,[]),/ID desconhecido/);
      assert.doesNotThrow(() => importarBuild(texto,extensao));
      assert.throws(() => importarBuild(texto,extensao,null),/Catálogo inválido/);
    }
  }
  const propria = base({componentes:{fan:[{proprio:"Sem catálogo",quantidade:1}]}});
  assert.doesNotThrow(() => importarBuild(exportarJson(propria),"json",[]));
});

test("rejeita quantidades JSON fracionadas, strings, nulas, booleanas e fora do limite",() => {
  for (const quantidade of [0,-1,1.5,65,"2","2x","",null,true,1e100]) {
    assert.throws(() => importarBuild(json({fan:[{proprio:"Fan",quantidade}]}),"json"),/Quantidade/);
  }
  assert.throws(() => importarBuild(json({processador:{proprio:"CPU",quantidade:2}}),"json"),/Quantidade/);
  assert.throws(() => importarBuild('{"componentes":{"fan":[{"proprio":"Fan","quantidade":1e999}]}}',"json"),/JSON inválido/);
});

test("rejeita quantidades CSV não canônicas e fora do limite",() => {
  for (const quantidade of ["","0","-1","1.1","65","1e1","0x10","2x"," 2","2 ","+2","01","NaN","Infinity"]) {
    assert.throws(() => importarBuild(csv([["fan","","Fan",quantidade,""]]),"csv"),/Quantidade/);
  }
  assert.throws(() => importarBuild(csv([["processador","","CPU","2",""]]),"csv"),/Quantidade/);
});

test("limita a 64 modelos por categoria e 64 unidades acumuladas por modelo",() => {
  for (const quantidade of [64,65]) {
    const itens = Array.from({length:quantidade},(_,i) => ({proprio:"Modelo " + i,quantidade:1}));
    const linhas = itens.map(i => ["fan","",i.proprio,"1",""]);
    for (const [texto,extensao] of [[json({fan:itens}),"json"],[csv(linhas),"csv"]]) {
      if (quantidade === 64) assert.equal(importarBuild(texto,extensao).componentes.fan.length,64);
      else assert.throws(() => importarBuild(texto,extensao),/64 modelos/);
    }
  }
  const itens = [{proprio:"Repetida",quantidade:64},{proprio:"Repetida",quantidade:1}];
  assert.throws(() => importarBuild(json({fan:itens}),"json"),/acumulada/);
  assert.throws(() => importarBuild(csv(itens.map(i => ["fan","",i.proprio,String(i.quantidade),""])),"csv"),/acumulada/);
});

test("rejeita categorias desconhecidas, componentes inválidos e identidades ambíguas",() => {
  for (const componentes of [
    {desconhecida:{proprio:"Peça"}},{armazenamento:{proprio:"Peça"}},{cooler:{proprio:"Peça"}},
    {fan:null},{fan:[null]},{fan:[{}]},{fan:["Fan"]},{fan:[{id:"a",proprio:"b"}]},
    {fan:[{id:1}]},{fan:[{proprio:""}]},{fan:[{id:"  "}]},{fan:[{proprio:"x".repeat(121)}]},
    {processador:[{proprio:"CPU"}]},{fan:[{proprio:"Fan",desconhecido:1}]},
  ]) assert.throws(() => importarBuild(json(componentes),"json"));
  for (const linha of [["desconhecida","","Fan","1",""],["fan","id","próprio","1",""],["fan","","","1",""]])
    assert.throws(() => importarBuild(csv([linha]),"csv"));
});

test("rejeita rede e orçamento inválidos em JSON e metadados CSV",() => {
  const invalidos = [
    {rede:null},{rede:[]},{rede:"wifi"},{rede:{tipo:"ethernet"}},{rede:{possuiAcessorio:"false"}},
    {rede:{possuiAcessorio:0}},{rede:{campoDesconhecido:1}},
    ...["velocidadeMbps","comprimentoCaboM","custoPrevisto"].flatMap(campo =>
      ["500",false,-1,0,1000001].map(valor => ({rede:{...rede,[campo]:valor}}))),
    ...[-1,1000001,"100",true,{}].map(orcamento => ({orcamento})),
  ];
  for (const alteracoes of invalidos) {
    const build = base({...alteracoes,componentes:{}});
    const {componentes,...metadados} = build;
    assert.throws(() => importarBuild(JSON.stringify(build),"json"));
    assert.throws(() => importarBuild(csv([],metadados),"csv"));
    assert.throws(() => exportarJson(build));
    assert.throws(() => exportarCsv(build));
  }
  const limite = base({rede:{...rede,velocidadeMbps:100000,comprimentoCaboM:1000,custoPrevisto:100000},orcamento:1000000});
  assert.deepEqual(importarBuild(exportarJson(limite),"json").rede,{...limite.rede,custoPrevisto:null});
});

test("rejeita metadados com tipos inválidos ou que seriam truncados",() => {
  for (const alteracoes of [
    {titulo:1},{titulo:"x".repeat(101)},{descricao:"x".repeat(301)},{id:"x".repeat(101)},
    {travada:"false"},{incluirPerifericos:1},{visibilidade:"secreto"},{criadoEm:"ontem"},{criadoEm:null},
  ]) {
    const build = base({...alteracoes,componentes:{}}), {componentes,...metadados} = build;
    assert.throws(() => importarBuild(JSON.stringify(build),"json"));
    assert.throws(() => importarBuild(csv([],metadados),"csv"));
  }
});

test("rejeita JSON malformado, raízes inválidas e envelopes desconhecidos",() => {
  for (const texto of ["{","null","[]","true","42",'"texto"',"{}",'{"componentes":[]}',
    '{"componentes":null}',JSON.stringify({formato:"outro",versao:1,build:base()}),
    JSON.stringify({formato:"boostio-build",versao:2,build:base()}),
    JSON.stringify({formato:"boostio-build",versao:"1",build:base()}),
    JSON.stringify({formato:"boostio-build",versao:1}),
    JSON.stringify({formato:"boostio-build",versao:1,build:base(),extra:true}),
  ]) assert.throws(() => importarBuild(texto,"json"));
});

test("rejeita CSV incompleto, aspas malformadas, colunas extras e categorias únicas repetidas",() => {
  const valido = csv([["processador","","CPU","1",""]]);
  for (const texto of [
    'categoria,id,proprio,quantidade,nome\n',valido.replace('"boostio-build","1"','"boostio-build","2"'),
    valido.replace('"metadados"','"outra"'),valido.replace('"categoria","id"','"categoria","modelo"'),
    csv([],null),csv([],{componentes:{}}),valido.replace('"{}"','"{invalido}"'),
    csv([["fan","","Fan","1"]]),csv([["fan","","Fan","1","","extra"]]),
    valido + '\r\n',valido + '"aspas abertas',valido + 'fan,,"Fan"x,1,\n',
    valido + 'fan,,Fa"n,1,\n',valido.replace('"metadados","{}"\r\n',''),
    csv([["processador","","CPU","1",""],["processador","","Outro CPU","1",""]]),
    valido + "\n".repeat(300),
  ]) assert.throws(() => importarBuild(texto,"csv"));
});

test("rejeita extensões desconhecidas, tipos de entrada inválidos e arquivos vazios",() => {
  for (const extensao of ["txt","build.json","",".xml",null,undefined,1])
    assert.throws(() => importarBuild(exportarJson(base()),extensao),/Extensão/);
  for (const texto of [null,{},42,undefined]) assert.throws(() => importarBuild(texto,"json"),/texto/);
  for (const extensao of ["json","csv"]) for (const texto of [""," \r\n\t","\uFEFF"])
    assert.throws(() => importarBuild(texto,extensao),/vazio/);
});

test("limite inclusivo de 1 MiB conta bytes UTF-8 antes de remover o BOM",() => {
  for (const [extensao,exportar] of formatos) {
    const texto = exportar(base({componentes:{}})), tamanho = new TextEncoder().encode(texto).length;
    // Espaço JSON é um sufixo válido; no CSV vai dentro da célula nome.
    const cabeca = extensao === "json" ? texto : csv([["fan","","Fan","1",""]]);
    const bytes = new TextEncoder().encode(cabeca).length;
    const completar = n => extensao === "json" ? cabeca + " ".repeat(n) : cabeca.replace('"Fan","1",""','"Fan","1","' + " ".repeat(n) + '"');
    assert.equal(tamanho > 0,true);
    const limite = completar(1024 * 1024 - bytes);
    assert.equal(new TextEncoder().encode(limite).length,1024 * 1024);
    assert.doesNotThrow(() => importarBuild(limite,extensao));
    assert.throws(() => importarBuild("\uFEFF" + limite,extensao),/1 MB/);
    assert.throws(() => importarBuild(completar(1024 * 1024 - bytes + 1),extensao),/1 MB/);
    assert.throws(() => importarBuild("é".repeat(524289),extensao),/1 MB/);
  }
  assert.throws(() => exportarJson(base({extra:"x".repeat(1024 * 1024)})),/1 MB/);
  assert.throws(() => exportarCsv(base({extra:"x".repeat(1024 * 1024)})),/1 MB/);
});

test("rejeita protótipos, profundidade excessiva, NUL e valores não JSON",() => {
  for (const chave of ["__proto__","constructor","prototype"]) {
    const texto = '{"componentes":{},"extra":{' + JSON.stringify(chave) + ':{"poluido":true}}}';
    assert.throws(() => importarBuild(texto,"json"),/Chave/);
    assert.throws(() => importarBuild(csv([],{extra:JSON.parse('{"' + chave + '":1}')}),"csv"),/Chave/);
  }
  assert.equal({}.poluido,undefined);
  assert.throws(() => importarBuild(json({fan:[{proprio:"Fan\0"}]}),"json"),/nulo/);
  let profundo = null;
  for (let i = 0; i < 70; i++) profundo = {profundo};
  assert.throws(() => importarBuild(JSON.stringify({componentes:{},profundo}),"json"),/profundidade/);
  const circular = base(); circular.extra = circular;
  for (const exportar of [exportarJson,exportarCsv]) {
    assert.throws(() => exportar(circular),/circular/);
    for (const extra of [NaN,Infinity,undefined,1n,() => {},new Date()]) assert.throws(() => exportar(base({extra})));
  }
});
