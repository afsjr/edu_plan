# Estado atual do projeto

> Snapshot para retomar o trabalho sem depender do histórico do chat.
> Última atualização: 2026-11-15.

## Status em uma frase

MVP em **duas etapas**: código BNCC → plano → validação do professor →
atividades. Funciona de ponta a ponta em modo **mock estrutural**. O provedor
OpenAI está implementado, mas ainda **não foi exercitado** neste ambiente.

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
| `data/bncc/mapeamento_escolar.csv` | Berçário, Maternal, Pré I, Pré II |
| `data/icons/icones.csv` | Biblioteca provisória de ícones/emoji |
| `scripts/extrair_bncc_ei.py` | Extrai os 93 objetivos do PDF oficial |
| `scripts/validar_bncc.py` | Valida contagem, códigos, campos e textos |
| `app/bncc.py` | Consulta e seleção do âncora + 6 relacionados |
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
| `tests/` | 37 testes automatizados |
| `docs/` | Estado, decisões, escopo, teste, questionário e provedores |

## Números atuais

- Base BNCC: 93 linhas, todas `revisado=S`; grupos 29/32/32.
- Plano: 10 seções, 7 códigos, 4 campos, 7 momentos, 6–8 recursos.
- Caderno: capa + 5 atividades + nota de cobertura.
- Tipos de atividade: 8 (`cobrir_palavra`, `ligar`, `contar`, `colorir`,
  `completar`, `desenhar`, `labirinto`, `recortar_colar`).
- Ícones/emoji: ~80 chaves provisórias.
- Testes: 37 passando.
- Sanitização: ícone fora da biblioteca vira `•`; texto com caracteres CJK é
  rejeitado e entra no loop de reparo.
- Imagem em runtime: Cloudflare FLUX, 1 por pacote, base64 no JSON; fallback
  para ícone/emoji.

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
- O verificador com `gpt-4o-mini` ainda será ligado; o determinístico já roda.

## Limitações conhecidas

- Só Educação Infantil (93 códigos). Fundamental I não entrou.
- OpenAI não testado neste ambiente; o mock não mede qualidade pedagógica.
- Os modelos do cliente são por tema; o fluxo por código é uma decisão de produto.
- Sem PDF, login, pagamento ou multiusuário.
- Sem histórico no web/Vercel; o plano JSON fica no navegador entre as etapas.
- A imagem em runtime é 1 por pacote e não é usada em contagem/letras.
- A biblioteca estática de PNG/SVG ainda não foi criada.
- Os 8 tipos de atividade são templates; alguns temas vão exigir ajuste.
- O verificador LLM (`gpt-4o-mini`) está previsto, mas ainda não implementado.

## Próximos passos

1. Configurar OpenAI e rodar um lote real de 3 códigos.
2. Comparar com os 2 modelos do cliente.
3. Ligar o verificador LLM + reparo.
4. Rodar o questionário do cliente (`docs/questionario_cliente.md`).
5. Decidir Fundamental I, imagens e PDF.
