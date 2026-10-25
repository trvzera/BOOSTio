# Revisão para publicação — 25/10/2026

## Resultado local

Conflitos de `.dockerignore`, `.gitignore` e `Dockerfile.api` resolvidos preservando as exclusões de segredos, testes, materiais internos e `frontend/coletados`. O modelo `.env.production.example` permanece versionável.

Werkzeug atualizado de 3.1.8 para 3.1.9 para eliminar PYSEC-2026-4312 (GHSA-g6x2-hccm-hh4m). O aviso trata de nomes de dispositivos Windows em `safe_join`; não é evidência de exploração na implantação Linux.
Referência: https://github.com/pallets/werkzeug/security/advisories/GHSA-g6x2-hccm-hh4m

Validação após a atualização:

- Backend: 784 testes e 20 subtestes passaram. Há avisos de APIs obsoletas de SQLAlchemy e Flask-Login.
- Frontend: 587 testes passaram.
- `pip-audit -r requirements.txt`: nenhuma vulnerabilidade conhecida encontrada, incluindo a resolução de dependências transitivas no ambiente da auditoria.
- Registro npm, endpoint de auditoria bulk: nenhum aviso para `lottie-web` 5.13.0, única dependência do lock.
- Busca por padrões de chaves privadas, Google API/OAuth e tokens GitHub nos arquivos de texto versionados atuais: nenhum resultado. Não constitui auditoria do histórico Git nem de todos os formatos de segredo.
- `.env.production` e `backend/.env` são ignorados por Git; o primeiro não existe neste checkout.

O código revisado possui CSRF, cookies Secure/HttpOnly em produção, CORS restrito, validação de Host, limites com Redis e validação das variáveis obrigatórias. O Compose não publica portas dos serviços diretamente no host. Isso não certifica a segurança da VPS nem substitui testes no ambiente público.

## Pendências para liberar a publicação

1. Na VPS, preencher `.env.production` a partir do exemplo, com segredos próprios de produção, e aplicar `chmod 600`. Não reutilizar nem publicar o `.env` de desenvolvimento.
2. Confirmar DNS dos dois domínios, rede `traefik-proxy`, resolvedor `letsencrypt`, redirecionamento HTTP para HTTPS no Traefik e firewall permitindo somente as portas públicas necessárias. Conferir o número de proxies e o IP real usado pelo rate limit.
3. Registrar no Google OAuth o callback `https://api.boostio.com.br/auth/google/entrar` e conferir a disponibilidade do aplicativo OAuth para os usuários pretendidos.
4. Construir as imagens e iniciar MySQL/Redis. Em banco novo, executar `banco-preparar` e `pecas-popular` conforme `configuracao-producao.md`. Se houver dados que precisem sair do SQLite local, planejar a transferência: esse comando não os importa. Em MySQL existente, usar migração específica com backup; o comando de preparação recusa tabelas existentes.
5. Subir API/frontend e validar saúde, login por senha/Google, verificação e recuperação por e-mail, sessão, ações com CSRF, geração de builds e persistência das imagens após recriar os containers.
6. Agendar backup fora da VPS e testar restauração do MySQL e das imagens coletadas. Agendar a atualização de preços se desejada.

Atualização após instalar Docker: imagens construídas e stack isolada validada com Python 3.12, Gunicorn, Nginx, MySQL 8.4 e Redis reais. Cadastro/login, permissões, CSRF/CORS, builds, persistência e restauração do banco passaram. Foram corrigidos o redirecionamento do Nginx, um teste dependente do .env privado e o pip vulnerável herdado da imagem base. Veja `testes-docker.md`. Traefik, HTTPS público, credenciais reais e integrações externas continuam pendentes na VPS.

## Melhorias adicionais

Avaliar CSP compatível com scripts, estilos e imagens do site; atualmente não há CSP configurada no Nginx/labels do Compose. A API roda como root na imagem atual: reduzir privilégios exige também preparar as permissões do volume de imagens. Fixar versões/digests das imagens e automatizar novas auditorias evita depender apenas da checagem pontual de hoje. Essas melhorias não foram usadas como substituto dos testes reais de implantação.
