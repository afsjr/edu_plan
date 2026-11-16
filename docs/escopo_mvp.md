# Escopo do MVP

## Objetivo

Permitir que o professor gere um plano de aula a partir de **um código da BNCC**
e, só depois de validar o plano, gere as atividades. Tudo sai em `.docx` e
`.pptx` editáveis, ancorado em `data/bncc`.

## Público

- Professores e coordenação da Educação Infantil (Pré I e Pré II).
- Responsável técnico que mantém a ferramenta.

## Fluxo

1. Professor escolhe turma e **1 código âncora**.
2. O sistema valida o código na base e a turma.
3. O sistema seleciona **6 códigos relacionados** (mesmo campo primeiro, depois
   mesma turma) até **7 códigos e 4 campos**.
4. Gera o **plano** com 10 seções.
5. O professor baixa o `.docx` e **valida**.
6. Só então o sistema gera **5 atividades** a partir do plano.
7. O `.pptx` termina com a **nota de cobertura**.

## Dentro do escopo

- Educação Infantil, com os 93 objetivos da BNCC.
- Entrada por turma + 1 código âncora.
- 7 códigos, 4 campos, 10 seções, 6–8 recursos e 7 momentos.
- 5 atividades derivadas do plano, com 8 tipos genéricos.
- Nota de cobertura: códigos/objetivos não trabalhados e sugestões extras.
- `.docx` e `.pptx` editáveis.
- Dois passos com validação do professor; plano JSON no navegador.
- Consulta à BNCC por grupo, campo e palavra.
- Modo mock estrutural e provedor OpenAI.

## Fora do escopo

- Fundamental I e Fundamental II.
- Múltiplos códigos simultâneos (o cliente pode pedir depois).
- Tema livre (a entrada é por código).
- Exportação em PDF.
- Histórico persistente no web/Vercel.
- Imagens geradas por IA em runtime.
- Login, pagamento, multiusuário e permissões.
- Coleta de dados de alunos.
- Treinamento de modelo com os modelos da instituição.

## Regras de negócio

- Códigos e descrições vêm **somente** de `data/bncc`.
- Se o código não existir ou não pertencer à turma:
  **"não possuo esta informação na minha base de dados"**.
- O plano tem exatamente 7 códigos e 4 campos.
- As 5 atividades usam apenas códigos do plano; o âncora é obrigatório.
- Cada atividade copia verbatim um objetivo do plano.
- A nota de cobertura lista o que não foi trabalhado e o que é sugestão extra.
- Nada é inventado; a descrição oficial é injetada pelo sistema.

## Critérios de aceite

1. A base tem 93 linhas válidas e nenhum código duplicado.
2. O professor escolhe o código e o plano sai com 7 códigos e 4 campos.
3. O plano tem as 10 seções e 6–8 recursos.
4. O `.docx` abre no Word e é editável.
5. Após a validação, o `.pptx` tem 5 atividades e a nota de cobertura.
6. Nenhum código inválido é entregue.
7. A professora aprova estrutura, códigos e impressão.

## Riscos

| Risco | Mitigação |
|---|---|
| Código inventado | Lista fechada de candidatos + descrição do CSV |
| Atividade fora do plano | Códigos só do plano + objetivo verbatim |
| Plano incompleto | 10 seções obrigatórias + 6–8 recursos |
| Modelo fraco no texto | OpenAI gpt-4o; verificação e reparo |
| Código fora da turma | Validação de grupo + mensagem clara |
| Imagem errada | Sem imagem em runtime no MVP |

## Evolução

1. Verificador LLM + reparo automático.
2. Múltiplos códigos simultâneos.
3. Fundamental I.
4. Imagens em runtime (Cloudflare) com curadoria.
5. PDF.
6. Integração com o sistema próprio.
