<div align="center">
  <img src="./frontend/imgs/logoBOOSTio.gif" alt="BOOSTio" width="100%">
  <h1>BOOSTio</h1>
  <p>Planeje, monte e evolua seu computador em um só lugar.</p>
  <p><strong>Site oficial: <a href="https://boostio.com.br/">boostio.com.br</a></strong></p>
  <p>
    <strong>Python · Flask · SQLAlchemy · JavaScript · HTML · CSS</strong><br>
    Projeto acadêmico · Colégio Cotemig · Em desenvolvimento
  </p>
  <p>
    <a href="#sobre">Sobre</a> ·
    <a href="#funcionalidades">Funcionalidades</a> ·
    <a href="#arquitetura">Arquitetura</a> ·
    <a href="#documentação">Documentação</a>
  </p>
</div>

---

## Sobre

A **BOOSTio** ajuda a escolher componentes de computador considerando objetivo,
orçamento e peças já possuídas. Reúne montagem manual, formulário inteligente,
compatibilidade, comparação de builds, preços e consultas de desempenho.

Desenvolvida como projeto de software anual e final do curso no **Colégio Cotemig**,
a plataforma acompanha o planejamento do primeiro computador e as melhorias de
um setup existente. Conheça a proposta na [página Sobre nós](frontend/pages/sobre.html).

Novas contas recebem um tutorial opcional de três passos. O nível de conhecimento
ajusta as explicações, mantendo todas as ferramentas disponíveis, e pode ser alterado
nas configurações junto do botão para rever o tutorial.

<details>
  <summary>English overview</summary>

BOOSTio is a PC-building platform for planning configurations within a budget,
reusing existing hardware and comparing components. It includes account-based
builds, ready-made configurations, LLM-assisted assembly and expected
gaming/rendering performance from public benchmark sources.

</details>

## Funcionalidades

As 20 funcionalidades obrigatórias do projeto estão implementadas no escopo abaixo. Regras de cada área
(orçamento, builds prontas, desempenho, administração) estão em [docs/funcionalidades.md](docs/funcionalidades.md).
Funcionalidade implementada não equivale a homologação em produção; e-mail depende do SMTP e a geração
inteligente depende da LLM.

| Nº | Requisito | Status | Escopo atual |
| --- | --- | --- | --- |
| 01 | O sistema deve permitir ao usuário criar sua conta e fazer login | ✅ **Implementado** | Cadastro, autenticação, logout e sessão. Código de e-mail enviado ao iniciar a verificação e conferido ao completar seis dígitos; vínculo Google explícito no perfil, com confirmação de identidade. |
| 02 | O sistema deve permitir ao usuário cadastrar seu setup atual | ✅ **Implementado** | Definir ou remover uma build como computador atual. |
| 03 | O sistema deve permitir ao usuário pesquisar compatibilidade e peças | ✅ **Implementado** | Catálogo por categoria e diagnóstico durante a montagem, com as limitações do requisito 13. |
| 04 | O sistema deve permitir ao usuário montar seu setup atual através de formulário | ✅ **Implementado** | Geração por LLM com orçamento, peças próprias identificadas pelo catálogo, preferências opcionais de gabinete/cor, ventilação obrigatória (contando fans inclusas) e uma revisão automática de saídas inválidas antes de salvar. |
| 05 | O sistema deve permitir ao usuário salvar configurações de computadores feitas | ✅ **Implementado** | Builds persistidas na conta, inclusive incompletas, com salvamento automático e avisos de falha. |
| 06 | O sistema deve permitir ao usuário excluir configurações salvas no perfil | ✅ **Implementado** | Exclusão com verificação de proprietário e tranca. |
| 07 | O sistema deve permitir ao usuário comparar configurações salvas | ✅ **Implementado** | Duas ou três builds: preços, componentes, consumo e renderização no Blender. FPS é uma ampliação pendente, não uma condição da comparação atual. |
| 08 | O sistema deve permitir ao usuário compartilhar suas configurações por link | ✅ **Implementado** | Builds públicas podem ser vistas sem login, somente leitura. Testar exige sessão; salvar uma cópia privada exige também e-mail verificado e vaga na conta. |
| 09 | O sistema deve permitir ao usuário buscar melhorias do seu setup | ✅ **Implementado** | RAM: acrescentar ou substituir pentes conforme a placa-mãe. SSD/HD: expandir quantidades mantendo os atuais, respeitando conexões/baias conhecidas, ou substituir sem regressões verificáveis. Orçamento obrigatório para aplicar; CPU/GPU e outras categorias dependem de métricas confiáveis. |
| 10 | O sistema deve permitir ao usuário ver configurações prontas | ✅ **Implementado** | 16 modelos sem periféricos, referências revisadas no catálogo, filtro de budget e preço crescente. A cópia respeita e-mail verificado e limite da conta. |
| 11 | O sistema deve permitir ao usuário editar e modificar configurações salvas | ✅ **Implementado** | Alteração de componentes, nome, descrição e orçamento; desfazer/refazer até 25 alterações de peças nesta visita ao editor, por botões ou Ctrl/Cmd+Z e Ctrl/Cmd+Shift+Z. Campos de texto mantêm o desfazer nativo. |
| 12 | O sistema deve permitir ao usuário verificar o preço da peça direto pelo site, sem precisar consultar em diversas abas | ✅ **Implementado** | Preços cadastrados, data quando disponível e links das lojas. Antes da compra, o catálogo é reconsultado e diferenças/indisponibilidade são mostradas. Não inclui frete nem garante o valor no checkout. |
| 13 | O sistema deve permitir ao usuário ver todas as informações de compatibilidade e consumo de energia do setup que está montando | ✅ **Implementado** | Diagnóstico da build, consumo estimado e fichas técnicas conforme os dados cadastrados. Conflitos ficam em destaque; conferências e dicas são agrupadas por assunto, com detalhes recolhidos. Referências visuais de fans são identificadas como estimativas e não aprovam encaixes. Ampliar a cobertura de modelos permanece uma melhoria de catálogo. |
| 14 | O sistema deve permitir ao usuário adicionar ao setup periféricos, que muitas vezes não pensado anteriormente, acaba estourando o orçamento | ✅ **Implementado** | Inclusão e reaproveitamento com tetos separados para PC e periféricos. |
| 15 | O sistema deve permitir ao usuário registrar em seu perfil o seu budget, assim fica registrado o seu dinheiro disponível para comprar e futuras melhorias | ✅ **Implementado** | Valor e autorização usados no formulário e em novas montagens manuais, sem alterar builds existentes. |
| 16 | O sistema deve permitir ao usuário baixar a build em JSON e CSV para ter o arquivo local | ✅ **Implementado** | Exportação para guardar a configuração localmente. |
| 17 | O sistema deve permitir ao usuário alterar a visibilidade da build | ✅ **Implementado** | Alternância entre pública e privada. |
| 18 | O sistema deve permitir ao usuário duplicar a sua build | ✅ **Implementado** | Cópia independente, respeitando o limite da conta. |
| 19 | O sistema deve permitir ao usuário definir um nome e descrição para a build | ✅ **Implementado** | Identificação e edição dos detalhes da build. |
| 20 | O sistema deve permitir ao usuário importar builds por meio de arquivos CSV ou JSON | ✅ **Implementado** | Validação do arquivo e criação de uma configuração na conta. |

## Arquitetura

```text
Frontend → Controller → Service → Model → Banco
                           └────→ Repository (consultas que não são CRUD)
```

- [Controllers](backend/controllers/): recebem a requisição, chamam **um** service e devolvem JSON.
- [Services](backend/services/): um caso de uso por arquivo (`executar`), com validações, regras e integrações externas.
- [Models](backend/models/): entidades SQLAlchemy e o CRUD da própria tabela.
- [Repositories](backend/repositories/): consultas especiais que vão além do CRUD.
- [Frontend](frontend/): páginas HTML/CSS e módulos JavaScript que consomem a API.

O diagrama de classes está em [docs/diagrama-classes.png](docs/diagrama-classes.png) (fonte em
[DOT](docs/diagrama-classes.dot)). A arquitetura segue o repositório de referência da disciplina e o que
ainda foge dela está em [docs/arquitetura.md](docs/arquitetura.md).

## Documentação

- [docs/funcionalidades.md](docs/funcionalidades.md): o que o sistema faz e as regras de cada área.
- [docs/arquitetura.md](docs/arquitetura.md): regra de camadas e pendências de arquitetura.

---

<div align="center">
  <strong>Projeto acadêmico em desenvolvimento</strong><br>
  Funcionalidades implementadas não equivalem a homologação em produção.
</div>

[Apresentação da BOOSTio](https://docs.google.com/presentation/d/1T8IafJe7wyfnaIWoAmYwfCx_qvOP4aw2x5slewX20uo/edit)
