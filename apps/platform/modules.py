from dataclasses import dataclass
from enum import Enum


class Module(str, Enum):
    CORE = "core"
    AGENDA = "agenda"
    ATENDIMENTO = "atendimento"
    EXAME = "exame"
    QC = "qc"
    COMUNICACAO = "comunicacao"
    PORTAL_PACIENTE = "portal_paciente"
    TISS = "tiss"
    ESTOQUE = "estoque"
    INTEGRACOES = "integracoes"


@dataclass(frozen=True)
class ModuleInfo:
    key: str
    label: str
    description: str
    icon: str  # nome do ícone Lucide


MODULE_REGISTRY: dict[Module, ModuleInfo] = {
    Module.CORE: ModuleInfo(
        key="core",
        label="Gestão de Pacientes",
        description="Cadastro e gestão de pacientes e funcionários.",
        icon="users",
    ),
    Module.AGENDA: ModuleInfo(
        key="agenda",
        label="Agenda e Fila",
        description="Ordem de chegada, agendamento e planos de preço.",
        icon="calendar",
    ),
    Module.ATENDIMENTO: ModuleInfo(
        key="atendimento",
        label="Atendimento e Financeiro",
        description="Orçamentos, pagamentos e relatórios financeiros.",
        icon="receipt",
    ),
    Module.EXAME: ModuleInfo(
        key="exame",
        label="Exames e Laudos",
        description="Catálogo de exames, resultados e geração de laudos PDF.",
        icon="flask-conical",
    ),
    Module.QC: ModuleInfo(
        key="qc",
        label="Controle de Qualidade",
        description="QC analítico, gráfico de Levey-Jennings e regras de Westgard.",
        icon="activity",
    ),
    Module.COMUNICACAO: ModuleInfo(
        key="comunicacao",
        label="Comunicação",
        description="Notificações por e-mail, SMS e WhatsApp Business.",
        icon="bell",
    ),
    Module.PORTAL_PACIENTE: ModuleInfo(
        key="portal_paciente",
        label="Portal do Paciente",
        description="Acesso do paciente aos próprios laudos via CPF e data de nascimento.",
        icon="user-circle",
    ),
    Module.TISS: ModuleInfo(
        key="tiss",
        label="Convênios e TISS",
        description="Faturamento de convênios e geração de XML TISS para ANS.",
        icon="file-text",
    ),
    Module.ESTOQUE: ModuleInfo(
        key="estoque",
        label="Estoque e Reagentes",
        description="Controle de reagentes com rastreabilidade por lote e validade.",
        icon="package",
    ),
    Module.INTEGRACOES: ModuleInfo(
        key="integracoes",
        label="Integrações",
        description="HL7 FHIR R4 e integrações com sistemas hospitalares (HIS/RIS).",
        icon="git-branch",
    ),
}

# Módulos incluídos em cada plano.
# CORE é implícito em todos — nunca pode ser desabilitado.
PLAN_MODULES: dict[str, frozenset[Module]] = {
    "FREE_TRIAL": frozenset({
        Module.CORE,
        Module.AGENDA,
        Module.ATENDIMENTO,
    }),
    "BASIC": frozenset({
        Module.CORE,
        Module.AGENDA,
        Module.ATENDIMENTO,
    }),
    "PROFESSIONAL": frozenset({
        Module.CORE,
        Module.AGENDA,
        Module.ATENDIMENTO,
        Module.EXAME,
        Module.QC,
        Module.COMUNICACAO,
        Module.PORTAL_PACIENTE,
    }),
    "ENTERPRISE": frozenset({
        Module.CORE,
        Module.AGENDA,
        Module.ATENDIMENTO,
        Module.EXAME,
        Module.QC,
        Module.COMUNICACAO,
        Module.PORTAL_PACIENTE,
        Module.TISS,
        Module.ESTOQUE,
        Module.INTEGRACOES,
    }),
}

# Módulos que NUNCA podem ser desabilitados, independente do plano ou override.
MANDATORY_MODULES: frozenset[Module] = frozenset({Module.CORE})


def get_modules_for_plan(plan: str) -> frozenset[Module]:
    """Retorna os módulos incluídos em um plano. Retorna apenas CORE para planos desconhecidos."""
    return PLAN_MODULES.get(plan, frozenset({Module.CORE}))


def get_effective_modules(tenant) -> frozenset[Module]:
    """
    Computa o conjunto efetivo de módulos ativos para um tenant:
        (módulos do plano ∪ módulos extras) − módulos desabilitados ∪ MANDATORY_MODULES

    Os módulos obrigatórios (CORE) nunca são removidos, mesmo que estejam em
    `modulos_desabilitados`.
    """
    base = get_modules_for_plan(tenant.plan)

    extras: frozenset[Module] = frozenset(
        Module(m)
        for m in (tenant.modulos_extras or [])
        if m in Module._value2member_map_
    )
    disabled: frozenset[Module] = frozenset(
        Module(m)
        for m in (tenant.modulos_desabilitados or [])
        if m in Module._value2member_map_
    )

    return (base | extras | MANDATORY_MODULES) - (disabled - MANDATORY_MODULES)
