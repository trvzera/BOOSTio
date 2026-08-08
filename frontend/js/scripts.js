// Ponto de entrada carregado em todas as páginas.
// Cada comportamento vive no seu próprio módulo — veja header.js e services-carousel.js.
import "./header.js";
import "./services-carousel.js";
import {confirmaLogin} from "./api/auth_api/me_auth.js"
import {fazerLogout} from "./api/auth_api/logout_auth.js"

const menuComLogin = document.querySelector("#profile-nav-list-logado")
const menuSemLogin = document.querySelector("#profile-nav-list-deslogado")

const btnSair = document.querySelector("#btn-sair")

async function confirmaUsuario(){
  const resposta = await confirmaLogin()
  //Se a resposta do flask em relacao ao usuario logado for false,redireciono para login
  console.log(resposta)
  if (!resposta.auth){
    menuComLogin.style.display = "none"
    menuSemLogin.style.display = "block"
  }
  else{
    menuComLogin.style.display = "block"
    menuSemLogin.style.display = "none"
  }
}

window.addEventListener('load',() =>{
 confirmaUsuario()
})

async function sairSessao(){
  const resposta = await fazerLogout()
  console.log(resposta.mensagem)
}

btnSair.addEventListener('click',()=>{
  sairSessao()
  window.location.href = "./pages/login.html";
})

