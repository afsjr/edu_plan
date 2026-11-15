# Roteiro de teste com o cliente

Objetivo: validar se o material gerado serve para a professora usar em sala e
se o fluxo economiza tempo de verdade.

## Preparação

- Rodar a aplicação (`python3 -m uvicorn app.main:app --reload`).
- Confirmar que está no modo mock ou com a chave real configurada.
- Separar os 2 modelos de referência para comparação lado a lado.
- Ter Word e PowerPoint instalados para abrir os arquivos.

## Passo a passo (20 a 30 minutos)

1. **Consulta à BNCC**
   - Abrir "Consultar BNCC".
   - Filtrar por grupo "Crianças pequenas (EI03)" e campo "Escuta, fala,
     pensamento e imaginação".
   - Pedir para a professora localizar uma habilidade pelo texto, sem abrir o PDF.
   - Observar: achou rápido? O texto está claro?

2. **Geração**
   - Abrir "Gerar".
   - Turma: Pré II. Tema: "Meu nome, minha identidade".
   - Clicar em "Gerar plano + caderno".
   - Cronometrar o tempo até a tela de resultado.

3. **Plano de aula**
   - Baixar o `.docx` e abrir no Word.
   - Comparar com o modelo:
     - As 7 seções estão presentes e na ordem?
     - Os códigos da BNCC estão corretos?
     - Os objetivos separam Pré I e Pré II?
     - Os tempos dos momentos somam algo próximo de 60 minutos?
     - O texto está no tom da instituição?
   - Pedir para a professora editar uma frase e salvar.

4. **Caderno de atividades**
   - Baixar o `.pptx` e abrir no PowerPoint.
   - Verificar:
     - Capa + 5 atividades.
     - Cada atividade tem código BNCC e campo.
     - Os elementos são editáveis (texto, forma, tabela).
     - O layout cabe em A4 e imprime legível em preto e branco.
   - Pedir para mover uma forma ou trocar uma palavra.

5. **Consulta e histórico**
   - Abrir "Histórico" e localizar a geração.
   - Confirmar que os links continuam funcionando.

## Checklist de aceite

- [ ] A consulta à BNCC é mais rápida que procurar no PDF.
- [ ] O plano tem as 7 seções do modelo.
- [ ] Os códigos da BNCC estão corretos e coerentes com as atividades.
- [ ] O caderno tem 5 atividades e cabe em A4.
- [ ] Os ícones/emoji aparecem e são reconhecíveis para a faixa etária.
- [ ] Os arquivos abrem no Word/PowerPoint e são editáveis.
- [ ] A professora consegue corrigir sem dificuldade.
- [ ] O tempo de geração é aceitável para uso interno.

## Perguntas para o cliente

1. O que ficou diferente do modelo que mais importa para você?
2. Qual seção do plano você sempre reescreve? Ela deveria vir pronta?
3. As atividades estão no nível certo para Pré I e Pré II?
4. Falta algum tipo de atividade?
5. O que você não usaria de jeito nenhum?
6. Quanto tempo você leva para montar isso hoje? Quanto tempo economizou?
7. O que precisa existir para você usar toda semana?

## O que registrar

- Tempo de geração.
- Número de códigos corretos e incorretos.
- Seções aprovadas e seções reescritas.
- Atividades aprovadas e atividades descartadas.
- Impressão: legível? gasta tinta? cabe na folha?
- Custo por pacote, se estiver no modo real.

## Critério de sucesso do MVP

- A professora aprova a estrutura e os códigos.
- Pelo menos 4 das 5 atividades são aproveitáveis com ajustes pequenos.
- O tempo de geração é menor que o tempo de montagem manual.
- O cliente quer continuar usando e pede a próxima evolução.
