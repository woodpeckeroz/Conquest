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
- [Análise e Sugestões de Melhoria](#análise-e-sugestões-de-melhoria)
- [Fluxo de Atualização](#fluxo-de-atualização)

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

## Fluxo de Atualização

Diagrama completo de como cada componente (código e infra) é atualizado em produção:

```
  ┌─────────────────────────────────────────────────────────────────────────────┐
  │                      FLUXO DE ATUALIZAÇÃO — CONQUEST                        │
  └─────────────────────────────────────────────────────────────────────────────┘


  ══════════════════════════════════════════════════════════════════════════════
   1. CÓDIGO DAS APLICAÇÕES (app-go / app-python)
  ══════════════════════════════════════════════════════════════════════════════

  Developer        Git             CI/CD              Registry          Produção
  ─────────       ─────           ──────             ─────────         ────────
      │               │               │                   │               │
      │  git push     │               │                   │               │
      │──────────────▶│               │                   │               │
      │               │  webhook      │                   │               │
      │               │──────────────▶│                   │               │
      │               │               │                   │               │
      │               │               │  docker build     │               │
      │               │               │──────────────────▶│               │
      │               │               │                   │               │
      │               │               │  docker push      │               │
      │               │               │──────────────────▶│               │
      │               │               │                   │  docker pull  │
      │               │               │  deploy trigger   │──────────────▶│
      │               │               │──────────────────────────────────▶│
      │               │               │                   │               │
      │               │               │               rolling restart     │
      │               │               │                   │        ┌──────┤
      │               │               │                   │        │ v2 ↑ │
      │               │               │                   │        │ v1 ↓ │
      │               │               │                   │        └──────┘

  Passos (desenvolvimento local):
    $ vi app-go/main.go              # altera código
    $ docker compose up --build -d   # rebuild + restart automático
    → Nginx detecta upstream saudável via healthcheck


  ══════════════════════════════════════════════════════════════════════════════
   2. CONFIGURAÇÃO DO NGINX (cache / proxy / headers)
  ══════════════════════════════════════════════════════════════════════════════

  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
  │  Editar      │     │  Rebuild     │     │  Validar     │
  │  nginx.conf  │────▶│  container   │────▶│  cache/hdrs  │
  └──────────────┘     └──────────────┘     └──────────────┘

  Passos:
    $ vi nginx/nginx.conf                    # altera config
    $ docker compose up --build -d nginx     # rebuild só do Nginx
    $ curl -sI http://localhost:80/time      # valida headers

  ⚠ Mudanças no nginx.conf exigem rebuild do container (config é COPY no build).
    Cache em disco (/var/cache/nginx/) persiste entre restarts do container.
    Para limpar cache: docker compose down nginx && docker compose up -d nginx


  ══════════════════════════════════════════════════════════════════════════════
   3. PROMETHEUS (scrape targets / regras / alertas)
  ══════════════════════════════════════════════════════════════════════════════

  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
  │  Editar      │     │  Restart ou  │     │  Verificar   │
  │  prometheus  │────▶│  reload      │────▶│  /targets    │
  │  .yml        │     │              │     │              │
  └──────────────┘     └──────────────┘     └──────────────┘

  Passos:
    $ vi observability/prometheus/prometheus.yml   # altera scrape config
    $ docker compose restart prometheus            # aplica (volume :ro, sem rebuild)
    → Verificar em http://localhost:9090/targets

  ✔ Volume montado como :ro — não precisa rebuild, apenas restart.
  ✔ Para hot-reload sem restart: curl -X POST http://localhost:9090/-/reload


  ══════════════════════════════════════════════════════════════════════════════
   4. GRAFANA (dashboards / datasources / credenciais)
  ══════════════════════════════════════════════════════════════════════════════

  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
  │  Editar      │     │  Restart     │     │  Verificar   │
  │  provisioning│────▶│  container   │────▶│  :3000       │
  │  ou .env     │     │              │     │              │
  └──────────────┘     └──────────────┘     └──────────────┘

  Dashboards (via provisioning — versionado):
    $ vi observability/grafana/dashboards/infra-overview.json
    $ docker compose restart grafana

  Dashboards (via UI — efêmero):
    → Editar direto no Grafana UI (:3000)
    → ⚠ Perdido ao recriar container (a menos que salvo no volume grafana-data)

  Credenciais:
    $ vi .env                               # altera GF_SECURITY_ADMIN_PASSWORD
    $ docker compose up -d grafana          # recria container com nova senha

  ✔ Provisioning (datasources + dashboards) montado como :ro.
  ✔ Dados persistem no volume grafana-data entre restarts.


  ══════════════════════════════════════════════════════════════════════════════
   5. DOCKER COMPOSE (orquestração / novos serviços)
  ══════════════════════════════════════════════════════════════════════════════

  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
  │  Editar      │     │  docker      │     │  Verificar   │
  │  docker-     │────▶│  compose up  │────▶│  docker ps   │
  │  compose.yml │     │  --build -d  │     │              │
  └──────────────┘     └──────────────┘     └──────────────┘

  Passos:
    $ vi docker-compose.yml
    $ docker compose up --build -d           # aplica diff (só recria o necessário)
    $ docker compose ps                      # valida estado

  Adicionar novo serviço:
    1. Criar pasta + Dockerfile + código
    2. Adicionar service no docker-compose.yml
    3. Adicionar scrape job no prometheus.yml (se expõe métricas)
    4. docker compose up --build -d


  ══════════════════════════════════════════════════════════════════════════════
   6. DEPENDÊNCIAS (go.mod / requirements.txt)
  ══════════════════════════════════════════════════════════════════════════════

  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
  │  Atualizar   │     │  Rebuild     │     │  Testar      │
  │  deps        │────▶│  imagem      │────▶│  endpoints   │
  └──────────────┘     └──────────────┘     └──────────────┘

  Go:
    $ cd app-go
    $ go get -u github.com/prometheus/client_golang@latest
    $ go mod tidy
    $ cd .. && docker compose up --build -d app-go

  Python:
    $ vi app-python/requirements.txt         # bump versões
    $ docker compose up --build -d app-python

  ⚠ Sempre pinar versões (ex: fastapi==0.115.0) para builds reproduzíveis.


  ══════════════════════════════════════════════════════════════════════════════
   RESUMO — MÉTODO DE ATUALIZAÇÃO POR COMPONENTE
  ══════════════════════════════════════════════════════════════════════════════

  ┌─────────────────────┬───────────────┬────────────────────────────────────┐
  │ Componente          │ Método        │ Comando                            │
  ├─────────────────────┼───────────────┼────────────────────────────────────┤
  │ App Go (código)     │ rebuild       │ compose up --build -d app-go       │
  │ App Python (código) │ rebuild       │ compose up --build -d app-python   │
  │ Nginx (config)      │ rebuild       │ compose up --build -d nginx        │
  │ Prometheus (config) │ restart/reload│ compose restart prometheus         │
  │ Grafana (dashboard) │ restart       │ compose restart grafana            │
  │ Grafana (senha)     │ recreate      │ compose up -d grafana              │
  │ Docker Compose      │ up            │ compose up --build -d              │
  │ Dependências        │ rebuild       │ compose up --build -d <service>    │
  │ Tudo (from scratch) │ full rebuild  │ compose down -v && compose up -d   │
  └─────────────────────┴───────────────┴────────────────────────────────────┘
```

---

## Licença

MIT — veja [LICENSE](LICENSE).
