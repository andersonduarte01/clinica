# Re-exporta todas as views legadas para que apps/core/urls.py continue funcionando
# sem alterações enquanto a migração para a API REST não é concluída.
from apps.core.views_legacy import (
    Home, Sobre, Servicos, Blog, Contato,
    Painel,
    Cadastrar, AtualizarUser, CadastrarFuncionario,
    EnderecoCad,
    custom_login_redirect,
    Pacientes, Funcionarios,
    MostrarPerfil, AtualizarPerfil, AtualizarEndereco, AtualizarSenha,
    BuscarAtendimentoPaciente, BuscarOpcoesPaciente, OpcoesPaciente,
    buscar_atendimento_paciente, buscar_paciente,
    Erro400, Erro500,
)
