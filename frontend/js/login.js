let barra = document.querySelector(".carrega")
let senhaInput = document.querySelector("input")

let caracteres = document.querySelector(".caracteres span")
let maiusculas = document.querySelector(".maiusculas span")
let minusculas = document.querySelector(".caracteres span")
let simbolos = document.querySelector(".caracteres span")
let numeros = document.querySelector(".numeros span")



senhaInput.addEventListener('input',compara)

function compara(){
    let textoInput = senhaInput.value
    let total = 0
    if (textoInput.length >= 8){
        total += 20
        caracteres.style.backgroundcolor = grenn
    }
    if (/[A-Z]/.test(textoInput)){
        total += 20
        caracteres.style.backgroundcolor = grenn
    }
    if (/[a-z]/.test(textoInput)){
        total += 20
        caracteres.style.backgroundcolor = grenn
    }
    if (/\d/.test(textoInput)){
        total += 20
        caracteres.style.backgroundcolor = grenn
    }
    if(/[\^£¢¬§@%&#!$*+?.()|[\]{}\\]/.test(textoInput)){
        total += 20
        caracteres.style.backgroundcolor = grenn
    }

    
    barra.style.width= `${total}%` 
}