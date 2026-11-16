# Layout dos documentos

Os arquivos `.docx` e `.pptx` são montados em código, com elementos nativos do
Word e do PowerPoint, para manter tudo editável:

- Plano: `app/render_docx.py`
- Caderno: `app/render_pptx.py`

Os modelos de referência da instituição ficam localmente em
`exemplos base_inicial/` (pasta **não versionada**).

## Plano — 10 seções

1. Identificação
2. Campos de experiência
3. Objetivos de aprendizagem (Pré I e Pré II)
4. Habilidades da BNCC (7 códigos)
5. Recursos e materiais (6 a 8)
6. Desenvolvimento da aula (7 momentos)
7. Brincadeira e atividade para casa
8. Avaliação
9. Adaptações e acessibilidade
10. Observações do(a) professor(a)

O título/tema do plano é a descrição oficial do código âncora. O sistema
sobrescreve o título e o tema com o texto verbatim da base.

## Caderno — capa + 5 atividades + nota

- Capa com título, subtítulo, etapa, faixa etária, código âncora e selo BNCC.
- 5 atividades, cada uma com código, campo, objetivo do plano e tipo.
- Tipos: `cobrir_palavra`, `ligar`, `contar`, `colorir`, `completar`,
  `desenhar`, `labirinto`, `recortar_colar`.
- Slide final **"Nota para o professor"** com o que do plano não foi trabalhado
  e o que foi acrescentado como sugestão. O professor pode remover o slide.

## Paleta

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
- Estrutura do plano: `render_plano` em `app/render_docx.py`.
- Tipos de atividade: funções `_conteudo_*` em `app/render_pptx.py`.
- Conteúdo: contrato em `app/contract.py`; nunca no layout.

## Por que não Google Docs/Slides

É determinístico, testável e não depende de conta, permissão ou cota de
terceiros. O professor recebe um arquivo que abre no Word/PowerPoint sem
conversão.
