# Biblioteca de ícones

Mapa entre palavras concretas e ícones/emojis usados nas atividades.

## Status

**Provisória.** O conjunto inicial foi montado a partir dos campos de
experiência da BNCC e será validado com a professora. Ajuste as linhas conforme
o retorno dela.

## Arquivo

`icones.csv`, com separador `;` e UTF-8 com BOM.

| Coluna | Uso |
|---|---|
| `chave` | Identificador estável, sem acento (ex.: `abacaxi`) |
| `emoji` | Ícone usado hoje |
| `arquivo` | Reservado para PNG/SVG futuro; vazio por enquanto |
| `categoria` | identidade, corpo, arte, cor, forma, linguagem, natureza, animal, alimento, objeto, brinquedo, higiene, transporte |
| `campo_bncc` | Campo de experiência que sugere o item (`EO`, `CG`, `TS`, `EF`, `ET`) |
| `fonte` | Origem do ícone |
| `licenca` | Licença, quando houver arquivo |

## Como o sistema usa

- `app/icons.py` carrega o CSV.
- `icone_para("ABACAXI")` devolve `🍍`.
- A busca ignora acento, maiúscula e pontuação.
- Se a palavra não existir, devolve `✨` como fallback.
- O renderizador do `.pptx` coloca o ícone ao lado da palavra na atividade
  `ligar_letra_inicial`.
- Quando `arquivo` estiver preenchido no futuro, o renderizador poderá usar a
  imagem no lugar do emoji.

## Como validar

1. Abra o CSV no Excel ou em um editor de texto.
2. Confira se cada palavra tem um ícone que uma criança de 4 ou 5 anos reconhece.
3. Remova o que não fizer sentido e acrescente o que faltar.
4. Evite palavras abstratas: o ícone precisa ser óbvio.
5. Rode `python3 -m pytest -q`.

## Regras

- Um ícone por palavra.
- Preferir objetos concretos e do cotidiano escolar.
- Não usar ícone para representar contagem; a contagem é feita por repetição
  determinística de formas, não por imagem gerada.
- Emoji pode variar entre sistemas; se a impressão não ficar boa, migrar para
  PNG/SVG na coluna `arquivo`.
