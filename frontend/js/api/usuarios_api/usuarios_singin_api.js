
export async function criar_usuario(usuario,email,senha) {
  const response = await fetch('http://127.0.0.1:5000/usuarios/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      "nome":usuario,
      "email":email,
      "senha":senha
    })
  });
  
  const resultado = await response.json();
  
  return resultado
}