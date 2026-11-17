# Estado atual do projeto

> Snapshot para retomar o trabalho sem depender do histórico do chat.
> Última atualização: 2026-11-16.

## Status em uma frase

MVP em **duas etapas**: código BNCC → plano → validação do professor →
atividades. O provedor real está ativo com **OpenAI `gpt-4o`** no plano e no
verificador. O mock fica restrito a testes (`LLM_PROVIDER=mock`); não há
fallback silencioso para mock.

O **Ensino Fundamental I** (574 habilidades) tem base, consulta `/bncc-ef` e
geração em `/fund1`, com prompts dedicados e contrato adaptado. O design system
dos modelos foi extraído para `app/design_tokens.json` e
`_reversa_sdd/design-system/`.

## Fluxo

1. Professor escolhe turma (Pré I/Pré II) e **1 código âncora**.
2. O sistema busca **6 códigos relacionados** em `data/bncc`: mesmo campo
   primeiro, depois outros campos da mesma turma, até **7 códigos e 4 campos**.
3. Gera o plano com **10 seções**, 7 códigos, 6–8 recursos e 7 momentos.
4. O professor baixa o `.docx` e valida.
5. Só depois gera as **5 atividades**, derivadas do plano.
6. O `.pptx` termina com a **nota de cobertura**: códigos/objetivos não
   trabalhados e sugestões extras.

## O que existe

| Módulo | Responsabilidade |
|---|---|
| `data/bncc/bncc_ei.csv` | 93 objetivos de Educação Infantil, com descrição oficial |
| `data/bncc/bncc_ef.csv` | 574 habilidades do Ensino Fundamental I |
| `data/bncc/mapeamento_escolar.csv` | Berçário, Maternal, Pré I, Pré II |
| `data/icons/icones.csv` | Biblioteca provisória de ícones/emoji |
| `scripts/extrair_bncc_ei.py` | Extrai os 93 objetivos do PDF oficial |
| `scripts/validar_bncc.py` | Valida contagem, códigos, campos e textos |
| `scripts/extrair_bncc_ef.py` | Extrai as 574 habilidades do Fund. I do PDF |
| `scripts/validar_bncc_ef.py` | Valida contagem, ciclos, componentes e textos |
| `scripts/extrair_design_system.py` | Extrai tokens dos modelos DOCX/PPTX |
| `app/bncc.py` | Consulta e seleção do âncora + 6 relacionados |
| `app/bncc_ef.py` | Consulta e seleção de códigos do Fundamental I |
| `app/design.py` | Tokens de design e fontes abertas |
| `app/contract.py` | Contrato do plano e do caderno, resolução e validação |
| `app/llm.py` | Mock estrutural e cliente OpenAI/compatível em duas etapas |
| `app/image.py` | Geração de imagem em runtime com Cloudflare/FLUX |
| `app/pipeline.py` | `gerar_plano` → `gerar_atividades` → verificação → imagem |
| `app/render_docx.py` | Plano em `.docx` com as 10 seções |
| `app/render_pptx.py` | Capa + 5 atividades + nota de cobertura |
| `app/main.py` | Duas etapas: código → plano → validar → atividades |
| `app/templates/` | Formulário, plano e atividades |
| `app/static/style.css` | Estilo |
| `prompts/system_plano.md` | Prompt da etapa do plano |
| `prompts/system_atividades.md` | Prompt da etapa das atividades |
| `prompts/schema_plano.json` | Schema da etapa do plano |
| `prompts/schema_caderno.json` | Schema da etapa das atividades |
| `tests/` | 43 testes automatizados |
| `docs/` | Estado, decisões, escopo, teste, questionário e provedores |

## Números atuais

- Base BNCC EI: 93 linhas, todas `revisado=S`; grupos 29/32/32.
- Base BNCC EF: 574 linhas, todas `revisado=S`; ciclos 79/89/94/95/95/31/45/46.
- Plano: 10 seções, 7 códigos, 4 campos, 7 momentos, 6–8 recursos.
- Caderno: capa + 5 atividades + nota de cobertura.
- Tipos de atividade: 8 (`cobrir_palavra`, `ligar`, `contar`, `colorir`,
  `completar`, `desenhar`, `labirinto`, `recortar_colar`).
- Ícones/emoji: ~80 chaves provisórias.
- Testes: 56 passando.
- Sanitização: ícone fora da biblioteca vira `•`; texto com caracteres CJK é
  rejeitado e entra no loop de reparo.
- Imagem em runtime: Cloudflare FLUX, 5 por pacote (uma por atividade), 512 px,
  base64 no JSON; fallback para ícone/emoji.

## Comandos

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

python3 scripts/validar_bncc.py
python3 -m pytest -q

python3 -m uvicorn app.main:app --reload
# http://127.0.0.1:8000

python3 -m app.pipeline --codigo EI03EF01 --uso "Pré II" --provider mock
```

## Provedor de IA

- Sem chave: mock estrutural.
- OpenAI: `LLM_PROVIDER=openai-compativel`, `LLM_BASE_URL=https://api.openai.com/v1`,
  `LLM_MODEL=gpt-4o`, `LLM_API_KEY`.
- O verificador semântico usa `gpt-4o`; o determinístico também roda.

## Qualidade real (2026-11-17)

- EI (`EI03EF01`, `gpt-4o`): 24/24 verificações, 95,8% de correspondência
  estrutural com o modelo, verificador sem avisos.
- Fund. I (`EF01LP01`, `gpt-4o`): 24/24 verificações, 95,2% (referência
  ajustada para 1 bloco de objetivos), verificador sem avisos.
- DOCX: 9 tabelas, 48 parágrafos, 10 seções, capa e fontes abertas.
- PPTX: 6 slides, 5 atividades, 5 tipos, 5 códigos e 5 imagens geradas.

## Limitações conhecidas

- O Fund. I foi validado com LLM real, mas não existe modelo visual de Fund. I
  da instituição; a comparação usa o modelo de EI como referência ajustada.
- O modelo tem 22 imagens no PPTX; a geração usa 5 imagens grandes + ícones/
  emojis. A biblioteca visual estática ainda é a próxima trilha.
- O contrato do Fund. I é uma adaptação: 4 componentes, 1 bloco de objetivos
  (7 itens) e avaliação Inicial/Esperado.
- OpenAI não testado neste ambiente; o mock não mede qualidade pedagógica.
- Os modelos do cliente são por tema; o fluxo por código é uma decisão de produto.
- Sem PDF, login, pagamento ou multiusuário.
- Sem histórico no web/Vercel; o plano JSON fica no navegador entre as etapas.
- A imagem em runtime é 1 por atividade e é ilustrativa; não serve para contar/escrever.
- A biblioteca estática de PNG/SVG ainda não foi criada.
- Os 8 tipos de atividade são templates; alguns temas vão exigir ajuste.
- O verificador semântico (`gpt-4o`) roda após as atividades; se reprovar 3 vezes, entrega com `avisos_qualidade` visíveis.

## Próximos passos

1. Rodar um lote real de 3 códigos de EI e 3 de Fund. I.
2. Comparar lado a lado com os 2 modelos e medir fidelidade visual.
3. Ampliar a biblioteca de ilustrações para reduzir a diferença de 5 vs 22 imagens.
4. Validar o contrato do Fund. I com a professora (4 componentes, 1 ano).
5. Rodar o questionário do cliente (`docs/questionario_cliente.md`).
