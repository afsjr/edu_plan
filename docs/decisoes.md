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
| D-020 | Ícones/emoji antes de imagem generativa | aceita |
| D-021 | Biblioteca estática agora; runtime depois | provisória |
| D-022 | Vercel em modo demo one-shot (ZIP, sem histórico) | substituída por D-026 |
| D-023 | Groq free para o texto do teste | substituída por D-028 |
| D-024 | Entrada por código âncora + 6 relacionados | aceita |
| D-025 | 7 códigos, 4 campos, 10 seções e 6–8 recursos | aceita |
| D-026 | Duas etapas: plano → validação → atividades | aceita |
| D-027 | Nota de cobertura no fim do PPT | aceita |
| D-028 | OpenAI gpt-4o para gerar e gpt-4o-mini para verificar | provisória |
| D-029 | 8 tipos genéricos de atividade | aceita |
| D-030 | Sanitização de ícones e texto fora do português | aceita |
| D-031 | Imagem em runtime com Cloudflare, 1 por pacote | substituída por D-034 |
| D-032 | Atividade aponta objetivo por índice; prompt sem descrição BNCC | aceita |
| D-033 | Título curto, sem reticências, a partir da descrição oficial | aceita |
| D-034 | 5 imagens por pacote, 512 px, ilustrativas | aceita |
| D-035 | Atividades variam (temperatura 0.8) e botão de nova versão | aceita |
| D-036 | Verificador semântico gpt-4o-mini + regra campo → tipo | aceita |
| D-037 | Entrega com avisos se o verificador não convergir | aceita |

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

### D-020 — Ícones/emoji antes de imagem generativa

- **Contexto:** o caderno precisa de desenhos na atividade de ligar palavra à
  letra, mas imagem gerada por IA erra contagem, letras e não é editável.
- **Decisão:** usar uma biblioteca de ícones/emoji (`data/icons/icones.csv`) e
  resolver a palavra no renderizador. Imagem gerada por IA fica para depois.
- **Consequência:** determinístico, barato e editável; menos rico visualmente.
- **Reabrir se:** o cliente exigir ilustrações que emoji não representa.
- **Status:** aceita.

### D-021 — Biblioteca estática agora; runtime depois

- **Contexto:** o teste precisa de previsibilidade e custo zero; geração de
  imagem em runtime adiciona chave, latência, falhas e curadoria.
- **Decisão:** manter a biblioteca versionada e pré-revisada. Geração em runtime
  (Cloudflare/Fal/OpenAI) só na fase seguinte.
- **Consequência:** demo sem dependência de API de imagem; expansão exige
  curadoria manual.
- **Reabrir se:** o cliente pedir temas novos com frequência e a curadoria virar
  gargalo.
- **Status:** provisória.

### D-022 — Vercel em modo demo one-shot

- **Contexto:** o Vercel não tem disco persistente; o teste do cliente não
  precisa de histórico.
- **Decisão:** `VERCEL_DEMO=1` gera os dois arquivos em `/tmp`, devolve um ZIP no
  mesmo POST e desativa histórico, resultado e download.
- **Consequência:** deploy simples e público; sem histórico e sem links
  permanentes.
- **Reabrir se:** o cliente pedir histórico ou links persistentes; aí entra
  Blob + Postgres.
- **Status:** provisória.

### D-023 — Groq free para o texto do teste

- **Contexto:** o teste é de baixo volume e o código já impede código de BNCC
  inventado; o custo precisa ser zero nesta fase.
- **Decisão:** usar `openai/gpt-oss-120b` no Groq via endpoint compatível com
  OpenAI, com mock como padrão e chave só no ambiente.
- **Consequência:** custo zero; TPM de 8K aperta uma geração completa e a
  qualidade pedagógica ainda precisa ser validada.
- **Reabrir se:** aparecer `429` com frequência, a qualidade ficar abaixo do
  aceite ou o volume crescer.
- **Status:** provisória.

### D-024 — Entrada por código âncora + 6 relacionados

- **Contexto:** o professor precisa partir de um código oficial, não de um tema
  livre; o modelo do cliente usa 7 códigos no plano.
- **Decisão:** o professor escolhe turma + 1 código âncora; o sistema seleciona
  6 relacionados em `data/bncc`, mesmo campo primeiro, depois mesma turma, até
  7 códigos e 4 campos.
- **Consequência:** tudo ancorado na base; o título/tema vem da descrição
  oficial do âncora.
- **Reabrir se:** o cliente pedir múltiplos códigos simultâneos ou tema livre.
- **Status:** aceita.

### D-025 — 7 códigos, 4 campos, 10 seções e 6–8 recursos

- **Contexto:** o modelo do cliente tem 10 seções, 7 códigos, 4 campos, 8
  recursos e 7 momentos.
- **Decisão:** o plano segue essa estrutura; a avaliação, as adaptações e as
  observações entram como seções 08, 09 e 10.
- **Consequência:** fidelidade ao modelo; planos mais longos.
- **Reabrir se:** o cliente reduzir o formato.
- **Status:** aceita.

### D-026 — Duas etapas: plano → validação → atividades

- **Contexto:** o PPT só pode existir a partir do plano validado pelo professor.
- **Decisão:** o plano é gerado e exibido primeiro; o botão "Validar plano"
  libera a geração das atividades. O plano JSON fica no navegador; sem estado
  no servidor.
- **Consequência:** fluxo fiel ao processo pedagógico; funciona no Vercel sem
  disco nem SQLite.
- **Reabrir se:** for necessário persistir planos entre sessões.
- **Status:** aceita.

### D-027 — Nota de cobertura no fim do PPT

- **Contexto:** o modelo tem 7 códigos e 5 atividades; alguns códigos ficam sem
  atividade, e o professor precisa saber o que não foi trabalhado.
- **Decisão:** o PPT termina com um slide "Nota para o professor" listando
  códigos/objetivos não trabalhados e sugestões extras. O slide é opcional.
- **Consequência:** transparência; o professor decide manter ou remover.
- **Reabrir se:** o cliente não quiser a nota no material final.
- **Status:** aceita.

### D-028 — OpenAI gpt-4o e gpt-4o-mini

- **Contexto:** o mock não serve para validação pedagógica; o Groq free tem TPM
  de 8K e aperta uma geração completa.
- **Decisão:** `gpt-4o` para gerar o plano e as atividades; `gpt-4o-mini` para o
  verificador (a implementar). O cliente continua compatível com outros
  provedores.
- **Consequência:** melhor qualidade e structured outputs; custo maior que o
  mock.
- **Reabrir se:** o custo ou a latência não couberem no piloto.
- **Status:** provisória.

### D-029 — 8 tipos genéricos de atividade

- **Contexto:** o fluxo por código precisa funcionar com temas diferentes; os 5
  tipos do modelo eram específicos de "Meu nome".
- **Decisão:** `cobrir_palavra`, `ligar`, `contar`, `colorir`, `completar`,
  `desenhar`, `labirinto`, `recortar_colar`. O modelo escolhe 5.
- **Consequência:** cobre mais temas; alguns layouts ainda são simples.
- **Reabrir se:** o cliente exigir tipos específicos por campo.
- **Status:** aceita.

### D-030 — Sanitização de ícones e texto fora do português

- **Contexto:** o OpenAI devolveu caracteres chineses e glifos não suportados nos
  campos `icone`; o Word exibiu caracteres estranhos e caixas.
- **Decisão:** o ícone dos campos de experiência vem do mapa oficial
  (`EO`, `CG`, `TS`, `EF`, `ET` no DOCX); o ícone dos recursos é validado contra
  a biblioteca e cai para `•`; o DOCX não usa emojis. Texto com caracteres
  chineses, japoneses ou coreanos é rejeitado e entra no loop de reparo.
- **Consequência:** documento limpo e imprimível; menos emoji no DOCX.
- **Reabrir se:** houver uma biblioteca PNG/SVG própria para os ícones.
- **Status:** aceita.

### D-031 — Imagem em runtime com Cloudflare

- **Contexto:** o cliente espera ilustrações; imagem por IA é barata no
  Cloudflare e não precisa de Blob.
- **Decisão:** FLUX.1 Schnell, 1 imagem por pacote (configurável por
  `IMAGE_MAX`), base64 no JSON do caderno, fallback para ícone/emoji. Sem imagem
  para contagem, letras ou sílabas.
- **Consequência:** imagem sem storage persistente; o JSON cresce ~100–250 KB;
  o download re-renderiza.
- **Reabrir se:** o cliente quiser 2+ imagens, biblioteca estática ou Blob.
- **Status:** substituída por D-034.

### D-032 — Atividade aponta objetivo por índice

- **Contexto:** o modelo copiava a descrição da BNCC em `objetivo_relacionado`,
  em vez de um objetivo do plano; a validação falhava e o reparo era acionado.
- **Decisão:** o prompt das atividades não inclui as descrições da BNCC; cada
  atividade preenche `objetivo_indice` (1 a 8). O resolvedor usa o índice e, se
  faltar, tenta um casamento aproximado com os objetivos do plano.
- **Consequência:** atividades sempre ligadas a um objetivo do plano; menos 400.
- **Reabrir se:** o modelo ainda errar o índice; nesse caso, usar IDs explícitos.
- **Status:** aceita.

### D-033 — Título curto sem reticências

- **Contexto:** o título era um recorte com "…", o que soava amador.
- **Decisão:** usar um trecho **completo** da descrição oficial (até uma vírgula/
  ponto final), sem reticências; a descrição completa fica no plano.
- **Consequência:** capa limpa e profissional; o título pode ter 2–3 linhas.
- **Status:** aceita.

### D-034 — 5 imagens por pacote

- **Contexto:** o cliente quer uma imagem por atividade e não apenas no pacote.
- **Decisão:** `IMAGE_MAX=5`, uma imagem por atividade, 512 px, JPEG comprimido,
  base64 no JSON; imagem ilustrativa, nunca usada para contar/escrever.
- **Consequência:** JSON/página ~1 MB; Cloudflare free (~46 pacotes/dia).
- **Status:** aceita.

### D-035 — Atividades variam

- **Contexto:** com temperatura 0.3, o mesmo plano gerava as mesmas atividades.
- **Decisão:** plano a 0.4 e atividades a 0.8; botão "Gerar outras atividades"
  reaproveita o plano e gera uma nova versão.
- **Consequência:** variação real; o professor pode comparar versões.
- **Status:** aceita.

### D-036 — Verificador semântico e regra campo → tipo

- **Contexto:** uma atividade de ligar palavras foi usada para um objetivo de
  corpo/movimento (`CG`), sem o validador perceber.
- **Decisão:** regra explícita de campo → tipo no prompt; verificador
  `gpt-4o-mini` com reparo automático; se o verificador falhar, segue o
  determinístico.
- **Consequência:** menos atividades desalinhadas; uma chamada extra de IA.
- **Status:** aceita.

### D-037 — Entrega com avisos do verificador

- **Contexto:** o verificador pode reprovar 3 vezes e bloquear a entrega com 400.
- **Decisão:** se a estrutura estiver correta, entregar o último caderno com
  `avisos_qualidade` visíveis na tela; não bloquear o professor.
- **Consequência:** o professor recebe o material e vê o que revisar.
- **Status:** aceita.

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
| 2026-11-15 | Ícones/emoji na atividade de ligar e biblioteca estática (D-020, D-021). |
| 2026-11-15 | Deploy Vercel one-shot e Groq free para o teste (D-022, D-023). |
| 2026-11-15 | Fluxo por código, duas etapas, 10 seções e nota de cobertura (D-024 a D-029). |
| 2026-11-15 | Sanitização de ícones e rejeição de texto CJK (D-030). |
| 2026-11-16 | Imagem em runtime com Cloudflare (D-031). |
| 2026-11-16 | Objetivo por índice e prompt sem descrição BNCC (D-032). |
| 2026-11-16 | Título curto, 5 imagens, variação e verificador (D-033 a D-036). |
| 2026-11-16 | Entrega com avisos do verificador (D-037). |
