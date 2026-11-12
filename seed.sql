-- Dados de exemplo para a base de conhecimento
-- Execute depois do schema.sql.

INSERT INTO solucoes (
    titulo,
    descricao,
    categoria,
    sintomas,
    causa_provavel,
    procedimento,
    validacao,
    nivel_dificuldade,
    revisado
)
VALUES
(
    'Erro HTTP 403 ao acessar um sistema',
    'O usuário recebe uma mensagem de acesso negado ao tentar utilizar uma funcionalidade.',
    'Acesso e permissões',
    'Acesso bloqueado, autorização insuficiente ou mensagem HTTP 403.',
    'Permissões insuficientes ou configuração incorreta de autorização.',
    'Verificar as permissões da conta e solicitar análise ao administrador do sistema.',
    'Confirmar que o usuário consegue acessar o recurso autorizado.',
    'basico',
    FALSE
),
(
    'Lentidão no sistema',
    'O sistema apresenta demora para carregar páginas ou responder aos comandos.',
    'Desempenho',
    'Carregamento lento e demora nas operações.',
    'Problemas de conexão, sobrecarga ou desempenho da aplicação.',
    'Verificar a conexão, identificar quando ocorre a lentidão e consultar os registros do sistema.',
    'Repetir a operação e verificar se o tempo de resposta melhorou.',
    'basico',
    FALSE
),
(
    'Falha no recebimento de notificações por e-mail',
    'O usuário não recebe notificações enviadas pela plataforma.',
    'Notificações',
    'E-mails não recebidos ou notificações ausentes.',
    'Endereço incorreto, filtros de spam ou falha no serviço de envio.',
    'Confirmar o endereço cadastrado, verificar spam e consultar os registros de envio.',
    'Enviar uma notificação de teste e confirmar o recebimento.',
    'basico',
    FALSE
),
(
    'Erro ao gerar relatório em sistema web',
    'A aplicação apresenta uma falha ao tentar gerar ou exportar relatórios.',
    'Relatórios',
    'Falha na geração, arquivo não criado ou erro na exportação.',
    'Falha no processamento, permissões insuficientes ou problema na geração do arquivo.',
    'Verificar os filtros utilizados, as permissões e os registros de erro da aplicação.',
    'Gerar novamente o relatório e confirmar que o arquivo foi criado corretamente.',
    'basico',
    FALSE
);