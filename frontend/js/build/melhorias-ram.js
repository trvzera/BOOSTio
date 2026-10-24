import { itensCategoria } from './estado.js';
import { slotsRam } from './hardware.js';

const positivo = valor => typeof valor !== 'boolean' && ['number','string'].includes(typeof valor)
  && String(valor).trim() && Number.isFinite(Number(valor)) && Number(valor) > 0 ? Number(valor) : null;
const inteiro = valor => Number.isInteger(positivo(valor)) ? Number(valor) : null;
const ddr = valor => /^DDR[1-9]$/.test(String(valor).replace(/[\s-]/g,'').toUpperCase())
  ? String(valor).replace(/[\s-]/g,'').toUpperCase() : null;
const latencia = peca => {
  const cl = /^(?:CL\s*)?(\d+(?:[.,]\d+)?)(?:-\d+)*$/i.exec(String(peca.latencia ?? '').trim());
  const freq = positivo(peca.frequencia_mhz);
  const ciclos = cl ? positivo(cl[1].replace(',','.')) : null;
  return ciclos && freq ? ciclos / freq : null;
};

export const AVISO_DUAL_CHANNEL = 'Prefira dois pentes do mesmo modelo e capacidade, idealmente de um kit testado junto, nos slots indicados no manual da placa-mãe. Isso favorece dual channel nas plataformas compatíveis; dois pentes, por si só, não garantem sua ativação. Misturar modelos pode afetar estabilidade, timings e XMP/EXPO.';

export function contextoMelhoriaRam(build,catalogo) {
  const id = itensCategoria(build,'placa_mae')[0]?.id;
  const placa = catalogo.find(p=>p.categoria === 'placa_mae' && p.id === id);
  if (!placa) throw new Error('Identifique a placa-mãe atual no catálogo antes de melhorar a RAM.');
  const {slots,provisorio:slotsProvisorios} = slotsRam(placa), maximoGb = inteiro(placa.memoria_maxima_gb), padrao = ddr(placa.tipo_memoria);
  if (!slots) throw new Error('A placa-mãe está cadastrada sem slots de RAM disponíveis. Confira esse dado antes de melhorar a memória.');
  if (!maximoGb || !padrao) throw new Error('Faltam DDR ou capacidade máxima da placa-mãe para conferir a melhoria de RAM.');
  return {placa,slots,slotsProvisorios,maximoGb,padrao};
}

// Uma proposta contém somente as unidades/kit que serão compradas. Não grava a build.
export function planejarMelhoriaRam(build,catalogo,{modo = 'adicionar',itens = []} = {}) {
  if (build?.travada) throw new Error('Destranque a build para melhorar a RAM.');
  if (!build?.componentes || !Array.isArray(catalogo) || !Array.isArray(itens) || !['adicionar','substituir'].includes(modo))
    throw new Error('Proposta de memória RAM inválida.');
  const proxima = structuredClone(build);
  if (!itens.length) return {build:proxima,gastoCentavos:0,compras:[]};
  const contexto = contextoMelhoriaRam(build,catalogo);
  function identificar(item,compra = false) {
    const quantidade = item?.quantidade === undefined ? 1 : item.quantidade;
    const peca = catalogo.find(p=>p.categoria === 'memoria_ram' && p.id === item?.id);
    if (!peca || !Number.isInteger(quantidade) || quantidade < 1 || quantidade > 64)
      throw new Error('Identifique todos os modelos e quantidades da RAM atual e da proposta.');
    const capacidade = inteiro(peca.capacidade_gb), pentes = inteiro(peca.quantidade_pentes), frequencia = positivo(peca.frequencia_mhz);
    if (!capacidade || !pentes || !frequencia || !ddr(peca.ddr)) throw new Error('Faltam capacidade, pentes, DDR ou frequência para conferir esta memória.');
    if (ddr(peca.ddr) !== contexto.padrao) throw new Error('A RAM deve usar o padrão DDR da placa-mãe atual.');
    if (compra && (peca.esgotado || positivo(peca.preco) == null)) throw new Error('Uma memória da proposta está indisponível ou sem preço válido.');
    return {peca,quantidade,capacidade,pentes,frequencia};
  }
  const atuais = itensCategoria(build,'memoria_ram').map(i=>identificar(i));
  const compras = itens.map(i=>identificar(i,true));
  if (new Set(compras.map(i=>i.peca.id)).size !== compras.length) throw new Error('Agrupe a quantidade do mesmo modelo de RAM na proposta.');
  for (const nova of compras) for (const atual of atuais) {
    if (modo === 'adicionar' && nova.frequencia !== atual.frequencia)
      throw new Error('Para acrescentar RAM, use a mesma frequência e DDR das memórias atuais.');
    if (modo === 'substituir' && nova.frequencia < atual.frequencia)
      throw new Error('A troca reduziria a frequência da RAM atual.');
    if (nova.peca.id !== atual.peca.id) {
      const antes = latencia(atual.peca), depois = latencia(nova.peca);
      if (antes == null || depois == null) throw new Error('Falta a latência CAS para descartar uma piora ao misturar ou substituir modelos.');
      if (depois > antes + 1e-12) throw new Error('Esta memória aumentaria a latência CAS relativa à frequência.');
    }
  }
  const finais = new Map();
  for (const selecao of [...(modo === 'adicionar' ? atuais : []),...compras]) {
    const quantidade = (finais.get(selecao.peca.id)?.quantidade || 0) + selecao.quantidade;
    if (quantidade > 64) throw new Error('O limite de unidades deste modelo de RAM foi atingido.');
    finais.set(selecao.peca.id,{...selecao,quantidade});
  }
  const somar = (lista,campo) => lista.reduce((s,i)=>s + i[campo] * i.quantidade,0);
  const lista = [...finais.values()], pentes = somar(lista,'pentes'), capacidadeGb = somar(lista,'capacidade');
  if (pentes > contexto.slots) throw new Error('Os pentes da proposta excedem os slots da placa-mãe atual.');
  if (capacidadeGb > contexto.maximoGb) throw new Error('A capacidade proposta supera o máximo de RAM da placa-mãe atual.');
  if (new Set(lista.map(i=>i.frequencia)).size > 1) throw new Error('As memórias da proposta precisam usar a mesma frequência.');
  if (modo === 'substituir' && (capacidadeGb < somar(atuais,'capacidade') || somar(atuais,'pentes') >= 2 && pentes < 2))
    throw new Error('A troca reduziria a capacidade atual ou passaria de vários pentes para apenas um.');
  if (modo === 'substituir' && lista.length === atuais.length && lista.every(nova=>atuais.some(atual=>atual.peca.id === nova.peca.id && atual.quantidade === nova.quantidade)))
    throw new Error('Essa proposta mantém as mesmas memórias. Para expandir esse modelo, escolha adicionar sem remover as atuais.');
  proxima.componentes.memoria_ram = lista.map(i=>({id:i.peca.id,quantidade:i.quantidade}));
  if (proxima.compatibilidade) {
    // Somente os erros de RAM podem estar obsoletos. Não esconda conflitos de outras peças.
    const erros = (proxima.compatibilidade.erros || []).filter(r=>!/^ram-/.test(r.codigo || ''));
    proxima.compatibilidade = {status:erros.length ? 'incompativel' : 'nao_verificado',escopo:'parcial',
      rotulo:erros.length ? 'Incompatibilidade identificada' : 'Prévia local: revalidação pendente',erros,naoVerificado:[],
      aviso:'A prévia não certifica BIOS, perfis de memória ou demais dados ausentes. O servidor reavalia a configuração ao salvar.'};
  }
  return {build:proxima,compras,pentes,capacidadeGb,...contexto,
    gastoCentavos:compras.reduce((s,i)=>s + Math.round(Number(i.peca.preco) * 100) * i.quantidade,0)};
}
