# Documentação

Índice dos documentos do projeto. A ideia é que qualquer pessoa consiga retomar
o trabalho sem depender do histórico do chat.

## Por onde começar

1. **`estado_atual.md`** — o que existe hoje, números, comandos e limitações.
2. **`decisoes.md`** — por que o sistema é assim e o que faria uma decisão mudar.
3. **`escopo_mvp.md`** — o que está dentro e fora do MVP.
4. **`roteiro_teste_cliente.md`** — como conduzir o teste com a professora.

> O documento de dor e validação do cliente é mantido **fora do repositório
> público**, porque contém contexto comercial e perguntas internas.

## O que cada documento responde

| Documento | Pergunta que responde | Quando atualizar |
|---|---|---|
| `estado_atual.md` | O que já está pronto e como rodar? | Depois de cada incremento relevante |
| `decisoes.md` | Por que escolhemos isso? | A cada decisão nova ou reaberta |
| `escopo_mvp.md` | O que entra e o que não entra? | Quando o escopo mudar |
| `roteiro_teste_cliente.md` | Como testar e o que observar? | Antes de cada rodada de teste |
| `cloudflare.md` | Como preparar a geração de imagem futura? | Quando for implementar imagens em runtime |

## Regra de manutenção

- Não apague decisões antigas; registre a substituição.
- Números do `estado_atual.md` devem ser conferidos com os comandos citados.
- Toda mudança de escopo deve aparecer em `escopo_mvp.md` e, se for uma escolha
  técnica, em `decisoes.md`.
- Toda resposta do cliente deve atualizar o documento interno de validação
  (não versionado).

## Relação com o código

- Base da BNCC: `data/bncc/README.md`.
- Layout dos documentos: `templates/README.md`.
- Prompt e contrato: `prompts/system.md`, `prompts/few_shot.md` e
  `prompts/schema_pacote.json`.
- Visão geral do projeto: `README.md` na raiz.
