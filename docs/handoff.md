# Handoff — retomada do projeto

> Documento de passagem de sessão. Leia este arquivo primeiro ao retomar.
> Última atualização: 2026-11-16.

## Estado

- **Repositório:** https://github.com/afsjr/edu_plan (público, branch `main`)
- **Último commit antes deste handoff:** `fd378ac`
- **Produção:** https://plano-aula-bncc.vercel.app
- **Vercel:** projeto `plano-aula-bncc`, time `adelinos-projects`, CLI logado como `afsjr`
- **Provedor ativo:** `openai-compativel` (`LLM_MODEL=gpt-4o`); o selo na home confirma
- **Imagem:** Cloudflare FLUX, 5 por pacote (uma por atividade), 512 px, base64
- **Testes:** 42 passando
- **Produção validada em 2026-11-16:** OpenAI gpt-4o + Cloudflare, 1 imagem, PPTX 7 slides, DOCX limpo

## O que está funcionando

- Entrada por **turma + código âncora**.
- Seleção de **6 códigos relacionados** em `data/bncc` (mesmo campo primeiro) → 7 códigos e 4 campos.
- Plano com **10 seções**, 7 códigos, 6–8 recursos e 7 momentos.
- Botão **Validar plano** libera as **5 atividades**.
- Atividades derivadas do plano; **nota de cobertura** no fim do PPT (não trabalhados + sugestões extras).
- **Loop de reparo** de até 3 tentativas; se não convergir, bloqueia.
- **Sanitização:** ícone de campo vira sigla no DOCX (`EO`, `CG`, `TS`, `EF`, `ET`); recurso vira `•`; DOCX sem emojis; texto CJK é rejeitado e reparado.
- **Imagem em runtime:** Cloudflare FLUX, 5 por pacote, no slide de cada atividade; 512 px; fallback; sem Blob.
- **Verificador semântico:** `gpt-4o-mini` com reparo; regra campo → tipo de atividade.
- Documentos `.docx` e `.pptx` editáveis; fluxo sem estado no servidor (plano JSON no navegador).
- Consulta à BNCC em `/bncc`.
- Questionário do cliente em `docs/questionario_cliente.md`.

## Fora do repositório (proposital)

- `exemplos base_inicial/` — modelos do cliente e PDF da BNCC
- `docs/dor_e_validacao.md` — contexto comercial interno

## Decisões pendentes para a próxima sessão

1. **Biblioteca de imagens**
   - Fonte/estilo: colorido (OpenMoji/Twemoji) ou linha (Lucide/Tabler)?
   - Implementar `scripts/buscar_icones.py` + `data/icons/arquivos/` + `CREDITS.md`.
   - Tamanho sugerido: 200–300 SVGs para EI (~2–6 MB); +200–300 para Fund I (~5–15 MB).
   - Não raspar Google Imagens; usar Iconify/Openverse/Wikimedia com licença.
2. **Cloudflare / imagens**
   - Chaves validadas: token ativo e FLUX gerando imagem.
   - Runtime implementado: `IMAGE_PROVIDER=cloudflare`, `IMAGE_MAX=5`, 512 px, base64 no JSON.
   - Próximo: biblioteca estática de PNG/SVG para os ícones.
3. **Verificador semântico**
   - `gpt-4o-mini` + reparo implementado; regra campo → tipo de atividade.
4. **Cliente**
   - Aplicar o questionário e comparar o material real com os 2 modelos.
5. **Futuro**
   - Fundamental I, PDF, múltiplos códigos simultâneos, integração com o sistema próprio.

## Como retomar

```bash
cd /Users/itouch/Documents/PESSOAL/plano_aula_bncc
source .venv/bin/activate   # se existir
pip install -r requirements-dev.txt
python3 scripts/validar_bncc.py
python3 -m pytest -q
python3 -m uvicorn app.main:app --reload
```

- Sem `LLM_API_KEY` no `.env`, o app usa o mock estrutural.
- Para o material real, o `.env` precisa de:

```env
LLM_PROVIDER=openai-compativel
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o
LLM_API_KEY=...
```

- Deploy: `vercel --prod --yes`.

## Limitações atuais

- O mock é estrutural; só o OpenAI real mede qualidade pedagógica.
- Os modelos do cliente são por tema; o fluxo por código é uma decisão de produto.
- O `.pptx` ainda usa emojis decorativos na capa e nos ícones; a imagem de atividade é gerada.
- Sem histórico no web/Vercel; sem PDF; sem Fund I.
- A biblioteca estática de PNG/SVG e o verificador semântico são as próximas trilhas.

## Primeiro passo da próxima sessão

1. Ler `docs/estado_atual.md`, `docs/decisoes.md` e `docs/questionario_cliente.md`.
2. Conferir `git status` e os commits.
3. Rodar `python3 -m pytest -q`.
4. Confirmar o provedor no selo da home.
5. Decidir a fonte/estilo da biblioteca de imagens e se o Cloudflare entra em paralelo.
