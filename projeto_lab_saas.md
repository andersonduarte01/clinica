# Documento de Projeto — LabSaaS: Sistema de Gestão de Laboratório Clínico

**Versão:** 1.0.0  
**Data:** 2026-06-24  
**Autor:** Equipe de Arquitetura  
**Status:** Referência Técnica Oficial

---

## Sumário

1. [Visão Geral e Objetivos](#1-visão-geral-e-objetivos)
2. [Arquitetura Geral](#2-arquitetura-geral)
3. [Modelagem de Dados](#3-modelagem-de-dados)
4. [Módulos do Sistema](#4-módulos-do-sistema)
5. [API e Integrações](#5-api-e-integrações)
6. [Frontend](#6-frontend)
7. [Segurança](#7-segurança)
8. [Infraestrutura e DevOps](#8-infraestrutura-e-devops)
9. [Testes](#9-testes)
10. [Migração do Sistema Atual](#10-migração-do-sistema-atual)
11. [Roadmap de Implementação](#11-roadmap-de-implementação)
12. [Padrões de Código e Convenções](#12-padrões-de-código-e-convenções)
13. [Glossário](#13-glossário)

---

# 1. Visão Geral e Objetivos

## 1.1 Descrição do Produto

O **LabSaaS** é uma plataforma de gestão laboratorial clínica entregue como Software as a Service (SaaS) multitenancy. O sistema digitaliza e integra os fluxos operacionais de laboratórios de análises clínicas: recepção de pacientes, coleta e triagem de amostras biológicas, realização e validação de exames, emissão de laudos digitais assinados, gestão financeira e faturamento de convênios.

O produto serve laboratórios de análises clínicas de pequeno, médio e grande porte, clínicas médicas com serviço de coleta próprio, e redes de laboratórios com múltiplas unidades. Cada laboratório cliente (denominado **tenant**) opera em ambiente isolado dentro da plataforma compartilhada, com dados, configurações e identidade visual próprios.

O problema central que o LabSaaS resolve é a fragmentação tecnológica do setor: a maioria dos laboratórios brasileiros de pequeno e médio porte opera com sistemas locais desatualizados, planilhas paralelas e processos manuais que causam erros de identificação de amostras, atrasos na entrega de laudos, perda de receita por subcobrança de convênios e dificuldade de rastreabilidade para fins de acreditação (PALC, ISO 15189).

## 1.2 Proposta de Valor do Modelo SaaS Multiclinicas

| Dimensão | Sistema Local (modelo atual) | LabSaaS (modelo SaaS) |
|---|---|---|
| Infraestrutura | Responsabilidade do cliente (servidor local, backup manual) | Gerenciada pela plataforma (cloud, backup automático, 99,9% SLA) |
| Atualizações | Agendadas com técnico, custo por visita | Contínuas, sem interrupção, sem custo adicional |
| Acesso remoto | VPN ou TeamViewer — frágil | HTTPS nativo de qualquer dispositivo |
| Multi-unidade | Sistemas separados sem integração | Uma conta, todas as unidades, dados consolidados |
| Custo inicial | Alto (licença perpétua + hardware) | Zero (mensalidade por uso) |
| Escalonamento | Compra de hardware adicional | Automático via cloud |
| Conformidade LGPD | Responsabilidade isolada do cliente | Modelo de responsabilidade compartilhada com controles auditáveis |
| Laudos digitais | PDF local sem assinatura válida | Assinatura eletrônica com validade jurídica (MP 2.200-2/2001) |

A decisão de construir como SaaS multiclinicas é motivada por três fatores: (a) redução do custo de operação por economia de escala na infraestrutura compartilhada; (b) capacidade de oferecer funcionalidades que seriam inviáveis para um laboratório manter individualmente (integração TISS, QC analítico com gráficos de Levey-Jennings, portal do paciente); (c) modelo de receita recorrente previsível para o provedor da plataforma.

## 1.3 Objetivos Mensuráveis

| Objetivo | Métrica | Meta |
|---|---|---|
| Disponibilidade da plataforma | Uptime mensal medido por monitoramento externo | ≥ 99,9% (downtime máximo de 43 min/mês) |
| Tempo de entrega de laudo (TAT) | Tempo entre coleta e laudo disponível para o paciente | ≤ 4 horas para exames de rotina |
| Onboarding de novo tenant | Tempo entre cadastro e primeiro atendimento real | ≤ 2 dias úteis |
| Tempo de resposta da API | P95 de latência em endpoints críticos | ≤ 300ms |
| Cobertura de testes | Percentual de código de domínio crítico coberto | ≥ 80% |
| Tempo de geração de laudo PDF | Geração server-side de laudo completo | ≤ 5 segundos |
| Notificação de valor crítico | Tempo entre detecção e notificação ao médico solicitante | ≤ 5 minutos |
| Retenção de dados de prontuário | Conformidade com CFM 1821/2007 | 20 anos mínimo |

## 1.4 Personas

### 1.4.1 Administrador da Clínica (`admin_clinica`)
Responsável pelo laboratório ou clínica. Configura o sistema (planos de preço, convênios, equipe, parâmetros de exames), acessa relatórios gerenciais e financeiros, aprova orçamentos acima de limite configurável. Não realiza exames, mas precisa de visão completa de todos os dados do seu tenant. Acesso via navegador desktop. Nível de familiaridade tecnológica: intermediário.

### 1.4.2 Biomédico (`biomedico`)
Profissional responsável pela análise técnica dos exames. Acessa a área restrita para preencher resultados, validar laudos, detectar e notificar valores críticos, registrar controle de qualidade e assinar digitalmente laudos. Trabalha em bancada com computador desktop ou notebook. Exige interface ágil e sem fricção para entrada de dados numéricos. Precisa de acesso 2FA obrigatório por lidar com dados clínicos sensíveis.

### 1.4.3 Recepcionista (`recepcionista`)
Realiza o atendimento inicial: cadastra pacientes, cria ordem de chegada na fila, gera orçamento, registra pagamento e entrega comprovante. Acessa etiquetas de amostra. Opera em balcão com teclado e mouse; velocidade de fluxo é crítica. Não acessa resultados de exames nem laudos.

### 1.4.4 Paciente (`paciente`)
Acessa o portal do paciente via CPF + data de nascimento (sem necessidade de senha) ou com conta criada. Visualiza histórico de atendimentos, baixa laudos disponíveis, recebe notificações de laudo pronto. Acesso predominantemente mobile. Interação esporádica — a interface deve ser autoexplicativa.

### 1.4.5 Gestor da Plataforma (`superadmin`)
Equipe interna do LabSaaS. Gerencia todos os tenants: cria, suspende, configura planos de assinatura, monitora uso e saúde da plataforma, clona exames-padrão entre tenants, acessa logs de auditoria globais. Nunca acessa dados clínicos de pacientes individuais — apenas metadados operacionais.

## 1.5 Fora de Escopo

Os itens abaixo não serão implementados neste projeto, independentemente de demanda:

- **Prontuário Eletrônico do Paciente (PEP/RES):** O LabSaaS é um sistema de informação laboratorial (LIS). Não armazena diagnósticos médicos, evoluções clínicas, prescrições ou qualquer dado de consulta médica.
- **Telemedicina:** Videoconferência, consultas remotas ou teleconsulta não fazem parte do produto.
- **Integração HL7 FHIR na Fase inicial:** A integração com sistemas hospitalares via FHIR R4 está planejada para a Fase 5 do roadmap; não será desenvolvida antes.
- **App mobile nativo (iOS/Android):** O acesso mobile será coberto pela interface web responsiva. Não será desenvolvido aplicativo nativo em nenhuma fase deste roadmap.
- **Módulo de contabilidade:** O sistema registra pagamentos e gera relatórios financeiros operacionais, mas não substitui software contábil. Não emite DRE, balanço patrimonial nem integra com SPED.
- **Gestão de RH e folha de pagamento:** Cadastro de funcionários existe apenas para controle de acesso ao sistema, sem módulo de ponto, férias ou salários.
- **Laudos de imagem (radiologia, ultrassonografia):** O sistema é voltado a análises clínicas (hematologia, bioquímica, microbiologia, parasitologia, imunologia). Laudos de imagem com DICOM não são suportados.

---

# 2. Arquitetura Geral

## 2.1 Diagrama Descritivo da Arquitetura

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            INTERNET / CLIENTES                          │
│  Navegador (Recepcionista, Biomédico, Admin)   Navegador (Paciente)     │
│  App Mobile Web (Portal Paciente)              Webhooks externos        │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │ HTTPS / TLS 1.3
┌──────────────────────────────▼──────────────────────────────────────────┐
│                         CDN (CloudFlare)                                │
│  - Assets estáticos (JS, CSS, imagens)                                  │
│  - Cache de laudos PDF públicos (com TTL curto)                         │
│  - WAF e proteção DDoS                                                  │
│  - Resolução de subdomínio: *.labsaas.com.br → origin                  │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────────────┐
│                      NGINX (Reverse Proxy)                              │
│  - Terminação SSL (certificado wildcard *.labsaas.com.br)              │
│  - Roteamento por Host header (subdomínio → app server)                 │
│  - Rate limiting por IP                                                 │
│  - Serve arquivos estáticos e media local (em dev)                      │
└──────┬───────────────────────────────────────────────┬──────────────────┘
       │                                               │
┌──────▼──────────────┐                   ┌───────────▼───────────────────┐
│   Gunicorn          │                   │   Uvicorn (ASGI)              │
│   Workers Síncronos │                   │   Workers Assíncronos         │
│   (API REST / Views)│                   │   (WebSocket / SSE — fila)    │
└──────┬──────────────┘                   └───────────┬───────────────────┘
       │                                               │
┌──────▼───────────────────────────────────────────────▼──────────────────┐
│                     DJANGO APPLICATION (Python 3.12)                    │
│                                                                         │
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────────────────┐ │
│  │  TenantMiddle-  │  │  DRF REST API    │  │  Django Views (HTMX)   │ │
│  │  ware           │  │  /api/v1/        │  │  Templates + Alpine.js  │ │
│  │  (resolução de  │  │  JWT Auth        │  │  shadcn/ui             │ │
│  │  tenant por     │  │  Serializers     │  │                        │ │
│  │  subdomínio)    │  │  Viewsets        │  │                        │ │
│  └─────────────────┘  └──────────────────┘  └────────────────────────┘ │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    CAMADA DE SERVIÇOS DE DOMÍNIO                │   │
│  │  services/atendimento.py  services/exame.py  services/fila.py  │   │
│  │  services/laudo.py        services/qc.py     services/tiss.py  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                       REPOSITÓRIOS / ORM                        │   │
│  │  QuerySets customizados, Managers por tenant, soft delete       │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└──────┬──────────────────────────────────────────────────────────────────┘
       │
┌──────▼──────────────────────────────────────────────────────────────────┐
│                         CAMADA DE DADOS E SERVIÇOS                      │
│                                                                         │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────┐  │
│  │  PostgreSQL 16   │  │  Redis 7         │  │  S3-compatible       │  │
│  │  - Schema único  │  │  - Cache Django  │  │  (Cloudflare R2 /    │  │
│  │    com tenant_id │  │  - Celery broker │  │   MinIO em dev)      │  │
│  │  - Row-level sec │  │  - Canal Django  │  │  - Laudos PDF        │  │
│  │  - Backups diár. │  │    Channels      │  │  - Uploads de exames │  │
│  └──────────────────┘  └──────────────────┘  │  - Logos de tenants  │  │
│                                               └──────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                     CELERY WORKERS                               │   │
│  │  - Geração de laudos PDF (WeasyPrint — CPU intensivo)           │   │
│  │  - Envio de notificações (e-mail, SMS, WhatsApp)                │   │
│  │  - Geração de relatórios pesados                                │   │
│  │  - Verificação de valores críticos (pós-salvamento de resultado) │   │
│  │  - Sincronização TISS, NFS-e                                    │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

## 2.2 Padrão Arquitetural

**Escolha: Monólito Modular com separação por domínios**

O sistema é implementado como um único processo Django com módulos internos bem definidos e fronteiras de domínio explícitas — não como microserviços independentes. A justificativa é tripla:

**Por que não microserviços:** O sistema tem menos de 10 desenvolvedores na fase inicial. Microserviços introduzem sobrecarga operacional (service discovery, circuit breakers, tracing distribuído, múltiplos deployments) que é desproporcional para equipes pequenas. Falhas de comunicação entre serviços são uma categoria inteira de bugs que o monólito elimina. Martin Fowler denomina esse antipadrão de "microserviços prematuros". A complexidade transacional do domínio (um atendimento toca fila + orçamento + exames + pagamento em uma mesma operação) se torna orquestração distribuída complexa se quebrada em serviços.

**Por que monólito modular e não monólito acoplado:** Cada domínio de negócio (atendimento, exame, agenda, etc.) é um pacote Python com imports explícitos. Comunicação entre domínios ocorre apenas via interfaces de serviço — nunca por import direto de models de outro app. Isso preserva a opção de extrair um módulo como serviço independente no futuro, quando o volume justificar, sem reescrita.

**Separação de responsabilidades dentro do monólito:**
- `presentation/` — Views Django, serializers DRF, templates
- `services/` — Lógica de negócio pura, sem dependência de HTTP ou ORM direto
- `repositories/` — QuerySets e Managers, única camada que toca o ORM
- `tasks/` — Tasks Celery, que chamam serviços
- `models/` — Entidades e relacionamentos, sem lógica de negócio pesada

## 2.3 Estratégia de Multitenancy

**Escolha: Row-Level Multitenancy (campo `tenant` em cada tabela)**

A alternativa descartada foi o schema-based multitenancy (um schema PostgreSQL por tenant, usando `SET search_path`). As razões do descarte:

- **Complexidade de migrations:** Com Django, cada nova migration precisa ser aplicada em todos os schemas de tenants existentes — um loop com potencial de falha parcial que não tem rollback simples.
- **Conexões de banco:** PostgreSQL por padrão permite 100 conexões simultâneas. Com schema-per-tenant, cada tenant com conexão ativa consome conexões separadas; com row-level, todos os tenants compartilham o mesmo pool.
- **Backups e restore:** Backup por tenant é mais complexo com schemas separados do que com row-level filtrado por `tenant_id`.
- **Custo operacional:** Schema-based exige scripts de provisionamento mais complexos a cada novo tenant.

**Implementação Row-Level:**

```python
# apps/core/models/base.py
from django.db import models


class TenantAwareModel(models.Model):
    tenant = models.ForeignKey(
        "platform.Tenant",
        on_delete=models.CASCADE,
        db_index=True,
        editable=False,
    )

    class Meta:
        abstract = True


class TenantAwareManager(models.Manager):
    def get_queryset(self):
        # Thread-local storage injeta o tenant atual
        from apps.platform.middleware import get_current_tenant
        tenant = get_current_tenant()
        if tenant is None:
            return super().get_queryset().none()
        return super().get_queryset().filter(tenant=tenant)
```

**Proteção adicional com PostgreSQL Row-Level Security (RLS):**

Mesmo com o manager filtrando por tenant, adiciona-se uma política RLS no PostgreSQL como segunda camada de defesa — mesmo que um bug no código Python permita um queryset sem filtro de tenant, o banco bloqueará o acesso a dados de outro tenant.

```sql
-- Executado uma vez por tabela tenant-aware
ALTER TABLE exame_exame ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON exame_exame
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid);
```

O middleware injeta `SET app.current_tenant_id = '<uuid>'` em cada transação.

**Mitigação do risco principal do row-level:** O risco de "tenant leak" (retornar dados de outro tenant) é mitigado por: (a) manager padrão filtra automaticamente, (b) RLS no PostgreSQL como fallback, (c) testes de isolamento de tenant no CI (ver Seção 9).

## 2.4 Camadas da Aplicação

```
┌─────────────────────────────────────────────────────┐
│  APRESENTAÇÃO                                       │
│  Views Django (HTMX), Serializers DRF, Templates   │
│  Responsabilidade: receber request, validar entrada,│
│  chamar serviço, serializar resposta. Sem lógica de │
│  negócio.                                           │
├─────────────────────────────────────────────────────┤
│  API (DRF)                                          │
│  ViewSets, Routers, Permissions, Throttling         │
│  Responsabilidade: autenticação JWT, serialização,  │
│  paginação, documentação OpenAPI.                   │
├─────────────────────────────────────────────────────┤
│  SERVIÇOS DE DOMÍNIO                                │
│  services/*.py — funções e classes puras            │
│  Responsabilidade: regras de negócio, cálculos,     │
│  orquestração de operações, sem dependência de HTTP │
│  ou ORM direto.                                     │
├─────────────────────────────────────────────────────┤
│  REPOSITÓRIOS                                       │
│  Managers, QuerySets customizados                   │
│  Responsabilidade: única camada que escreve SQL     │
│  (via ORM). Filtragem por tenant centralizada aqui. │
├─────────────────────────────────────────────────────┤
│  MODELOS                                            │
│  Django Models — entidades, relacionamentos,        │
│  propriedades derivadas simples. Sem chamadas HTTP, │
│  sem lógica de orçamento ou cálculo complexo.       │
└─────────────────────────────────────────────────────┘
```

## 2.5 Componentes de Infraestrutura

| Componente | Tecnologia | Justificativa |
|---|---|---|
| App Server (sync) | Gunicorn 22+ com workers gevent | Compatível com Django síncrono, battle-tested em produção |
| App Server (async) | Uvicorn + Django Channels | Necessário para WebSocket de atualização de fila em tempo real |
| Reverse Proxy | Nginx 1.25+ | Terminação SSL, roteamento de subdomínio, servir estáticos |
| Banco de dados | PostgreSQL 16 | ACID, RLS, JSONB para configurações, extensão pgcrypto para criptografia |
| Cache | Redis 7 | Cache de sessão, broker Celery, pub/sub para Django Channels |
| Fila de tarefas | Celery 5+ com Redis broker | Geração de PDF, notificações, TISS — operações lentas fora do request |
| Storage de arquivos | S3-compatible (Cloudflare R2) | Laudos PDF, uploads — R2 sem custo de egress, compatível com boto3 |
| CDN | Cloudflare | Proteção DDoS, WAF, cache de assets, resolução wildcard DNS |
| Monitoramento de erros | Sentry | Rastreamento de exceções com contexto de tenant |
| Métricas | Prometheus + Grafana | Latência, filas, uso por tenant |
| Logs estruturados | structlog + Loki | Logs JSON indexáveis com campo `tenant_id` |

## 2.6 Estratégia de Ambientes

**Desenvolvimento local:**
```
# .env.development (nunca commitado — apenas .env.example)
DJANGO_SETTINGS_MODULE=config.settings.development
DATABASE_URL=postgres://labsaas:labsaas@localhost:5432/labsaas_dev
REDIS_URL=redis://localhost:6379/0
AWS_S3_ENDPOINT_URL=http://localhost:9000  # MinIO local
DEBUG=True
SECRET_KEY=dev-secret-key-only-local
```

**Staging:**
- Banco de dados PostgreSQL separado com dados anonimizados da produção (dump mensal com CPFs substituídos)
- Redis separado
- S3 bucket separado
- URL: `staging.labsaas.com.br` e `*.staging.labsaas.com.br`
- Deploy automático a cada merge na branch `main`

**Produção:**
- Secrets gerenciados via AWS Secrets Manager ou Doppler (nunca variáveis de ambiente hardcoded na imagem Docker)
- Banco de dados com réplica de leitura para relatórios pesados
- Redis com Sentinel para alta disponibilidade
- Deploy via GitHub Actions com aprovação manual obrigatória para produção

**Carregamento de settings por ambiente:**
```python
# config/settings/__init__.py — vazio
# config/settings/base.py — configurações comuns
# config/settings/development.py — importa base, sobrescreve para dev
# config/settings/staging.py — importa base, configurações de staging
# config/settings/production.py — importa base, sem DEBUG, sem SECRET_KEY hardcoded
```

---

# 3. Modelagem de Dados

## 3.1 Política de Soft Delete

| Categoria de entidade | Política | Justificativa |
|---|---|---|
| Dados clínicos (Exame, Resultado, Laudo, Atendimento) | Soft delete obrigatório (`deleted_at`) | CFM 1821/2007 exige retenção de 20 anos; hard delete é vedado |
| Dados de paciente | Soft delete + anonimização após prazo LGPD | Direito ao esquecimento vs obrigação de retenção clínica |
| Dados financeiros (Pagamento, OrcamentoItem) | Soft delete | Auditoria fiscal e tributária |
| Configurações (Plano, Convenio, GrupoExame) | Soft delete | Histórico de configuração para laudos antigos |
| Logs de auditoria (AuditLog) | Hard delete nunca permitido | Imutabilidade é requisito de compliance |
| Dados de plataforma (Tenant, Plano de assinatura) | Soft delete | Histórico de billing |

**Mixin de soft delete:**
```python
# apps/core/models/mixins.py
from django.db import models
from django.utils import timezone


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)

    def with_deleted(self):
        return super().get_queryset()

    def only_deleted(self):
        return super().get_queryset().filter(deleted_at__isnull=False)


class SoftDeleteMixin(models.Model):
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    def delete(self, using=None, keep_parents=False):
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at"])

    def hard_delete(self):
        super().delete()

    def restore(self):
        self.deleted_at = None
        self.save(update_fields=["deleted_at"])

    class Meta:
        abstract = True
```

## 3.2 Entidades da Plataforma

### Tenant

```python
# apps/platform/models/tenant.py
import uuid
from django.db import models
from apps.core.models.mixins import SoftDeleteMixin


class Tenant(SoftDeleteMixin):
    class Status(models.TextChoices):
        TRIAL = "TRIAL", "Trial"
        ACTIVE = "ACTIVE", "Ativo"
        SUSPENDED = "SUSPENDED", "Suspenso"
        CANCELLED = "CANCELLED", "Cancelado"

    class Plan(models.TextChoices):
        FREE_TRIAL = "FREE_TRIAL", "Trial Gratuito (30 dias)"
        BASIC = "BASIC", "Básico (até 500 atendimentos/mês)"
        PROFESSIONAL = "PROFESSIONAL", "Profissional (até 2000 atendimentos/mês)"
        ENTERPRISE = "ENTERPRISE", "Enterprise (ilimitado)"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, help_text="Nome comercial do laboratório")
    slug = models.SlugField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Subdomínio: slug.labsaas.com.br",
    )
    cnpj = models.CharField(max_length=18, unique=True)
    responsible_name = models.CharField(max_length=200, help_text="Nome do responsável técnico")
    responsible_crm_crbm = models.CharField(max_length=30, help_text="CRM ou CRBM do responsável")
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    logo = models.ImageField(upload_to="tenants/logos/", null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.TRIAL, db_index=True)
    plan = models.CharField(max_length=20, choices=Plan.choices, default=Plan.FREE_TRIAL)
    trial_ends_at = models.DateTimeField(null=True, blank=True)
    settings = models.JSONField(
        default=dict,
        help_text=(
            "Configurações do tenant: timeout de sessão, 2FA obrigatório, "
            "modelo de laudo padrão, fuso horário, prefixo de sequência de fila."
        ),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Tenant"
        verbose_name_plural = "Tenants"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.slug})"
```

| Campo | Tipo | Nullable | Default | Índice | Justificativa |
|---|---|---|---|---|---|
| `id` | UUID | Não | uuid4 | PK | UUIDs evitam enumeração de tenants por ID inteiro |
| `slug` | SlugField(100) | Não | — | Único | Subdomínio único; consultado em todo request |
| `cnpj` | CharField(18) | Não | — | Único | Identificação fiscal obrigatória |
| `settings` | JSONField | Não | `{}` | Não | Configurações variáveis sem schema migration |
| `trial_ends_at` | DateTimeField | Sim | Null | Não | Null quando não é trial |

### TenantUser

```python
# apps/platform/models/tenant_user.py
class TenantUser(models.Model):
    class Role(models.TextChoices):
        ADMIN = "admin_clinica", "Administrador da Clínica"
        BIOMEDICO = "biomedico", "Biomédico"
        RECEPCIONISTA = "recepcionista", "Recepcionista"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="tenant_users")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tenant_memberships",
    )
    role = models.CharField(max_length=30, choices=Role.choices, db_index=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("tenant", "user")]
        indexes = [models.Index(fields=["tenant", "role"])]
```

## 3.3 Entidades de Usuários e Pessoas

### User (extensão do AbstractUser)

```python
# apps/accounts/models.py
from django.contrib.auth.models import AbstractUser
import uuid


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    is_superadmin = models.BooleanField(default=False, help_text="Acesso ao painel da plataforma")
    totp_secret = models.CharField(max_length=32, blank=True, help_text="Segredo TOTP para 2FA; em branco = 2FA não configurado")
    totp_enabled = models.BooleanField(default=False)
    last_tenant = models.ForeignKey(
        "platform.Tenant",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="Último tenant acessado — para redirect pós-login",
    )
```

### Paciente

```python
# apps/core/models/paciente.py
class Paciente(TenantAwareModel, SoftDeleteMixin):
    class Sexo(models.TextChoices):
        MASCULINO = "M", "Masculino"
        FEMININO = "F", "Feminino"
        NAO_INFORMADO = "N", "Não Informado"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="paciente_profile",
        help_text="Preenchido somente se o paciente tiver acesso ao portal",
    )
    nome_completo = models.CharField(max_length=200, db_index=True)
    cpf = models.CharField(max_length=14, db_index=True)
    rg = models.CharField(max_length=20, blank=True)
    data_nascimento = models.DateField(db_index=True)
    sexo = models.CharField(max_length=1, choices=Sexo.choices)
    telefone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    nome_mae = models.CharField(max_length=200, blank=True)
    convenio = models.ForeignKey(
        "financeiro.Convenio",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="pacientes",
    )
    numero_carteirinha = models.CharField(max_length=50, blank=True)
    lgpd_consentimento_at = models.DateTimeField(null=True, blank=True)
    lgpd_versao_termo = models.CharField(max_length=20, blank=True, help_text="Ex: '2024-01'")
    anonimizado_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("tenant", "cpf")]
        indexes = [
            models.Index(fields=["tenant", "nome_completo"]),
            models.Index(fields=["tenant", "data_nascimento"]),
        ]
```

### Endereco

```python
class Endereco(TenantAwareModel):
    paciente = models.OneToOneField(Paciente, on_delete=models.CASCADE, related_name="endereco")
    logradouro = models.CharField(max_length=200)
    numero = models.CharField(max_length=20)
    complemento = models.CharField(max_length=100, blank=True)
    bairro = models.CharField(max_length=100)
    cidade = models.CharField(max_length=100)
    estado = models.CharField(max_length=2)
    cep = models.CharField(max_length=10)
```

### Funcionario

```python
class Funcionario(TenantAwareModel, SoftDeleteMixin):
    class Cargo(models.TextChoices):
        RECEPCIONISTA = "recepcionista", "Recepcionista"
        BIOMEDICO = "biomedico", "Biomédico"
        TECNICO = "tecnico", "Técnico de Laboratório"
        ADMIN = "admin_clinica", "Administrador"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    tenant_user = models.OneToOneField(TenantUser, on_delete=models.CASCADE)
    nome_completo = models.CharField(max_length=200)
    cpf = models.CharField(max_length=14)
    crbm = models.CharField(max_length=20, blank=True, help_text="Conselho Regional de Biomedicina")
    cargo = models.CharField(max_length=30, choices=Cargo.choices)
    assinatura_imagem = models.ImageField(upload_to="funcionarios/assinaturas/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

### Medico (Solicitante)

```python
class Medico(TenantAwareModel, SoftDeleteMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome_completo = models.CharField(max_length=200)
    crm = models.CharField(max_length=20, db_index=True)
    uf_crm = models.CharField(max_length=2)
    especialidade = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)

    class Meta:
        unique_together = [("tenant", "crm", "uf_crm")]
```

## 3.4 Entidades de Agenda e Fila

### Fila

```python
# apps/agenda/models/fila.py
class Fila(TenantAwareModel):
    """Configuração da fila por dia. Criada automaticamente ao primeiro item do dia."""
    data = models.DateField(db_index=True)
    aberta = models.BooleanField(default=True)
    sequencia_atual = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = [("tenant", "data")]
```

### ItemFila

```python
class ItemFila(TenantAwareModel, SoftDeleteMixin):
    class Status(models.TextChoices):
        AGUARDANDO = "AGUARDANDO", "Aguardando"
        CHAMADO = "CHAMADO", "Chamado"
        ATENDIDO = "ATENDIDO", "Atendido"
        CANCELADO = "CANCELADO", "Cancelado"
        AUSENTE = "AUSENTE", "Ausente (não compareceu)"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fila = models.ForeignKey(Fila, on_delete=models.PROTECT, related_name="itens")
    paciente = models.ForeignKey("core.Paciente", on_delete=models.PROTECT, related_name="itens_fila")
    numero_sequencia = models.CharField(max_length=13, help_text="Formato AAAAMMDDNNNNN")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AGUARDANDO, db_index=True)
    hora_chegada = models.DateTimeField(auto_now_add=True)
    hora_chamada = models.DateTimeField(null=True, blank=True)
    hora_atendimento = models.DateTimeField(null=True, blank=True)
    prioridade = models.BooleanField(default=False, help_text="Fila preferencial (idoso, gestante, etc.)")
    criado_por = models.ForeignKey(
        "core.Funcionario", null=True, on_delete=models.SET_NULL, related_name="filas_criadas"
    )

    class Meta:
        indexes = [
            models.Index(fields=["fila", "status"]),
            models.Index(fields=["tenant", "numero_sequencia"]),
        ]
```

## 3.5 Entidades de Exames

### Exame (template/catálogo)

```python
# apps/exame/models/exame.py
class Exame(TenantAwareModel, SoftDeleteMixin):
    class Status(models.TextChoices):
        ATIVO = "ATIVO", "Ativo"
        INATIVO = "INATIVO", "Inativo"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=20, db_index=True, help_text="Código interno gerado automaticamente")
    codigo_tuss = models.CharField(max_length=20, blank=True, db_index=True, help_text="Código TUSS para TISS")
    nome = models.CharField(max_length=200, db_index=True)
    sigla = models.CharField(max_length=20, blank=True)
    material = models.CharField(max_length=100, help_text="Ex: Sangue venoso, Urina, Swab nasal")
    metodo = models.CharField(max_length=200, help_text="Ex: Citometria de fluxo, PCR, Colorimetria")
    prazo_entrega_horas = models.PositiveSmallIntegerField(default=24, help_text="TAT esperado em horas")
    instrucoes_preparo = models.TextField(blank=True, help_text="Exibidas ao paciente no agendamento")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ATIVO, db_index=True)
    terceirizado = models.BooleanField(default=False)
    laboratorio_terceiro = models.CharField(max_length=200, blank=True)
    biomédico_responsavel = models.ForeignKey(
        "core.Funcionario",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        limit_choices_to={"cargo": "biomedico"},
    )
    grupos = models.ManyToManyField("GrupoExame", blank=True, related_name="exames")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("tenant", "codigo")]
        indexes = [models.Index(fields=["tenant", "nome"])]
```

### GrupoExame

```python
class GrupoExame(TenantAwareModel, SoftDeleteMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    ativo = models.BooleanField(default=True)
```

### ReferenciaExame

```python
class ReferenciaExame(TenantAwareModel, SoftDeleteMixin):
    class TipoUnidade(models.TextChoices):
        NUMERICO = "numerico", "Numérico com limites"
        QUALITATIVO = "qualitativo", "Qualitativo (positivo/negativo)"
        TEXTO = "texto", "Texto livre"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exame = models.ForeignKey(Exame, on_delete=models.CASCADE, related_name="referencias")
    descricao = models.CharField(max_length=200, help_text="Ex: 'Adultos', 'Crianças 0-12 anos', 'Gestantes'")
    tipo = models.CharField(max_length=20, choices=TipoUnidade.choices)
    sexo = models.CharField(max_length=1, choices=[("M", "Masculino"), ("F", "Feminino"), ("A", "Ambos")], default="A")
    idade_minima_anos = models.PositiveSmallIntegerField(null=True, blank=True)
    idade_maxima_anos = models.PositiveSmallIntegerField(null=True, blank=True)
    valor_minimo = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    valor_maximo = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    unidade = models.CharField(max_length=50, blank=True, help_text="Ex: mg/dL, g/dL, 10³/µL")
    valor_critico_minimo = models.DecimalField(
        max_digits=12, decimal_places=4, null=True, blank=True,
        help_text="Abaixo deste valor: alerta de pânico analítico",
    )
    valor_critico_maximo = models.DecimalField(
        max_digits=12, decimal_places=4, null=True, blank=True,
        help_text="Acima deste valor: alerta de pânico analítico",
    )
    valor_esperado_texto = models.CharField(max_length=200, blank=True, help_text="Para tipo qualitativo")
    ordem = models.PositiveSmallIntegerField(default=0, help_text="Ordem de exibição no laudo")
```

### ResultadoExame (instância por atendimento)

```python
class ResultadoExame(TenantAwareModel, SoftDeleteMixin):
    class Status(models.TextChoices):
        AGUARDANDO = "AGUARDANDO", "Aguardando Coleta"
        COLETADO = "COLETADO", "Coletado"
        EM_ANALISE = "EM_ANALISE", "Em Análise"
        REALIZADO = "REALIZADO", "Realizado"
        VALIDADO = "VALIDADO", "Validado pelo Biomédico"
        CANCELADO = "CANCELADO", "Cancelado"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    atendimento = models.ForeignKey("atendimento.Atendimento", on_delete=models.PROTECT, related_name="resultados")
    exame = models.ForeignKey(Exame, on_delete=models.PROTECT)
    amostra = models.ForeignKey("coleta.AmostraBiologica", null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AGUARDANDO, db_index=True)
    valores = models.JSONField(
        default=dict,
        help_text=(
            "Dicionário {referencia_id: valor_obtido}. "
            "Armazena resultados numéricos e textuais de forma flexível."
        ),
    )
    comentario_biomedico = models.TextField(blank=True)
    valor_critico_detectado = models.BooleanField(default=False, db_index=True)
    valor_critico_notificado_at = models.DateTimeField(null=True, blank=True)
    valor_critico_notificado_por = models.ForeignKey(
        "core.Funcionario", null=True, blank=True, on_delete=models.SET_NULL, related_name="criticos_notificados"
    )
    realizado_por = models.ForeignKey(
        "core.Funcionario", null=True, on_delete=models.SET_NULL, related_name="resultados_realizados"
    )
    realizado_at = models.DateTimeField(null=True, blank=True)
    validado_por = models.ForeignKey(
        "core.Funcionario", null=True, on_delete=models.SET_NULL, related_name="resultados_validados"
    )
    validado_at = models.DateTimeField(null=True, blank=True)
    anexo_terceirizado = models.FileField(upload_to="exames/terceirizados/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["tenant", "status"]),
            models.Index(fields=["atendimento", "exame"]),
        ]
```

## 3.6 Entidades de Atendimento e Financeiro

### Atendimento

```python
# apps/atendimento/models/atendimento.py
class Atendimento(TenantAwareModel, SoftDeleteMixin):
    class Status(models.TextChoices):
        ORCAMENTO = "ORCAMENTO", "Orçamento"
        CONFIRMADO = "CONFIRMADO", "Confirmado"
        EM_ANDAMENTO = "EM_ANDAMENTO", "Em Andamento"
        CONCLUIDO = "CONCLUIDO", "Concluído"
        CANCELADO = "CANCELADO", "Cancelado"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    numero = models.CharField(max_length=20, db_index=True, help_text="Número sequencial do atendimento")
    item_fila = models.OneToOneField(
        "agenda.ItemFila", null=True, blank=True, on_delete=models.SET_NULL, related_name="atendimento"
    )
    paciente = models.ForeignKey("core.Paciente", on_delete=models.PROTECT, related_name="atendimentos")
    medico_solicitante = models.ForeignKey(
        "core.Medico", null=True, blank=True, on_delete=models.SET_NULL, related_name="atendimentos"
    )
    convenio = models.ForeignKey(
        "financeiro.Convenio", null=True, blank=True, on_delete=models.SET_NULL
    )
    plano_convenio = models.ForeignKey(
        "financeiro.PlanoConvenio", null=True, blank=True, on_delete=models.SET_NULL
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ORCAMENTO, db_index=True)
    data_atendimento = models.DateTimeField(auto_now_add=True, db_index=True)
    observacoes = models.TextField(blank=True)
    criado_por = models.ForeignKey("core.Funcionario", null=True, on_delete=models.SET_NULL)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("tenant", "numero")]
        indexes = [models.Index(fields=["tenant", "data_atendimento"])]
```

### ItemAtendimento

```python
class ItemAtendimento(TenantAwareModel, SoftDeleteMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    atendimento = models.ForeignKey(Atendimento, on_delete=models.CASCADE, related_name="itens")
    exame = models.ForeignKey("exame.Exame", on_delete=models.PROTECT)
    plano = models.ForeignKey("agenda.Plano", null=True, blank=True, on_delete=models.SET_NULL)
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    desconto = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    @property
    def preco_final(self):
        return self.preco_unitario - self.desconto
```

### Pagamento

```python
class Pagamento(TenantAwareModel, SoftDeleteMixin):
    class FormaPagamento(models.TextChoices):
        DINHEIRO = "dinheiro", "Dinheiro"
        CREDITO = "credito", "Cartão de Crédito"
        DEBITO = "debito", "Cartão de Débito"
        PIX = "pix", "Pix"
        CONVENIO = "convenio", "Convênio"
        OUTRO = "outro", "Outro"

    class Status(models.TextChoices):
        PENDENTE = "PENDENTE", "Pendente"
        PAGO = "PAGO", "Pago"
        ESTORNADO = "ESTORNADO", "Estornado"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    atendimento = models.ForeignKey(Atendimento, on_delete=models.PROTECT, related_name="pagamentos")
    forma = models.CharField(max_length=20, choices=FormaPagamento.choices)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDENTE)
    pago_at = models.DateTimeField(null=True, blank=True)
    registrado_por = models.ForeignKey("core.Funcionario", null=True, on_delete=models.SET_NULL)
    observacao = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

### Convenio e PlanoConvenio

```python
# apps/financeiro/models/convenio.py
class Convenio(TenantAwareModel, SoftDeleteMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(max_length=200)
    registro_ans = models.CharField(max_length=20, blank=True, help_text="Número de registro na ANS")
    codigo_operadora_tiss = models.CharField(max_length=20, blank=True)
    email_faturamento = models.EmailField(blank=True)
    ativo = models.BooleanField(default=True)


class PlanoConvenio(TenantAwareModel, SoftDeleteMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    convenio = models.ForeignKey(Convenio, on_delete=models.CASCADE, related_name="planos")
    nome = models.CharField(max_length=200, help_text="Ex: 'Unimed Nacional', 'Bradesco Saúde Premium'")
    tabela_precos = models.JSONField(
        default=dict,
        help_text="Mapeamento {codigo_tuss: preco_decimal} para este plano",
    )
    ativo = models.BooleanField(default=True)
```

## 3.7 Entidades de Coleta e Amostras

### AmostraBiologica

```python
# apps/coleta/models/amostra.py
class AmostraBiologica(TenantAwareModel, SoftDeleteMixin):
    class Status(models.TextChoices):
        AGUARDANDO_COLETA = "AGUARDANDO_COLETA", "Aguardando Coleta"
        COLETADA = "COLETADA", "Coletada"
        TRIADA = "TRIADA", "Triada"
        EM_ANALISE = "EM_ANALISE", "Em Análise"
        CONCLUIDA = "CONCLUIDA", "Concluída"
        REJEITADA = "REJEITADA", "Rejeitada"
        DESCARTADA = "DESCARTADA", "Descartada"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo_barras = models.CharField(max_length=50, unique=True, db_index=True)
    atendimento = models.ForeignKey("atendimento.Atendimento", on_delete=models.PROTECT, related_name="amostras")
    paciente = models.ForeignKey("core.Paciente", on_delete=models.PROTECT)
    material = models.CharField(max_length=100, help_text="Tipo de material biológico")
    tubo = models.CharField(max_length=50, blank=True, help_text="Ex: EDTA, Seco, Citrato")
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.AGUARDANDO_COLETA, db_index=True)
    coletada_por = models.ForeignKey("core.Funcionario", null=True, on_delete=models.SET_NULL, related_name="coletas")
    coletada_at = models.DateTimeField(null=True, blank=True)
    motivo_rejeicao = models.CharField(max_length=500, blank=True)
    rejeitada_por = models.ForeignKey("core.Funcionario", null=True, on_delete=models.SET_NULL, related_name="rejeicoes")
    rejeitada_at = models.DateTimeField(null=True, blank=True)
    descartada_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

## 3.8 Entidades de Controle de Qualidade

### EquipamentoLab

```python
# apps/qc/models/equipamento.py
class EquipamentoLab(TenantAwareModel, SoftDeleteMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(max_length=200)
    marca = models.CharField(max_length=100)
    modelo = models.CharField(max_length=100)
    numero_serie = models.CharField(max_length=100, blank=True)
    data_aquisicao = models.DateField(null=True, blank=True)
    proxima_calibracao = models.DateField(null=True, blank=True, db_index=True)
    ativo = models.BooleanField(default=True)
```

### ControleQualidade

```python
class ControleQualidade(TenantAwareModel, SoftDeleteMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    equipamento = models.ForeignKey(EquipamentoLab, on_delete=models.PROTECT, related_name="controles")
    exame = models.ForeignKey("exame.Exame", on_delete=models.PROTECT)
    lote_soro_controle = models.CharField(max_length=100)
    nivel = models.CharField(max_length=20, help_text="Ex: 'Normal', 'Patológico', 'Nível 1', 'Nível 2'")
    valor_obtido = models.DecimalField(max_digits=12, decimal_places=4)
    media_acumulada = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    desvio_padrao = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    cv_percentual = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    regras_westgard_violadas = models.JSONField(
        default=list,
        help_text="Lista de regras violadas: ['1_2s', '1_3s', 'R_4s', etc.]",
    )
    alerta_emitido = models.BooleanField(default=False)
    registrado_por = models.ForeignKey("core.Funcionario", null=True, on_delete=models.SET_NULL)
    data_hora = models.DateTimeField(auto_now_add=True, db_index=True)
```

## 3.9 Entidades de Estoque

### Reagente

```python
# apps/estoque/models/reagente.py
class Reagente(TenantAwareModel, SoftDeleteMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(max_length=200)
    fabricante = models.CharField(max_length=200)
    numero_anvisa = models.CharField(max_length=50, blank=True)
    unidade_medida = models.CharField(max_length=20, help_text="Ex: mL, unidade, caixa")
    estoque_atual = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    ponto_pedido = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    exames_utilizados = models.ManyToManyField("exame.Exame", blank=True, related_name="reagentes")


class MovimentacaoEstoque(TenantAwareModel):
    class Tipo(models.TextChoices):
        ENTRADA = "ENTRADA", "Entrada (Compra/Doação)"
        SAIDA = "SAIDA", "Saída (Uso em Exame)"
        AJUSTE = "AJUSTE", "Ajuste de Inventário"
        DESCARTE = "DESCARTE", "Descarte (Vencimento/Quebra)"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reagente = models.ForeignKey(Reagente, on_delete=models.PROTECT, related_name="movimentacoes")
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    quantidade = models.DecimalField(max_digits=10, decimal_places=2)
    lote = models.CharField(max_length=100, blank=True)
    validade = models.DateField(null=True, blank=True)
    resultado_exame = models.ForeignKey(
        "exame.ResultadoExame", null=True, blank=True, on_delete=models.SET_NULL,
        help_text="Rastreabilidade: qual exame consumiu este reagente",
    )
    registrado_por = models.ForeignKey("core.Funcionario", null=True, on_delete=models.SET_NULL)
    data_hora = models.DateTimeField(auto_now_add=True, db_index=True)
    observacao = models.CharField(max_length=500, blank=True)
```

## 3.10 Entidades de Auditoria e Notificação

### AuditLog (imutável)

```python
# apps/auditoria/models/audit_log.py
class AuditLog(models.Model):
    """
    Imutável por design: sem soft delete, sem método delete() customizado.
    Nunca deve ser deletado. Particionamento por data recomendado em produção.
    """
    class Acao(models.TextChoices):
        CREATE = "CREATE", "Criação"
        UPDATE = "UPDATE", "Atualização"
        DELETE = "DELETE", "Exclusão (Soft)"
        VIEW = "VIEW", "Visualização de dado sensível"
        LOGIN = "LOGIN", "Login"
        LOGOUT = "LOGOUT", "Logout"
        EXPORT = "EXPORT", "Exportação de dados"
        LAUDO_GERADO = "LAUDO_GERADO", "Laudo gerado"
        LAUDO_ACESSADO = "LAUDO_ACESSADO", "Laudo acessado"
        VALOR_CRITICO = "VALOR_CRITICO", "Valor crítico detectado"
        PAGAMENTO = "PAGAMENTO", "Registro de pagamento"

    id = models.BigAutoField(primary_key=True)
    tenant = models.ForeignKey(
        "platform.Tenant", null=True, on_delete=models.SET_NULL, db_index=True,
        help_text="Null apenas para ações de superadmin sem tenant",
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, db_index=True
    )
    acao = models.CharField(max_length=30, choices=Acao.choices, db_index=True)
    modelo = models.CharField(max_length=100, help_text="Ex: 'exame.ResultadoExame'")
    objeto_id = models.CharField(max_length=50, db_index=True)
    dados_antes = models.JSONField(null=True, blank=True, help_text="Estado do objeto antes da ação")
    dados_depois = models.JSONField(null=True, blank=True, help_text="Estado do objeto após a ação")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["tenant", "timestamp"]),
            models.Index(fields=["usuario", "timestamp"]),
            models.Index(fields=["modelo", "objeto_id"]),
        ]

    def delete(self, *args, **kwargs):
        raise PermissionError("AuditLog é imutável. Exclusão não permitida.")

    def save(self, *args, **kwargs):
        if self.pk:
            raise PermissionError("AuditLog é imutável. Atualização não permitida.")
        super().save(*args, **kwargs)
```

### Notificacao

```python
# apps/comunicacao/models/notificacao.py
class Notificacao(TenantAwareModel):
    class Canal(models.TextChoices):
        EMAIL = "email", "E-mail"
        SMS = "sms", "SMS"
        WHATSAPP = "whatsapp", "WhatsApp"
        SISTEMA = "sistema", "Notificação no sistema"

    class Status(models.TextChoices):
        PENDENTE = "PENDENTE", "Pendente"
        ENVIANDO = "ENVIANDO", "Enviando"
        ENVIADO = "ENVIADO", "Enviado"
        FALHOU = "FALHOU", "Falhou"
        ENTREGUE = "ENTREGUE", "Entregue (com confirmação)"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    paciente = models.ForeignKey("core.Paciente", null=True, on_delete=models.SET_NULL)
    canal = models.CharField(max_length=20, choices=Canal.choices)
    destinatario = models.CharField(max_length=200, help_text="Telefone, e-mail ou user_id")
    assunto = models.CharField(max_length=200, blank=True)
    mensagem = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDENTE, db_index=True)
    tentativas = models.PositiveSmallIntegerField(default=0)
    enviado_at = models.DateTimeField(null=True, blank=True)
    erro_detalhe = models.TextField(blank=True)
    gatilho = models.CharField(
        max_length=100, blank=True,
        help_text="Ex: 'laudo_pronto', 'valor_critico', 'agendamento_confirmado'",
    )
    objeto_referencia_tipo = models.CharField(max_length=100, blank=True)
    objeto_referencia_id = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

---

# 4. Módulos do Sistema

## 4.1 Plataforma (SaaS Core)

**Responsabilidade:** Gerenciamento do ciclo de vida dos tenants (clínicas/laboratórios), planos de assinatura, subdomínios, cobrança e painel de controle da plataforma. Este módulo é operado exclusivamente pelo superadmin — nenhum tenant tem acesso a dados de outro tenant através deste módulo.

**Fronteiras:** Pertence a este módulo tudo que existe no nível da plataforma (acima dos tenants). Não pertence: qualquer dado clínico, operacional ou financeiro dos laboratórios clientes.

**Decisão: Criar do zero.** O sistema atual não tem multitenancy. Todo este módulo é novo.

**Middleware de resolução de tenant:**

```python
# apps/platform/middleware.py
import threading
from django.http import Http404
from apps.platform.models import Tenant

_thread_local = threading.local()


def get_current_tenant() -> Tenant | None:
    return getattr(_thread_local, "current_tenant", None)


def set_current_tenant(tenant: Tenant | None) -> None:
    _thread_local.current_tenant = tenant


class TenantMiddleware:
    """
    Resolve o tenant pelo subdomínio do Host header.
    Injeta o tenant no thread-local e configura o parâmetro RLS no PostgreSQL.
    """
    EXEMPT_HOSTS = {"labsaas.com.br", "www.labsaas.com.br", "api.labsaas.com.br"}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(":")[0].lower()

        if host in self.EXEMPT_HOSTS or host.startswith("staging."):
            set_current_tenant(None)
            return self.get_response(request)

        slug = host.replace(".labsaas.com.br", "").replace(".staging.labsaas.com.br", "")

        try:
            tenant = Tenant.objects.get(slug=slug, status__in=["TRIAL", "ACTIVE"])
        except Tenant.DoesNotExist:
            raise Http404(f"Laboratório '{slug}' não encontrado ou suspenso.")

        set_current_tenant(tenant)
        request.tenant = tenant

        response = self.get_response(request)
        return response
```

**Endpoints principais:**

| Método | URL | Auth | Descrição |
|---|---|---|---|
| POST | `/api/v1/platform/tenants/` | superadmin | Criar novo tenant |
| GET | `/api/v1/platform/tenants/` | superadmin | Listar todos os tenants |
| PATCH | `/api/v1/platform/tenants/{id}/` | superadmin | Atualizar status/plano |
| POST | `/api/v1/platform/tenants/{id}/suspend/` | superadmin | Suspender tenant |
| GET | `/api/v1/platform/metrics/` | superadmin | Métricas globais |
| POST | `/api/v1/platform/onboarding/` | público | Cadastro self-service de novo laboratório |

**Regras de negócio críticas:**
- O `slug` do tenant deve conter apenas letras minúsculas, números e hífens. Validação com regex `^[a-z0-9-]+$`. Comprimento entre 3 e 50 caracteres.
- O subdomínio gerado é `{slug}.labsaas.com.br`. O sistema deve verificar se o slug já existe antes de confirmar o cadastro.
- Trial de 30 dias começa na criação. Ao expirar, status muda para `SUSPENDED` automaticamente via task Celery diária.
- Antes de suspender, o sistema envia 3 notificações: 7 dias antes, 3 dias antes e 1 dia antes do vencimento.
- Tenant suspenso: usuários recebem tela de suspensão, sem acesso a dados. Dados preservados por 90 dias antes de soft delete.

**Task Celery:**
```python
# apps/platform/tasks.py
from celery import shared_task
from django.utils import timezone
from datetime import timedelta


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def verificar_trials_expirados(self):
    """Executa diariamente às 00:05. Suspende tenants com trial expirado."""
    from apps.platform.models import Tenant
    from apps.comunicacao.services import enviar_notificacao_admin

    agora = timezone.now()
    expirados = Tenant.objects.filter(status="TRIAL", trial_ends_at__lte=agora)

    for tenant in expirados:
        tenant.status = "SUSPENDED"
        tenant.save(update_fields=["status"])
        enviar_notificacao_admin(tenant, gatilho="trial_expirado")
```

## 4.2 Accounts e Permissões

**Responsabilidade:** Autenticação de usuários, gerenciamento de papéis por tenant, 2FA, emissão e validação de tokens JWT.

**Decisão: Recriar do zero.** O sistema atual usa sessão Django padrão com redirecionamento por tipo. O novo sistema requer JWT para suporte à API REST e potencial uso mobile futuro.

**Biblioteca JWT: `djangorestframework-simplejwt`**

```python
# config/settings/base.py
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": env("JWT_SECRET_KEY"),
    "AUTH_HEADER_TYPES": ("Bearer",),
    "TOKEN_OBTAIN_SERIALIZER": "apps.accounts.serializers.CustomTokenObtainPairSerializer",
}
```

**Serializer com contexto de tenant:**
```python
# apps/accounts/serializers.py
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        tenant = user.last_tenant
        if tenant:
            token["tenant_id"] = str(tenant.id)
            token["tenant_slug"] = tenant.slug
            role = user.tenant_memberships.filter(tenant=tenant).values_list("role", flat=True).first()
            token["role"] = role or ""
        token["is_superadmin"] = user.is_superadmin
        return token
```

**Endpoints:**

| Método | URL | Auth | Descrição |
|---|---|---|---|
| POST | `/api/v1/auth/token/` | público | Login — retorna access + refresh token |
| POST | `/api/v1/auth/token/refresh/` | refresh token | Renovar access token |
| POST | `/api/v1/auth/token/blacklist/` | access token | Logout — invalida refresh token |
| POST | `/api/v1/auth/2fa/setup/` | autenticado | Configurar TOTP |
| POST | `/api/v1/auth/2fa/verify/` | autenticado | Verificar código TOTP |
| POST | `/api/v1/auth/password/change/` | autenticado | Alterar senha |

**Regras de negócio:**
- Access token expira em 15 minutos. Refresh token expira em 7 dias com rotação automática.
- 2FA TOTP obrigatório para papéis `biomedico` e `admin_clinica` quando `tenant.settings["2fa_obrigatorio"] == True`.
- Login bem-sucedido sem 2FA para papel que exige 2FA retorna token com campo `"2fa_required": true` e acesso limitado apenas ao endpoint de verificação TOTP.
- Após 5 tentativas de login falhas consecutivas, a conta é bloqueada por 15 minutos. Registro no `AuditLog`.
- Timeout de sessão configurável por tenant em `tenant.settings["session_timeout_minutes"]` (padrão: 480 — 8 horas). Implementado via tempo de vida do access token sobrescrito para o tenant.

## 4.3 Pacientes e Cadastro

**Responsabilidade:** Cadastro, consulta, atualização de dados de pacientes. Portal de acesso do paciente aos próprios laudos. Conformidade LGPD.

**Decisão: Refatorar.** O modelo atual tem os campos corretos, mas precisa de separação entre `User` Django e `Paciente`, adição do campo LGPD, e criptografia de CPF/RG.

**Criptografia de campos sensíveis:**
```python
# apps/core/models/paciente.py
from django_encrypted_fields.fields import EncryptedCharField

class Paciente(TenantAwareModel, SoftDeleteMixin):
    # CPF e RG são criptografados em repouso
    # A busca por CPF é feita via hash determinístico em campo separado
    cpf_criptografado = EncryptedCharField(max_length=14)
    cpf_hash = models.CharField(max_length=64, db_index=True, help_text="SHA-256 do CPF normalizado para busca")
    rg_criptografado = EncryptedCharField(max_length=20, blank=True)
```

```python
# apps/core/services/paciente.py
import hashlib

def normalizar_cpf(cpf: str) -> str:
    return "".join(filter(str.isdigit, cpf))

def hash_cpf(cpf: str) -> str:
    cpf_normalizado = normalizar_cpf(cpf)
    return hashlib.sha256(f"labsaas-cpf-{cpf_normalizado}".encode()).hexdigest()
```

**Portal do paciente — acesso sem senha:**
O paciente acessa via CPF + data de nascimento. O sistema valida o hash do CPF e a data de nascimento (sem expor o CPF real). Retorna um token de curta duração (2 horas, não renovável) com papel `paciente`.

**Endpoints:**

| Método | URL | Auth | Descrição |
|---|---|---|---|
| GET | `/api/v1/pacientes/` | recepcionista+ | Listar pacientes do tenant |
| POST | `/api/v1/pacientes/` | recepcionista+ | Cadastrar paciente |
| GET | `/api/v1/pacientes/{id}/` | recepcionista+ | Detalhe do paciente |
| PATCH | `/api/v1/pacientes/{id}/` | recepcionista+ | Atualizar dados |
| GET | `/api/v1/pacientes/{id}/atendimentos/` | recepcionista+ | Histórico de atendimentos |
| POST | `/api/v1/portal/acesso/` | público | Login do portal do paciente |
| GET | `/api/v1/portal/laudos/` | token paciente | Laudos do paciente logado |
| POST | `/api/v1/pacientes/{id}/lgpd/consentimento/` | recepcionista+ | Registrar consentimento LGPD |
| POST | `/api/v1/pacientes/{id}/lgpd/solicitacao/` | admin_clinica | Registrar solicitação de titular LGPD |

**Regras de negócio:**
- CPF validado com dígitos verificadores antes do cadastro. Biblioteca `validate-docbr`.
- CPF único por tenant (combinação `tenant + cpf_hash`).
- Consentimento LGPD registrado com `lgpd_versao_termo` e `lgpd_consentimento_at` no ato da recepção. Se o paciente já existe e a versão do termo mudou, deve consentir novamente.
- Anonimização: pacientes sem atendimento nos últimos `tenant.settings["meses_para_anonimizacao"]` meses (padrão: 60 meses / 5 anos) têm CPF, RG, nome substituídos por hashes e `anonimizado_at` preenchido. Dados clínicos são preservados.

## 4.4 Agenda e Fila

**Responsabilidade:** Criação e gestão da ordem de chegada de pacientes, atualização de status em tempo real via WebSocket.

**Decisão: Refatorar.** A lógica de geração de número sequencial é preservada e aprimorada. Adiciona-se WebSocket via Django Channels.

**Geração de número de sequência:**
```python
# apps/agenda/services/fila.py
from django.db import transaction
from apps.agenda.models import Fila, ItemFila
from apps.core.models import Paciente


def adicionar_paciente_fila(tenant, paciente: Paciente, prioridade: bool = False) -> ItemFila:
    with transaction.atomic():
        fila, _ = Fila.objects.select_for_update().get_or_create(
            tenant=tenant,
            data=timezone.localdate(),
        )
        fila.sequencia_atual += 1
        fila.save(update_fields=["sequencia_atual"])

        data_str = fila.data.strftime("%Y%m%d")
        numero = f"{data_str}{fila.sequencia_atual:05d}"

        item = ItemFila.objects.create(
            tenant=tenant,
            fila=fila,
            paciente=paciente,
            numero_sequencia=numero,
            prioridade=prioridade,
        )

    # Notifica WebSocket após commit
    transaction.on_commit(lambda: notificar_atualizacao_fila(tenant.id))
    return item
```

**WebSocket (Django Channels):**
```python
# apps/agenda/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer


class FilaConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        tenant_id = self.scope["url_route"]["kwargs"]["tenant_id"]
        self.group_name = f"fila_{tenant_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def fila_update(self, event):
        await self.send(text_data=json.dumps(event["payload"]))
```

**Endpoints:**

| Método | URL | Auth | Descrição |
|---|---|---|---|
| POST | `/api/v1/fila/` | recepcionista+ | Adicionar paciente à fila |
| GET | `/api/v1/fila/` | recepcionista+ | Listar fila do dia atual |
| GET | `/api/v1/fila/?data=YYYY-MM-DD` | recepcionista+ | Fila de data específica |
| PATCH | `/api/v1/fila/{id}/` | recepcionista+ | Atualizar status do item |
| WS | `ws://{slug}.labsaas.com.br/ws/fila/` | autenticado | Atualizações em tempo real |

## 4.5 Atendimento e Financeiro

**Responsabilidade:** Criação de orçamentos, confirmação de atendimentos, registro de pagamentos (incluindo split), emissão de comprovante PDF, relatórios financeiros.

**Decisão: Refatorar.** A lógica de orçamento é preservada. Adiciona-se: split de pagamento, integração NFS-e, relatórios com filtros avançados.

**Serviço de orçamento:**
```python
# apps/atendimento/services/orcamento.py
from decimal import Decimal
from apps.atendimento.models import Atendimento, ItemAtendimento
from apps.exame.models import Exame
from apps.agenda.models import Plano


def calcular_preco_exame(exame: Exame, plano: Plano | None, convenio_plano=None) -> Decimal:
    if convenio_plano and exame.codigo_tuss:
        tabela = convenio_plano.tabela_precos
        if exame.codigo_tuss in tabela:
            return Decimal(str(tabela[exame.codigo_tuss]))

    if plano:
        return plano.preco

    raise ValueError(f"Exame {exame.codigo} não tem preço configurado para o plano selecionado.")


def criar_atendimento(tenant, paciente, exames_planos: list[dict], criado_por) -> Atendimento:
    """
    exames_planos: [{"exame_id": uuid, "plano_id": uuid | None}, ...]
    """
    from apps.atendimento.services.numero import gerar_numero_atendimento

    atendimento = Atendimento.objects.create(
        tenant=tenant,
        paciente=paciente,
        numero=gerar_numero_atendimento(tenant),
        criado_por=criado_por,
    )

    for item in exames_planos:
        exame = Exame.objects.get(id=item["exame_id"], tenant=tenant)
        plano = Plano.objects.get(id=item["plano_id"]) if item.get("plano_id") else None
        preco = calcular_preco_exame(exame, plano)
        ItemAtendimento.objects.create(
            tenant=tenant,
            atendimento=atendimento,
            exame=exame,
            plano=plano,
            preco_unitario=preco,
        )

    return atendimento
```

**Integração NFS-e:**
A emissão de NFS-e municipal varia por prefeitura. A abordagem adotada é o padrão ABRASF com adaptadores por município:

```python
# apps/atendimento/services/nfse/base.py
from abc import ABC, abstractmethod


class NfseAdapter(ABC):
    @abstractmethod
    def emitir(self, atendimento) -> dict:
        """Retorna {'numero_nfse': str, 'pdf_url': str, 'xml': str}"""
        ...

    @abstractmethod
    def cancelar(self, numero_nfse: str) -> bool:
        ...


# apps/atendimento/services/nfse/fortaleza.py
class NfseFortalezaAdapter(NfseAdapter):
    def emitir(self, atendimento) -> dict:
        # Implementação específica da prefeitura de Fortaleza via SOAP/REST
        ...
```

O registro do tenant contém `settings["municipio_codigo_ibge"]` e `settings["nfse_certificado_pfx_s3_key"]`. Um `NfseAdapterFactory` retorna o adapter correto para o código IBGE.

**Relatórios:**
```python
# apps/atendimento/services/relatorio.py
from django.db.models import Sum, Count, Q
from apps.atendimento.models import Pagamento


def relatorio_financeiro(tenant, data_inicio, data_fim) -> dict:
    pagamentos = Pagamento.objects.filter(
        tenant=tenant,
        status="PAGO",
        pago_at__date__range=(data_inicio, data_fim),
    )
    return {
        "total": pagamentos.aggregate(total=Sum("valor"))["total"] or 0,
        "por_forma": list(
            pagamentos.values("forma").annotate(total=Sum("valor"), quantidade=Count("id"))
        ),
        "quantidade_atendimentos": pagamentos.values("atendimento").distinct().count(),
    }
```

## 4.6 Coleta e Amostras

**Responsabilidade:** Registro de coleta de amostras, rastreabilidade por código de barras, gestão de rejeições e recoletas, impressão de etiquetas.

**Decisão: Criar do zero.** O sistema atual trata amostras implicitamente no exame, sem rastreabilidade formal.

**Geração de código de barras (etiqueta ZPL para Zebra):**
```python
# apps/coleta/services/etiqueta.py
import barcode
from barcode.writer import ImageWriter
from io import BytesIO


def gerar_zpl_etiqueta(amostra) -> str:
    """Gera ZPL para impressoras Zebra ZD220/ZD420."""
    codigo = amostra.codigo_barras
    paciente = amostra.paciente
    return f"""^XA
^FO50,30^BCN,80,Y,N,N^FD{codigo}^FS
^FO50,130^ADN,18,10^FD{paciente.nome_completo[:30]}^FS
^FO50,155^ADN,14,8^FD{paciente.data_nascimento.strftime('%d/%m/%Y')} - {amostra.material}^FS
^FO50,175^ADN,12,7^FD{amostra.atendimento.data_atendimento.strftime('%d/%m/%Y %H:%M')}^FS
^XZ"""


def gerar_pdf_etiquetas(amostras: list) -> bytes:
    """Fallback PDF para impressoras comuns (A4, 2 colunas de etiquetas)."""
    from weasyprint import HTML
    from django.template.loader import render_to_string

    html = render_to_string("coleta/etiquetas_pdf.html", {"amostras": amostras})
    return HTML(string=html).write_pdf()
```

**Regras de negócio:**
- Cada `AmostraBiologica` tem um `codigo_barras` único na plataforma inteira (não apenas por tenant), gerado com UUID truncado + dígito verificador Luhn.
- A transição de status segue a máquina de estados: `AGUARDANDO_COLETA → COLETADA → TRIADA → EM_ANALISE → CONCLUIDA`. Qualquer estado pode ir para `REJEITADA`. `REJEITADA → AGUARDANDO_COLETA` (recoleta). `CONCLUIDA → DESCARTADA`.
- Rejeição exige campo `motivo_rejeicao` preenchido (não pode ser vazio).
- Toda mudança de status registra no `AuditLog`.

## 4.7 Exames e Laudos

**Responsabilidade:** Catálogo de exames com referências de normalidade, fluxo de realização e validação pelo biomédico, geração de laudos PDF com WeasyPrint, assinatura digital.

**Decisão: Refatorar.** A estrutura de exames e referências é mantida. Substitui-se ReportLab por WeasyPrint (templates HTML/CSS mais manuteníveis). Adiciona-se assinatura digital.

**Detecção de valores críticos:**
```python
# apps/exame/services/resultado.py
from apps.exame.models import ResultadoExame, ReferenciaExame
from apps.comunicacao.tasks import enviar_notificacao_valor_critico
from decimal import Decimal


def salvar_resultado(resultado: ResultadoExame, valores: dict, realizado_por) -> ResultadoExame:
    resultado.valores = valores
    resultado.realizado_por = realizado_por
    resultado.realizado_at = timezone.now()
    resultado.status = ResultadoExame.Status.REALIZADO

    critico = False
    for ref_id_str, valor_str in valores.items():
        try:
            ref = ReferenciaExame.objects.get(id=ref_id_str, exame=resultado.exame)
            valor = Decimal(str(valor_str))
            if ref.valor_critico_minimo and valor < ref.valor_critico_minimo:
                critico = True
            if ref.valor_critico_maximo and valor > ref.valor_critico_maximo:
                critico = True
        except (ReferenciaExame.DoesNotExist, (ValueError, TypeError)):
            continue

    resultado.valor_critico_detectado = critico
    resultado.save()

    if critico:
        enviar_notificacao_valor_critico.delay(resultado.id)

    return resultado
```

**Geração de laudo PDF com WeasyPrint:**
```python
# apps/exame/services/laudo.py
from weasyprint import HTML, CSS
from django.template.loader import render_to_string
from apps.exame.models import ResultadoExame


def gerar_laudo_pdf(atendimento) -> bytes:
    resultados = ResultadoExame.objects.filter(
        atendimento=atendimento,
        status__in=["VALIDADO"],
    ).select_related("exame", "realizado_por", "validado_por")

    contexto = {
        "atendimento": atendimento,
        "paciente": atendimento.paciente,
        "resultados": resultados,
        "tenant": atendimento.tenant,
        "logo_url": atendimento.tenant.logo.url if atendimento.tenant.logo else None,
    }

    html_string = render_to_string("exame/laudo/base.html", contexto)
    css = CSS(filename="static/css/laudo.css")
    return HTML(string=html_string, base_url="http://localhost").write_pdf(stylesheets=[css])
```

**Assinatura digital:**
Adota-se assinatura eletrônica simples com validade jurídica pela Medida Provisória 2.200-2/2001 (ICP-Brasil não obrigatória para todos os casos). O laudo em PDF recebe:

1. **Hash SHA-256** do conteúdo do laudo gerado.
2. **Identificação do biomédico** (nome, CRBM, data/hora de assinatura) embutida no PDF.
3. **Registro no banco** do hash + ID do biomédico + timestamp.
4. **QR Code** no laudo apontando para URL de verificação: `https://labsaas.com.br/verificar/{laudo_hash}`.

Para laboratórios que exigem certificado ICP-Brasil (acreditação ISO 15189), a integração com uma Autoridade Certificadora é configurável por tenant via `settings["assinatura_certificado_digital"]`.

**Task de geração:**
```python
# apps/exame/tasks.py
from celery import shared_task


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def gerar_e_salvar_laudo(self, atendimento_id: str):
    from apps.atendimento.models import Atendimento
    from apps.exame.services.laudo import gerar_laudo_pdf
    from apps.core.storage import salvar_laudo_s3
    from apps.comunicacao.tasks import notificar_laudo_pronto

    try:
        atendimento = Atendimento.objects.get(id=atendimento_id)
        pdf_bytes = gerar_laudo_pdf(atendimento)
        url = salvar_laudo_s3(atendimento, pdf_bytes)
        atendimento.url_laudo = url
        atendimento.save(update_fields=["url_laudo"])
        notificar_laudo_pronto.delay(atendimento_id)
    except Exception as exc:
        raise self.retry(exc=exc)
```

## 4.8 Controle de Qualidade Analítica

**Responsabilidade:** Registro de soros controle, cálculo estatístico (média, DP, CV%), avaliação pelas regras de Westgard, gráfico de Levey-Jennings.

**Decisão: Criar do zero.** O sistema atual não tem este módulo.

**Cálculo das regras de Westgard:**
```python
# apps/qc/services/westgard.py
from decimal import Decimal
from statistics import mean, stdev
from typing import NamedTuple


class ResultadoWestgard(NamedTuple):
    regras_violadas: list[str]
    alerta: bool


def avaliar_westgard(valores_anteriores: list[Decimal], valor_novo: Decimal) -> ResultadoWestgard:
    """
    Avalia as 6 regras de Westgard Multirregra.
    valores_anteriores: lista dos últimos N valores do mesmo controle/nível/equipamento.
    """
    todos = valores_anteriores + [valor_novo]
    if len(todos) < 2:
        return ResultadoWestgard(regras_violadas=[], alerta=False)

    media = Decimal(str(mean(float(v) for v in todos)))
    dp = Decimal(str(stdev(float(v) for v in todos))) if len(todos) > 1 else Decimal("0")
    if dp == 0:
        return ResultadoWestgard(regras_violadas=[], alerta=False)

    violadas = []
    z_scores = [(v - media) / dp for v in todos]
    z_novo = z_scores[-1]

    # 1_2s: warning — valor fora de ±2DP
    if abs(z_novo) > 2:
        violadas.append("1_2s")

    # 1_3s: rejeição — valor fora de ±3DP
    if abs(z_novo) > 3:
        violadas.append("1_3s")

    # 2_2s: dois consecutivos do mesmo lado além de ±2DP
    if len(z_scores) >= 2:
        z_ant = z_scores[-2]
        if (z_novo > 2 and z_ant > 2) or (z_novo < -2 and z_ant < -2):
            violadas.append("2_2s")

    # R_4s: dois consecutivos com diferença de 4DP (um acima, outro abaixo)
    if len(z_scores) >= 2:
        z_ant = z_scores[-2]
        if abs(z_novo - z_ant) > 4:
            violadas.append("R_4s")

    # 4_1s: quatro consecutivos além de ±1DP (mesmo lado)
    if len(z_scores) >= 4:
        ultimos4 = z_scores[-4:]
        if all(z > 1 for z in ultimos4) or all(z < -1 for z in ultimos4):
            violadas.append("4_1s")

    # 10x: dez consecutivos do mesmo lado da média
    if len(z_scores) >= 10:
        ultimos10 = z_scores[-10:]
        if all(z > 0 for z in ultimos10) or all(z < 0 for z in ultimos10):
            violadas.append("10x")

    alerta = any(r in violadas for r in ["1_3s", "2_2s", "R_4s", "4_1s", "10x"])
    return ResultadoWestgard(regras_violadas=violadas, alerta=alerta)
```

## 4.9 Convênios e TISS

**Responsabilidade:** Cadastro de convênios, tabelas de preço, geração de XML TISS para faturamento, controle de glosas.

**Decisão: Criar do zero.** O sistema atual tem planos de preço básicos mas não suporta TISS.

**Geração de XML TISS 3.x:**
```python
# apps/financeiro/services/tiss.py
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom


def gerar_xml_tiss_lote(atendimentos: list, convenio) -> bytes:
    """Gera XML no padrão TISS 3.05.00 da ANS."""
    root = Element("ans:mensagemTISS")
    root.set("xmlns:ans", "http://www.ans.gov.br/padroes/tiss/schemas")

    cabecalho = SubElement(root, "ans:cabecalho")
    SubElement(cabecalho, "ans:identificacaoTransacao").text = "ENVIOLOTERPS"
    SubElement(cabecalho, "ans:versaoSchema").text = "3.05.00"
    SubElement(cabecalho, "ans:dataRegistroTransacao").text = timezone.now().strftime("%Y-%m-%d")

    prestador = SubElement(cabecalho, "ans:identificacaoPrestador")
    SubElement(prestador, "ans:codigoPrestadorNaOperadora").text = convenio.codigo_operadora_tiss

    lote = SubElement(root, "ans:prestadorParaOperadora")
    lote_guias = SubElement(lote, "ans:loteGuias")

    for atendimento in atendimentos:
        guia = SubElement(lote_guias, "ans:guiasSP-SADT")
        SubElement(guia, "ans:numeroGuiaPrestador").text = atendimento.numero
        # ... campos obrigatórios conforme layout TISS

    xml_str = minidom.parseString(tostring(root)).toprettyxml(indent="  ")
    return xml_str.encode("utf-8")
```

## 4.10 Comunicação e Notificações

**Responsabilidade:** Envio de mensagens por e-mail, SMS e WhatsApp com templates configuráveis por tenant. Fila de envio com retry.

**Task com retry:**
```python
# apps/comunicacao/tasks.py
from celery import shared_task
from django.utils import timezone


@shared_task(bind=True, max_retries=5, default_retry_delay=60)
def enviar_notificacao(self, notificacao_id: int):
    from apps.comunicacao.models import Notificacao
    from apps.comunicacao.services import get_adapter_para_canal

    try:
        notif = Notificacao.objects.get(id=notificacao_id)
        notif.status = "ENVIANDO"
        notif.tentativas += 1
        notif.save(update_fields=["status", "tentativas"])

        adapter = get_adapter_para_canal(notif.canal, notif.tenant)
        adapter.enviar(notif)

        notif.status = "ENVIADO"
        notif.enviado_at = timezone.now()
        notif.save(update_fields=["status", "enviado_at"])

    except Exception as exc:
        notif.status = "FALHOU"
        notif.erro_detalhe = str(exc)
        notif.save(update_fields=["status", "erro_detalhe"])
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def enviar_notificacao_valor_critico(self, resultado_id: str):
    """Notificação de valor crítico — prioridade máxima, canal preferido: WhatsApp/SMS."""
    from apps.exame.models import ResultadoExame

    resultado = ResultadoExame.objects.select_related(
        "atendimento__paciente", "exame", "atendimento__medico_solicitante"
    ).get(id=resultado_id)

    # Notifica biomédico responsável
    # Notifica médico solicitante (se cadastrado)
    # Registra no AuditLog com acao=VALOR_CRITICO
    ...
```

## 4.11 Estoque e Insumos

**Responsabilidade:** Controle de reagentes com rastreabilidade por lote, alertas de ponto de pedido, custo por exame.

**Decisão: Criar do zero.** O sistema atual não tem este módulo.

**Alerta automático de ponto de pedido:**
```python
# apps/estoque/tasks.py
from celery import shared_task


@shared_task
def verificar_ponto_pedido():
    """Executa diariamente. Emite alerta para reagentes abaixo do ponto de pedido."""
    from apps.estoque.models import Reagente
    from apps.comunicacao.services import notificar_admin_tenant

    abaixo = Reagente.objects.filter(
        estoque_atual__lte=models.F("ponto_pedido"),
        deleted_at__isnull=True,
    ).select_related("tenant")

    for reagente in abaixo:
        notificar_admin_tenant(
            reagente.tenant,
            gatilho="estoque_abaixo_ponto_pedido",
            contexto={"reagente": reagente.nome, "estoque": float(reagente.estoque_atual)},
        )
```

## 4.12 LGPD e Auditoria

**Responsabilidade:** Registro imutável de ações sobre dados sensíveis, relatórios de acesso, execução de solicitações de titulares, retenção e descarte automático.

**Decisão: Criar do zero.** O sistema atual não tem auditoria formal.

**Middleware de auditoria:**
```python
# apps/auditoria/middleware.py
from apps.auditoria.models import AuditLog


def registrar_auditoria(
    tenant,
    usuario,
    acao: str,
    modelo: str,
    objeto_id: str,
    dados_antes=None,
    dados_depois=None,
    request=None,
) -> None:
    AuditLog.objects.create(
        tenant=tenant,
        usuario=usuario,
        acao=acao,
        modelo=modelo,
        objeto_id=str(objeto_id),
        dados_antes=dados_antes,
        dados_depois=dados_depois,
        ip_address=get_client_ip(request) if request else None,
        user_agent=request.META.get("HTTP_USER_AGENT", "")[:500] if request else "",
    )
```

**Task de retenção:**
```python
@shared_task
def executar_politica_retencao():
    """Executa mensalmente. Anonimiza pacientes inativos conforme configuração do tenant."""
    from apps.platform.models import Tenant
    from apps.core.services.paciente import anonimizar_paciente

    for tenant in Tenant.objects.filter(status="ACTIVE"):
        meses = tenant.settings.get("meses_para_anonimizacao", 60)
        cutoff = timezone.now() - timedelta(days=meses * 30)

        pacientes_inativos = Paciente.objects.filter(
            tenant=tenant,
            anonimizado_at__isnull=True,
            atendimentos__data_atendimento__lte=cutoff,
        ).exclude(atendimentos__data_atendimento__gte=cutoff)

        for paciente in pacientes_inativos:
            anonimizar_paciente(paciente)
```

---

# 5. API e Integrações

## 5.1 Padrões Gerais da API

**Versionamento:** Via URL prefix `/api/v1/`. Quando uma breaking change for necessária, uma nova versão `/api/v2/` é lançada e mantida em paralelo por no mínimo 6 meses. A versão anterior é depreciada com header `Deprecation: true` e `Sunset: <data>`.

**Autenticação:** JWT Bearer Token no header `Authorization: Bearer <token>`. Endpoints públicos (portal do paciente, onboarding) não requerem token.

**Formato de resposta:** JSON com `snake_case`. Erros seguem o formato:
```json
{
  "error": {
    "code": "PACIENTE_NOT_FOUND",
    "message": "Paciente com o ID informado não encontrado neste laboratório.",
    "detail": null
  }
}
```

**Paginação cursor-based** (preferencial para listas grandes):
```json
{
  "count": 1547,
  "next": "/api/v1/pacientes/?cursor=cD0yMDI2LTA2LTI0&page_size=20",
  "previous": null,
  "results": []
}
```

**Filtros:** via `django-filter` com parâmetros na query string:
```
GET /api/v1/atendimentos/?status=CONCLUIDO&data_inicio=2026-01-01&data_fim=2026-06-30
```

**Rate limiting por tenant:** 1000 requests/hora por tenant (Redis como backend). Endpoints de geração de PDF: 60/hora por tenant. Endpoints públicos: 20/hora por IP.

**Documentação OpenAPI 3.1:** via `drf-spectacular`. Acessível em `/api/v1/schema/`, com Swagger UI em `/api/v1/docs/` (desativado em produção por padrão, habilitável por configuração).

```python
# config/settings/base.py
SPECTACULAR_SETTINGS = {
    "TITLE": "LabSaaS API",
    "VERSION": "1.0.0",
    "DESCRIPTION": "API do sistema de gestão laboratorial LabSaaS.",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
}
```

## 5.2 Tabela de Endpoints por Módulo

| Módulo | Método | URL | Auth mínima | Descrição |
|---|---|---|---|---|
| Auth | POST | `/api/v1/auth/token/` | público | Login JWT |
| Auth | POST | `/api/v1/auth/token/refresh/` | refresh token | Renovar access token |
| Auth | POST | `/api/v1/auth/token/blacklist/` | access token | Logout |
| Auth | POST | `/api/v1/auth/2fa/setup/` | autenticado | Configurar TOTP |
| Auth | POST | `/api/v1/auth/2fa/verify/` | autenticado | Verificar código TOTP |
| Pacientes | GET | `/api/v1/pacientes/` | recepcionista | Listar pacientes |
| Pacientes | POST | `/api/v1/pacientes/` | recepcionista | Cadastrar paciente |
| Pacientes | GET | `/api/v1/pacientes/{id}/` | recepcionista | Detalhe do paciente |
| Pacientes | PATCH | `/api/v1/pacientes/{id}/` | recepcionista | Atualizar dados |
| Pacientes | GET | `/api/v1/pacientes/{id}/atendimentos/` | recepcionista | Histórico |
| Pacientes | POST | `/api/v1/pacientes/{id}/lgpd/consentimento/` | recepcionista | Registrar consentimento |
| Portal | POST | `/api/v1/portal/acesso/` | público | Login do paciente |
| Portal | GET | `/api/v1/portal/laudos/` | token paciente | Laudos do paciente |
| Fila | POST | `/api/v1/fila/` | recepcionista | Adicionar à fila |
| Fila | GET | `/api/v1/fila/` | recepcionista | Fila do dia |
| Fila | PATCH | `/api/v1/fila/{id}/` | recepcionista | Atualizar status |
| Atendimento | POST | `/api/v1/atendimentos/` | recepcionista | Criar atendimento |
| Atendimento | GET | `/api/v1/atendimentos/{id}/` | recepcionista | Detalhe |
| Atendimento | POST | `/api/v1/atendimentos/{id}/pagamentos/` | recepcionista | Registrar pagamento |
| Atendimento | GET | `/api/v1/relatorios/financeiro/` | admin_clinica | Relatório financeiro |
| Exames | GET | `/api/v1/exames/` | biomedico | Catálogo de exames |
| Exames | POST | `/api/v1/exames/` | admin_clinica | Cadastrar exame |
| Resultados | GET | `/api/v1/resultados/?status=REALIZADO` | biomedico | Resultados pendentes |
| Resultados | PATCH | `/api/v1/resultados/{id}/` | biomedico | Salvar resultado |
| Resultados | POST | `/api/v1/resultados/{id}/validar/` | biomedico | Validar e assinar |
| Laudos | POST | `/api/v1/atendimentos/{id}/laudo/` | biomedico | Gerar laudo PDF |
| Laudos | GET | `/api/v1/atendimentos/{id}/laudo/` | recepcionista+ | URL do laudo |
| Amostras | GET | `/api/v1/amostras/{codigo_barras}/` | recepcionista | Buscar por código |
| Amostras | PATCH | `/api/v1/amostras/{id}/status/` | recepcionista | Atualizar status |
| QC | POST | `/api/v1/qc/registros/` | biomedico | Registrar QC |
| QC | GET | `/api/v1/qc/levey-jennings/{exame_id}/` | biomedico | Dados para gráfico |
| Estoque | GET | `/api/v1/estoque/reagentes/` | admin_clinica | Listar reagentes |
| Estoque | POST | `/api/v1/estoque/movimentacoes/` | recepcionista | Registrar entrada/saída |
| Platform | POST | `/api/v1/platform/tenants/` | superadmin | Criar tenant |
| Platform | GET | `/api/v1/platform/metrics/` | superadmin | Métricas globais |

## 5.3 Webhooks

Cada tenant pode configurar até 5 endpoints webhook em `tenant.settings["webhooks"]`.

| Evento | Quando dispara | Payload chave |
|---|---|---|
| `laudo.finalizado` | Todos exames do atendimento validados | `atendimento_id`, `url_laudo` |
| `pagamento.registrado` | Pagamento salvo com status PAGO | `atendimento_id`, `valor`, `forma` |
| `amostra.rejeitada` | Rejeição de amostra | `codigo_barras`, `motivo` |
| `valor_critico.detectado` | Detecção de pânico analítico | `resultado_id`, `exame_nome` |
| `fila.atualizada` | Mudança de status na fila | `item_fila_id`, `status_novo` |

Assinatura HMAC-SHA256 no header `X-LabSaaS-Signature` para verificação de autenticidade. Retry automático: 5 tentativas com backoff exponencial (1min, 5min, 30min, 2h, 24h).

## 5.4 Integrações Externas

### WhatsApp Business (Meta Cloud API)

Cada tenant cadastra seu próprio `whatsapp_phone_number_id` e `whatsapp_token` nas configurações. A plataforma não gerencia conta de WhatsApp centralizada — cada laboratório usa sua conta Meta Business.

```python
# apps/comunicacao/adapters/whatsapp.py
import requests


class WhatsAppAdapter:
    BASE_URL = "https://graph.facebook.com/v19.0"

    def __init__(self, tenant):
        self.phone_number_id = tenant.settings["whatsapp_phone_number_id"]
        self.token = tenant.settings["whatsapp_token"]

    def enviar(self, notificacao) -> None:
        url = f"{self.BASE_URL}/{self.phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "to": notificacao.destinatario,
            "type": "template",
            "template": {
                "name": notificacao.gatilho,  # Template aprovado pela Meta
                "language": {"code": "pt_BR"},
                "components": [
                    {
                        "type": "body",
                        "parameters": [{"type": "text", "text": notificacao.mensagem}],
                    }
                ],
            },
        }
        resp = requests.post(
            url,
            json=payload,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=15,
        )
        resp.raise_for_status()
```

### Gateway de E-mail (SendGrid)

```python
# apps/comunicacao/adapters/email.py
import sendgrid
from sendgrid.helpers.mail import Mail
from django.conf import settings


class EmailAdapter:
    def __init__(self, tenant):
        api_key = tenant.settings.get("sendgrid_api_key") or settings.SENDGRID_DEFAULT_API_KEY
        self.client = sendgrid.SendGridAPIClient(api_key=api_key)
        self.remetente = tenant.settings.get("email_remetente", settings.DEFAULT_FROM_EMAIL)

    def enviar(self, notificacao) -> None:
        message = Mail(
            from_email=self.remetente,
            to_emails=notificacao.destinatario,
            subject=notificacao.assunto,
            html_content=notificacao.mensagem,
        )
        self.client.send(message)
```

### Gateway de SMS

Integração via API REST genérica compatível com Zenvia, Twilio ou Infobip. Configurado por tenant via `settings["sms_provider"]` e `settings["sms_api_key"]`. Um `SmsAdapterFactory` retorna o adapter correto conforme o provider configurado.

### Storage S3-Compatible (Cloudflare R2)

```python
# config/settings/base.py
DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
AWS_ACCESS_KEY_ID = env("R2_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = env("R2_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = env("R2_BUCKET_NAME")
AWS_S3_ENDPOINT_URL = env("R2_ENDPOINT_URL")  # ex: https://<id>.r2.cloudflarestorage.com
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = "private"
```

Laudos PDF armazenados com path `tenants/{tenant_id}/laudos/{atendimento_id}/{timestamp}.pdf`. URLs de acesso são pré-assinadas com expiração de 1 hora — nunca expostas publicamente sem prazo.

### NFS-e Municipal

O padrão ABRASF é adotado com adaptadores por município:

```python
# apps/atendimento/services/nfse/base.py
from abc import ABC, abstractmethod


class NfseAdapter(ABC):
    @abstractmethod
    def emitir(self, atendimento) -> dict:
        """Retorna {'numero_nfse': str, 'pdf_url': str, 'xml': str}"""

    @abstractmethod
    def cancelar(self, numero_nfse: str) -> bool:
        ...


class NfseAdapterFactory:
    ADAPTERS = {
        "2304400": "apps.atendimento.services.nfse.fortaleza.NfseFortalezaAdapter",
        "3550308": "apps.atendimento.services.nfse.sao_paulo.NfseSaoPauloAdapter",
        # Adicionar adaptadores conforme demanda de municípios
    }

    @classmethod
    def get(cls, tenant) -> NfseAdapter:
        codigo_ibge = tenant.settings.get("municipio_codigo_ibge")
        adapter_path = cls.ADAPTERS.get(codigo_ibge)
        if not adapter_path:
            raise NotImplementedError(
                f"NFS-e não suportado para o município com código IBGE {codigo_ibge}."
            )
        module_path, class_name = adapter_path.rsplit(".", 1)
        module = __import__(module_path, fromlist=[class_name])
        return getattr(module, class_name)(tenant)
```

---

# 6. Frontend

## 6.1 Decisão Arquitetural

**Escolha: Django Templates + HTMX + Alpine.js com estilos shadcn/ui via TailwindCSS 4.**

A alternativa descartada foi SPA React/Next.js separado. O descarte se justifica por: (a) a equipe inicial é pequena — dois deployments, build pipelines separados e gerenciamento de estado client-side triplicariam a carga operacional sem benefício proporcional; (b) HTMX cobre 95% das interações CRUD do sistema com zero JavaScript adicional; (c) o único requisito de real-time (fila de atendimento) é atendido com Alpine.js + WebSocket, sem framework reativo pesado.

**Stack frontend:**
- **HTMX 2.x:** Requisições AJAX declarativas em HTML, substituição parcial de DOM.
- **Alpine.js 3.x:** Reatividade micro-localizada (dropdowns, modais, estado de UI simples).
- **TailwindCSS 4:** Build via CLI no pipeline CI. Zero runtime JavaScript.
- **Lucide Icons:** Bundled via npm, referenciados com `data-lucide` attribute e inicializados via `lucide.createIcons()`.

## 6.2 Configuração de Tema TailwindCSS 4

```css
/* static/css/theme.css */
@import "tailwindcss";

@theme {
  --color-primary-50: oklch(0.97 0.02 250);
  --color-primary-100: oklch(0.93 0.05 250);
  --color-primary-500: oklch(0.55 0.18 250);
  --color-primary-600: oklch(0.48 0.18 250);
  --color-primary-700: oklch(0.42 0.18 250);

  --color-success-500: oklch(0.60 0.15 145);
  --color-warning-500: oklch(0.75 0.15 75);
  --color-danger-500: oklch(0.55 0.22 25);

  --font-sans: "Inter", ui-sans-serif, system-ui;
  --font-mono: "JetBrains Mono", ui-monospace;

  --radius-sm: 0.375rem;
  --radius-md: 0.5rem;
  --radius-lg: 0.75rem;
}
```

## 6.3 Convenções de Ícones Lucide

- Tamanho padrão: `size-4` (16px) inline em texto, `size-5` (20px) em botões, `size-6` (24px) em cabeçalhos.
- Cor: herda via `currentColor` — nunca definir cor no ícone, definir no container.
- Acessibilidade: ícones decorativos com `aria-hidden="true"`. Ícones funcionais sem texto visível exigem `aria-label` no elemento pai.

## 6.4 Telas e Componentes

| Tela | Responsividade | Componentes shadcn/ui |
|---|---|---|
| Painel principal | Desktop-only (lg+) | Card, Table, Badge, Button, Dialog |
| Cadastro de paciente | Desktop-only (lg+) | Form, Input, Label, Select, Checkbox, Alert |
| Fila de atendimento | Desktop-only (lg+) | Table, Badge, Button, Popover |
| Orçamento / Atendimento | Desktop-only (lg+) | Form, Combobox, Table, Separator |
| Preenchimento de resultado | Desktop-only (lg+) | Sheet, Table, Tooltip, Badge, Progress |
| Etiquetas de amostra | Print-only CSS | — |
| Relatórios financeiros | Desktop-only (lg+) | DataTable, DateRangePicker, Chart |
| Gráfico Levey-Jennings | Desktop-only (lg+) | Chart (Recharts via CDN) |
| Portal do paciente | Mobile-first | Card, Accordion, Button, Avatar |
| Painel do superadmin | Desktop-only (lg+) | DataTable, Chart, Alert, Tabs |
| Login | Responsiva (sm+) | Form, Input, Button, Alert |

## 6.5 Responsividade

| Tela | Estratégia | Justificativa |
|---|---|---|
| Painel principal | Desktop-only (lg+) | Recepcionistas em balcão com monitor |
| Área do biomédico | Desktop-only (lg+) | Entrada intensa de dados numéricos |
| Relatórios | Desktop-only (lg+) | Tabelas largas requerem espaço horizontal |
| Portal do paciente | Mobile-first | Paciente acessa predominantemente por celular |
| Login | Responsiva | Qualquer dispositivo pode precisar logar |
| Etiquetas | Print-only | Formato definido pela etiqueta física |

## 6.6 Dark Mode

Não suportado na versão inicial. Sistemas clínicos operam em ambientes com iluminação controlada onde o modo claro com contraste adequado é mais seguro para leitura de valores numéricos e identificação de alertas por cor. A adição futura é viável sem refatoração — TailwindCSS 4 suporta `data-theme` nativamente.

## 6.7 Acessibilidade (WCAG 2.1 AA)

- Contraste mínimo de 4.5:1 para texto normal, 3:1 para texto grande (verificado com `axe-core` no CI).
- Navegação completa por teclado (Tab, Enter, Escape, Arrow Keys em menus).
- `aria-label` em todos os ícones funcionais e botões sem texto visível.
- Focus ring visível em todos os elementos interativos.
- Mensagens de erro associadas ao campo via `aria-describedby`.
- Formulários com `<label>` associado via `for`/`id`.

## 6.8 Estados Padrão de UI

**Loading state:** HTMX adiciona classe `.htmx-request` automaticamente durante requisição. Ícone spinner via Alpine.js com `x-show`.

**Error state:**
```html
<div class="rounded-lg border border-danger-200 bg-danger-50 p-4" role="alert">
  <div class="flex gap-3">
    <i data-lucide="circle-alert" class="size-5 text-danger-500 shrink-0" aria-hidden="true"></i>
    <div>
      <p class="font-medium text-danger-800">Erro ao carregar dados</p>
      <p class="text-sm text-danger-700 mt-1">{{ mensagem_erro }}</p>
    </div>
  </div>
</div>
```

**Empty state:**
```html
<div class="flex flex-col items-center justify-center py-16 text-center">
  <i data-lucide="inbox" class="size-12 text-gray-300 mb-4" aria-hidden="true"></i>
  <h3 class="text-lg font-medium text-gray-900">{{ titulo_vazio }}</h3>
  <p class="text-sm text-gray-500 mt-1 max-w-sm">{{ descricao_vazio }}</p>
</div>
```

---

# 7. Segurança

## 7.1 Autenticação e Tokens

- **JWT com refresh rotation:** a cada uso do refresh token ele é invalidado e um novo par é emitido. Tokens revogados registrados na tabela `OutstandingToken` do simplejwt com blacklist.
- **Armazenamento:** access token no `sessionStorage` (limpo ao fechar aba). Refresh token em cookie `HttpOnly; Secure; SameSite=Strict`.
- **Access token de 15 minutos:** minimiza janela de ataque em caso de token roubado.
- **Bloqueio por tentativas:** 5 falhas consecutivas = conta bloqueada por 15 minutos. Registrado no `AuditLog`.

## 7.2 Autorização por Papel e Objeto

```python
# apps/core/permissions.py
from rest_framework.permissions import BasePermission


class IsTenantMember(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        tenant = getattr(request, "tenant", None)
        if tenant is None:
            return False
        return request.user.tenant_memberships.filter(
            tenant=tenant, is_active=True
        ).exists()


class HasRole(BasePermission):
    def __init__(self, *roles: str):
        self.roles = roles

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        tenant = getattr(request, "tenant", None)
        return request.user.tenant_memberships.filter(
            tenant=tenant, role__in=self.roles, is_active=True
        ).exists()
```

`django-guardian` é usado para permissões por objeto quando necessário (ex: biomédico só valida exames do próprio turno).

## 7.3 Proteções Obrigatórias

| Proteção | Implementação |
|---|---|
| CSRF | Ativo para todas as views Django (exceto API JWT com Bearer) |
| XSS | Auto-escape Django templates; `bleach` para sanitizar HTML de templates de notificação configurados por admin |
| SQL Injection | ORM exclusivo; raw SQL proibido sem revisão; `params` parametrizados quando inevitável |
| Clickjacking | `X-Frame-Options: DENY` via Nginx |
| CORS | `django-cors-headers` com regex de origens por subdomínio do tenant |
| Rate limiting | `djangorestframework-ratelimit` com backend Redis |

## 7.4 Headers HTTP de Segurança

```nginx
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-Frame-Options "DENY" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Permissions-Policy "camera=(), microphone=(), geolocation=()" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'nonce-{nonce}'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self' wss://*.labsaas.com.br; frame-ancestors 'none';" always;
```

O nonce do CSP é gerado por request e injetado via context processor no template.

## 7.5 Criptografia de Dados Sensíveis

**Em repouso:** CPF, RG e campo `valores` de `ResultadoExame` criptografados com `django-encrypted-fields` (AES-256 com chave derivada do AWS Secrets Manager). Busca por CPF via hash SHA-256 determinístico em campo separado não criptografado.

**Em trânsito:** TLS 1.3 obrigatório. TLS 1.0 e 1.1 desabilitados no Nginx. Certificado wildcard `*.labsaas.com.br` gerenciado via Cloudflare com renovação automática.

## 7.6 Secrets Management

Em produção: AWS Secrets Manager. Em desenvolvimento: `django-environ` lendo `.env` local não commitado. `.env.example` com placeholders é commitado como documentação. Nunca variáveis de ambiente hardcoded na imagem Docker.

## 7.7 Pen Test e Resposta a Incidentes

**Frequência:** Trimestral para API e autenticação (OWASP ZAP automático no CI + Burp Suite manual). Anual para engenharia social.

**Plano de resposta a vazamento de dados:**

1. **Detecção (0–30 min):** Alerta Sentry/Prometheus. On-call notificado via PagerDuty.
2. **Contenção (30 min–2h):** Revogar todos os tokens JWT do tenant afetado. Suspender tenant (`status=SUSPENDED`).
3. **Análise (2h–24h):** `AuditLog` para determinar escopo. Identificar pacientes afetados.
4. **Notificação (24h–72h):** Notificação à ANPD (Art. 48 LGPD, prazo 72h). Notificação ao tenant.
5. **Erradicação (24h–7 dias):** Patch da vulnerabilidade. Reautenticação obrigatória para todos os usuários.
6. **Pós-incidente (7–30 dias):** Post-mortem. Atualização do modelo de ameaças.

---

# 8. Infraestrutura e DevOps

## 8.1 Dockerfile Multi-Stage

```dockerfile
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc libcairo2 libpango-1.0-0 libpangocairo-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

FROM base AS deps
COPY requirements/production.txt .
RUN pip install --no-cache-dir -r production.txt

FROM node:20-slim AS frontend
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY static/ ./static/
COPY templates/ ./templates/
RUN npm run build

FROM base AS production
COPY --from=deps /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin
COPY --from=frontend /app/static/dist ./static/dist
COPY . .
RUN python manage.py collectstatic --noinput --settings=config.settings.production
EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--workers", "4", \
     "--worker-class", "gevent", "--bind", "0.0.0.0:8000", "--timeout", "120"]
```

## 8.2 Docker Compose (Desenvolvimento)

```yaml
version: "3.9"
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: labsaas_dev
      POSTGRES_USER: labsaas
      POSTGRES_PASSWORD: labsaas
    volumes: [postgres_data:/var/lib/postgresql/data]
    ports: ["5432:5432"]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    environment: {MINIO_ROOT_USER: labsaas, MINIO_ROOT_PASSWORD: labsaas123}
    ports: ["9000:9000", "9001:9001"]
    volumes: [minio_data:/data]

  web:
    build: {context: ., target: base}
    command: python manage.py runserver 0.0.0.0:8000
    volumes: [.:/app]
    ports: ["8000:8000"]
    environment:
      DJANGO_SETTINGS_MODULE: config.settings.development
      DATABASE_URL: postgres://labsaas:labsaas@db:5432/labsaas_dev
      REDIS_URL: redis://redis:6379/0
    depends_on: [db, redis, minio]

  celery_worker:
    build: {context: ., target: base}
    command: celery -A config.celery worker -l info -Q default,laudos,notificacoes
    volumes: [.:/app]
    environment:
      DJANGO_SETTINGS_MODULE: config.settings.development
      DATABASE_URL: postgres://labsaas:labsaas@db:5432/labsaas_dev
      REDIS_URL: redis://redis:6379/0
    depends_on: [db, redis]

  celery_beat:
    build: {context: ., target: base}
    command: celery -A config.celery beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    volumes: [.:/app]
    environment:
      DJANGO_SETTINGS_MODULE: config.settings.development
      DATABASE_URL: postgres://labsaas:labsaas@db:5432/labsaas_dev
      REDIS_URL: redis://redis:6379/0
    depends_on: [db, redis]

  channels:
    build: {context: ., target: base}
    command: uvicorn config.asgi:application --host 0.0.0.0 --port 8001 --reload
    volumes: [.:/app]
    ports: ["8001:8001"]
    environment:
      DJANGO_SETTINGS_MODULE: config.settings.development
      DATABASE_URL: postgres://labsaas:labsaas@db:5432/labsaas_dev
      REDIS_URL: redis://redis:6379/0
    depends_on: [db, redis]

volumes:
  postgres_data:
  minio_data:
```

## 8.3 Pipeline CI/CD (GitHub Actions)

```yaml
name: CI/CD
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: "3.12"}
      - run: pip install ruff black isort mypy
      - run: ruff check . && black --check . && isort --check-only .
      - run: mypy apps/ --config-file pyproject.toml

  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env: {POSTGRES_DB: labsaas_test, POSTGRES_USER: labsaas, POSTGRES_PASSWORD: labsaas}
        options: --health-cmd pg_isready --health-interval 10s --health-retries 5
      redis:
        image: redis:7
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: "3.12"}
      - run: pip install -r requirements/development.txt
      - run: pytest --cov=apps --cov-report=xml --cov-fail-under=80
        env:
          DATABASE_URL: postgres://labsaas:labsaas@localhost:5432/labsaas_test
          REDIS_URL: redis://localhost:6379/0
          DJANGO_SETTINGS_MODULE: config.settings.test
      - uses: codecov/codecov-action@v4

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install bandit safety
      - run: bandit -r apps/ -ll && safety check -r requirements/production.txt

  build:
    needs: [lint, test, security]
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - uses: docker/build-push-action@v5
        with:
          push: true
          tags: ghcr.io/labsaas/app:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy-staging:
    needs: build
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - run: kubectl set image deployment/labsaas-web web=ghcr.io/labsaas/app:${{ github.sha }}
        env: {KUBECONFIG: "${{ secrets.STAGING_KUBECONFIG }}"}

  deploy-production:
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment: production
    steps:
      - run: kubectl set image deployment/labsaas-web web=ghcr.io/labsaas/app:${{ github.sha }}
        env: {KUBECONFIG: "${{ secrets.PROD_KUBECONFIG }}"}
```

## 8.4 Banco de Dados e Migrations Zero-Downtime

**Padrão expand-contract:**

1. Migration adiciona coluna nullable (nunca `NOT NULL` sem default imediato em tabelas grandes).
2. Deploy: código escreve na coluna nova E na antiga simultaneamente.
3. Backfill: script preenche coluna nova para registros existentes.
4. Migration: torna coluna `NOT NULL`, remove coluna antiga.
5. Deploy: código remove referência à coluna antiga.

Nunca renomear coluna diretamente — cria coluna nova, migra dados, remove antiga em migration subsequente.

## 8.5 Backup

| Item | Frequência | Retenção | Destino |
|---|---|---|---|
| Dump PostgreSQL completo | Diário (03:00 BRT) | 20 anos (CFM 1821/2007) | S3 Glacier Deep Archive |
| WAL streaming (Point-in-Time Recovery) | Contínuo | 30 dias | S3 Standard |
| Arquivos S3 (laudos, uploads) | Replicação cross-region automática | 20 anos | S3 Glacier + réplica |
| Teste de restore automatizado | Mensal | — | Ambiente isolado de restore |

O teste mensal de restore: restaura último backup em ambiente isolado, executa verificações básicas de integridade (contagem de registros, leitura de laudo de amostra), reporta resultado. Falha no teste aciona alerta crítico.

## 8.6 Monitoramento

- **Sentry:** Captura exceções com contexto de `tenant_id` e `user_id`. Alerta para taxa de erro > 1% em janela de 5 minutos.
- **Prometheus + Grafana:** Métricas de latência, tamanho de filas Celery, uso por tenant.
- **Structured logging (structlog):** Todos os logs em JSON com campos `tenant_id`, `user_id`, `request_id`. Ingeridos no Grafana Loki.

```python
# apps/core/metrics.py
from prometheus_client import Counter, Histogram

atendimentos_criados = Counter(
    "labsaas_atendimentos_criados_total",
    "Total de atendimentos criados",
    ["tenant_slug"],
)

tempo_geracao_laudo = Histogram(
    "labsaas_laudo_geracao_segundos",
    "Tempo de geração de laudo PDF em segundos",
    ["tenant_slug"],
    buckets=[0.5, 1, 2, 5, 10, 30],
)
```

## 8.7 Estratégia de Deploy: Rolling Update

**Escolha: Rolling Update no Kubernetes** com `maxUnavailable: 0` e `maxSurge: 1`. Alternativa descartada (Blue-Green) exige o dobro de infraestrutura sempre disponível, custo desproporcional para o estágio atual.

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: labsaas-web
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate: {maxUnavailable: 0, maxSurge: 1}
  template:
    spec:
      containers:
        - name: web
          image: ghcr.io/labsaas/app:latest
          ports: [{containerPort: 8000}]
          readinessProbe:
            httpGet: {path: /health/, port: 8000}
            initialDelaySeconds: 10
            periodSeconds: 5
          livenessProbe:
            httpGet: {path: /health/, port: 8000}
            initialDelaySeconds: 30
            periodSeconds: 10
          resources:
            requests: {memory: "256Mi", cpu: "250m"}
            limits: {memory: "512Mi", cpu: "1000m"}
```

## 8.8 SLA e Contingência

**SLA alvo:** 99,9% uptime mensal (máximo 43 min downtime/mês).

| Falha | Comportamento | Tempo de recuperação |
|---|---|---|
| Banco de dados primary | Promoção automática da réplica (Patroni/RDS Multi-AZ) | < 60 segundos |
| Redis | Modo degradado: sem WebSocket, sem cache de sessão; JWT funciona independentemente | Imediato (degradado) |
| S3 | Laudos já gerados inacessíveis; novos laudos enfileirados para retrogeração | Automático ao restabelecer |
| Pico de tráfego | HPA escala de 3 para 10 réplicas quando CPU > 70% por 2 min | < 3 minutos |

---

# 9. Testes

## 9.1 Estratégia: Pirâmide de Testes

```
        /\
       /  \
      / E2E \        ← Playwright: fluxos críticos (login, atendimento, laudo)
     /--------\
    / Integração\    ← pytest-django com banco real: módulos, API endpoints
   /-------------\
  /   Unitários   \  ← pytest puro: serviços de domínio, cálculos, regras
 /-----------------\
```

**Unitários (70% do total):** Testam funções e classes de `services/` sem banco de dados nem HTTP. Rápidos, isolados, sem fixtures pesadas.

**Integração (25% do total):** Testam views, serializers e a camada de banco juntos. Usam banco PostgreSQL real (não SQLite — o comportamento do ORM difere). Usam `factory_boy` para criar dados de teste.

**E2E (5% do total):** Testam fluxos completos no navegador via Playwright. Executam em ambiente de staging antes de cada deploy em produção.

## 9.2 Ferramentas

| Ferramenta | Uso |
|---|---|
| `pytest-django` | Runner principal, fixtures de banco, cliente de teste |
| `factory_boy` | Factories para criação de dados de teste (substitui fixtures estáticas) |
| `faker` | Dados realistas (CPFs válidos, nomes, endereços) |
| `coverage.py` | Medição de cobertura; mínimo 80% para código de domínio |
| `Playwright` | Testes E2E no Chromium |
| `responses` | Mock de chamadas HTTP externas (WhatsApp, SendGrid, S3) |
| `freezegun` | Controle de data/hora em testes de fila, QC e relatórios |

## 9.3 Configuração pytest

```toml
# pyproject.toml
[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "config.settings.test"
python_files = ["tests.py", "test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--reuse-db",
    "--strict-markers",
    "-x",
]
markers = [
    "slow: testes lentos (e2e, relatórios pesados)",
    "integration: testes que requerem banco de dados",
    "unit: testes puramente unitários",
]
```

## 9.4 Factories

```python
# tests/factories.py
import factory
from factory.django import DjangoModelFactory
from faker import Faker
from validate_docbr import CPF

fake = Faker("pt_BR")
cpf_gen = CPF()


class TenantFactory(DjangoModelFactory):
    class Meta:
        model = "platform.Tenant"

    name = factory.Faker("company", locale="pt_BR")
    slug = factory.Sequence(lambda n: f"tenant-{n}")
    cnpj = factory.LazyFunction(lambda: fake.cnpj())
    status = "ACTIVE"
    plan = "PROFESSIONAL"


class UserFactory(DjangoModelFactory):
    class Meta:
        model = "accounts.User"

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda o: f"{o.username}@example.com")
    password = factory.PostGenerationMethodCall("set_password", "testpass123")


class PacienteFactory(DjangoModelFactory):
    class Meta:
        model = "core.Paciente"

    tenant = factory.SubFactory(TenantFactory)
    nome_completo = factory.Faker("name", locale="pt_BR")
    cpf_hash = factory.LazyFunction(lambda: hash_cpf(cpf_gen.generate()))
    data_nascimento = factory.Faker("date_of_birth", minimum_age=1, maximum_age=90)
    sexo = factory.Iterator(["M", "F"])


class ExameFactory(DjangoModelFactory):
    class Meta:
        model = "exame.Exame"

    tenant = factory.SubFactory(TenantFactory)
    nome = factory.Sequence(lambda n: f"Hemograma Completo {n}")
    codigo = factory.Sequence(lambda n: f"HEM{n:06d}")
    material = "Sangue venoso"
    metodo = "Citometria de fluxo"
    status = "ATIVO"
```

## 9.5 Testes Obrigatórios

### Isolamento de Multitenancy

```python
# tests/test_multitenancy.py
import pytest
from tests.factories import TenantFactory, PacienteFactory


@pytest.mark.django_db
def test_paciente_de_outro_tenant_nao_aparece(client, tenant_a, tenant_b):
    """
    Garante que dados de um tenant nunca vazam para outro.
    Esse teste deve passar em CADA deploy — é a proteção mais crítica do sistema.
    """
    paciente_a = PacienteFactory(tenant=tenant_a)
    PacienteFactory(tenant=tenant_b)

    # Simula request autenticado no tenant_a
    client.force_login(tenant_a.admin_user)
    client.defaults["SERVER_NAME"] = f"{tenant_a.slug}.labsaas.com.br"

    response = client.get("/api/v1/pacientes/")
    ids_retornados = [p["id"] for p in response.json()["results"]]

    assert str(paciente_a.id) in ids_retornados
    assert len(ids_retornados) == 1  # Apenas o paciente do tenant_a
```

### Regras de Westgard

```python
# tests/test_westgard.py
from decimal import Decimal
from apps.qc.services.westgard import avaliar_westgard


def test_regra_1_3s_detecta_valor_extremo():
    media = Decimal("100")
    dp = Decimal("10")
    valores_anteriores = [media + dp * Decimal(str(i * 0.1)) for i in range(-5, 5)]
    valor_critico = media + dp * Decimal("3.5")  # 3.5 desvios padrões

    resultado = avaliar_westgard(valores_anteriores, valor_critico)

    assert "1_3s" in resultado.regras_violadas
    assert resultado.alerta is True


def test_regra_10x_detecta_tendencia():
    media = Decimal("100")
    dp = Decimal("10")
    # 10 valores consecutivos acima da média
    valores = [media + dp * Decimal("0.5")] * 10
    novo_valor = media + dp * Decimal("0.3")

    resultado = avaliar_westgard(valores, novo_valor)

    assert "10x" in resultado.regras_violadas
```

### Permissões por papel

```python
# tests/test_permissions.py
@pytest.mark.django_db
def test_recepcionista_nao_pode_validar_resultado(client, tenant, resultado_exame):
    recepcionista = criar_funcionario(tenant, role="recepcionista")
    client.force_login(recepcionista.user)

    response = client.post(f"/api/v1/resultados/{resultado_exame.id}/validar/")

    assert response.status_code == 403


@pytest.mark.django_db
def test_biomedico_pode_validar_resultado(client, tenant, resultado_exame):
    biomedico = criar_funcionario(tenant, role="biomedico")
    client.force_login(biomedico.user)

    response = client.post(f"/api/v1/resultados/{resultado_exame.id}/validar/")

    assert response.status_code == 200
```

### Geração de laudo PDF

```python
# tests/test_laudo.py
@pytest.mark.django_db
def test_gerar_laudo_pdf_retorna_bytes_validos(atendimento_com_resultados_validados):
    from apps.exame.services.laudo import gerar_laudo_pdf

    pdf_bytes = gerar_laudo_pdf(atendimento_com_resultados_validados)

    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes[:4] == b"%PDF"  # Assinatura do formato PDF
    assert len(pdf_bytes) > 1000  # Laudo não pode ser vazio
```

### Cálculo de TISS

```python
@pytest.mark.django_db
def test_xml_tiss_contem_campos_obrigatorios(atendimento_convenio):
    from apps.financeiro.services.tiss import gerar_xml_tiss_lote

    xml_bytes = gerar_xml_tiss_lote([atendimento_convenio], atendimento_convenio.convenio)
    xml_str = xml_bytes.decode("utf-8")

    assert "ans:mensagemTISS" in xml_str
    assert "ans:identificacaoTransacao" in xml_str
    assert atendimento_convenio.numero in xml_str
```

## 9.6 Seeds para Desenvolvimento

```python
# scripts/seed_dev.py
"""
Popula o banco de desenvolvimento com dados realistas.
Executar: python manage.py runscript seed_dev
"""
from tests.factories import TenantFactory, PacienteFactory, ExameFactory
from apps.agenda.models import Plano


def run():
    tenant = TenantFactory(slug="demo", name="Laboratório Demo LTDA", status="ACTIVE")

    # 50 pacientes
    pacientes = PacienteFactory.create_batch(50, tenant=tenant)

    # 20 exames com preços
    exames = ExameFactory.create_batch(20, tenant=tenant)
    for exame in exames:
        Plano.objects.create(tenant=tenant, exame=exame, nome="Particular", preco="45.00")

    print(f"Seed concluído: {len(pacientes)} pacientes, {len(exames)} exames no tenant '{tenant.slug}'")
```

---

# 10. Migração do Sistema Atual

## 10.1 Inventário de Dados a Migrar

| Tabela atual | Model novo | Transformações necessárias |
|---|---|---|
| `core_usuario` (paciente) | `core.Paciente` | Separar em `User` + `Paciente`; criptografar CPF/RG; adicionar `cpf_hash`; adicionar `tenant_id` |
| `core_usuario` (funcionário) | `core.Funcionario` + `TenantUser` | Separar por flag `is_funcionario`; mapear cargo; criar vínculo `TenantUser` |
| `core_endereco` | `core.Endereco` | Adicionar `tenant_id`; manter relacionamento com Paciente |
| `agenda_plano` | `agenda.Plano` | Adicionar `tenant_id` |
| `agenda_ordemchegada` | `agenda.Fila` + `agenda.ItemFila` | Decompor em Fila (por dia) + ItemFila (por paciente); novo formato de sequência |
| `atendimento_orcamentoexames` | `atendimento.Atendimento` + `ItemAtendimento` + `Pagamento` | Decompor: cabeçalho vira Atendimento, M2M de exames vira ItemAtendimento, pagamento vira Pagamento |
| `exame_exame` | `exame.Exame` | Adicionar `tenant_id`; adicionar `codigo_tuss`; separar flag `terceirizado` |
| `exame_referenciaexame` | `exame.ReferenciaExame` | Adicionar `tenant_id`; adicionar campos de valor crítico |
| `exame_fatoresreferencia` | Integrado em `ReferenciaExame` com campos de faixa etária | Migrar como referências com `idade_minima_anos`/`idade_maxima_anos` |
| `exame_valorEsperado` | Integrado em `ReferenciaExame` com tipo `qualitativo` | Migrar como referências do tipo qualitativo |
| `exame_grupoexame` | `exame.GrupoExame` | Adicionar `tenant_id` |

## 10.2 Estratégia de Migração

**Abordagem escolhida: Migração Incremental com Execução Paralela.**

A alternativa descartada foi "big bang" (migrar tudo de uma vez com sistema parado). O big bang é inadequado porque: (a) o tempo de downtime seria de horas, inaceitável para um laboratório em operação; (b) qualquer erro na migração resulta em rollback total e nova tentativa com downtime adicional.

**Plano de execução incremental:**

**Semana 1 — Preparação:**
- Deploy do novo sistema em subdomínio paralelo (`novo.clinicalaboratorio.com.br`).
- Script de migração inicial (read-only): lê o banco SQLite antigo e escreve no PostgreSQL novo sem alterar o antigo.
- Validação pós-migração com dados históricos completos.

**Semana 2 — Execução Paralela:**
- Ambos os sistemas ativos simultaneamente.
- Novos atendimentos entram no sistema novo.
- Atendimentos antigos acessíveis no sistema antigo (somente leitura) e espelhados no novo.
- Equipe treinada no novo sistema em ambiente real.

**Semana 3 — Corte:**
- Janela de manutenção de 2 horas (fim de semana, fora do horário de pico).
- Sincronização final dos dados remanescentes.
- DNS redireciona para o novo sistema.
- Sistema antigo fica em modo read-only por 30 dias como fallback.

## 10.3 Script de Migração

```python
# scripts/migrate_from_legacy.py
import sqlite3
import django
from django.db import transaction

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from apps.platform.models import Tenant
from apps.core.models import Paciente
from apps.core.services.paciente import hash_cpf


def migrar_pacientes(conn: sqlite3.Connection, tenant: Tenant) -> dict[int, str]:
    """Retorna mapeamento {id_antigo: uuid_novo}."""
    cursor = conn.execute(
        "SELECT id, first_name, last_name, cpf, rg, data_nascimento, sexo, telefone "
        "FROM core_usuario WHERE is_paciente = 1"
    )
    mapeamento = {}
    for row in cursor.fetchall():
        antigo_id, primeiro_nome, sobrenome, cpf, rg, data_nasc, sexo, telefone = row
        cpf_normalizado = "".join(filter(str.isdigit, cpf or ""))

        with transaction.atomic():
            paciente = Paciente.objects.create(
                tenant=tenant,
                nome_completo=f"{primeiro_nome} {sobrenome}".strip(),
                cpf_hash=hash_cpf(cpf_normalizado) if cpf_normalizado else "",
                data_nascimento=data_nasc,
                sexo=sexo or "N",
                telefone=telefone or "",
            )
            mapeamento[antigo_id] = str(paciente.id)

    return mapeamento


def executar_migracao(sqlite_path: str, tenant_slug: str):
    conn = sqlite3.connect(sqlite_path)
    tenant = Tenant.objects.get(slug=tenant_slug)

    print("Migrando pacientes...")
    mapa_pacientes = migrar_pacientes(conn, tenant)
    print(f"  {len(mapa_pacientes)} pacientes migrados.")

    # Continuar com exames, atendimentos, etc.
    conn.close()
```

## 10.4 Validação Pós-Migração

```python
# scripts/validar_migracao.py
def validar(tenant_slug: str, sqlite_path: str):
    conn = sqlite3.connect(sqlite_path)
    tenant = Tenant.objects.get(slug=tenant_slug)

    checks = []

    # Contagem de pacientes
    qtd_antigo = conn.execute("SELECT COUNT(*) FROM core_usuario WHERE is_paciente=1").fetchone()[0]
    qtd_novo = Paciente.objects.filter(tenant=tenant).count()
    checks.append(("Pacientes", qtd_antigo, qtd_novo, qtd_antigo == qtd_novo))

    # Contagem de exames
    qtd_exames_antigo = conn.execute("SELECT COUNT(*) FROM exame_exame").fetchone()[0]
    qtd_exames_novo = Exame.objects.filter(tenant=tenant).count()
    checks.append(("Exames", qtd_exames_antigo, qtd_exames_novo, qtd_exames_antigo == qtd_exames_novo))

    print("\nResultado da validação:")
    for nome, antigo, novo, ok in checks:
        status = "OK" if ok else "FALHOU"
        print(f"  [{status}] {nome}: antigo={antigo}, novo={novo}")

    return all(ok for _, _, _, ok in checks)
```

## 10.5 Rollback

Se a migração falhar após o corte de DNS:

1. **Reverter DNS** para o sistema antigo (TTL de 60 segundos configurado previamente).
2. **Sistema antigo** retoma em modo normal (nunca foi desligado, apenas ficou em standby).
3. **Análise** do ponto de falha com logs e dados do AuditLog.
4. **Nova tentativa** após correção, com outra janela de manutenção.

O sistema antigo permanece operacional em paralelo por no mínimo 30 dias após o corte bem-sucedido, como garantia de rollback emergencial.

## 10.6 Estimativa de Downtime

Com a abordagem incremental, o downtime real é de **2 horas** (janela de manutenção para sincronização final e corte de DNS). A janela recomendada é sábado ou domingo entre 23h e 01h.

---

# 11. Roadmap de Implementação

## Fase 0 — Fundação (Semanas 1–6)

**Objetivo:** Infraestrutura, multitenancy, autenticação e CI/CD operacionais. Nenhuma funcionalidade clínica — apenas a base que tudo o mais precisa.

**Entregáveis:**
- Repositório com estrutura de diretórios definida, `pyproject.toml` configurado, hooks de commit (ruff, black, isort).
- Docker Compose de desenvolvimento funcionando com PostgreSQL, Redis, MinIO.
- Modelo `Tenant` e `TenantUser` com migrations.
- Middleware de resolução de tenant por subdomínio com testes de isolamento.
- Autenticação JWT com `simplejwt` (login, logout, refresh, blacklist).
- Template base de layout (Django Templates + HTMX + TailwindCSS 4 compilado).
- Pipeline GitHub Actions: lint → testes → build → deploy staging.
- Endpoint `/health/` para readiness/liveness probes do Kubernetes.
- `AuditLog` imutável com middleware de registro automático.

**Critérios de aceite:**
- Dois tenants (`tenant-a.labsaas.com.br` e `tenant-b.labsaas.com.br`) retornam dados isolados.
- Login gera JWT válido com `tenant_id` e `role` no payload.
- CI passa em menos de 10 minutos.
- Deploy automático no staging a cada push na `main`.

---

## Fase 1 — Core Clínico MVP (Semanas 7–14)

**Objetivo:** Fluxo mínimo de atendimento: paciente → fila → exame → laudo PDF.

**Entregáveis:**
- Módulo de Pacientes: cadastro, busca por CPF (com hash), validação de CPF, consentimento LGPD.
- Módulo de Fila: ordem de chegada com número sequencial, WebSocket de atualização em tempo real.
- Catálogo de Exames: cadastro de exames com código automático, referências de normalidade, grupos.
- Módulo de Atendimento: criação de orçamento, seleção de exames, cálculo de valor.
- Coleta e Amostras: registro de coleta, código de barras, etiquetas ZPL e PDF.
- Área do Biomédico: preenchimento de resultados, detecção de valor crítico, validação.
- Geração de Laudo PDF com WeasyPrint: template HTML/CSS com logo do tenant, resultados formatados, QR Code de verificação.
- Portal do Paciente: acesso via CPF + data de nascimento, download de laudos.

**Critérios de aceite:**
- Fluxo completo funciona para 3 tipos de exame (hemograma, glicemia, urina rotina).
- Laudo PDF gerado em menos de 5 segundos.
- Valor crítico detectado dispara alerta em menos de 5 minutos.
- Portal do paciente acessível no celular (WCAG AA).

---

## Fase 2 — Financeiro e Convênios (Semanas 15–22)

**Objetivo:** Atendimento financeiro completo com convênios e faturamento.

**Entregáveis:**
- Registro de pagamento com split (múltiplas formas em um atendimento).
- Fechamento de caixa diário com conferência.
- Relatórios: diário, semanal, mensal, por convênio, por exame (com exportação CSV).
- Módulo de Convênios: cadastro, tabelas de preço por TUSS, associação com pacientes.
- Geração de XML TISS 3.x para faturamento de convênios.
- Integração NFS-e para os dois primeiros municípios (Fortaleza e São Paulo como referência).
- Comprovante de atendimento em PDF.

**Critérios de aceite:**
- XML TISS gerado passa na validação do validador oficial da ANS.
- Relatório financeiro mensal carrega em menos de 3 segundos para 5.000 atendimentos.
- NFS-e emitida e número retornado pela prefeitura em menos de 30 segundos.

---

## Fase 3 — Qualidade e Compliance (Semanas 23–30)

**Objetivo:** Controle de qualidade analítica, auditoria LGPD e 2FA.

**Entregáveis:**
- Módulo QC: registro de controles por lote e equipamento, cálculo de média/DP/CV%.
- Gráfico de Levey-Jennings interativo (Recharts) com alertas por regras de Westgard.
- Cadastro de equipamentos e registro de calibrações e manutenções.
- Relatório de QC por período para acreditação (exportação PDF e CSV).
- 2FA TOTP obrigatório para `biomedico` e `admin_clinica` quando configurado pelo tenant.
- Relatório de acesso a dados LGPD por usuário e período.
- Fluxo de solicitação de titular (acesso, correção, exclusão, portabilidade) com prazo de 15 dias rastreado.
- Task de anonimização automática de pacientes inativos.

**Critérios de aceite:**
- Regras de Westgard calculadas corretamente (validado com dataset de referência do CLIA).
- 2FA configurado e obrigatório bloqueia acesso sem código TOTP.
- Relatório LGPD de acesso a dados cobre 100% das ações registradas no AuditLog.

---

## Fase 4 — Comunicação e Portal (Semanas 31–38)

**Objetivo:** Notificações multicanal e agendamento online pelo paciente.

**Entregáveis:**
- Notificações por e-mail (SendGrid), SMS e WhatsApp Business API.
- Templates de notificação configuráveis por tenant (editor de texto no painel do admin).
- Gatilhos automáticos: laudo pronto, valor crítico, agendamento confirmado, lembrete de preparo.
- Log de entrega com status de cada notificação.
- Agendamento com hora marcada: calendário de disponibilidade, confirmação automática por WhatsApp.
- Exibição de instruções de preparo ao agendar o exame.
- Portal do paciente aprimorado: histórico completo, notificações no sistema.

**Critérios de aceite:**
- Notificação de laudo pronto entregue em menos de 2 minutos após validação.
- Taxa de entrega de e-mail > 95% (medida via webhook SendGrid).
- Agendamento online funciona sem intervenção de recepcionista.

---

## Fase 5 — Estoque e Integrações (Semanas 39–48)

**Objetivo:** Controle de estoque de reagentes e integração com sistemas hospitalares.

**Entregáveis:**
- Módulo de Estoque: cadastro de reagentes com lote/validade/ANVISA, entradas e saídas.
- Rastreabilidade: movimentação de estoque vinculada ao resultado do exame.
- Alertas de ponto de pedido com notificação ao admin.
- Custo de reagente por exame (para cálculo de margem de contribuição).
- Integração HL7 FHIR R4: endpoint para receber pedidos de exame de HIS/RIS externos e retornar resultados.
- Importação de tabela TUSS atualizada via script agendado.

**Critérios de aceite:**
- Saída de estoque registrada automaticamente ao marcar resultado como REALIZADO.
- Alerta de ponto de pedido disparado antes do estoque zerar (validado em teste de integração).
- Endpoint FHIR retorna Bundle de DiagnosticReport válido (validado com HAPI FHIR validator).

---

## Fase 6 — Escala e Produto (Semanas 49–60)

**Objetivo:** Self-service completo, billing automatizado e analytics.

**Entregáveis:**
- Self-service onboarding: cadastro de novo laboratório sem intervenção manual, trial automático, configuração guiada (wizard de 5 passos).
- Billing automatizado: integração com Stripe ou PagarMe para cobrança mensal por plano + uso excedente.
- Dashboard de analytics para o superadmin: receita recorrente mensal (MRR), churn, NPS, atendimentos por tenant.
- Dashboard de analytics para o admin da clínica: TAT por exame, volume por período, exames mais solicitados.
- API pública documentada para integrações de parceiros (com chave de API por tenant).
- Clonagem de catálogo de exames entre tenants pelo superadmin (para onboarding rápido).

**Critérios de aceite:**
- Novo laboratório completa onboarding e realiza primeiro atendimento em menos de 2 dias úteis sem suporte humano.
- Billing gera cobrança correta para 10 tenants simulados com planos e volumes diferentes.
- Dashboard de analytics carrega em menos de 2 segundos para 12 meses de histórico.

---

# 12. Padrões de Código e Convenções

## 12.1 Estrutura de Diretórios

```
labsaas/
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   ├── staging.py
│   │   ├── production.py
│   │   └── test.py
│   ├── urls.py
│   ├── wsgi.py
│   ├── asgi.py
│   └── celery.py
├── apps/
│   ├── platform/
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── tenant.py
│   │   │   └── tenant_user.py
│   │   ├── middleware.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── tasks.py
│   │   ├── services.py
│   │   ├── admin.py
│   │   └── tests/
│   │       ├── test_middleware.py
│   │       └── test_tenant.py
│   ├── accounts/
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── tests/
│   ├── core/
│   │   ├── models/
│   │   │   ├── mixins.py      ← SoftDeleteMixin, TenantAwareModel
│   │   │   ├── paciente.py
│   │   │   ├── funcionario.py
│   │   │   └── medico.py
│   │   ├── services/
│   │   │   └── paciente.py
│   │   ├── permissions.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── tests/
│   ├── agenda/
│   │   ├── models/
│   │   │   ├── fila.py
│   │   │   └── plano.py
│   │   ├── services/
│   │   │   └── fila.py
│   │   ├── consumers.py       ← Django Channels WebSocket
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── tests/
│   ├── atendimento/
│   │   ├── models/
│   │   │   ├── atendimento.py
│   │   │   └── pagamento.py
│   │   ├── services/
│   │   │   ├── orcamento.py
│   │   │   ├── relatorio.py
│   │   │   └── nfse/
│   │   │       ├── base.py
│   │   │       └── fortaleza.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── tasks.py
│   │   └── tests/
│   ├── coleta/
│   │   ├── models/
│   │   │   └── amostra.py
│   │   ├── services/
│   │   │   └── etiqueta.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── tests/
│   ├── exame/
│   │   ├── models/
│   │   │   ├── exame.py
│   │   │   ├── referencia.py
│   │   │   └── resultado.py
│   │   ├── services/
│   │   │   ├── resultado.py
│   │   │   └── laudo.py
│   │   ├── templates/
│   │   │   └── exame/laudo/
│   │   │       ├── base.html
│   │   │       └── hemograma.html
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── tasks.py
│   │   └── tests/
│   ├── financeiro/
│   │   ├── models/
│   │   │   └── convenio.py
│   │   ├── services/
│   │   │   └── tiss.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── tests/
│   ├── qc/
│   │   ├── models/
│   │   │   ├── equipamento.py
│   │   │   └── controle.py
│   │   ├── services/
│   │   │   └── westgard.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── tests/
│   ├── estoque/
│   │   ├── models/
│   │   │   └── reagente.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── tasks.py
│   │   └── tests/
│   ├── auditoria/
│   │   ├── models/
│   │   │   └── audit_log.py
│   │   ├── middleware.py
│   │   ├── views.py
│   │   └── tests/
│   └── comunicacao/
│       ├── models/
│       │   └── notificacao.py
│       ├── adapters/
│       │   ├── email.py
│       │   ├── sms.py
│       │   └── whatsapp.py
│       ├── services.py
│       ├── tasks.py
│       └── tests/
├── templates/
│   ├── base.html
│   ├── painel/
│   │   └── base.html
│   └── registration/
│       └── login.html
├── static/
│   ├── css/
│   │   └── theme.css
│   └── js/
│       └── main.js
├── tests/
│   ├── conftest.py
│   └── factories.py
├── scripts/
│   ├── seed_dev.py
│   └── migrate_from_legacy.py
├── k8s/
│   ├── deployment.yaml
│   ├── service.yaml
│   └── ingress.yaml
├── requirements/
│   ├── base.txt
│   ├── development.txt
│   └── production.txt
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── manage.py
└── .env.example
```

## 12.2 Convenções de Nomenclatura

| Artefato | Convenção | Exemplo |
|---|---|---|
| Models | `PascalCase`, singular | `ResultadoExame`, `ItemFila` |
| Views (class) | `PascalCase` + sufixo do verbo | `PacienteListView`, `ResultadoUpdateView` |
| Views (função) | `snake_case` + verbo + substantivo | `gerar_laudo_pdf`, `buscar_paciente_ajax` |
| Serializers | `PascalCase` + `Serializer` | `PacienteSerializer`, `AtendimentoCreateSerializer` |
| URLs | `snake_case` com hífens no path | `/api/v1/pacientes/`, `/api/v1/resultados/{id}/validar/` |
| Templates | `app/nome_funcao.html` | `exame/resultado_form.html`, `agenda/fila_lista.html` |
| Tasks Celery | `snake_case` descritivo | `gerar_e_salvar_laudo`, `verificar_trials_expirados` |
| Services | `snake_case` descritivo | `criar_atendimento`, `calcular_preco_exame` |
| CSS classes | Tailwind utilitário (sem classes customizadas desnecessárias) | `flex gap-4 items-center` |
| Variáveis JS | `camelCase` | `tenantSlug`, `laudoUrl` |
| Constantes | `UPPER_SNAKE_CASE` | `MAX_TENTATIVAS_LOGIN = 5` |
| Branches Git | `feat/`, `fix/`, `chore/` + slug curto | `feat/modulo-qc`, `fix/westgard-10x` |

## 12.3 Configuração pyproject.toml

```toml
[tool.ruff]
target-version = "py312"
line-length = 100
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "N",   # pep8-naming
    "UP",  # pyupgrade
    "B",   # flake8-bugbear
    "S",   # flake8-bandit (segurança)
    "DJ",  # flake8-django
]
ignore = [
    "S101",  # assert em testes é permitido
    "S106",  # senha hardcoded em fábricas de teste
]

[tool.ruff.per-file-ignores]
"tests/*" = ["S", "B"]

[tool.black]
line-length = 100
target-version = ["py312"]

[tool.isort]
profile = "black"
line_length = 100
known_django = ["django", "rest_framework"]
sections = ["FUTURE", "STDLIB", "DJANGO", "THIRDPARTY", "FIRSTPARTY", "LOCALFOLDER"]

[tool.mypy]
python_version = "3.12"
strict = true
plugins = ["mypy_django_plugin.main"]
ignore_missing_imports = false

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false

[tool.django-stubs]
django_settings_module = "config.settings.test"

[tool.coverage.run]
source = ["apps"]
omit = ["*/tests/*", "*/migrations/*", "*/admin.py"]

[tool.coverage.report]
fail_under = 80
show_missing = true
```

## 12.4 Type Hints

Obrigatórios em todas as funções públicas de `services/`, `tasks/` e `serializers/`. Opcional em views e templates. Configuração `strict` do mypy ativada — sem `Any` implícito.

```python
# Correto
def calcular_preco_exame(exame: Exame, plano: Plano | None) -> Decimal:
    ...

# Proibido — sem tipo de retorno, sem tipo de argumento
def calcular_preco_exame(exame, plano):
    ...
```

## 12.5 Comentários e Docstrings

Comentários apenas quando o **porquê** é não-óbvio. Nunca comentar o **quê** (o código já diz).

```python
# Correto — explica uma invariante não-óbvia
# select_for_update() é obrigatório aqui: sem ele, duas recepcionistas
# simultâneas podem gerar o mesmo número de sequência.
fila = Fila.objects.select_for_update().get(...)

# Proibido — descreve o que o código já diz
# Incrementa a sequência da fila
fila.sequencia_atual += 1
```

Docstrings em Google style apenas para funções de serviço com mais de 3 parâmetros ou comportamento não-óbvio:

```python
def avaliar_westgard(valores_anteriores: list[Decimal], valor_novo: Decimal) -> ResultadoWestgard:
    """Avalia as regras de Westgard Multirregra para controle de qualidade analítica.

    Args:
        valores_anteriores: Histórico de valores do mesmo controle/nível/equipamento.
            Mínimo de 2 valores para cálculo estatístico significativo.
        valor_novo: Valor do controle a ser avaliado.

    Returns:
        ResultadoWestgard com lista de regras violadas e flag de alerta.
    """
```

## 12.6 Git e Branching

**Estratégia: Trunk-Based Development.** A alternativa descartada foi GitFlow. GitFlow é adequado para releases com ciclos longos. O LabSaaS usa deploy contínuo (CD) — a complexidade de branches `develop`, `release`, `hotfix` é desnecessária e atrasa a entrega.

**Regras:**
- Branch principal: `main` (sempre deployável).
- Feature branches de vida curta: máximo 3 dias antes de merge.
- Commits seguem Conventional Commits: `feat:`, `fix:`, `chore:`, `docs:`, `test:`, `refactor:`.
- Pull requests exigem: 1 aprovação, CI verde, sem conflitos.

**Template de PR:**
```markdown
## O que muda

<!-- Uma linha descrevendo a mudança -->

## Por que

<!-- Contexto e motivação -->

## Como testar

- [ ] Abrir o painel no slug `demo.labsaas.com.br`
- [ ] Cadastrar um paciente com CPF válido
- [ ] Verificar que o paciente aparece na lista

## Checklist

- [ ] Testes escritos/atualizados
- [ ] Migrations revisadas (zero-downtime)
- [ ] `AuditLog` registra ações sensíveis
- [ ] Sem `SELECT *` no código novo
- [ ] Sem lógica de negócio em template
- [ ] Sem `except Exception` genérico
```

## 12.7 Proibições Explícitas

As seguintes práticas são proibidas e falharão no code review:

- **`SELECT *`:** sempre especificar campos ou usar `.only()` e `.defer()`.
- **Lógica de negócio em templates:** templates apenas exibem dados, nunca calculam.
- **`except Exception as e: pass`:** capturar exceção genérica sem re-raise ou log é vedado.
- **Import direto de model de outro app:** usar interface de serviço ou FK. Ex: `exame/services/` não importa diretamente de `atendimento/models/`.
- **Campos `null=True` em CharField/TextField:** use `blank=True` com `default=""`. `null=True` em string fields cria dois estados para "vazio".
- **`print()` em código de produção:** usar `structlog` ou `logging`.
- **Secret ou URL hardcoded em código:** usar `env()` do `django-environ`.
- **Migration que altera coluna em tabela com dados sem estratégia zero-downtime.**
- **Raw SQL sem revisão de segurança explícita no PR.**
- **Deletar `AuditLog` por qualquer motivo.**

---

# 13. Glossário

**TAT (Turnaround Time):** Tempo entre a coleta da amostra biológica e a disponibilização do laudo para o paciente ou médico solicitante. Métrica central de qualidade operacional de um laboratório.

**QC (Quality Control / Controle de Qualidade):** Processo de verificação da acurácia e precisão dos resultados analíticos por meio da análise periódica de amostras de referência (soros controle) com valores conhecidos.

**TISS (Troca de Informações em Saúde Suplementar):** Padrão eletrônico definido pela ANS (Agência Nacional de Saúde Suplementar) para troca de informações entre prestadores de serviços de saúde e operadoras de planos de saúde. Usado para faturamento de convênios.

**TUSS (Terminologia Unificada da Saúde Suplementar):** Tabela de procedimentos, medicamentos e materiais de saúde com códigos padronizados, usada no padrão TISS. O `codigo_tuss` de um exame é o código que identifica o procedimento para fins de faturamento de convênio.

**NFS-e (Nota Fiscal de Serviços Eletrônica):** Documento fiscal digital emitido pelos municípios para serviços prestados. A emissão ocorre via integração com o sistema da prefeitura de cada município, que possui APIs próprias (em geral, baseadas no padrão ABRASF).

**Glosa:** Recusa total ou parcial do pagamento de um procedimento por parte da operadora de convênio. Ocorre quando a documentação ou codificação TISS está incorreta ou quando o procedimento não é coberto pelo plano. O sistema registra glosas e permite recurso.

**Biomédico:** Profissional de saúde com formação em Biomedicina, habilitado pelo CRBM (Conselho Regional de Biomedicina). É o responsável técnico pela realização, validação e assinatura de laudos de análises clínicas.

**Laudo:** Documento oficial emitido pelo biomédico contendo os resultados dos exames realizados, com valores obtidos, valores de referência e assinatura do responsável técnico. É o produto final de um atendimento laboratorial.

**Exame:** No contexto do LabSaaS, "exame" tem dois significados relacionados: (a) o tipo de análise no catálogo (`Exame` — template), e (b) a instância de análise realizada para um paciente específico em um atendimento (`ResultadoExame`). Quando o contexto não é claro, usa-se "exame-template" ou "resultado de exame".

**Atendimento:** Conjunto de exames solicitados para um paciente em uma visita ao laboratório, com seu respectivo orçamento e pagamento. Um paciente pode ter múltiplos atendimentos.

**Fila (Ordem de Chegada):** Sistema de controle sequencial de chegada de pacientes. Cada paciente recebe um número de sequência ao chegar (`ItemFila`) que determina a ordem de atendimento.

**Pânico Analítico (Valor Crítico):** Resultado de exame que indica risco imediato à vida do paciente. Exemplos: glicemia < 40 mg/dL ou > 500 mg/dL, potássio sérico < 2,5 mEq/L. Ao detectar valor crítico, o sistema exige notificação imediata e registrada ao médico solicitante.

**Tenant:** No LabSaaS, um tenant é um laboratório ou clínica cliente da plataforma. Cada tenant possui dados completamente isolados dos demais, opera em seu próprio subdomínio e tem configurações, usuários e catálogo de exames independentes. Os termos "clínica", "laboratório" e "tenant" são usados como sinônimos neste documento quando o contexto é o cliente da plataforma SaaS.

**Multitenancy:** Arquitetura de software onde uma única instância da aplicação serve múltiplos clientes (tenants), com isolamento lógico de dados entre eles.

**Row-Level Security (RLS):** Funcionalidade do PostgreSQL que restringe quais linhas de uma tabela são visíveis ou modificáveis por uma sessão, com base em uma política definida. Usado como segunda camada de isolamento de tenants.

**Soft Delete:** Técnica de exclusão que não remove o registro do banco de dados, mas marca-o como deletado via campo `deleted_at`. O registro permanece no banco para fins de auditoria e histórico, mas é filtrado automaticamente em queries normais.

**JWT (JSON Web Token):** Padrão aberto (RFC 7519) para transmissão segura de informações entre partes como objeto JSON assinado. Usado para autenticação stateless — o servidor não precisa armazenar sessões.

**TOTP (Time-based One-Time Password):** Algoritmo de senha de uso único baseado em tempo (RFC 6238), implementado em aplicativos como Google Authenticator. Usado para 2FA (autenticação de dois fatores).

**TAT interno:** Tempo entre a recepção da amostra (triagem) e a validação do resultado pelo biomédico. Diferente do TAT total, que inclui o tempo de entrega ao paciente.

**Levey-Jennings:** Gráfico de controle estatístico usado em laboratórios clínicos para monitorar a estabilidade dos processos analíticos ao longo do tempo. O eixo X representa o tempo (ou número de série do controle) e o eixo Y representa o valor obtido, com linhas de referência em ±1DP, ±2DP e ±3DP da média.

**Westgard Multirregra:** Conjunto de 6 regras estatísticas (12s, 13s, 22s, R4s, 41s, 10x) desenvolvido por James Westgard para avaliação do Controle de Qualidade analítico. Regras de aviso (ex: 12s) indicam instabilidade potencial; regras de rejeição (ex: 13s) indicam erro sistemático ou randômico e exigem investigação antes de liberar resultados.

**PALC:** Programa de Acreditação de Laboratórios Clínicos da SBPC/ML. Certificação de qualidade para laboratórios brasileiros.

**ISO 15189:** Norma internacional para laboratórios médicos que especifica requisitos de qualidade e competência. Exige rastreabilidade de amostras, controle de qualidade documentado e sistema de gestão de qualidade.

**LGPD (Lei Geral de Proteção de Dados):** Lei brasileira (13.709/2018) que regula o tratamento de dados pessoais. Em laboratórios clínicos, os dados de saúde são considerados "dados sensíveis" com proteção reforçada (Art. 11).

**CFM 1821/2007:** Resolução do Conselho Federal de Medicina que estabelece normas técnicas sobre a digitalização e uso dos sistemas informatizados para a guarda e manuseio dos documentos dos prontuários dos pacientes. Define retenção mínima de prontuários por 20 anos.

**ANPD:** Autoridade Nacional de Proteção de Dados, órgão federal responsável por zelar pela proteção dos dados pessoais no Brasil e fiscalizar o cumprimento da LGPD.

**SLA (Service Level Agreement):** Acordo de nível de serviço que define as métricas de desempenho e disponibilidade que a plataforma compromete-se a entregar. No LabSaaS: 99,9% de uptime mensal.

**Superadmin:** Usuário interno da equipe do LabSaaS com acesso ao painel de gestão da plataforma (todos os tenants, métricas globais, billing). Não tem acesso a dados clínicos de pacientes individuais.

**MRR (Monthly Recurring Revenue):** Receita recorrente mensal — soma das assinaturas ativas de todos os tenants. Métrica principal de saúde financeira do negócio SaaS.

**ZPL (Zebra Programming Language):** Linguagem de programação proprietária da Zebra Technologies para controle de impressoras de etiquetas térmicas. Usada para geração de etiquetas de amostras com código de barras.

**FHIR (Fast Healthcare Interoperability Resources):** Padrão internacional (HL7 FHIR R4) para troca de informações de saúde via API REST. Permite integração entre o LabSaaS e sistemas hospitalares (HIS/RIS/EHR).

**HIS (Hospital Information System):** Sistema de informação hospitalar. Sistemas externos que podem integrar com o LabSaaS via FHIR para enviar pedidos de exame e receber resultados.

---

*Fim do documento. Versão 1.0.0 — 2026-06-24.*
