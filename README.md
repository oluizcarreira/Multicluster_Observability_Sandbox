# Multicluster Observability Sandbox 🚀
### FastAPI | OpenTelemetry | KinD | Tempo | Prometheus | Grafana

Este repositório contém a implementação completa de uma arquitetura de observabilidade corporativa distribuída em ambiente local utilizando **Kubernetes (KinD)**. O projeto demonstra a separação completa de contextos entre o ambiente de aplicação e a infraestrutura de monitoramento, utilizando o padrão de mercado **OpenTelemetry** para coleta de Traces, Métricas e Logs (os três pilares da observabilidade).

---

## 🏗️ Arquitetura do Sistema

O ambiente é composto por dois clusters Kubernetes locais isolados rodando via KinD, comunicando-se através da rede interna do Docker:

```text
[ CLUSTER 1: cluster-app ]                          [ CLUSTER 2: cluster-obs ]
┌────────────────────────┐                          ┌────────────────────────┐
│  ┌──────────────────┐  │                          │  ┌──────────────────┐  │
│  │    FastAPI API   │──┼───(OTLP HTTP Traces)────>│  │  OTel Collector  │  │
│  └────────┬─────────┘  │      Metrics & Logs      │  └────────┬─────────┘  │
│           │            │                          │           │            │
│  ┌────────▼─────────┐  │                          │     ┌─────┼─────┐      │
│  │    PostgreSQL    │  │                          │     │     │     │      │
│  └──────────────────┘  │                          │ ┌───▼─┐ ┌─▼───┐ ┌───▼──┐ │
│                        │                          │ │Tempo│ │Prom │ │Grafal│ │
│  ┌──────────────────┐  │                          │ └─────┘ └─────┘ └──────┘ │
│  │ OTel Host Agent  │──┼───(System Metrics)──────>│                        │
│  └──────────────────┘  │                          └────────────────────────┘
└────────────────────────┘
1. Cluster 1: cluster-app
FastAPI Application: API Python instrumentada nativamente com o OpenTelemetry SDK, gerando spans automáticos de rotas HTTP, expondo logs de aplicação via logging nativo e métricas de performance.

PostgreSQL: Banco de dados relacional para persistência de dados da API.

OTel Agent: Coletor OpenTelemetry configurado em modo Daemon/Agent para raspar métricas de hardware do host (hostmetrics como CPU, memória e disco do nó do cluster).

2. Cluster 2: cluster-obs
OpenTelemetry Collector: O cérebro da recepção de dados. Configurado com processadores de otimização de pipeline e distribuindo os dados para seus respectivos backends de armazenamento.

Grafana Tempo: Backend de armazenamento de alta performance e baixo custo para Traces distribuídos.

Prometheus: Servidor de séries temporais encarregado de raspar e armazenar as métricas da aplicação e da infraestrutura fornecidas pelo Collector.

Grafana: A interface unificada de visualização (UI), nascendo com os datasources do Tempo e Prometheus pré-provisionados via código.

⚙️ Otimizações do OTel Collector (Recurso Avançado)
O coletor central não atua apenas como um proxy passivo. Ele implementa uma pipeline de processamento avançada (processors) para garantir a estabilidade do cluster:

memory_limiter: Garante que o processo do Collector não estoure a memória RAM atribuída ao container do Kubernetes, derrubando o pod em picos de tráfego.

batch: Agrupa os registros em lotes antes de despachá-los para o Tempo e Prometheus, reduzindo drasticamente o overhead de rede e chamadas de I/O.

📂 Estrutura de Pastas
Plaintext
.
├── k8s/
│   ├── cluster-app/
│   │   ├── api-deployment.yaml     # Deployment e Service da API FastAPI
│   │   └── otel-agent.yaml         # Coletor de métricas de infraestrutura do Cluster 1
│   └── cluster-obs/
│       ├── otel-collector.yaml     # Configuração central, pipelines e portas do Collector
│       ├── tempo.yaml              # ConfigMap, Deployment e Service do Grafana Tempo
│       ├── prometheus.yaml         # ConfigMap de Scrape e Servidor Prometheus
│       └── grafana.yaml            # ConfigMap de DataSources e Servidor Grafana
├── main.py                         # Código-fonte da API Python instrumentada
├── requirements.txt                # Dependências do ecossistema OpenTelemetry Python
└── Dockerfile                      # Receita de build da aplicação
🚀 Como Executar o Projeto
Passo 1: Construir e Carregar a Imagem da API
Navegue até a pasta raiz do projeto onde estão o Dockerfile e o main.py, e execute o build da imagem:

Bash
docker build -t minha-api-app:latest .
Envie a imagem construída para dentro do nó do cluster KinD correspondente à aplicação:

Bash
kind load docker-image minha-api-app:latest --name cluster-app
Passo 2: Implantar o Cluster de Aplicação
Aplique os manifestos garantindo o contexto correto do Kubernetes (kind-cluster-app):

Bash
kubectl apply -f k8s/cluster-app/api-deployment.yaml --context kind-cluster-app
kubectl apply -f k8s/cluster-app/otel-agent.yaml --context kind-cluster-app
Passo 3: Implantar a Stack de Observabilidade
Mude o contexto para o cluster de monitoramento (kind-cluster-obs) e suba toda a stack técnica:

Bash
kubectl apply -f k8s/cluster-obs/tempo.yaml --context kind-cluster-obs
kubectl apply -f k8s/cluster-obs/otel-collector.yaml --context kind-cluster-obs
kubectl apply -f k8s/cluster-obs/prometheus.yaml --context kind-cluster-obs
kubectl apply -f k8s/cluster-obs/grafana.yaml --context kind-cluster-obs
Garanta que todos os componentes leram as configurações reiniciando os deployments chaves:

Bash
kubectl rollout restart deployment otel-collector --context kind-cluster-obs
kubectl rollout restart deployment tempo --context kind-cluster-obs
🧪 Validação e Testes
1. Gerando Dados de Tráfego
Dispare uma bateria de requisições sequenciais contra a rota pública da API local para alimentar o coletor de dados:

Bash
for i in {1..20}; do curl -s http://localhost:8080/health; echo ""; done
2. Acessando a Interface Visual (Grafana)
Como o ambiente roda localmente isolado via Docker/WSL, utilize o recurso de port-forwarding seguro do Kubernetes para mapear a porta da interface visual para a sua máquina de trabalho:

Bash
kubectl port-forward svc/grafana 3000:3000 --context kind-cluster-obs
Abra o seu navegador web e acesse: http://localhost:3000 (Credenciais padrão: Usuário: admin | Senha: admin)

3. Visualizando os Painéis
Para Traces Distribuidos (Tempo): Acesse o menu Explore, selecione a fonte de dados Tempo, clique na aba Search, filtre pelo serviço api-app-python e clique em Run Query para analisar os gráficos de Gantt de cada requisição HTTP.

Para Métricas (Prometheus): Altere o datasource do topo para Prometheus, pesquise por http_server_duration_milliseconds_count para ver volumetria de requisições da API, ou system_cpu_utilization para monitorar a saúde do processador do cluster K8s.