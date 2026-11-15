# Estado atual do projeto

> Snapshot para retomar o trabalho em outra sessão sem depender do histórico do chat.
> Última atualização: 2026-11-15.

## Status em uma frase

MVP funcional em modo **mock**: gera plano de aula `.docx` e caderno de
atividades `.pptx` para Educação Infantil, com códigos da BNCC validados.
O provedor real de IA ainda **não foi testado** com uma chave de API.

## O que existe

| Módulo | Responsabilidade |
|---|---|
| `data/bncc/bncc_ei.csv` | 93 objetivos de Educação Infantil extraídos do PDF oficial |
| `data/bncc/mapeamento_escolar.csv` | Correspondência institucional: Berçário, Maternal, Pré I, Pré II |
| `scripts/extrair_bncc_ei.py` | Extrai os 93 objetivos do PDF e gera o CSV |
| `scripts/validar_bncc.py` | Valida contagem, códigos, campos e textos |
| `app/bncc.py` | Consulta em memória por grupo, campo e palavra |
| `app/contract.py` | Contrato Pydantic e resolução dos códigos na base |
| `app/llm.py` | Cliente mock e cliente OpenAI-compatível |
| `app/pipeline.py` | Pedido → candidatos → IA → validação → documentos |
| `app/render_docx.py` | Plano de aula em `.docx` A4 editável |
| `app/render_pptx.py` | Caderno de atividades em `.pptx` A4 editável |
| `app/storage.py` | Histórico em SQLite e arquivos em `storage/` |
| `app/main.py` | Aplicação FastAPI: gerar, consultar BNCC, histórico, download |
| `app/templates/` | Páginas HTML server-rendered |
| `app/static/style.css` | Estilo da aplicação |
| `prompts/system.md` | Prompt de sistema com as regras pedagógicas e de BNCC |
| `prompts/few_shot.md` | Contrato destilado dos dois modelos de referência |
| `prompts/schema_pacote.json` | JSON Schema do pacote gerado |
| `tests/` | 19 testes automatizados |
| `docs/` | Escopo, roteiro de teste, dor/validação, decisões e este snapshot |

## Números atuais

- **Base BNCC:** 93 linhas, todas com `revisado=S`.
  - Grupos: `EI01` 29, `EI02` 32, `EI03` 32.
  - Campos: `EO` 20, `CG` 15, `TS` 9, `EF` 27, `ET` 22.
- **Testes:** 19 passando (`python3 -m pytest -q`).
- **Plano:** 7 seções, 4 campos de experiência, objetivos Pré I/Pré II.
- **Caderno:** capa + 5 atividades, cada uma com código BNCC e campo.
- **Modelos de referência:** 2 (plano `.docx` e caderno `.pptx`).
- **Gerações de demonstração:** pastas em `storage/geracoes/`.
- **Tamanho do código:** aproximadamente 3.900 linhas em `app/`, `scripts/`,
  `tests/`, `prompts/` e `docs/`.

## Comandos

```bash
# ambiente
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# base da BNCC
python3 scripts/extrair_bncc_ei.py
python3 scripts/validar_bncc.py

# aplicação
python3 -m uvicorn app.main:app --reload
# abra http://127.0.0.1:8000

# geração por linha de comando
python3 -m app.pipeline --tema "Meu nome, minha identidade" --uso "Pré II" --provider mock

# consulta rápida
python3 -m app.bncc --texto "nome"
python3 -m app.bncc --uso "Pré II" --campo EF

# testes
python3 -m pytest -q
```

## Ambiente observado em 2026-11-15

- macOS (darwin), Python 3.10.1.
- `pymupdf` 1.28.2
- `python-docx` 1.2.0
- `docxtpl` 0.20.2 (instalado, mas os renderizadores atuais usam `python-docx` direto)
- `python-pptx` 1.0.2
- `fastapi` 0.138.0
- `pydantic` 2.13.4
- `jinja2` 3.1.6
- `pytest` 9.1.1
- `uvicorn` 0.49.0
- `python-multipart` 0.0.32
- `httpx` instalado (usado pelo cliente de IA e pelo TestClient)

As versões acima são um retrato do ambiente, não um lockfile.

## Como retomar

1. Ler este arquivo e `docs/decisoes.md`.
2. Rodar `python3 scripts/validar_bncc.py` e `python3 -m pytest -q`.
3. Se for testar IA real, copiar `.env.example` para `.env` e preencher
   `LLM_API_KEY` (e, se necessário, `LLM_BASE_URL` e `LLM_MODEL`).
4. Conferir as gerações em `storage/geracoes/`.
5. Revisar o documento interno de dor/validação (não versionado) antes de
   decidir o próximo incremento.

## Limitações conhecidas

- Só Educação Infantil (93 códigos). Fundamental I não entrou.
- Caderno com 5 atividades fixas.
- Sem exportação em PDF.
- Contrato extraído de 2 modelos; os outros 8 não chegaram.
- O modo mock é ilustrativo; não mede qualidade pedagógica.
- Nenhuma integração com o "sistema próprio" do cliente.
- Sem revisão pedagógica, login, pagamento ou multiusuário.
- Provedor real de IA não exercitado neste ambiente.

## Riscos abertos

| Risco | Estado |
|---|---|
| Construir para a dor errada | Não validado com o cliente |
| Fundamental I ser a prioridade | Não confirmado |
| Contrato incompleto (2 de 10 modelos) | Aberto |
| Qualidade real da IA | Não medida |
| Custo por pacote | Não medido |
| Integração com o sistema do cliente | Não especificada |
| Ilustrações para outros temas | Não resolvido |

## Próximos passos

1. Entrevista de validação com o cliente (documento interno, não versionado).
2. Lote real de 3 a 5 temas com provedor real.
3. Comparação estruturada com os 2 modelos.
4. Amostra de Fundamental I, mesmo manual, para medir prioridade.
5. Definir o contrato de integração com o sistema próprio.
6. Só então decidir o próximo incremento.
