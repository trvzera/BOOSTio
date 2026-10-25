import { iniciarCodigoVerificacao } from "./verification-code.js";

// Um envio automático por destino nesta página; reabrir o modal nunca dispara SMTP.
export function iniciarFluxoVerificacaoEmail({modal,enviar,confirmar,aoConfirmar,agora=Date.now}) {
  const inputs=[...modal.querySelectorAll(".code-input")];
  const enviarBtn=modal.querySelector("#btn-send-code"),confirmarBtn=modal.querySelector("#btn-confirm-code");
  const erro=modal.querySelector("#verify-email-error"),status=modal.querySelector("#verify-email-status");
  const alvo=modal.querySelector("#verify-email-target"),automaticos=new Set();
  let usuario,chave="",enviando=false,conferindo=false,enviado=false,concluido=false,ultimoCodigo="",proximoEnvio=0,expiraEm=0,timer,revisao=0;
  const aberto=()=>modal.classList.contains("open");
  const codigo=()=>inputs.map(i=>i.value).join("");
  function atualizar() {
    const segundos=Math.max(0,Math.ceil((proximoEnvio-agora())/1000));
    enviarBtn.disabled=enviando||conferindo||concluido||segundos>0;
    enviarBtn.textContent=enviando?"Enviando…":segundos?"Reenviar em "+segundos+"s":automaticos.has(chave)?"Reenviar código":"Enviar código";
    enviarBtn.setAttribute("aria-label",enviarBtn.textContent);
    enviarBtn.setAttribute("aria-busy",String(enviando));
    enviarBtn.setAttribute("data-disabled-reason",enviando?"Aguarde o envio do código.":segundos?"Aguarde "+segundos+" segundos antes de reenviar.":"Conclua a verificação em andamento.");
    inputs.forEach(i=>i.disabled=!enviado||conferindo||concluido||enviando);
    confirmarBtn.disabled=!enviado||conferindo||concluido||!/^[0-9]{6}$/.test(codigo());
    confirmarBtn.textContent=conferindo?"Verificando…":"Confirmar código";
    confirmarBtn.setAttribute("aria-busy",String(conferindo));
    confirmarBtn.setAttribute("data-disabled-reason",conferindo?"Aguarde a conferência do código.":!enviado?"Aguarde o envio do código para este e-mail.":"Preencha os 6 dígitos do código recebido.");
  }
  function iniciarTimer() { clearInterval(timer);timer=setInterval(atualizar,1000); }
  function focar() { if(aberto()&&!inputs[0].disabled)(inputs.find(i=>!i.value)||inputs[0]).focus(); }
  async function enviarCodigo() {
    if(!usuario||enviando||conferindo||concluido||agora()<proximoEnvio)return;
    const versao=revisao,atual=usuario;
    enviando=true;enviado=false;erro.textContent="";status.textContent="Enviando o código…";atualizar();
    try {
      await enviar(atual.id);
      if(versao!==revisao)return;
      enviado=true;expiraEm=agora()+5*60*1000;ultimoCodigo="";
      inputs.forEach(i=>i.value="");proximoEnvio=agora()+30000;
      status.textContent="Código enviado. Confira sua caixa de entrada.";
    } catch(e) {
      if(versao!==revisao)return;
      erro.textContent=e.message||"Não foi possível enviar o código. Tente novamente.";
      status.textContent="";
      if(e.status===429)proximoEnvio=agora()+Math.max(30,Math.min(3600,Number(e.espera)||30))*1000;
    } finally {
      if(versao===revisao){enviando=false;atualizar();if(aberto()){iniciarTimer();focar();}}
    }
  }
  async function conferirCodigo(manual=false) {
    const valor=codigo();
    if(!usuario||!enviado||enviando||conferindo||concluido||!/^[0-9]{6}$/.test(valor)||(!manual&&valor===ultimoCodigo))return;
    if(agora()>=expiraEm){erro.textContent="O código expirou. Solicite outro código.";return;}
    const versao=revisao,atual=usuario;
    conferindo=true;ultimoCodigo=valor;erro.textContent="";status.textContent="Verificando o código…";atualizar();
    try {
      const resposta=await confirmar(atual.id,valor);
      if(versao!==revisao)return;
      concluido=true;fechar();await aoConfirmar(resposta);
    } catch(e) {
      if(versao!==revisao)return;
      erro.textContent=e.message||"Não foi possível verificar o código. Tente novamente.";
      status.textContent="";
    } finally { if(versao===revisao){conferindo=false;atualizar();if(!concluido)focar();} }
  }
  function fechar() { clearInterval(timer);modal.classList.remove("open"); }
  function abrir(atual) {
    if(!atual?.id||atual.verificado)return;
    const nova=String(atual.id)+":"+atual.email;
    if(nova!==chave){
      revisao++;chave=nova;usuario=atual;enviado=false;concluido=false;enviando=false;conferindo=false;
      ultimoCodigo="";proximoEnvio=0;expiraEm=0;inputs.forEach(i=>i.value="");erro.textContent="";status.textContent="";
    }
    modal.classList.add("open");alvo.textContent=atual.email;atualizar();iniciarTimer();
    if(!automaticos.has(chave)){automaticos.add(chave);void enviarCodigo();}else focar();
  }
  iniciarCodigoVerificacao(inputs,()=>{atualizar();if(aberto())void conferirCodigo();});
  enviarBtn.addEventListener("click",()=>void enviarCodigo());
  confirmarBtn.addEventListener("click",()=>void conferirCodigo(true));
  modal.addEventListener("click",e=>{if(e.target===modal)fechar();});
  return {abrir,fechar,destruir(){revisao++;clearInterval(timer);}};
}
