# Base BNCC — Educação Infantil

Base estruturada dos objetivos de aprendizagem e desenvolvimento da Educação
Infantil, extraída do documento oficial da BNCC.

## Fonte

- Arquivo: `exemplos base_inicial/BNCC_EI_EF_110518_versaofinal_site.pdf`
- Seção: Educação Infantil, tabelas detalhadas (páginas 47 a 54 do PDF)
- Documento: Base Nacional Comum Curricular, versão final de 2018
- Escopo desta base: apenas Educação Infantil (93 códigos `EI01`, `EI02`, `EI03`)
- O PDF **não é versionado** no repositório; o artefato versionado é o CSV gerado.
  O script de extração espera o PDF localmente em `exemplos base_inicial/`.

## Arquivos

| Arquivo | Conteúdo |
|---|---|
| `bncc_ei.csv` | 93 linhas, uma por objetivo de aprendizagem e desenvolvimento |
| `mapeamento_escolar.csv` | Correspondência institucional entre grupo etário da BNCC e uso escolar (Berçário, Maternal, Pré I, Pré II) |

## Como regenerar e validar

```bash
python3 scripts/extrair_bncc_ei.py
python3 scripts/validar_bncc.py
```

O extrator escolhe, para cada código, a descrição mais completa encontrada no
PDF (a tabela detalhada vence o quadro-resumo da página 28) e corrige
hifenização de quebra de linha.

## Colunas de `bncc_ei.csv`

| Coluna | Descrição |
|---|---|
| `ordem` | Ordem de exibição (campo de experiência e, dentro dele, grupo etário) |
| `codigo` | Código oficial, ex.: `EI03EF01` |
| `etapa` | Sempre `Educação Infantil` |
| `grupo_etario` | Bebês, Crianças bem pequenas ou Crianças pequenas |
| `faixa_etaria` | Faixa etária oficial do grupo |
| `campo_experiencia` | Um dos cinco campos de experiência da BNCC |
| `sigla_campo` | `EO`, `CG`, `TS`, `EF` ou `ET` (derivada do código) |
| `objetivo` | Texto oficial do objetivo de aprendizagem e desenvolvimento |
| `palavras_chave` | Termos de apoio à busca, gerados automaticamente a partir do objetivo |
| `pagina_pdf` | Página do PDF de onde a descrição foi extraída |
| `fonte` | Proveniência do dado |
| `revisado` | `S` quando passou nas checagens automáticas; `N` quando precisa de revisão |
| `observacao` | Motivo da sinalização, quando houver |

## Regras e cuidados

- O texto de `objetivo` é o dado oficial. `palavras_chave` é apenas um apoio de
  busca e não deve ser tratado como conteúdo da BNCC.
- Pré I (4 anos) e Pré II (5 anos) usam os mesmos códigos `EI03`. A diferença
  entre eles é pedagógica, não de código. O ano escolar fica em
  `mapeamento_escolar.csv`, separado da base oficial.
- O `mapeamento_escolar.csv` é uma correspondência institucional. A BNCC não
  define "Pré I" ou "Pré II"; ela define grupos por faixa etária.
- O CSV usa `;` como separador e UTF-8 com BOM para abrir corretamente no
  Excel em português.
- Ao gerar documentos, o sistema deve usar a descrição oficial desta base, não
  uma paráfrase do modelo de linguagem.
- Esta base cobre somente Educação Infantil. Fundamental I (1º ao 5º ano) será
  uma base separada, com outro conjunto de colunas.
