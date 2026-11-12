-- Estrutura do banco de dados InsightDesk AI
-- Execute após criar o banco insightdesk_ai.

CREATE EXTENSION IF NOT EXISTS vector;

-- Chamados de suporte técnico
CREATE TABLE IF NOT EXISTS chamados (
    id SERIAL PRIMARY KEY,
    titulo VARCHAR(150) NOT NULL,
    descricao TEXT NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'aberto',
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Base de conhecimento utilizada pelo agente de IA
CREATE TABLE IF NOT EXISTS solucoes (
    id SERIAL PRIMARY KEY,
    titulo VARCHAR(255) NOT NULL,
    descricao TEXT,
    categoria VARCHAR(100),
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sintomas TEXT,
    causa_provavel TEXT,
    procedimento TEXT,
    validacao TEXT,
    fonte_url TEXT,
    nivel_dificuldade VARCHAR(20) DEFAULT 'basico',
    revisado BOOLEAN DEFAULT FALSE,
    embedding vector(768)
);