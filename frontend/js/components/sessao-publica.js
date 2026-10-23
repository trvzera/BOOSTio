const PADRAO_ID = /^s-[1-9][0-9]{0,17}$/;
const ACOES = new Set(['testar','salvar']);
const CHAVE = 'boostio:retorno-build-publica';
const PRAZO = 15 * 60 * 1000;

export function idCompartilhamentoPublico(busca = '') {
  const params = new URLSearchParams(busca);
  if (params.getAll('compartilhar_id').length !== 1 || !PADRAO_ID.test(params.get('compartilhar_id'))
    || params.getAll('acao_publica').length > 1 || [...params.keys()].some(k => !['compartilhar_id','acao_publica'].includes(k))
    || params.has('acao_publica') && !ACOES.has(params.get('acao_publica'))) return null;
  return params.get('compartilhar_id');
}

export function guardarRetornoPublico(id,acao,storage = null,agora = Date.now()) {
  if (!PADRAO_ID.test(id) || !ACOES.has(acao)) return false;
  try { (storage ?? globalThis.sessionStorage).setItem(CHAVE,JSON.stringify({id,acao,criadoEm:agora})); return true; }
  catch { return false; }
}

export function consumirRetornoPublico(storage = null,agora = Date.now()) {
  try {
    storage ??= globalThis.sessionStorage;
    const bruto = storage.getItem(CHAVE); storage.removeItem(CHAVE);
    if (!bruto) return null;
    const dado = JSON.parse(bruto), decorrido = agora - dado.criadoEm;
    if (!PADRAO_ID.test(dado.id) || !ACOES.has(dado.acao) || !Number.isFinite(dado.criadoEm) || decorrido < 0 || decorrido > PRAZO) return null;
    return './configuracao-build.html?' + new URLSearchParams({compartilhar_id:dado.id,acao_publica:dado.acao});
  } catch { return null; }
}
