"""Pacote de referência baseado no modelo 'Meu nome, minha identidade'.

Usado pelo modo mock (sem chave de API) e pelos testes.
"""

from __future__ import annotations

from app.contract import (
    AtividadeGerada,
    BrincadeiraCasa,
    CadernoGerado,
    CampoExperienciaItem,
    CapaCaderno,
    ConteudoAtividade,
    HabilidadeSelecionada,
    Identificacao,
    ItemLegendaCor,
    Momento,
    ObjetivosAno,
    PacoteGerado,
    ParLigar,
    PlanoGerado,
    Recurso,
)

CODIGOS_PLANO = [
    "EI03EO01",
    "EI03EO02",
    "EI03EO04",
    "EI03CG05",
    "EI03TS02",
    "EI03EF01",
    "EI03EF09",
]


def pacote_exemplo() -> PacoteGerado:
    return PacoteGerado(
        plano=PlanoGerado(
            titulo="Meu Nome, Minha Identidade",
            subtitulo="Educação Infantil • Pré I e Pré II • 4 a 5 anos",
            identificacao=Identificacao(
                tema="Meu Nome, Minha Identidade",
                turmas=["Pré I (4 anos)", "Pré II (5 anos)"],
                faixa_etaria="4 a 5 anos",
                tempo_estimado="60 minutos",
                area_integradora="Identidade e linguagem oral e escrita",
            ),
            campos_experiencia=[
                CampoExperienciaItem(
                    icone="👥",
                    nome="O eu, o outro e o nós",
                    justificativa="O nome próprio é o primeiro marco da identidade.",
                ),
                CampoExperienciaItem(
                    icone="📚",
                    nome="Escuta, fala, pensamento e imaginação",
                    justificativa="Envolve oralidade e hipóteses de escrita.",
                ),
                CampoExperienciaItem(
                    icone="🎨",
                    nome="Traços, sons, cores e formas",
                    justificativa="Explora o nome como imagem gráfica.",
                ),
                CampoExperienciaItem(
                    icone="🏃",
                    nome="Corpo, gestos e movimentos",
                    justificativa="Mobiliza coordenação motora fina.",
                ),
            ],
            objetivos=[
                ObjetivosAno(
                    ano="Pré I",
                    itens=["Reconhecer o próprio nome.", "Identificar a letra inicial."],
                ),
                ObjetivosAno(
                    ano="Pré II",
                    itens=["Escrever o próprio nome.", "Contar as letras do nome."],
                ),
            ],
            habilidades=[HabilidadeSelecionada(codigo=codigo) for codigo in CODIGOS_PLANO],
            recursos=[Recurso(icone="🪪", descricao="Crachás individuais com o nome de cada criança.")],
            desenvolvimento=[
                Momento(
                    ordem=1,
                    titulo="Acolhida",
                    descricao="Receber cada criança chamando pelo nome e entregar o crachá.",
                    minutos=5,
                ),
                Momento(
                    ordem=2,
                    titulo="Dinâmica de abertura — Caixa dos Nomes",
                    descricao="Retirar um crachá por vez, ler em voz alta e perguntar de quem é o nome.",
                    minutos=8,
                ),
                Momento(
                    ordem=3,
                    titulo="Roda de conversa",
                    descricao="Perguntar quem escolheu o nome, por que ganhou esse nome e registrar as falas.",
                    minutos=10,
                ),
                Momento(
                    ordem=4,
                    titulo="Exploração do cartaz de nomes",
                    descricao="Comparar tamanhos e letras iniciais; contar as letras de alguns nomes.",
                    minutos=7,
                ),
                Momento(
                    ordem=5,
                    titulo="Atividade principal impressa",
                    descricao="Entregar as folhas do caderno e acompanhar a realização das tarefas.",
                    minutos=18,
                ),
                Momento(
                    ordem=6,
                    titulo="Brincadeira Roda dos Nomes",
                    descricao="Bater palmas no ritmo das sílabas do próprio nome.",
                    minutos=8,
                ),
                Momento(
                    ordem=7,
                    titulo="Encerramento",
                    descricao="Mostrar as produções e afixar no mural Nossa Turma.",
                    minutos=4,
                ),
            ],
            dica="Os tempos são estimativas. Ajuste conforme a rotina da instituição e o ritmo da turma.",
            brincadeira_casa=BrincadeiraCasa(
                titulo="Corre-corre do nome",
                descricao="Variação para o pátio, em outro momento da rotina.",
                organizacao="Cada criança recebe uma cópia grande do próprio nome.",
            ),
        ),
        caderno=CadernoGerado(
            capa=CapaCaderno(
                titulo="Meu Nome, Minha Identidade",
                subtitulo="Caderno de Atividades",
                etapa="Educação Infantil",
                faixa_etaria="Pré I e Pré II • 4 a 5 anos",
                alinhamento_bncc="Alinhado à BNCC",
            ),
            atividades=[
                AtividadeGerada(
                    numero=1,
                    titulo="Este é o meu nome!",
                    enunciado="Cubra as letrinhas pontilhadas e escreva o seu nome.",
                    tipo="cobrir_nome",
                    codigo_bncc="EI03EF01",
                    conteudo=ConteudoAtividade(texto_para_cobrir="NOME", linhas_escrita=2),
                    gabarito="A criança pode usar o crachá como apoio.",
                ),
                AtividadeGerada(
                    numero=2,
                    titulo="Este sou eu!",
                    enunciado="Desenhe o seu rostinho no espelho e pinte do seu jeito.",
                    tipo="desenhar_rosto",
                    codigo_bncc="EI03EO02",
                    conteudo=ConteudoAtividade(
                        frases=[
                            "De mim, eu gosto de...",
                            "Minha cor favorita é:",
                            "A comida que eu amo é:",
                            "A brincadeira que eu gosto é:",
                        ]
                    ),
                ),
                AtividadeGerada(
                    numero=3,
                    titulo="A letrinha do meu nome",
                    enunciado="Ligue cada desenho à letra com que o nome começa.",
                    tipo="ligar_letra_inicial",
                    codigo_bncc="EI03EF09",
                    conteudo=ConteudoAtividade(
                        pares=[
                            ParLigar(palavra="ABACAXI", letra="A"),
                            ParLigar(palavra="BOLA", letra="B"),
                            ParLigar(palavra="CACHORRO", letra="C"),
                            ParLigar(palavra="DADO", letra="D"),
                        ]
                    ),
                    gabarito="ABACAXI–A; BOLA–B; CACHORRO–C; DADO–D.",
                ),
                AtividadeGerada(
                    numero=4,
                    titulo="A turma colorida",
                    enunciado="Pinte cada espaço seguindo a cor de cada número.",
                    tipo="colorir_por_numero",
                    codigo_bncc="EI03TS02",
                    conteudo=ConteudoAtividade(
                        legenda_cores=[
                            ItemLegendaCor(numero=1, cor="Rosa"),
                            ItemLegendaCor(numero=2, cor="Amarelo"),
                            ItemLegendaCor(numero=3, cor="Azul"),
                            ItemLegendaCor(numero=4, cor="Verde"),
                        ]
                    ),
                ),
                AtividadeGerada(
                    numero=5,
                    titulo="O caminho até a escola",
                    enunciado="Ajude a criança a chegar na escola seguindo o caminho.",
                    tipo="labirinto",
                    codigo_bncc="EI03CG05",
                    conteudo=ConteudoAtividade(rotulo_inicio="início", rotulo_fim="escola"),
                ),
            ],
        ),
    )
