# Plano de Aula BNCC — MVP interno

Ferramenta interna para gerar, a partir de um tema, um **plano de aula** em
`.docx` e um **caderno de atividades** em `.pptx`, no formato da instituição e
alinhados à BNCC de Educação Infantil.

O material sai editável (Word e PowerPoint) para o professor corrigir antes de
imprimir. PDF fica para uma etapa futura.

## O que já funciona

- Base da BNCC de Educação Infantil: **93 objetivos** extraídos do PDF oficial.
- Consulta rápida por grupo, campo de experiência e palavra-chave.
- Geração do pacote completo (plano + caderno) em um clique.
- Ícones/emoji na atividade de ligar palavra à letra, com biblioteca editável.
- Validação que **impede código de BNCC inventado** e injeta a descrição oficial.
- Histórico local das gerações.
- Modo **mock** para testar sem chave de API e sem custo.

## Início rápido

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python3 scripts/extrair_bncc_ei.py
python3 scripts/validar_bncc.py

python3 -m uvicorn app.main:app --reload
```

Abra `http://127.0.0.1:8000`.

Sem `LLM_API_KEY`, a aplicação usa o modo **mock**: gera um pacote de
demonstração, suficiente para testar o fluxo e a qualidade dos arquivos.

## Modo real de IA

Copie `.env.example` para `.env` e preencha:

```env
LLM_PROVIDER=openai-compativel
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sua-chave
LLM_MODEL=gpt-4o-mini
```

Também funciona com qualquer endpoint compatível com o formato
`/chat/completions` da OpenAI, incluindo o endpoint compatível do Gemini:

```env
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai
LLM_MODEL=gemini-2.5-flash
```

Para forçar o mock: `LLM_PROVIDER=mock`.

## Linha de comando

```bash
python3 -m app.pipeline --tema "Meu nome, minha identidade" --uso "Pré II" --provider mock
```

Os arquivos são gravados em `storage/geracoes/<id>/`.

## Testes

```bash
python3 -m pytest -q
```

A suíte cobre a base da BNCC, o contrato, a resolução de códigos, os
renderizadores `.docx`/`.pptx` e o fluxo HTTP completo.

## Estrutura

```
data/bncc/       bncc_ei.csv, mapeamento_escolar.csv, README.md
data/icons/      icones.csv, README.md
scripts/         extrair_bncc_ei.py, validar_bncc.py
prompts/         system.md, few_shot.md, schema_pacote.json
app/             bncc.py, contract.py, llm.py, pipeline.py
                 render_docx.py, render_pptx.py, storage.py, main.py
app/templates/   páginas HTML
app/static/      style.css
templates/       README sobre o layout dos documentos
tests/           testes automatizados
docs/            estado atual, decisões, dor/validação, escopo e teste
storage/         arquivos gerados (não versionar)
```

## Documentação

O índice completo está em [`docs/README.md`](docs/README.md). Os principais:

- [`docs/estado_atual.md`](docs/estado_atual.md) — snapshot do que existe hoje.
- [`docs/decisoes.md`](docs/decisoes.md) — decisões técnicas e de produto.
- [`docs/escopo_mvp.md`](docs/escopo_mvp.md) — o que entra e o que não entra.
- [`docs/roteiro_teste_cliente.md`](docs/roteiro_teste_cliente.md) — como testar com a professora.
- [`docs/cloudflare.md`](docs/cloudflare.md) — preparação para imagens em runtime.

## Regras de integridade

- A IA só pode escolher códigos que existem na base.
- A descrição oficial da BNCC vem do CSV, nunca da IA.
- Pré I e Pré II usam os mesmos códigos `EI03`; o ano escolar é um campo
  separado.
- O caderno tem **5 atividades** no MVP, com formas e textos editáveis.
- Nenhum dado de aluno é coletado.

## Limitações atuais

- Só Educação Infantil (93 códigos). Fundamental I entra depois.
- O caderno tem 5 atividades fixas (os cinco tipos do modelo).
- O modo mock é ilustrativo; a qualidade final depende do provedor real.
- O contrato foi extraído de **2 modelos**. Os outros 8 vão refiná-lo.
- Sem login, pagamento ou multiusuário.
- Sem PDF nesta fase.

## Próximos passos

1. Rodar a validação da dor com o cliente (documento interno, não versionado).
2. Rodar o roteiro de teste com a professora (`docs/roteiro_teste_cliente.md`).
3. Coletar os outros 8 modelos e ajustar o contrato.
4. Incluir Fundamental I (528 códigos) e, se necessário, busca semântica.
5. Exportação em PDF.
6. Quantidade variável de atividades.
