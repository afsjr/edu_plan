# Escopo do MVP

## Objetivo

Permitir que a escola gere, em poucos minutos, um plano de aula e um caderno de
atividades alinhados à BNCC, no formato dos modelos da instituição, com arquivos
editáveis para revisão do professor.

O MVP serve para **teste com o cliente**. Ele não é um protótipo descartável:
já separa dados, contrato, prompts e renderização para evoluir sem reescrever.

## Público

- Coordenação pedagógica e professores da Educação Infantil (Pré I e Pré II).
- Responsável técnico que mantém a ferramenta.

## Dentro do escopo

- Educação Infantil, com os 93 objetivos da BNCC.
- Tema inicial: "Meu nome, minha identidade".
- Saídas: plano de aula `.docx` e caderno de atividades `.pptx`, A4, editáveis.
- Plano com 7 seções: identificação, campos de experiência, objetivos,
  habilidades da BNCC, recursos, desenvolvimento e brincadeira/atividade para casa.
- Caderno com capa + 5 atividades, cada uma com código BNCC e campo.
- Ícones/emoji na atividade de ligar palavra à letra, com biblioteca versionada.
- Consulta à BNCC por grupo, campo e palavra-chave.
- Histórico local das gerações.
- Modo mock sem custo para demonstração.

## Fora do escopo

- Fundamental I e Fundamental II.
- Exportação em PDF.
- Quantidade variável de atividades.
- Imagens geradas por IA.
- Login, pagamento, multiusuário e permissões.
- Coleta de dados de alunos.
- Treinamento de modelo com os modelos da instituição.

## Fluxo do usuário

1. Abre a aplicação.
2. Escolhe a turma e digita o tema.
3. Recebe o pacote e baixa os dois arquivos.
4. Abre no Word/PowerPoint, revisa e imprime.

Em paralelo, pode consultar a BNCC na própria ferramenta, sem abrir o PDF.

## Regras de negócio

- A IA só escolhe códigos presentes na lista de candidatos.
- A descrição oficial é injetada pelo sistema a partir do CSV.
- Um código inválido interrompe a geração com erro claro.
- Pré I e Pré II compartilham códigos `EI03`; o ano é um campo separado.
- O caderno tem exatamente 5 atividades no MVP.

## Arquitetura

```
Navegador
   │
   ▼
FastAPI (app/main.py)
   │
   ├── consulta BNCC (app/bncc.py → data/bncc/bncc_ei.csv)
   ├── geração (app/pipeline.py)
   │      ├── seleção de candidatos
   │      ├── cliente de IA (app/llm.py: mock ou OpenAI-compatível)
   │      ├── resolução dos códigos (app/contract.py)
   │      └── renderização (app/render_docx.py, app/render_pptx.py)
   └── histórico (app/storage.py → SQLite + storage/)
```

Decisões:

- **Python** por causa da extração do PDF (`pymupdf`) e da geração de Office
  (`python-docx`, `python-pptx`).
- **Sem n8n no núcleo**: o fluxo precisa de testes, versionamento e refatoração
  segura. n8n serve para experimentos, não para o produto.
- **CSV em memória** para 93 registros. Embedding/pgvector só quando a base
  crescer para Fundamental I.
- **OpenAI-compatível** como interface de IA, para trocar de provedor sem mexer
  no pipeline.
- **SQLite + arquivos locais** no MVP, para reduzir infraestrutura.

## Critérios de aceite

1. A base tem 93 linhas válidas e nenhum código duplicado.
2. Um pedido de "Meu nome, minha identidade" gera um pacote completo.
3. Todos os códigos do material existem na base e pertencem à Educação Infantil.
4. O `.docx` abre no Word e mantém as 7 seções.
5. O `.pptx` abre no PowerPoint, tem 6 slides e 5 atividades.
6. Os arquivos são editáveis (texto, tabela e forma, não imagem).
7. A consulta à BNCC retorna resultados em menos de 1 segundo.
8. A professora aprova estrutura, códigos e impressão.

## Riscos e mitigação

| Risco | Mitigação |
|---|---|
| Código de BNCC inventado | Lista de candidatos + validação + descrição vinda do CSV |
| Extração do PDF com erro | Validador, contagem esperada e conferência por amostragem |
| Baixa fidelidade visual | Templates em código com a paleta e a estrutura dos modelos |
| Contrato incompleto (só 2 modelos) | Contrato versionado; os outros 8 refinam depois |
| Custo por geração | Modo mock para testar; medir tokens no provedor real |
| Dados sensíveis | Nenhum dado de aluno é coletado |

## Evolução

1. Outros 8 modelos → ajuste do contrato.
2. Fundamental I → nova base e, se necessário, busca híbrida com embeddings.
3. PDF via LibreOffice headless.
4. Atividades em quantidade variável.
5. Biblioteca de ícones e ilustrações fixas.
6. Revisão colaborativa e multiusuário.
