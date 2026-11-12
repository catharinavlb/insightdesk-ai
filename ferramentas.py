
import logging
import re
import unicodedata

import requests

from agents import function_tool
from database import conectar_banco


# ==========================================
# CONFIGURAÇÕES
# ==========================================

OLLAMA_EMBED_URL = "http://127.0.0.1:11434/api/embed"
MODELO_EMBEDDING = "nomic-embed-text"
DIMENSOES = 768

LIMITE_RESULTADOS = 3

# Busca híbrida
RRF_K = 60
PESO_SEMANTICO = 1.0
PESO_TEXTUAL = 2.0
PONTUACAO_TEXTUAL_MINIMA = 2

# Filtro de relevância
PONTUACAO_TEXTUAL_MINIMA_FILTRO = 3
PROPORCAO_MINIMA_MELHOR_RESULTADO = 0.60


# ==========================================
# LOGS
# ==========================================

logger = logging.getLogger("insightdesk.ferramentas")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s"
        )
    )
    logger.addHandler(handler)

logger.propagate = False


# ==========================================
# COLUNAS DO BANCO
# ==========================================

COLUNAS = """
    id,
    titulo,
    descricao,
    categoria,
    sintomas,
    causa_provavel,
    procedimento,
    validacao,
    fonte_url,
    nivel_dificuldade,
    revisado
"""


# ==========================================
# NORMALIZAÇÃO DE TEXTO
# ==========================================

PALAVRAS_IGNORADAS = {
    "com", "para", "uma", "uns", "umas", "das",
    "dos", "que", "nao", "esta", "estou",
    "meu", "minha", "esse", "essa", "quando",
    "tentar", "sistema", "problema", "erro",
    "consigo", "aparece", "sobre", "preciso",
    "tenho", "tentando", "entrar", "mas",
    "ela", "ele", "por", "falta", "seu",
    "sua", "nos", "nas", "aos", "isso",
    "aqui", "ser", "ter", "foi", "sao",
    "mais", "muito", "pelo", "pela",
    "como", "onde", "qual", "quais"
}


def normalizar_texto(texto: str) -> str:
    texto = (texto or "").lower()
    texto = unicodedata.normalize("NFKD", texto)

    return "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(caractere)
    )


def extrair_termos(texto: str) -> list[str]:
    texto = normalizar_texto(texto)

    palavras = re.findall(r"[a-z0-9]+", texto)

    termos = [
        palavra
        for palavra in palavras
        if len(palavra) >= 3
        and palavra not in PALAVRAS_IGNORADAS
    ]

    return list(dict.fromkeys(termos))


# ==========================================
# EXPANSÃO DE TERMOS
# ==========================================

GRUPOS_RELACIONADOS = [
    {
        "autorizacao", "permissao", "permissoes",
        "acesso", "bloqueado", "bloqueando",
        "negado", "403"
    },
    {
        "lento", "lenta", "lentidao",
        "demora", "desempenho"
    },
    {
        "email", "emails", "notificacao",
        "notificacoes", "recebimento"
    },
    {
        "relatorio", "relatorios",
        "geracao", "gerar"
    }
]


def expandir_termos(termos: list[str]) -> set[str]:
    expandidos = set(termos)

    for grupo in GRUPOS_RELACIONADOS:
        if expandidos.intersection(grupo):
            expandidos.update(grupo)

    return expandidos


# ==========================================
# EMBEDDINGS COM OLLAMA
# ==========================================

def gerar_embedding(texto: str) -> list[float]:
    resposta = requests.post(
        OLLAMA_EMBED_URL,
        json={
            "model": MODELO_EMBEDDING,
            "input": texto
        },
        timeout=120
    )

    resposta.raise_for_status()

    dados = resposta.json()
    embeddings = dados.get("embeddings", [])

    if not embeddings or not embeddings[0]:
        raise ValueError(
            "O Ollama não retornou um embedding válido."
        )

    vetor = embeddings[0]

    if len(vetor) != DIMENSOES:
        raise ValueError(
            f"Esperadas {DIMENSOES} dimensões, "
            f"recebidas {len(vetor)}."
        )

    return vetor


# ==========================================
# CARREGAMENTO DAS SOLUÇÕES
# ==========================================

def carregar_solucoes():
    consulta = f"""
        SELECT {COLUNAS}
        FROM solucoes
        ORDER BY id
    """

    with conectar_banco() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(consulta)
            return cursor.fetchall()


# ==========================================
# BUSCA SEMÂNTICA
# ==========================================

def pesquisar_por_similaridade(termo: str):
    embedding = gerar_embedding(termo)

    vetor = "[" + ",".join(
        str(valor) for valor in embedding
    ) + "]"

    consulta = f"""
        SELECT
            {COLUNAS},
            1 - (embedding <=> %s::vector)
                AS similaridade
        FROM solucoes
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> %s::vector ASC
    """

    with conectar_banco() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(consulta, (vetor, vetor))
            resultados = cursor.fetchall()

    logger.info(
        "[BUSCA SEMÂNTICA] Candidatos encontrados: %s",
        len(resultados)
    )

    for posicao, registro in enumerate(
        resultados, start=1
    ):
        logger.info(
            "[BUSCA SEMÂNTICA] Posição: %s | "
            "ID: %s | Título: %s | Similaridade: %.3f",
            posicao,
            registro[0],
            registro[1],
            registro[11]
        )

    return resultados


# ==========================================
# BUSCA TEXTUAL
# ==========================================

def pontuar_texto(registro, termos_consulta):
    titulo = registro[1]
    descricao = registro[2]
    categoria = registro[3]
    sintomas = registro[4]
    causa = registro[5]

    campos = [
        (titulo, 4),
        (sintomas, 3),
        (descricao, 2),
        (categoria, 2),
        (causa, 1)
    ]

    pontuacao = 0

    for conteudo, peso in campos:
        termos_campo = set(
            extrair_termos(conteudo or "")
        )

        correspondencias = (
            termos_consulta.intersection(termos_campo)
        )

        pontuacao += len(correspondencias) * peso

    return pontuacao


def pesquisar_por_palavras(
    termo: str,
    registros=None
):
    if registros is None:
        registros = carregar_solucoes()

    termos_originais = extrair_termos(termo)
    termos_expandidos = expandir_termos(
        termos_originais
    )

    logger.info(
        "[BUSCA TEXTUAL] Termos originais: %s",
        termos_originais
    )

    logger.info(
        "[BUSCA TEXTUAL] Termos expandidos: %s",
        sorted(termos_expandidos)
    )

    resultados = []

    for registro in registros:
        pontuacao = pontuar_texto(
            registro,
            termos_expandidos
        )

        if pontuacao >= PONTUACAO_TEXTUAL_MINIMA:
            resultados.append(
                (registro, pontuacao)
            )

    resultados.sort(
        key=lambda item: (
            -item[1],
            item[0][0]
        )
    )

    for posicao, (registro, pontuacao) in enumerate(
        resultados, start=1
    ):
        logger.info(
            "[BUSCA TEXTUAL] Posição: %s | "
            "ID: %s | Título: %s | Pontuação: %s",
            posicao,
            registro[0],
            registro[1],
            pontuacao
        )

    return resultados


# ==========================================
# COMBINAÇÃO DOS RANKINGS (RRF)
# ==========================================

def combinar_rankings(
    resultados_semanticos,
    resultados_textuais
):
    candidatos = {}

    # Ranking semântico
    for posicao, registro in enumerate(
        resultados_semanticos, start=1
    ):
        id_solucao = registro[0]

        candidatos[id_solucao] = {
            "registro": registro[:11],
            "similaridade": registro[11],
            "posicao_semantica": posicao,
            "posicao_textual": None,
            "pontuacao_textual": 0,
            "rrf": (
                PESO_SEMANTICO / (RRF_K + posicao)
            )
        }

    # Ranking textual
    for posicao, (registro, pontuacao) in enumerate(
        resultados_textuais, start=1
    ):
        id_solucao = registro[0]

        if id_solucao not in candidatos:
            candidatos[id_solucao] = {
                "registro": registro[:11],
                "similaridade": None,
                "posicao_semantica": None,
                "posicao_textual": None,
                "pontuacao_textual": 0,
                "rrf": 0.0
            }

        candidato = candidatos[id_solucao]

        candidato["posicao_textual"] = posicao
        candidato["pontuacao_textual"] = pontuacao

        candidato["rrf"] += (
            PESO_TEXTUAL / (RRF_K + posicao)
        )

    ordenados = sorted(
        candidatos.values(),
        key=lambda item: (
            -item["rrf"],
            -item["pontuacao_textual"],
            (
                item["posicao_semantica"]
                if item["posicao_semantica"] is not None
                else 999999
            )
        )
    )

    logger.info(
        "[BUSCA HÍBRIDA] Ranking combinado:"
    )

    for posicao, candidato in enumerate(
        ordenados, start=1
    ):
        registro = candidato["registro"]

        logger.info(
            "[BUSCA HÍBRIDA] Posição: %s | "
            "ID: %s | Título: %s | "
            "RRF: %.5f | Textual: %s | "
            "Semântica: %s",
            posicao,
            registro[0],
            registro[1],
            candidato["rrf"],
            candidato["pontuacao_textual"],
            candidato["posicao_semantica"]
        )

    # IMPORTANTE:
    # Retorna TODOS os candidatos para o filtro.
    # O limite será aplicado somente depois.
    return ordenados


# ==========================================
# FILTRO DE RELEVÂNCIA
# ==========================================

def filtrar_resultados_relevantes(resultados):
    """
    Filtra candidatos após a combinação RRF.

    Exige correspondência textual mínima e
    pontuação proporcional ao melhor candidato.

    Esta é uma heurística experimental:
    resultados semanticamente relevantes,
    mas sem correspondência textual, podem
    ser descartados.
    """

    if not resultados:
        return []

    melhor_pontuacao_textual = max(
        candidato["pontuacao_textual"]
        for candidato in resultados
    )

    if melhor_pontuacao_textual == 0:
        logger.info(
            "[FILTRO] Nenhum candidato apresentou "
            "correspondência textual."
        )
        return []

    pontuacao_minima_relativa = (
        melhor_pontuacao_textual
        * PROPORCAO_MINIMA_MELHOR_RESULTADO
    )

    selecionados = []

    for candidato in resultados:
        registro = candidato["registro"]
        pontuacao = candidato["pontuacao_textual"]

        aprovado = (
            pontuacao >= PONTUACAO_TEXTUAL_MINIMA_FILTRO
            and pontuacao >= pontuacao_minima_relativa
        )

        if aprovado:
            selecionados.append(candidato)

            logger.info(
                "[FILTRO] MANTIDO | ID: %s | "
                "Título: %s | Pontuação textual: %s",
                registro[0],
                registro[1],
                pontuacao
            )
        else:
            logger.info(
                "[FILTRO] DESCARTADO | ID: %s | "
                "Título: %s | Pontuação textual: %s",
                registro[0],
                registro[1],
                pontuacao
            )

    # Mantém a ordem determinada pelo RRF.
    return selecionados[:LIMITE_RESULTADOS]


# ==========================================
# FORMATAÇÃO PARA O AGENTE
# ==========================================

def formatar_resultados(
    resultados,
    tipo_busca: str
) -> str:
    respostas = []

    for candidato in resultados:
        (
            id_solucao,
            titulo,
            descricao,
            categoria,
            sintomas,
            causa,
            procedimento,
            validacao,
            fonte,
            dificuldade,
            revisado
        ) = candidato["registro"]

        status_revisao = (
            "Revisada" if revisado else "Não revisada"
        )

        similaridade = candidato["similaridade"]

        similaridade_texto = (
            f"{similaridade:.3f}"
            if similaridade is not None
            else "Não calculada"
        )

        resposta = f"""
SOLUÇÃO ID: {id_solucao}

Título: {titulo}

Categoria: {categoria}

Descrição: {descricao}

Sintomas:
{sintomas or 'Não informados'}

Causa provável:
{causa or 'Não informada'}

Procedimento:
{procedimento or 'Não informado'}

Como validar:
{validacao or 'Não informado'}

Fonte técnica:
{fonte or 'Não cadastrada'}

Nível de dificuldade:
{dificuldade or 'Não informado'}

Status de revisão:
{status_revisao}

Tipo de busca:
{tipo_busca}

Similaridade semântica:
{similaridade_texto}

Pontuação textual:
{candidato["pontuacao_textual"]}

Pontuação de fusão RRF:
{candidato["rrf"]:.5f}
"""

        respostas.append(resposta.strip())

    return "\n\n---\n\n".join(respostas)


# ==========================================
# FERRAMENTA DO AGENTE
# ==========================================

@function_tool
def buscar_solucoes(termo: str) -> str:
    """
    Pesquisa soluções técnicas no PostgreSQL.

    Combina busca semântica, busca textual,
    RRF e filtro de relevância.

    Retorna somente os registros selecionados
    para análise pelo agente de IA.
    """

    termo = termo.strip()

    if len(termo) < 3:
        return (
            "Descreva o problema com pelo menos "
            "3 caracteres."
        )

    logger.info(
        "[BUSCA] Termo pesquisado: %s",
        termo
    )

    try:
        # 1. Carregar os registros cadastrados.
        registros = carregar_solucoes()

        # 2. Executar a busca textual.
        resultados_textuais = pesquisar_por_palavras(
            termo,
            registros
        )

        # 3. Executar a busca semântica.
        try:
            resultados_semanticos = (
                pesquisar_por_similaridade(termo)
            )

        except Exception:
            logger.exception(
                "[BUSCA] Falha na busca semântica. "
                "Continuando com busca textual."
            )
            resultados_semanticos = []

        # 4. Verificar se há candidatos.
        if (
            not resultados_semanticos
            and not resultados_textuais
        ):
            return (
                "Nenhuma solução cadastrada apresentou "
                "correspondência com o problema. "
                "Não afirme que encontrou uma solução."
            )

        # 5. Combinar TODOS os candidatos.
        resultados_combinados = combinar_rankings(
            resultados_semanticos,
            resultados_textuais
        )

        # 6. Aplicar o filtro de relevância.
        resultados_filtrados = (
            filtrar_resultados_relevantes(
                resultados_combinados
            )
        )

        logger.info(
            "[FILTRO] Total de soluções selecionadas: %s",
            len(resultados_filtrados)
        )

        # 7. Tratar ausência de resultados relevantes.
        if not resultados_filtrados:
            logger.info(
                "[BUSCA] Nenhuma solução passou pelo filtro."
            )

            return (
                "A base de conhecimento foi consultada, "
                "mas nenhuma solução apresentou "
                "correspondência suficiente com o chamado. "
                "Não afirme que uma solução foi encontrada. "
                "Solicite informações adicionais ou "
                "sugira verificações iniciais de baixo risco."
            )

        # 8. Enviar somente os resultados selecionados.
        logger.info(
            "[BUSCA] Busca concluída com %s "
            "soluções relevantes.",
            len(resultados_filtrados)
        )

        return formatar_resultados(
            resultados_filtrados,
            "Híbrida com filtro de relevância"
        )

    except Exception:
        logger.exception(
            "[BUSCA] Erro ao consultar soluções."
        )

        return (
            "Não foi possível consultar a base "
            "de conhecimento neste momento. "
            "Não afirme que encontrou uma solução."
        )

