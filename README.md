# InsightDesk AI

Sistema de gerenciamento de chamados de suporte técnico com inteligência artificial, desenvolvido como projeto de portfólio para aplicar conhecimentos de desenvolvimento web, banco de dados e integração de IA.

O sistema permite registrar e acompanhar chamados técnicos, além de consultar um agente de inteligência artificial que utiliza uma base de conhecimento para sugerir possíveis causas e procedimentos de resolução.

## Funcionalidades

- Cadastro de chamados com título e descrição.
- Listagem e acompanhamento dos chamados registrados.
- Atualização de status: aberto, em andamento e resolvido.
- Dashboard com indicadores de chamados.
- Análise de problemas técnicos com inteligência artificial.
- Análise individual de chamados cadastrados.
- Consulta a uma base de soluções armazenada no PostgreSQL.
- Busca híbrida, combinando similaridade semântica e correspondência textual.
- Apresentação de orientações técnicas, possíveis causas e procedimentos de validação.

## Tecnologias utilizadas

### Frontend
- Vue 3
- JavaScript
- HTML e CSS
- Vite
- Marked e DOMPurify para exibição segura de respostas em Markdown

### Backend
- Python
- FastAPI
- OpenAI Agents SDK

### Banco de dados
- PostgreSQL
- pgvector para armazenamento e consulta de embeddings

### Inteligência artificial
- Ollama para execução local dos modelos
- Qwen3:4b para geração das respostas
- nomic-embed-text para geração de embeddings
- RAG (Retrieval-Augmented Generation)

## Como funciona

O InsightDesk AI possui duas funcionalidades principais: gerenciamento de chamados e análise técnica com IA.

No gerenciamento de chamados, o frontend envia requisições à API FastAPI, que realiza as operações necessárias no PostgreSQL.

Na análise com IA, o fluxo funciona da seguinte forma:

1. O usuário descreve um problema técnico ou seleciona um chamado cadastrado.
2. O frontend envia a descrição para a API.
3. O agente de IA utiliza uma ferramenta para consultar a base de soluções.
4. O sistema realiza uma busca híbrida, combinando correspondência textual e similaridade semântica por embeddings.
5. Um filtro seleciona as soluções consideradas mais relevantes.
6. As informações recuperadas são disponibilizadas ao agente como contexto.
7. O modelo de linguagem gera uma orientação técnica com possíveis causas, procedimentos recomendados e formas de validação.

Essa abordagem utiliza RAG para apoiar as respostas com informações cadastradas na base de conhecimento.

As sugestões geradas pela IA devem ser verificadas antes de sua aplicação em ambientes reais.

## Estrutura do projeto

```text
insightdesk-ia/
├── frontend/              # Interface web em Vue 3
├── agente.py              # Configuração do agente de IA
├── ferramentas.py         # Busca de soluções e recuperação de contexto
├── database.py            # Conexão com PostgreSQL
├── gerar_embeddings.py    # Geração de embeddings das soluções
├── main.py                # API FastAPI
├── .gitignore
└── README.md
```

## Como executar localmente

### Pré-requisitos

- Python
- Node.js e npm
- PostgreSQL com extensão pgvector
- Ollama
- Git

### 1. Clonar o repositório

```bash
git clone https://github.com/catharinavlb/insightdesk-ai.git
cd insightdesk-ai
```

### 2. Configurar o banco de dados

Crie um banco PostgreSQL chamado `insightdesk_ai` e habilite a extensão pgvector.

Execute os scripts SQL nesta ordem, conectando-se ao banco criado:

```sql
-- Primeiro: criar as tabelas
-- Execute o conteúdo de schema.sql

-- Depois: cadastrar soluções de exemplo
-- Execute o conteúdo de seed.sql
```

Crie um arquivo `.env` na pasta principal, utilizando `.env.example` como referência:

```dotenv
DB_HOST=localhost
DB_PORT=5432
DB_NAME=insightdesk_ai
DB_USER=postgres
DB_PASSWORD=sua_senha_local
```

Substitua os valores pelos dados da sua instalação. Não publique o arquivo `.env`.

Após instalar as dependências Python e iniciar o Ollama com o modelo de embeddings disponível, execute:

```bash
python gerar_embeddings.py
```

Esse comando gera e armazena os embeddings das soluções, necessários para a busca semântica.

### 3. Preparar o backend

Crie e ative um ambiente virtual Python.

No Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Instale as dependências Python necessárias para executar a API, acessar o PostgreSQL e utilizar o agente de IA.

### 4. Preparar os modelos de IA

Com o Ollama instalado, baixe os modelos:

```bash
ollama pull qwen3:4b
ollama pull nomic-embed-text
```

Inicie o serviço do Ollama, caso ele não esteja em execução.

O modelo `qwen3:4b` é utilizado para gerar as orientações técnicas, enquanto `nomic-embed-text` é responsável pela representação vetorial dos textos.

### 5. Executar o backend

Na pasta principal do projeto:

```bash
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

A documentação interativa da API ficará disponível em:

`http://127.0.0.1:8000/docs`

### 6. Executar o frontend

Em outro terminal:

```bash
cd frontend
npm install
npm run dev
```

Acesse a aplicação no endereço indicado pelo Vite, normalmente:

`http://localhost:5173`

**Observação:** a execução completa requer um banco PostgreSQL configurado e populado com soluções técnicas, além dos embeddings correspondentes. O repositório ainda não inclui um processo automatizado de preparação inicial do banco.

## Objetivo do projeto

O InsightDesk AI foi desenvolvido para colocar em prática conceitos de:

- Desenvolvimento e integração de aplicações frontend e backend.
- Criação e consumo de APIs REST.
- Modelagem, armazenamento e consulta de dados relacionais.
- Integração de modelos de linguagem em aplicações.
- Recuperação de informações com RAG e busca vetorial.
- Organização de um projeto de software para portfólio.

## Status

Primeira versão funcional, desenvolvida para fins de estudo e portfólio.

## Autoria

Desenvolvido por [Catharina](https://github.com/catharinavlb).