# Layout dos documentos

Os arquivos `.docx` e `.pptx` **não** usam um template estático com
`{{variáveis}}`. Eles são montados em código, com os mesmos elementos nativos
do Word e do PowerPoint, para manter tudo editável:

- Plano: `app/render_docx.py`
- Caderno: `app/render_pptx.py`

Os modelos de referência da instituição ficam localmente em
`exemplos base_inicial/` (pasta **não versionada**; plano `.docx` e caderno
`.pptx`).

## Paleta usada

| Cor | Código |
|---|---|
| Azul | `2D9CDB` |
| Azul escuro | `1B6CA8` |
| Laranja | `F2683C` |
| Verde | `4CAF73` |
| Roxo | `9B6DD6` |
| Rosa | `F45B9C` |
| Amarelo | `FDC22D` |
| Cinza claro | `F4F5F8` |
| Texto | `2E2E3A` |

## Onde mudar

- Cores e fontes: constantes no topo de `app/render_docx.py` e
  `app/render_pptx.py`.
- Estrutura das seções do plano: `render_plano` em `app/render_docx.py`.
- Tipos de atividade do caderno: funções `_conteudo_*` em `app/render_pptx.py`.
- Conteúdo: vem do contrato em `app/contract.py`, nunca do layout.

## Por que não usar Google Docs/Slides

Gerar os arquivos localmente é determinístico, testável e não depende de conta,
permissão ou cota de terceiros. O professor recebe um arquivo que abre no Word
e no PowerPoint sem conversão.
