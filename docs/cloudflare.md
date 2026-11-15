# Cloudflare Workers AI — guia de preparação

> Este guia é para a **fase futura** de imagens em runtime. A fase atual usa
> apenas ícones/emoji estáticos. Nada aqui é necessário para o primeiro teste.

## O que o Cloudflare é (e não é)

- **É** uma plataforma com modelos de imagem (FLUX.1 Schnell, FLUX.2, etc.) e
  também LLMs.
- **Não é** uma LLM de texto especializada em pedagogia. Para o texto do plano,
  continuamos com o Groq.
- Para ícones e ilustrações simples, o FLUX.1 Schnell atende.
- Para cenas complexas, realismo ou texto dentro da imagem, é preciso um modelo
  de imagem mais forte (FLUX Dev/Pro, GPT Image, Nano Banana).

## Limite gratuito

- **10.000 neurons por dia** no plano Workers Free.
- FLUX.1 Schnell consome aproximadamente **4,8 neurons por tile 512×512** mais
  **9,6 neurons por step**.
- Com 4 steps, dá cerca de **43 neurons por imagem** → **~230 imagens/dia**.
- Para 1 ou 2 imagens por pacote, sobra folga para o teste.

## Passo a passo no painel

1. Entre em <https://dash.cloudflare.com>.
2. No menu, abra **Workers AI**.
3. Clique em **Use REST API**.
4. Em **Get Account ID**, copie o valor e guarde como `CLOUDFLARE_ACCOUNT_ID`.
5. Clique em **Create a Workers AI API Token**.
6. Revise as permissões. O token precisa de **Workers AI — Read** e
   **Workers AI — Edit**.
7. Crie o token, copie e guarde como `CLOUDFLARE_API_TOKEN`.
   O token só aparece uma vez; não o coloque no repositório.

## Teste rápido com curl

```bash
export CLOUDFLARE_ACCOUNT_ID="seu-account-id"
export CLOUDFLARE_API_TOKEN="seu-token"

curl -X POST \
  "https://api.cloudflare.com/client/v4/accounts/$CLOUDFLARE_ACCOUNT_ID/ai/run/@cf/black-forest-labs/flux-1-schnell" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "flat vector illustration of a single pineapple, thick clean outlines, solid pastel colors, white background, centered, childrens textbook style, no text, no letters, no numbers",
    "steps": 4,
    "seed": 42
  }'
```

A resposta tem o formato:

```json
{
  "result": { "image": "<base64>" },
  "success": true,
  "errors": [],
  "messages": []
}
```

Para salvar a imagem:

```bash
curl -s -X POST \
  "https://api.cloudflare.com/client/v4/accounts/$CLOUDFLARE_ACCOUNT_ID/ai/run/@cf/black-forest-labs/flux-1-schnell" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"flat vector illustration of a single pineapple, white background, thick outlines, no text","steps":4,"seed":42}' \
| python3 -c "import sys,json,base64,pathlib; d=json.load(sys.stdin); pathlib.Path('teste.png').write_bytes(base64.b64decode(d['result']['image']))"
```

## No Vercel

Configure as variáveis no projeto (Production e Preview):

```env
CLOUDFLARE_ACCOUNT_ID=...
CLOUDFLARE_API_TOKEN=...
IMAGE_PROVIDER=cloudflare
```

Nunca comite esses valores. Use um token só para o projeto e rotacione se
houver suspeita de vazamento.

## Como integrar depois

1. Criar `app/image.py` com uma função `gerar_imagem(prompt: str) -> bytes`.
2. Chamar o endpoint `/ai/run/@cf/black-forest-labs/flux-1-schnell`.
3. Decodificar `result.image` de base64 para bytes.
4. Embutir a imagem no `.pptx` com `python-pptx`; não precisa de Blob nem de
   disco.
5. Gerar no máximo 1 ou 2 imagens por pacote, em paralelo.
6. Se a imagem falhar, usar o ícone/emoji como fallback.

## Regras de segurança pedagógica

- **Nunca** usar imagem gerada para contagem, sílabas ou letras.
- Um objeto por imagem; fundo branco; contorno grosso; estilo flat.
- Sem texto, letras, números ou marca d'água dentro da imagem.
- Revisão humana antes de entrar no material do cliente.
- Fixar modelo, seed e estilo para manter consistência.
- Verificar os termos de uso do modelo e a licença das imagens.

## Links úteis

- Workers AI — REST API:
  <https://developers.cloudflare.com/workers-ai/get-started/rest-api/>
- FLUX.1 Schnell:
  <https://developers.cloudflare.com/workers-ai/models/flux-1-schnell/>
- Preços:
  <https://developers.cloudflare.com/workers-ai/platform/pricing/>
