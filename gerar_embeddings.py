
import requests

from database import conectar_banco


OLLAMA_URL = "http://127.0.0.1:11434/api/embed"
MODELO_EMBEDDING = "nomic-embed-text"
DIMENSOES = 768


def gerar_embedding(texto):
    resposta = requests.post(
        OLLAMA_URL,
        json={
            "model": MODELO_EMBEDDING,
            "input": texto,
        },
        timeout=120,
    )

    resposta.raise_for_status()

    dados = resposta.json()
    embeddings = dados.get("embeddings", [])

    if not embeddings:
        raise ValueError(
            "O Ollama não retornou um embedding."
        )

    embedding = embeddings[0]

    if len(embedding) != DIMENSOES:
        raise ValueError(
            f"Dimensão inesperada: {len(embedding)}"
        )

    return embedding


def preparar_texto(solucao):
    titulo, descricao, categoria, sintomas = solucao

    partes = [
        f"Título: {titulo or ''}",
        f"Descrição do problema: {descricao or ''}",
        f"Categoria: {categoria or ''}",
        f"Sintomas: {sintomas or ''}",
    ]

    return "\n".join(partes)


def atualizar_embeddings():
    conexao = conectar_banco()

    try:
        with conexao.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    titulo,
                    descricao,
                    categoria,
                    sintomas
                FROM solucoes
                ORDER BY id
                """
            )

            solucoes = cursor.fetchall()

            print(
                f"Soluções encontradas: {len(solucoes)}"
            )

            for solucao in solucoes:
                solucao_id = solucao[0]
                titulo = solucao[1]

                texto = preparar_texto(
                    solucao[1:]
                )

                embedding = gerar_embedding(texto)

                vetor = "[" + ",".join(
                    str(valor) for valor in embedding
                ) + "]"

                cursor.execute(
                    """
                    UPDATE solucoes
                    SET embedding = %s::vector
                    WHERE id = %s
                    """,
                    (vetor, solucao_id),
                )

                print(
                    f"Embedding atualizado: "
                    f"{solucao_id} - {titulo}"
                )

        conexao.commit()
        print("Todos os embeddings foram atualizados!")

    except Exception:
        conexao.rollback()
        raise

    finally:
        conexao.close()


if __name__ == "__main__":
    atualizar_embeddings()
