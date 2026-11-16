# Roteiro de teste com o cliente

Objetivo: validar se o fluxo por código BNCC resolve o problema e se o material
gerado serve para a professora usar em sala.

## Preparação

- Rodar a aplicação (`python3 -m uvicorn app.main:app --reload`).
- Escolher um código âncora para o teste (ex.: `EI03EF01`).
- Separar os modelos de referência ("Meu nome") para comparação.
- Ter Word e PowerPoint instalados.

## Passo a passo (20 a 30 minutos)

1. **Consulta à BNCC**
   - Abrir "Consultar BNCC".
   - Filtrar por grupo EI03 e por um campo.
   - Confirmar que o código escolhido existe na base.

2. **Gerar o plano**
   - Abrir "Gerar".
   - Turma: Pré II. Código: o escolhido.
   - Clicar em "Gerar plano".
   - Conferir:
     - o título/tema é a descrição oficial do código âncora?
     - o plano tem as 10 seções?
     - há 7 códigos e 4 campos?
     - há 6 a 8 recursos e 7 momentos?
     - os objetivos estão separados em Pré I e Pré II?
   - Baixar o `.docx` e editar uma frase no Word.

3. **Validar**
   - Clicar em **"Validar plano e gerar atividades"**.
   - Confirmar que o PPT só é liberado depois desse clique.

4. **Conferir as atividades**
   - Baixar o `.pptx` e abrir no PowerPoint.
   - Verificar:
     - 5 atividades;
     - o código âncora aparece em pelo menos uma;
     - cada atividade mostra o objetivo do plano;
     - os tipos de atividade fazem sentido para o objetivo;
     - o slide final traz a nota de cobertura.
   - Mover uma forma ou trocar uma palavra.

5. **Nota de cobertura**
   - Conferir se os códigos/objetivos não trabalhados estão listados.
   - Perguntar se o professor quer manter ou remover o slide.

## Checklist de aceite

- [ ] O código existe na base e o plano usa só códigos de `data/bncc`.
- [ ] O plano tem as 10 seções.
- [ ] O plano tem 7 códigos e 4 campos.
- [ ] O professor valida antes de gerar o PPT.
- [ ] O caderno tem 5 atividades e a nota de cobertura.
- [ ] Os ícones/emoji são reconhecíveis para a faixa etária.
- [ ] Os arquivos abrem no Word/PowerPoint e são editáveis.
- [ ] O tempo de geração é aceitável.
- [ ] Nenhum código inválido foi entregue.

## Perguntas para o cliente

1. O fluxo por código âncora faz sentido para o planejamento da escola?
2. O plano está no nível certo para Pré I e Pré II?
3. As 5 atividades cobrem o plano? O que faltou?
4. A nota de cobertura ajuda ou atrapalha?
5. O que você não usaria de jeito nenhum?
6. Quanto tempo você leva hoje? Quanto tempo economizou?
7. O que precisa existir para usar toda semana?

## Depois do teste

- Preencher o questionário de consulta (`docs/questionario_cliente.md`).
- Registrar tempo, códigos corretos, seções reescritas e atividades descartadas.
- Decidir o próximo incremento com base no questionário, não só no material.
