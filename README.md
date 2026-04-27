# Conquest — Teste Técnico de Infraestrutura

> Duas aplicações em linguagens distintas, com cache diferenciado, observabilidade e infraestrutura 100% containerizada.

---

## Índice

- [Visão Geral](#visão-geral)
- [Stack Tecnológica](#stack-tecnológica)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Como Executar](#como-executar)
- [Endpoints Disponíveis](#endpoints-disponíveis)
- [Camada de Cache](#camada-de-cache)
- [Observabilidade](#observabilidade)
- [Diagrama de Arquitetura](#diagrama-de-arquitetura)
- [Fluxo de Atualização](#fluxo-de-atualização)
- [Análise e Sugestões de Melhoria](#análise-e-sugestões-de-melhoria)

---

## Visão Geral

O projeto é composto por:

| Componente | Tecnologia | Finalidade |
|---|---|---|
| **App 1** | Go 1.22 | API com 2 rotas (`/health`, `/time`) |
| **App 2** | Python 3.12 + FastAPI | API com 2 rotas (`/health`, `/time`) |
| **Cache/Proxy** | Nginx 1.25 | Reverse proxy com cache diferenciado |
| **Métricas** | Prometheus 2.51 | Coleta de métricas de todos os serviços |
| **Dashboards** | Grafana 10.4 | Visualização e alertas |

---

## Stack Tecnológica

- **Go 1.22** — Linguagem compilada, alta performance, zero dependências externas
- **Python 3.12 + FastAPI** — Framework async moderno, autodocumentação (OpenAPI)
- **Nginx** — Reverse proxy com módulo de proxy_cache nativo
- **Docker + Docker Compose** — Containerização e orquestração
- **Prometheus** — Time-series DB para métricas
- **Grafana** — Dashboards e alertas visuais

---

## Estrutura do Projeto

```
Conquest/
├── app-go/                        # Aplicação 1 (Go)
│   ├── main.go                    # Código-fonte
│   ├── go.mod                     # Dependências Go
│   └── Dockerfile                 # Build multi-stage
├── app-python/                    # Aplicação 2 (Python)
│   ├── main.py                    # Código-fonte FastAPI
│   ├── requirements.txt           # Dependências Python
│   └── Dockerfile                 # Build otimizado
├── nginx/                         # Cache Layer
│   ├── nginx.conf                 # Configuração com cache diferenciado
│   └── Dockerfile                 # Imagem customizada
├── observability/                 # Observabilidade
│   ├── prometheus/
│   │   └── prometheus.yml         # Configuração de scraping
│   └── grafana/
│       ├── provisioning/
│       │   ├── datasources/
│       │   │   └── datasource.yml # Auto-provisioning Prometheus
│       │   └── dashboards/
│       │       └── dashboard.yml  # Auto-provisioning dashboards
│       └── dashboards/
│           └── infra-overview.json # Dashboard pré-configurado
├── docker-compose.yml             # Orquestração completa
├── .gitignore
├── LICENSE
└── README.md                      # Este arquivo
```

---

## Como Executar

### Pré-requisitos

- [Docker](https://docs.docker.com/get-docker/) (v20+)
- [Docker Compose](https://docs.docker.com/compose/install/) (v2+)

### Subir tudo (1 comando)

```bash
docker compose up --build -d
```

### Verificar status

```bash
docker compose ps
```

### Parar tudo

```bash
docker compose down
```

### Rebuild completo (limpar cache)

```bash
docker compose down -v && docker compose up --build -d
```

---

## Endpoints Disponíveis

### Via Nginx (com cache)

| Endpoint | URL | Cache TTL |
|---|---|---|
| App Go — Texto fixo | http://localhost:80/health | 10s |
| App Go — Horário | http://localhost:80/time | 10s |
| App Python — Texto fixo | http://localhost:81/health | 60s |
| App Python — Horário | http://localhost:81/time | 60s |

### Direto nas aplicações (sem cache)

| Endpoint | URL |
|---|---|
| App Go — Texto fixo | http://localhost:8080/health |
| App Go — Horário | http://localhost:8080/time |
| App Python — Texto fixo | http://localhost:8081/health |
| App Python — Horário | http://localhost:8081/time |

### Observabilidade

| Serviço | URL | Credenciais |
|---|---|---|
| Grafana | http://localhost:3000 | admin / conquest |
| Prometheus | http://localhost:9090 | — |
| Nginx Metrics | http://localhost:9113/metrics | — |

---

## Camada de Cache

O Nginx atua como reverse proxy com **proxy_cache** diferenciado por aplicação:

```
┌─────────────┐     ┌────────────────────────────┐     ┌────────────┐
│   Cliente    │────▶│  Nginx (Reverse Proxy)     │────▶│  App Go    │
│             │     │  :80 → cache_go (TTL=10s)  │     │  :8080     │
└─────────────┘     │  :81 → cache_py (TTL=60s)  │────▶│  App Python│
                    └────────────────────────────┘     │  :8081     │
                                                       └────────────┘
```

### Como validar o cache

```bash
# Primeira requisição (MISS — busca no upstream)
curl -sI http://localhost:80/time | grep X-Cache
# X-Cache-Status: MISS

# Segunda requisição dentro do TTL (HIT — servido do cache)
curl -sI http://localhost:80/time | grep X-Cache
# X-Cache-Status: HIT

# Headers retornados:
# X-Cache-Status: MISS | HIT | EXPIRED | STALE
# X-Cache-TTL: 10s (app-go) ou 60s (app-python)
# X-App: app-go ou app-python
```

---

## Observabilidade

### Prometheus

Coleta métricas de:
- **Nginx** (via nginx-prometheus-exporter): requests/s, connections, status codes
- **App Go**: health check a cada 10s
- **App Python**: health check a cada 10s

### Grafana

Dashboard pré-provisionado **"Conquest — Infrastructure Overview"** com:
- Requests/sec por status e método (Nginx)
- Conexões ativas (Nginx)
- Conexões aceitas/tratadas (Nginx)
- Health status de cada aplicação (UP/DOWN)

Acesse em http://localhost:3000 (admin / conquest).

---

## Diagrama de Arquitetura

```
                         ┌─────────────────────────────────────────────────┐
                         │              Docker Network (conquest-net)       │
                         │                                                 │
  ┌──────────┐           │  ┌──────────────────────────────────────────┐   │
  │          │  :80      │  │          NGINX (Cache Layer)             │   │
  │          │──────────▶│  │                                          │   │
  │          │           │  │  :80 ─▶ proxy_cache (10s) ─▶ app-go     │   │
  │ Cliente  │           │  │  :81 ─▶ proxy_cache (60s) ─▶ app-python │   │
  │ (Browser │  :81      │  │                                          │   │
  │  / curl) │──────────▶│  │  /stub_status ─▶ nginx-exporter         │   │
  │          │           │  └──────────────────────────────────────────┘   │
  │          │           │       │                  │                      │
  └──────────┘           │       ▼                  ▼                      │
                         │  ┌──────────┐     ┌─────────────┐              │
                         │  │  App Go  │     │ App Python  │              │
                         │  │ (Go 1.22)│     │(FastAPI 3.12)│             │
                         │  │  :8080   │     │   :8081     │              │
                         │  │          │     │             │              │
                         │  │ /health  │     │ /health     │              │
                         │  │ /time    │     │ /time       │              │
                         │  └──────────┘     └─────────────┘              │
                         │                                                 │
                         │  ┌──────────────────────────────────────────┐   │
                         │  │         Observability Stack              │   │
                         │  │                                          │   │
                         │  │  ┌────────────┐    ┌─────────────────┐   │   │
                         │  │  │ Nginx      │    │   Prometheus    │   │   │
                         │  │  │ Exporter   │───▶│    :9090        │   │   │
                         │  │  │ :9113      │    │                 │   │   │
                         │  │  └────────────┘    └────────┬────────┘   │   │
                         │  │                             │            │   │
                         │  │                             ▼            │   │
                         │  │                    ┌─────────────────┐   │   │
                         │  │                    │    Grafana      │   │   │
                         │  │                    │    :3000        │   │   │
                         │  │                    │  (dashboards)   │   │   │
                         │  │                    └─────────────────┘   │   │
                         │  └──────────────────────────────────────────┘   │
                         └─────────────────────────────────────────────────┘
```

---

## Fluxo de Atualização

### Atualização de Código (App Go ou App Python)

```
Developer ─▶ git push ─▶ GitHub (main)
                              │
                              ▼
                    CI/CD (GitHub Actions)*
                              │
                    ┌─────────┴──────────┐
                    ▼                    ▼
              docker build          docker build
              (app-go)              (app-python)
                    │                    │
                    ▼                    ▼
              Push to Registry     Push to Registry
                    │                    │
                    └─────────┬──────────┘
                              ▼
                    docker compose up -d
                    (rolling restart do serviço alterado)
```

**Localmente (desenvolvimento):**
```bash
# Alterar código → rebuild apenas o serviço afetado
docker compose up --build -d app-go      # rebuild apenas App Go
docker compose up --build -d app-python  # rebuild apenas App Python
```

### Atualização de Configuração (Nginx / Cache)

```bash
# 1. Editar nginx/nginx.conf (ex: alterar TTL)
# 2. Rebuild + restart apenas o nginx
docker compose up --build -d nginx
```

> O cache é invalidado automaticamente no restart pois usa volume efêmero.

### Atualização de Observabilidade

```bash
# Prometheus — alterar regras de scraping
# 1. Editar observability/prometheus/prometheus.yml
# 2. Restart
docker compose restart prometheus

# Grafana — dashboards são auto-provisionados
# 1. Editar/adicionar JSON em observability/grafana/dashboards/
# 2. Restart
docker compose restart grafana
```

### Diagrama do Fluxo de Atualização

```
┌─────────────────────────────────────────────────────────────────────┐
│                    FLUXO DE ATUALIZAÇÃO                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌───────────┐    ┌───────────┐    ┌───────────┐    ┌───────────┐  │
│  │  Código   │    │  Config   │    │  Cache    │    │ Observab. │  │
│  │ (Go/Py)   │    │  (Nginx)  │    │  (TTLs)  │    │(Prom/Graf)│  │
│  └─────┬─────┘    └─────┬─────┘    └─────┬─────┘    └─────┬─────┘  │
│        │                │                │                │        │
│        ▼                ▼                ▼                ▼        │
│  ┌───────────┐    ┌───────────┐    ┌───────────┐    ┌───────────┐  │
│  │ git push  │    │ Edit conf │    │ Edit conf │    │ Edit yml/ │  │
│  │ + rebuild │    │ + rebuild │    │ + rebuild │    │ json      │  │
│  │ service   │    │ nginx     │    │ nginx     │    │ + restart │  │
│  └─────┬─────┘    └─────┬─────┘    └─────┬─────┘    └─────┬─────┘  │
│        │                │                │                │        │
│        ▼                ▼                ▼                ▼        │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │            docker compose up --build -d <service>           │   │
│  │               (zero-downtime com healthchecks)              │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Análise e Sugestões de Melhoria

### Pontos Positivos da Arquitetura Atual

| # | Ponto | Detalhe |
|---|---|---|
| 1 | **Single-command startup** | `docker compose up --build -d` sobe tudo |
| 2 | **Cache transparente** | Headers `X-Cache-Status` facilitam debug |
| 3 | **Healthchecks** | Compose aguarda apps saudáveis antes de subir Nginx |
| 4 | **Observabilidade provisionada** | Grafana sobe com datasource + dashboard prontos |
| 5 | **Isolamento** | Rede bridge dedicada, cada serviço em container separado |
| 6 | **Multi-stage build (Go)** | Imagem final ~15MB (Alpine + binário estático) |

### Pontos de Melhoria

| # | Área | Situação Atual | Melhoria Sugerida | Impacto |
|---|---|---|---|---|
| 1 | **SSL/TLS** | Sem HTTPS | Adicionar Certbot/Let's Encrypt ou Traefik com ACME | Segurança |
| 2 | **Rate Limiting** | Sem proteção | Adicionar `limit_req_zone` no Nginx | Resiliência |
| 3 | **CI/CD** | Manual (`docker compose`) | GitHub Actions: build → test → push image → deploy | Automação |
| 4 | **Container Registry** | Build local | Push para GHCR/Docker Hub em CI | Rastreabilidade |
| 5 | **Logs centralizados** | stdout dos containers | Adicionar Loki + Promtail → Grafana | Observabilidade |
| 6 | **Métricas das apps** | Apenas health | Instrumentar com `/metrics` (prom client Go + Python) | Observabilidade |
| 7 | **Alertas** | Sem alerting | Configurar Alertmanager no Prometheus | Proatividade |
| 8 | **Secrets** | Senha Grafana em plain text | Usar Docker secrets ou `.env` com git-crypt | Segurança |
| 9 | **Load Balancing** | 1 instância cada app | Escalar com `docker compose up --scale app-go=3` | Disponibilidade |
| 10 | **Cache invalidation** | Apenas TTL | Adicionar purge endpoint ou cache tags | Controle |
| 11 | **Health checks das apps** | HTTP 200 simples | Incluir readiness/liveness com dependência checks | Robustez |
| 12 | **Testes automatizados** | Sem testes | Adicionar testes de integração (ex: `curl` assertions em CI) | Qualidade |

### Evolução para Produção

```
                    EVOLUÇÃO SUGERIDA
  ┌─────────────────────────────────────────────────┐
  │                                                 │
  │   Atual              ──▶     Produção           │
  │                                                 │
  │   Nginx              ──▶     Traefik + ACME     │
  │   Docker Compose     ──▶     Kubernetes (K8s)   │
  │   Build local        ──▶     GitHub Actions CI  │
  │   Sem registry       ──▶     GHCR / ECR         │
  │   Prometheus only    ──▶     + Alertmanager      │
  │   Sem logs central.  ──▶     Loki + Promtail    │
  │   1 instância        ──▶     HPA (auto-scaling) │
  │   HTTP               ──▶     HTTPS + mTLS       │
  │                                                 │
  └─────────────────────────────────────────────────┘
```

---

## Licença

MIT — veja [LICENSE](LICENSE).
