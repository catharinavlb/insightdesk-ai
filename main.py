
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from agents import Runner

from database import conectar_banco
from agente import agente


# Configuração do FastAPI
app = FastAPI(
    title="InsightDesk AI",
    description=(
        "API inteligente para gerenciamento e análise "
        "de chamados de suporte técnico."
    ),
    version="1.0.0"
)


# Permite que o frontend Vue se comunique com a API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Content-Type"],
)


# ----------------------------------------
# MODELOS DE DADOS
# ----------------------------------------

class PedidoAnalise(BaseModel):
    problema: str = Field(min_length=3)


class NovoChamado(BaseModel):
    titulo: str = Field(min_length=3, max_length=150)
    descricao: str = Field(min_length=3)


class AtualizacaoStatus(BaseModel):
    status: Literal[
        "aberto",
        "em andamento",
        "resolvido"
    ]


# ----------------------------------------
# PÁGINA INICIAL
# ----------------------------------------

@app.get(
    "/",
    summary="Página inicial",
    description="Verifica se a API está funcionando."
)
def pagina_inicial():
    return {
        "mensagem": "InsightDesk AI funcionando!"
    }


# ----------------------------------------
# CONSULTAR CHAMADOS
# ----------------------------------------

@app.get(
    "/chamados",
    summary="Consultar chamados",
    description="Retorna os chamados cadastrados."
)
def listar_chamados():
    with conectar_banco() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, titulo, descricao, status
                FROM chamados
                ORDER BY id
                """
            )

            registros = cursor.fetchall()

    chamados = []

    for registro in registros:
        chamados.append({
            "id": registro[0],
            "titulo": registro[1],
            "descricao": registro[2],
            "status": registro[3]
        })

    return chamados


# ----------------------------------------
# CADASTRAR NOVO CHAMADO
# ----------------------------------------

@app.post(
    "/chamados",
    status_code=201,
    summary="Cadastrar chamado",
    description="Cria um chamado no banco de dados."
)
def criar_chamado(chamado: NovoChamado):
    with conectar_banco() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO chamados (
                    titulo,
                    descricao,
                    status
                )
                VALUES (%s, %s, 'aberto')
                RETURNING
                    id,
                    titulo,
                    descricao,
                    status,
                    criado_em
                """,
                (
                    chamado.titulo,
                    chamado.descricao
                )
            )

            registro = cursor.fetchone()

    return {
        "id": registro[0],
        "titulo": registro[1],
        "descricao": registro[2],
        "status": registro[3],
        "criado_em": registro[4]
    }


# ----------------------------------------
# ATUALIZAR STATUS DO CHAMADO
# ----------------------------------------

@app.patch(
    "/chamados/{chamado_id}/status",
    summary="Atualizar status",
    description="Altera o status de um chamado."
)
def atualizar_status(
    chamado_id: int,
    atualizacao: AtualizacaoStatus
):
    with conectar_banco() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(
                """
                UPDATE chamados
                SET status = %s
                WHERE id = %s
                RETURNING id, titulo, status
                """,
                (
                    atualizacao.status,
                    chamado_id
                )
            )

            registro = cursor.fetchone()

    if registro is None:
        raise HTTPException(
            status_code=404,
            detail="Chamado não encontrado."
        )

    return {
        "id": registro[0],
        "titulo": registro[1],
        "status": registro[2]
    }


# ----------------------------------------
# CONSULTAR SOLUÇÕES
# ----------------------------------------

@app.get(
    "/solucoes",
    summary="Consultar soluções",
    description="Retorna as soluções cadastradas."
)
def listar_solucoes():
    with conectar_banco() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    titulo,
                    descricao,
                    categoria
                FROM solucoes
                ORDER BY id
                """
            )

            registros = cursor.fetchall()

    solucoes = []

    for registro in registros:
        solucoes.append({
            "id": registro[0],
            "titulo": registro[1],
            "descricao": registro[2],
            "categoria": registro[3]
        })

    return solucoes


# ----------------------------------------
# BUSCAR SOLUÇÕES
# ----------------------------------------

@app.get(
    "/solucoes/buscar",
    summary="Buscar soluções",
    description="Pesquisa soluções por palavras-chave."
)
def buscar_solucoes(termo: str):
    with conectar_banco() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    titulo,
                    descricao,
                    categoria
                FROM solucoes
                WHERE titulo ILIKE %s
                   OR descricao ILIKE %s
                   OR categoria ILIKE %s
                ORDER BY id
                """,
                (
                    f"%{termo}%",
                    f"%{termo}%",
                    f"%{termo}%"
                )
            )

            registros = cursor.fetchall()

    resultados = []

    for registro in registros:
        resultados.append({
            "id": registro[0],
            "titulo": registro[1],
            "descricao": registro[2],
            "categoria": registro[3]
        })

    return resultados


# ----------------------------------------
# ANÁLISE COM INTELIGÊNCIA ARTIFICIAL
# ----------------------------------------

@app.post(
    "/agente/analisar",
    summary="Analisar chamado com IA",
    description=(
        "Consulta o agente para sugerir "
        "uma solução de suporte técnico."
    )
)
async def analisar_chamado(pedido: PedidoAnalise):
    resultado = await Runner.run(
        agente,
        (
            f"Chamado de suporte: {pedido.problema}\n"
            "Consulte a base de soluções e responda "
            "de forma curta, sem mostrar IDs "
            "ou dados internos."
        )
    )

    return {
        "problema": pedido.problema,
        "resposta": resultado.final_output
    }
