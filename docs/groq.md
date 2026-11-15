# Groq — configuração do provedor de texto

> O Groq é o provedor de texto do teste. Ele **não gera imagem**. Para imagem,
> use o Cloudflare (veja `docs/cloudflare.md`).

## Criar a chave

1. Entre em <https://console.groq.com>.
2. Abra **API Keys**.
3. Crie uma chave e copie. Ela só aparece uma vez.
4. Guarde no Vercel como `LLM_API_KEY`; nunca no repositório.

## Variáveis no Vercel

```env
LLM_PROVIDER=openai-compativel
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=openai/gpt-oss-120b
LLM_API_KEY=...
```

O cliente atual já é compatível com o formato OpenAI; não precisa de código
novo para o Groq. O schema é enviado com `strict: false`, que é o modo
compatível com os modelos do Groq.

## Limites do plano gratuito

Para `openai/gpt-oss-120b`, `openai/gpt-oss-20b` e `qwen/qwen3.8-27b`:

| Limite | Valor |
|---|---|
| Requisições/minuto | 30 |
| Requisições/dia | 1.000 |
| Tokens/minuto | 8.000 |
| Tokens/dia | 200.000 |

O TPM de 8K é o limite mais apertado. Uma geração completa fica perto disso.
Se aparecer `429`:

1. reduza a lista de candidatos da BNCC para os 12–15 mais relevantes;
2. encurte o prompt de sistema;
3. limite o tamanho da saída;
4. se necessário, divida a geração em duas chamadas (plano e caderno).

## Teste local

Com as variáveis exportadas:

```bash
python3 -m app.pipeline --tema "Meu nome, minha identidade" --uso "Pré II"
```

Sem `LLM_API_KEY`, o comando usa o mock.

## Segurança

- A chave fica só nas variáveis do Vercel.
- Use uma chave dedicada ao projeto e rotacione se houver suspeita.
- Não registre a chave em logs.
- Acompanhe o uso no painel do Groq durante o teste.

## Modelos

| Modelo | Uso |
|---|---|
| `openai/gpt-oss-120b` | Melhor qualidade de texto; recomendado para o teste |
| `openai/gpt-oss-20b` | Mais rápido; útil para comparar custo/qualidade |
| `qwen/qwen3.8-27b` | Alternativa para testar aderência ao português |

## Limite de teste recomendado

- 20 gerações/dia.
- 10 a 30 gerações no total.
- Medir tokens de entrada e saída em cada geração.
- Se o custo/limite apertar, congelar o teste e migrar para um plano pago.
