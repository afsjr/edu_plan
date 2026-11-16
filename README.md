# Plano de Aula BNCC — MVP interno

Ferramenta interna para gerar um **plano de aula** e um **caderno de atividades**
a partir de um **código da BNCC**, com foco em Educação Infantil (Pré I e Pré II).

O professor escolhe a turma e o código âncora. O sistema busca mais 6 códigos
na base, monta o plano, o professor valida e só então as atividades são geradas.
Tudo sai em `.docx` e `.pptx` editáveis.

## Regra principal

- Códigos e descrições vêm **somente** de `data/bncc`.
- A IA não escreve a descrição oficial da BNCC; o sistema injeta o texto do CSV.
- Se o código não existir na base, a resposta é:
  **"não possuo esta informação na minha base de dados"**.
- Nada é inventado.

## O que o sistema faz

1. Professor escolhe **turma** (Pré I/Pré II) e **1 código âncora**.
2. O sistema seleciona **6 códigos relacionados** na base: mesmo campo primeiro,
   depois outros campos da mesma turma, até **7 códigos e 4 campos**.
3. Gera o plano com **10 seções**, 7 códigos, 4 campos, 7 momentos e 6–8 recursos.
4. O professor baixa o `.docx` e clica em **Validar plano**.
5. Só depois da validação o sistema gera as **5 atividades** a partir do plano.
6. O `.pptx` termina com a **nota de cobertura**: o que do plano não foi
   trabalhado e o que foi acrescentado como sugestão.
7. Opcionalmente, **1 imagem do tema** é gerada via Cloudflare e entra no slide
   da atividade, com fallback para ícone/emoji.

## Início rápido

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

python3 scripts/validar_bncc.py
python3 -m uvicorn app.main:app --reload
```

Abra `http://127.0.0.1:8000`, escolha a turma e o código.

## IA

Sem `LLM_API_KEY`, a aplicação usa o **mock estrutural** (sem custo). Para o
material real:

```env
LLM_PROVIDER=openai-compativel
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o
LLM_API_KEY=...
```

O mesmo cliente aceita qualquer endpoint compatível com OpenAI. O Groq é uma
alternativa gratuita; veja `docs/groq.md`.

### Imagem em runtime

Com `IMAGE_PROVIDER=cloudflare` e as chaves `CLOUDFLARE_ACCOUNT_ID` /
`CLOUDFLARE_API_TOKEN`, o sistema gera **1 imagem por pacote** (FLUX.1 Schnell),
embutida em base64 no JSON do caderno. `IMAGE_MAX` controla o limite (padrão 1).
Detalhes em `docs/cloudflare.md`.

## Deploy no Vercel

O fluxo é **sem estado**: o plano JSON fica no formulário entre as duas etapas;
os downloads são re-renderizados a partir do JSON. Não há SQLite nem disco.

```bash
npx vercel login
npx vercel --prod
```

Configure `LLM_PROVIDER`, `LLM_BASE_URL`, `LLM_MODEL` e `LLM_API_KEY` no painel.
Passo a passo em `docs/vercel.md`.

## Linha de comando

```bash
python3 -m app.pipeline --codigo EI03EF01 --uso "Pré II" --provider mock
```

## Testes

```bash
python3 -m pytest -q
```

A suíte cobre a seleção dos 7 códigos, o contrato, a nota de cobertura, os
renderizadores e o fluxo HTTP completo.

## Estrutura

```
data/bncc/       bncc_ei.csv, mapeamento_escolar.csv, README.md
data/icons/      icones.csv, README.md
scripts/         extrair_bncc_ei.py, validar_bncc.py
prompts/         system_plano.md, system_atividades.md, schemas
app/             bncc.py, contract.py, llm.py, pipeline.py
                 render_docx.py, render_pptx.py, main.py
app/templates/   páginas HTML
app/static/      style.css
templates/       README sobre o layout dos documentos
tests/           testes automatizados
docs/            estado atual, decisões, escopo, teste, questionário e provedores
pyproject.toml   dependências de runtime e entrypoint do Vercel
vercel.json      configuração do deploy
.vercelignore    o que não sobe para o Vercel
storage/         histórico local do CLI (não versionar)
```

## Limitações atuais

- Só Educação Infantil (93 códigos). Fundamental I não entrou.
- O fluxo por código é uma decisão de produto; os modelos do cliente são por tema.
- O provedor OpenAI ainda não foi exercitado neste ambiente.
- O mock é estrutural: não mede qualidade pedagógica.
- Sem PDF, login, pagamento ou multiusuário.
- Os 8 tipos de atividade são templates genéricos; alguns temas vão precisar de ajuste.
- A imagem em runtime é 1 por pacote e não é usada em contagem/letras.
- A biblioteca estática de PNG/SVG ainda não foi criada.

## Documentação

- [`docs/handoff.md`](docs/handoff.md) — passagem de sessão e próximos passos.
- [`docs/estado_atual.md`](docs/estado_atual.md) — snapshot técnico.
- [`docs/decisoes.md`](docs/decisoes.md) — decisões e porquês.
- [`docs/escopo_mvp.md`](docs/escopo_mvp.md) — o que entra e o que não entra.
- [`docs/roteiro_teste_cliente.md`](docs/roteiro_teste_cliente.md) — como testar.
- [`docs/questionario_cliente.md`](docs/questionario_cliente.md) — consulta ao cliente (separado do MVP).
- [`docs/vercel.md`](docs/vercel.md), [`docs/groq.md`](docs/groq.md), [`docs/cloudflare.md`](docs/cloudflare.md) — deploy e provedores.

`exemplos base_inicial/` e `docs/dor_e_validacao.md` são mantidos fora do
repositório público.
