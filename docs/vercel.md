# Deploy no Vercel — fluxo em duas etapas

> O fluxo é **sem estado**: o plano JSON fica no formulário entre as etapas; os
> downloads são re-renderizados a partir do JSON. Não há SQLite, Blob nem disco
> persistente.

## Como funciona

1. `POST /gerar-plano` gera o plano e devolve a página do plano.
2. O plano JSON vai num campo oculto do formulário.
3. `POST /gerar-atividades` recebe o plano JSON e devolve as atividades.
4. `POST /baixar-plano` e `POST /baixar-atividades` renderizam os arquivos a
   partir do JSON e devolvem o `.docx`/`.pptx` na hora.

O professor só vê o botão de atividades depois de validar o plano.

## Arquivos de deploy

- `pyproject.toml` — dependências de runtime e entrypoint `app.main:app`.
- `vercel.json` — `maxDuration` de 300s e exclusões.
- `.vercelignore` — impede o envio de `exemplos base_inicial/`, `storage/` e docs.
- `requirements.txt` — runtime enxuto.
- `requirements-dev.txt` — local (`pymupdf`, `pytest`, `uvicorn`).

## Teste local

```bash
python3 -m uvicorn app.main:app --reload
```

Abra `http://127.0.0.1:8000`, gere o plano, valide e baixe os dois arquivos.

## Deploy

```bash
npx vercel login
npx vercel          # preview
npx vercel --prod   # produção
```

## Variáveis de ambiente

Primeiro publique com o mock:

```env
LLM_PROVIDER=mock
```

Depois troque para OpenAI:

```env
LLM_PROVIDER=openai-compativel
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o
LLM_API_KEY=...
```

Para imagem em runtime:

```env
IMAGE_PROVIDER=cloudflare
CLOUDFLARE_ACCOUNT_ID=...
CLOUDFLARE_API_TOKEN=...
IMAGE_MAX=1
```

`VERCEL_DEMO` não é mais usado: o fluxo em duas etapas funciona no Vercel sem
disco.

## Acesso

- O plano Hobby não tem proteção por senha; a URL de produção é pública.
- Para um teste controlado, use uma regra de rate limit no WAF:
  **Firewall → Custom Rules → Rate limiting** em `/gerar-plano` e
  `/gerar-atividades` (por IP).
- Não use o Hobby como arquitetura final de um projeto comercial. Para o
  projeto pago, migre para o Pro.

## Smoke test

1. `GET /saude` → `status: ok`, `base.total: 93`.
2. `GET /bncc` lista os 93 objetivos.
3. `POST /gerar-plano` com um código da base → página do plano.
4. `POST /gerar-atividades` com o plano JSON → página das atividades.
5. Baixar `.docx` e `.pptx`; abrir no Word/PowerPoint.
6. Conferir a nota de cobertura no último slide.
7. Com `IMAGE_PROVIDER=cloudflare`, conferir a imagem no slide de uma atividade.
8. Logs do Vercel sem erro de escrita em disco.

## Limites do Hobby

- 1.000.000 de invocações/mês.
- 4 CPU-horas de função.
- 360 GB-horas de memória provisionada.
- 300s por invocação.
- 100 deploys/dia.

Para 20 a 30 gerações de teste, isso não é o gargalo. O limite real é o provedor
de texto (OpenAI/Groq) e, depois, o de imagem (Cloudflare).
