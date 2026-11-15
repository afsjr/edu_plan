# Registro de decisões

> Registro no estilo ADR (Architecture Decision Record): o que foi decidido,
> por quê, o que isso custa e o que faria a decisão ser reaberta.
>
> Última atualização: 2026-11-15.

## Como usar

- Antes de mudar uma decisão, leia o item correspondente.
- Se a decisão for reaberta, registre uma nova entrada com data e motivo.
- Não apague decisões antigas: marque como `substituída por D-0XX`.

## Status

| Status | Significado |
|---|---|
| `aceita` | Decisão em vigor. |
| `provisória` | Vale para o MVP; precisa ser reavaliada antes da fase robusta. |
| `a revisar` | Depende de informação que ainda não temos. |
| `substituída` | Não vale mais; aponta para a decisão nova. |

## Resumo

| ID | Decisão | Status |
|---|---|---|
| D-001 | Python como linguagem do MVP | aceita |
| D-002 | Sem n8n no núcleo | aceita |
| D-003 | CSV em memória antes de embedding | aceita |
| D-004 | IA só escolhe código; descrição oficial vem do CSV | aceita |
| D-005 | MVP só Educação Infantil | provisória |
| D-006 | Saídas `.docx`/`.pptx` editáveis, sem PDF | aceita |
| D-007 | Caderno com 5 atividades fixas | provisória |
| D-008 | Sem imagem generativa no MVP | aceita |
| D-009 | Contrato provisório baseado em 2 modelos | a revisar |
| D-010 | Mock por padrão; provedor real via `.env` | provisória |
| D-011 | SQLite + arquivos locais | aceita |
| D-012 | Sem login, pagamento ou multiusuário | aceita |
| D-013 | Mapeamento escolar separado da BNCC | aceita |
| D-014 | Palavras-chave derivadas; objetivo oficial é a fonte | aceita |
| D-015 | Renderizadores em código, não Google Docs/Slides | aceita |
| D-016 | Loader interno de `.env` | aceita |
| D-017 | `strict: false` no JSON Schema do provedor | provisória |
| D-018 | App server-rendered com Jinja2 | provisória |
| D-019 | Tema do demo: "Meu nome, minha identidade" | provisória |

---

## Arquitetura e stack

### D-001 — Python como linguagem do MVP

- **Contexto:** era preciso extrair texto de um PDF de 600 páginas e gerar
  arquivos `.docx` e `.pptx` editáveis, com equipe pequena e prazo curto.
- **Decisão:** Python, com FastAPI, `pymupdf`, `python-docx` e `python-pptx`.
- **Consequência:** uma linguagem só; bibliotecas maduras para PDF e Office;
  aplicação simples de manter.
- **Reabrir se:** o time padronizar TypeScript, ou se houver exigência de um
  front-end separado com build próprio.

### D-002 — Sem n8n no núcleo

- **Contexto:** o sistema precisa evoluir com testes, versionamento e
  refatoração segura. No n8n, a lógica fica espalhada em nós e difícil de
  revisar.
- **Decisão:** núcleo em código; n8n apenas para experimentos e automações
  paralelas.
- **Consequência:** mais código inicial, porém testável e versionável.
- **Reabrir se:** não houver ninguém técnico para manter o código depois.

### D-011 — SQLite + arquivos locais

- **Contexto:** MVP de uso interno, uma pessoa gerando material.
- **Decisão:** histórico em SQLite e arquivos em `storage/`.
- **Consequência:** zero infraestrutura; não serve para multiusuário nem para
  produção distribuída.
- **Reabrir se:** houver mais de um usuário simultâneo ou necessidade de backup
  e retenção gerenciados.

### D-018 — App server-rendered com Jinja2

- **Contexto:** não havia necessidade de SPA nem build de front-end.
- **Decisão:** FastAPI com templates Jinja2 e CSS simples.
- **Consequência:** rápido de manter; menos interativo.
- **Reabrir se:** a experiência precisar de edição em tempo real ou de uma
  interface mais rica.

---

## Dados e BNCC

### D-003 — CSV em memória antes de embedding

- **Contexto:** 93 registros. Busca semântica não era necessária para o teste.
- **Decisão:** CSV + filtros determinísticos em memória. Embedding/pgvector
  quando a base crescer para Fundamental I (~528 códigos) ou quando a busca por
  sentido se mostrar necessária.
- **Consequência:** simples, auditável e rápido; sem infraestrutura de vetores.
- **Reabrir se:** a base crescer muito ou a busca por palavra se mostrar
  insuficiente.

### D-004 — IA só escolhe código; descrição oficial vem do CSV

- **Contexto:** código de BNCC inventado é o erro mais grave para uma escola.
- **Decisão:** o modelo escolhe apenas códigos da lista de candidatos. O sistema
  substitui pela descrição oficial da base antes de montar o documento.
- **Consequência:** fidelidade à BNCC; menos liberdade para a IA. A IA ainda
  escreve os objetivos da aula, mas não a descrição oficial da habilidade.
- **Reabrir se:** nunca para a descrição oficial. Se o cliente quiser uma versão
  resumida, criar um campo separado e explícito, sem substituir o oficial.

### D-013 — Mapeamento escolar separado da BNCC

- **Contexto:** a BNCC organiza por faixa etária (`EI01`, `EI02`, `EI03`), mas a
  escola usa Berçário, Maternal, Pré I e Pré II.
- **Decisão:** a base oficial fica intacta; a correspondência institucional fica
  em `data/bncc/mapeamento_escolar.csv`.
- **Consequência:** dado oficial preservado; um arquivo extra para manter.
- **Reabrir se:** nunca. Manter a separação evita inventar dado na BNCC.

### D-014 — Palavras-chave derivadas; objetivo oficial é a fonte

- **Contexto:** a busca precisava de apoio, mas as palavras-chave não são dado
  oficial.
- **Decisão:** `palavras_chave` é gerada automaticamente; `objetivo` é o texto
  oficial e a fonte de verdade.
- **Consequência:** busca funciona; algumas palavras-chave são fracas.
- **Reabrir se:** a qualidade da busca exigir curadoria manual ou sinônimos.

---

## Produto e escopo

### D-005 — MVP só Educação Infantil

- **Contexto:** o cliente citou Educação Infantil e Fundamental I até o 5º ano,
  mas os dois modelos disponíveis eram de Educação Infantil.
- **Decisão:** o MVP cobre os 93 objetivos de EI. Fundamental I fica para uma
  fase separada, com outra base e outro contrato.
- **Consequência:** teste mais rápido; Fund I continua em aberto.
- **Reabrir se:** o cliente disser que Fund I é a prioridade do teste.

### D-006 — Saídas `.docx`/`.pptx` editáveis, sem PDF

- **Contexto:** o cliente quer editar e corrigir o material depois.
- **Decisão:** entregar Word e PowerPoint editáveis. PDF fica para depois.
- **Consequência:** material corrigível; depende de Word/PowerPoint instalados.
- **Reabrir se:** o teste exigir impressão direta em PDF.

### D-007 — Caderno com 5 atividades fixas

- **Contexto:** o modelo tem 5 atividades; duplicar slides em `python-pptx`
  exige cópia de XML e aumenta o risco.
- **Decisão:** exatamente 5 atividades no MVP.
- **Consequência:** fiel ao modelo; menos flexível.
- **Reabrir se:** temas diferentes exigirem quantidade variável.

### D-008 — Sem imagem generativa no MVP

- **Contexto:** modelos de imagem erram contagem e letras; imagens gastam tinta e
  não são editáveis.
- **Decisão:** usar formas, textos e emojis nativos. Uma biblioteca fixa de
  ícones pode entrar depois.
- **Consequência:** determinístico, editável e barato; menos rico visualmente.
- **Reabrir se:** o cliente exigir ilustrações para temas além do exemplo.

### D-009 — Contrato provisório baseado em 2 modelos

- **Contexto:** só 2 dos 10 modelos foram entregues.
- **Decisão:** contrato versionado a partir desses 2; os outros 8 refinam depois.
- **Consequência:** risco de não cobrir variações de estrutura, ano e atividade.
- **Reabrir se:** os 8 modelos chegarem ou o cliente apontar uma variação.

### D-019 — Tema do demo: "Meu nome, minha identidade"

- **Contexto:** é o tema dos dois modelos disponíveis.
- **Decisão:** focar o demo nesse tema para comparar lado a lado.
- **Consequência:** boa fidelidade ao exemplo; outros temas ainda não provados.
- **Reabrir se:** o cliente quiser testar um tema diferente.

---

## Operação e ambiente

### D-010 — Mock por padrão; provedor real via `.env`

- **Contexto:** era preciso testar o fluxo sem custo e sem chave de API.
- **Decisão:** `MockLLM` por padrão; provedor OpenAI-compatível quando
  `LLM_PROVIDER` e `LLM_API_KEY` estiverem configurados.
- **Consequência:** demo funciona offline; qualidade e custo reais não medidos.
- **Reabrir se:** houver chave disponível para o lote real.

### D-012 — Sem login, pagamento ou multiusuário

- **Contexto:** ferramenta interna, um operador, teste controlado.
- **Decisão:** sem autenticação; acesso controlado pelo ambiente de deploy.
- **Consequência:** simples; não é seguro expor na internet pública.
- **Reabrir se:** o acesso sair do ambiente controlado.

### D-015 — Renderizadores em código, não Google Docs/Slides

- **Contexto:** era preciso determinismo, testabilidade e nenhuma dependência de
  conta externa.
- **Decisão:** montar `.docx` e `.pptx` com `python-docx` e `python-pptx`.
- **Consequência:** layout testável e editável; mais código de layout para manter.
- **Reabrir se:** o cliente exigir fidelidade absoluta a um template específico
  que só exista no Google Docs/Slides.

### D-016 — Loader interno de `.env`

- **Contexto:** evitar uma dependência extra para uma necessidade simples.
- **Decisão:** `app/config.py` lê `.env` com a biblioteca padrão.
- **Consequência:** suficiente para o MVP; sem recursos avançados de dotenv.
- **Reabrir se:** a configuração crescer ou precisar de interpolação.

### D-017 — `strict: false` no JSON Schema do provedor

- **Contexto:** o schema Pydantic tem campos opcionais; o modo estrito da OpenAI
  exige todos os campos em `required`.
- **Decisão:** enviar o schema com `strict: false` e validar a resposta com
  Pydantic.
- **Consequência:** mais compatibilidade entre provedores; menos garantia do lado
  do provedor.
- **Reabrir se:** valer a pena normalizar o schema para o modo estrito.

---

## Nova decisão (modelo)

```markdown
### D-0XX — Título curto

- **Contexto:** o problema ou a restrição que motivou a decisão.
- **Decisão:** o que foi decidido, em uma frase.
- **Consequência:** o que ganhamos e o que perdemos.
- **Reabrir se:** a condição objetiva que faria esta decisão ser revista.
- **Status:** aceita | provisória | a revisar | substituída por D-0YY
```

## Changelog

| Data | Mudança |
|---|---|
| 2026-11-15 | Registro inicial das decisões do MVP. |
