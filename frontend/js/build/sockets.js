// Mesmo contrato de backend/utils/sockets.py. Não infere pela marca/modelo da CPU.
const padrao = '(?:FC)?LGA[\\s-]*[0-9]{3,5}(?:-v?[0-9]+)?|AM\\s*[1-9][0-9]*\\+?|FM\\s*[1-9][0-9]*\\+?|s?TRX?[1-9][0-9]*|SP[1-9][0-9]*';
export function normalizarSocket(valor) {
  if(typeof valor!=='string')return null;
  const texto=valor.trim().replace(/^(?:(?:AMD|INTEL)\s+)?(?:(?:SOCKET|SOQUETE)\s*)?/i,'');
  if(!new RegExp('^(?:'+padrao+')$','i').test(texto))return null;
  return texto.toUpperCase().replace(/\s+/g,'').replace(/^(?:FC)?LGA-?/,'LGA').replace('-V','-').replace(/^STR/,'TR');
}
export function listarSockets(valor) {
  if(typeof valor!=='string')return [];
  valor=valor.replace(/\bLGA\s*115x\b/gi,'LGA1150, LGA1151, LGA1155, LGA1156');
  return [...new Set([...valor.matchAll(new RegExp('(?<![a-z0-9])(?:'+padrao+')(?![a-z0-9+]|-[a-z0-9])','gi'))].map(m=>normalizarSocket(m[0])))].sort();
}

export function suporteSocketCooler(socket,cooler) {
  socket=normalizarSocket(socket);
  const condicionais=cooler.sockets_suporte_condicional===undefined?[]:cooler.sockets_suporte_condicional;
  if(!socket||!Array.isArray(condicionais)||condicionais.map(normalizarSocket).includes(socket))return null;
  const sockets=listarSockets(cooler.compatibilidade);
  return sockets.length?sockets.includes(socket):null;
}
