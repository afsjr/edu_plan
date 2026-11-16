"""Pacote de referência no novo contrato (7 códigos, 10 seções, 5 atividades).

Usado pelo modo mock e pelos testes. O título/tema oficiais são sobrescritos
pelo resolvedor com a descrição do código âncora.
"""

from __future__ import annotations

from app.contract import (
    AtividadeGerada,
    Avaliacao,
    BrincadeiraCasa,
    CadernoGerado,
    CampoExperienciaItem,
    CapaCaderno,
    ConteudoAtividade,
    HabilidadeSelecionada,
    Identificacao,
    IndicadorAvaliacao,
    ItemLegendaCor,
    Momento,
    NotaCoberturaGerada,
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

ANCORA = "EI03EF01"

OBJETIVOS_PRE_1 = [
    "Reconhecer o próprio nome escrito em diferentes suportes (crachá, ficha, cartaz).",
    "Identificar a letra inicial do próprio nome e associá-la ao seu som.",
    "Perceber que o nome tem uma sequência específica de letras que não muda.",
    "Nomear colegas da turma, ampliando o vínculo com o grupo.",
]

OBJETIVOS_PRE_2 = [
    "Escrever o próprio nome de forma autônoma, respeitando a ordem das letras.",
    "Contar quantas letras tem o seu nome e comparar com o nome dos colegas.",
    "Identificar semelhanças e diferenças entre nomes (letra inicial, tamanho).",
    "Elaborar hipóteses sobre o significado histórico ou familiar do próprio nome.",
]


def pacote_exemplo() -> PacoteGerado:
    return PacoteGerado(
        plano=PlanoGerado(
            titulo="Meu nome, minha identidade",
            subtitulo="Educação Infantil • Pré I e Pré II • 4 a 5 anos",
            identificacao=Identificacao(
                tema="Meu nome, minha identidade",
                codigo_ancora=ANCORA,
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
                ObjetivosAno(ano="Pré I", itens=list(OBJETIVOS_PRE_1)),
                ObjetivosAno(ano="Pré II", itens=list(OBJETIVOS_PRE_2)),
            ],
            habilidades=[HabilidadeSelecionada(codigo=codigo) for codigo in CODIGOS_PLANO],
            recursos=[
                Recurso(icone="🪪", descricao="Crachás individuais com o nome de cada criança."),
                Recurso(icone="🚩", descricao="Cartaz-mural com todos os nomes da turma."),
                Recurso(icone="🔤", descricao="Cartelas com as letras do alfabeto móvel."),
                Recurso(icone="📄", descricao="Folha da atividade impressa (uma por criança)."),
                Recurso(icone="🖌️", descricao="Lápis de cor, giz de cera e canetinhas de ponta grossa."),
                Recurso(icone="✂️", descricao="Cola bastão e recortes de papel colorido."),
                Recurso(icone="📦", descricao="Caixa ou saco surpresa para a dinâmica de abertura."),
                Recurso(icone="🎵", descricao="Música do bom-dia com o nome de cada criança."),
            ],
            desenvolvimento=[
                Momento(ordem=1, titulo="Acolhida", descricao="Receber cada criança chamando pelo nome e entregar o crachá.", minutos=5),
                Momento(ordem=2, titulo="Dinâmica de abertura — Caixa dos Nomes", descricao="Retirar um crachá por vez, ler em voz alta e perguntar de quem é o nome.", minutos=8),
                Momento(ordem=3, titulo="Roda de conversa", descricao="Perguntar quem escolheu o nome, por que ganhou esse nome e registrar as falas.", minutos=10),
                Momento(ordem=4, titulo="Exploração do cartaz de nomes", descricao="Comparar tamanhos e letras iniciais; contar as letras de alguns nomes.", minutos=7),
                Momento(ordem=5, titulo="Atividade principal impressa", descricao="Entregar as folhas do caderno e acompanhar a realização das tarefas.", minutos=18),
                Momento(ordem=6, titulo="Brincadeira Roda dos Nomes", descricao="Bater palmas no ritmo das sílabas do próprio nome.", minutos=8),
                Momento(ordem=7, titulo="Encerramento", descricao="Mostrar as produções e afixar no mural Nossa Turma.", minutos=4),
            ],
            avaliacao=Avaliacao(
                introducao="A avaliação na Educação Infantil é processual e formativa. Use os indicadores como referência para o registro.",
                indicadores=[
                    IndicadorAvaliacao(criterio="Reconhece o próprio nome", pre_1="Com apoio do crachá", pre_2="Com autonomia"),
                    IndicadorAvaliacao(criterio="Identifica a letra inicial", pre_1="Com mediação", pre_2="Sozinho"),
                    IndicadorAvaliacao(criterio="Escreve o nome", pre_1="Com apoio visual", pre_2="De forma autônoma"),
                    IndicadorAvaliacao(criterio="Participa das brincadeiras", pre_1="Com incentivo", pre_2="Com iniciativa"),
                ],
            ),
            adaptacoes=[
                "Para crianças com dificuldade motora, oferecer letras móveis e crachás com letras maiores.",
                "Para crianças com deficiência visual, usar crachás com textura e letras em relevo.",
                "Para crianças tímidas, permitir que mostrem o crachá antes de falar o nome.",
                "Para turmas numerosas, dividir a roda dos nomes em pequenos grupos.",
            ],
            observacoes_professor="",
            dica="Os tempos são estimativas. Ajuste conforme a rotina da instituição e o ritmo da turma.",
            brincadeira_casa=BrincadeiraCasa(
                titulo="Corre-corre do nome",
                descricao="Variação para o pátio, em outro momento da rotina.",
                organizacao="Cada criança recebe uma cópia grande do próprio nome.",
            ),
        ),
        caderno=CadernoGerado(
            capa=CapaCaderno(
                titulo="Meu nome, minha identidade",
                subtitulo="Caderno de Atividades",
                etapa="Educação Infantil",
                faixa_etaria="Pré I e Pré II • 4 a 5 anos",
                alinhamento_bncc="Alinhado à BNCC",
                codigo_ancora=ANCORA,
            ),
            atividades=[
                AtividadeGerada(
                    numero=1,
                    titulo="Este é o meu nome!",
                    enunciado="Cubra as letrinhas pontilhadas e escreva o seu nome.",
                    tipo="cobrir_palavra",
                    codigo_bncc="EI03EF01",
                    objetivo_indice=5,
                    objetivo_relacionado=OBJETIVOS_PRE_2[0],
                    conteudo=ConteudoAtividade(texto_para_cobrir="NOME", linhas_escrita=2),
                    gabarito="A criança pode usar o crachá como apoio.",
                ),
                AtividadeGerada(
                    numero=2,
                    titulo="Este sou eu!",
                    enunciado="Desenhe o seu rostinho no espelho e pinte do seu jeito.",
                    tipo="desenhar",
                    codigo_bncc="EI03EO02",
                    objetivo_indice=8,
                    objetivo_relacionado=OBJETIVOS_PRE_2[3],
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
                    tipo="ligar",
                    codigo_bncc="EI03EF09",
                    objetivo_indice=2,
                    objetivo_relacionado=OBJETIVOS_PRE_1[1],
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
                    tipo="colorir",
                    codigo_bncc="EI03TS02",
                    objetivo_indice=6,
                    objetivo_relacionado=OBJETIVOS_PRE_2[1],
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
                    objetivo_indice=3,
                    objetivo_relacionado=OBJETIVOS_PRE_1[2],
                    conteudo=ConteudoAtividade(rotulo_inicio="início", rotulo_fim="escola"),
                ),
            ],
            nota_cobertura=NotaCoberturaGerada(
                objetivos_nao_trabalhados=[
                    OBJETIVOS_PRE_1[0],
                    OBJETIVOS_PRE_1[3],
                    OBJETIVOS_PRE_2[2],
                ],
                sugestoes_extras=[
                    "Ampliar a atividade 1 usando o crachá como apoio individual.",
                    "Levar a roda dos nomes para o pátio em outro momento da rotina.",
                ],
            ),
        ),
    )
