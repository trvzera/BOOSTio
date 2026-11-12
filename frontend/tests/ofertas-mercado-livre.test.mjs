import test from "node:test";
import assert from "node:assert/strict";
import { cartoesOfertasHtml } from "../js/build/ofertas-peca.js";
import { conteudoCompra } from "../js/build/acoes-build.js";

const oferta={id:7,loja:"mercado_livre",produto_id_loja:"MLB123",vendedor_id:"42",vendedor_nome:'<img src=x onerror=alert(1)>',url:"https://produto.mercadolivre.com.br/MLB-123-_JM",preco:500,esgotado:null,atualizadoEm:"2026-11-02T12:00:00Z"};
const peca={id:"processador:1",categoria:"processador",modelo:"CPU",fabricante:"AMD",preco:600,esgotado:true,ofertas:[oferta]};

test("cartão informa vendedor, data e estoque desconhecido, sem HTML injetado",()=>{
  const html=cartoesOfertasHtml(peca);
  assert.match(html,/Mercado Livre/);assert.match(html,/estoque não confirmado/);assert.match(html,/Consulta registrada/);
  assert.match(html,/&lt;img/);assert.doesNotMatch(html,/<img src=x/);assert.match(html,/500,00/);
});

test("referência KaBuM indisponível não oculta alternativas de marketplace",()=>{
  const item={id:peca.id,quantidade:1};
  const build={componentes:{processador:item},incluirRede:false};
  const comparacao={linhas:[{item,depois:peca,indisponivel:true,antigo:60000,novo:60000,diferenca:0}],antes:60000,depois:60000,parcial:true,diferenca:0};
  const html=conteudoCompra(build,[peca],comparacao);
  assert.match(html,/produto.mercadolivre.com.br/);assert.match(html,/confirme estoque e frete/);
  assert.doesNotMatch(html,/src="null"/);
});

test("layout de ofertas combina o filtro por loja com os controles exclusivos de administrador",()=>{
  const opcoes={loja:"mercado_livre",somenteDisponiveis:true,referenciaIndisponivel:true};
  const normal=cartoesOfertasHtml(peca,opcoes);
  assert.match(normal,/Conferir na loja/);
  assert.doesNotMatch(normal,/data-remover-oferta/);
  const admin=cartoesOfertasHtml(peca,{...opcoes,administrador:true});
  assert.match(admin,/data-remover-oferta="7"/);
  assert.match(admin,/Conferir na loja/);
  assert.doesNotMatch(admin,/KaBuM!|Pichau|<img src=x/);
});
