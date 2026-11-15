# Deploy no Vercel — modo demonstração

> Objetivo: colocar o MVP em uma URL pública para o cliente validar o caminho.
> Nesta fase **não há histórico** e o download vem em um ZIP com o plano
> `.docx` e o caderno `.pptx`. Imagem em runtime fica para depois.

## Como o modo demo funciona

- `VERCEL_DEMO=1` ativa o modo.
- `POST /gerar` monta os dois arquivos em `/tmp`, compacta em ZIP e devolve no
  mesmo request.
- `/historico`, `/resultado` e `/download` ficam desativados.
- `/bncc` e `/saude` continuam funcionando.
- Sem Blob, sem Postgres, sem disco persistente.

## Arquivos de deploy

- `pyproject.toml` — dependências de runtime e entrypoint `app.main:app`.
- `vercel.json` — `maxDuration` de 300s e exclusão de arquivos desnecessários.
- `.vercelignore` — impede o envio dos modelos do cliente, `storage/` e docs.
- `requirements.txt` — dependências de runtime.
- `requirements-dev.txt` — dependências locais (`pymupdf`, `pytest`, `uvicorn`).

## Teste local do modo demo

```bash
VERCEL_DEMO=1 python3 -m uvicorn app.main:app --reload
```

Abra `http://127.0.0.1:8000`, preencha o formulário e confirme que o navegador
baixa um `.zip` com os dois arquivos.

## Deploy

```bash
npx vercel login
npx vercel          # preview
npx vercel --prod   # produção
```

O projeto usa Python 3.12+ no Vercel. O entrypoint é `app.main:app`.

## Variáveis de ambiente

No painel do Vercel, em **Settings → Environment Variables**:

```env
VERCEL_DEMO=1
LLM_PROVIDER=mock
```

Primeiro publique com o mock para testar o encanamento. Depois troque para o
Groq seguindo `docs/groq.md`.

## Acesso

- O plano Hobby não tem proteção por senha; a URL de produção é pública.
- Para um teste controlado, use uma regra de rate limit no WAF:
  **Firewall → Custom Rules → Rate limiting** em `/gerar` (por IP).
- Não use o Hobby como arquitetura final de um projeto comercial. Para o
  projeto pago, migre para o Pro.

## Smoke test depois do deploy

1. `GET /saude` responde `status: ok` e `base.total: 93`.
2. `GET /bncc` lista os 93 objetivos.
3. `POST /gerar` baixa um ZIP.
4. O ZIP abre e contém `plano_aula.docx` e `caderno_atividades.pptx`.
5. Os dois arquivos abrem no Word/PowerPoint.
6. Os logs do Vercel não mostram erro de escrita em disco.

## Limites do Hobby

- 1.000.000 de invocações/mês.
- 4 CPU-horas de função.
- 360 GB-horas de memória provisionada.
- 300s por invocação.
- 100 deploys/dia.

Para 20 a 30 gerações de teste, isso não é o gargalo. O limite real é o provedor
de texto (Groq) e, depois, o de imagem (Cloudflare).
