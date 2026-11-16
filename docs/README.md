# Documentação

Índice dos documentos do projeto. A ideia é que qualquer pessoa consiga retomar
o trabalho sem depender do histórico do chat.

## Por onde começar

1. **`handoff.md`** — passagem de sessão: onde paramos e o que fazer agora.
2. **`estado_atual.md`** — o que existe hoje, números, comandos e limitações.
3. **`decisoes.md`** — por que o sistema é assim e o que faria uma decisão mudar.
4. **`escopo_mvp.md`** — o que está dentro e fora do MVP.
5. **`roteiro_teste_cliente.md`** — como conduzir o teste com a professora.
6. **`questionario_cliente.md`** — consulta ao cliente, **separada do MVP**.
7. **`vercel.md`**, **`groq.md`**, **`cloudflare.md`** — deploy e provedores.

## O que cada documento responde

| Documento | Pergunta que responde | Quando atualizar |
|---|---|---|
| `handoff.md` | Onde paramos e como retomar? | Ao encerrar uma sessão |
| `estado_atual.md` | O que já está pronto e como rodar? | Depois de cada incremento |
| `decisoes.md` | Por que escolhemos isso? | A cada decisão nova ou reaberta |
| `escopo_mvp.md` | O que entra e o que não entra? | Quando o escopo mudar |
| `roteiro_teste_cliente.md` | Como testar e o que observar? | Antes de cada rodada |
| `questionario_cliente.md` | A proposta resolve o problema do cliente? | Depois de cada conversa |
| `vercel.md` | Como publicar o fluxo em duas etapas? | Antes do deploy |
| `groq.md` | Como usar o Groq como alternativa? | Quando for testar |
| `cloudflare.md` | Como preparar a imagem futura? | Quando implementar imagens |

## Regra de manutenção

- Não apague decisões antigas; registre a substituição.
- Números do `estado_atual.md` devem ser conferidos com os comandos citados.
- Toda mudança de escopo deve aparecer em `escopo_mvp.md`.
- Toda resposta do cliente deve atualizar o questionário ou o documento interno
  de validação (não versionado).

## Relação com o código

- Base da BNCC: `data/bncc/README.md`.
- Layout dos documentos: `templates/README.md`.
- Prompt do plano: `prompts/system_plano.md`.
- Prompt das atividades: `prompts/system_atividades.md`.
- Schemas: `prompts/schema_plano.json`, `prompts/schema_caderno.json`.
- Visão geral: `README.md` na raiz.
