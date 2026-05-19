# Multicluster Observability Sandbox 🚀
### FastAPI | OpenTelemetry | KinD | Tempo | Prometheus | Loki | Grafana

Este repositório contém a implementação completa de uma arquitetura de observabilidade corporativa distribuída em ambiente local utilizando **Kubernetes (KinD)**. O projeto demonstra a separação completa de contextos entre o ambiente de aplicação, a infraestrutura de monitoramento e a camada de visualização, utilizando o padrão de mercado **OpenTelemetry** para coleta dos três pilares da observabilidade: Traces, Métricas e Logs.

---

## 🏗️ Arquitetura do Sistema (Topologia de 3 Clusters)

O ambiente foi desenhado simulando diretrizes de segurança de redes em produção, isolando os serviços em três clusters locais distintos que se comunicam através de port-forwarding e NodePorts na rede interna do Docker:

```text
[ CLUSTER 1: cluster-app ]      [ CLUSTER 2: cluster-obs ]      [ CLUSTER 3: cluster-grafana ]
┌────────────────────────┐      ┌────────────────────────┐      ┌────────────────────────────┐
│  ┌──────────────────┐  │      │  ┌──────────────────┐  │      │                            │
│  │    FastAPI API   │──┼─────>│  │  OTel Collector  │  │      │                            │
│  └────────┬─────────┘  │      │  └────────┬─────────┘  │      │                            │
│           │            │      │           │            │      │      ┌──────────────┐      │
│  ┌────────▼─────────┐  │      │     ┌─────┼─────┐      │      │      │              │      │
│  │    PostgreSQL    │  │      │     │     │     │      │      │      │ Grafana (UI) │      │
│  └──────────────────┘  │      │ ┌───▼─┐ ┌─▼───┐ ┌───▼──┐      │      │              │      │
│                        │      │ │Tempo│ │Prom │ │Loki │◄───┼──┤      └──────▲───────┘      │
│  ┌──────────────────┐  │      │ └─────┘ └─────┘ └──────┘      │             │              │
│  │ OTel Host Agent  │──┼─────>│                               │     ┌───────▼────────┐     │
│  └──────────────────┘  │      │                               │     │ Ingress (Nginx)│     │
└────────────────────────┘      └────────────────────────┘      └─────┴───────▲────────┴─────┘
                                                                              │
                                                                       (grafana.local)
1. Cluster 1: cluster-app
FastAPI Application: API Python instrumentada com o OpenTelemetry SDK.

PostgreSQL: Banco de dados relacional.

OTel Agent: Coletor em modo Daemon/Agent para raspar métricas do hardware do host (CPU, memória e disco).

Ingress NGINX: Gerencia a entrada de tráfego externo para a API.

2. Cluster 2: cluster-obs (A Central de Dados Trancada)
OpenTelemetry Collector: Atua como pipeline central. Implementa processors de otimização (memory_limiter, batch, resource para injeção de labels OTLP) antes de despachar os dados para os bancos de destino.

Grafana Tempo: Backend para armazenamento de Traces distribuídos.

Prometheus: Servidor Time-Series responsável pelas métricas.

Loki: Banco de dados especializado em armazenamento e busca textual de Logs.

3. Cluster 3: cluster-grafana (Camada Visual)
Grafana: Interface visual configurada via código (ConfigMaps) para se conectar ao cluster-obs usando NodePorts (30090, 30200, 30100).

Ingress NGINX: Responsável por expor a interface visual de forma elegante através da URL customizada grafana.local.

📂 Estrutura de Pastas
Plaintext
.
├── app/
│   ├── Dockerfile                  # Receita de build da aplicação
│   ├── main.py                     # Código-fonte da API Python instrumentada
│   └── requirements.txt            # Dependências Python
├── infra/
│   ├── kind-cluster-app.yaml       # Definição física do Cluster 1 (App)
│   ├── kind-cluster-grafana.yaml   # Definição física do Cluster 3 (UI - Porta 80)
│   └── kind-cluster-obs.yaml       # Definição física do Cluster 2 (Obs)
└── k8s/
    ├── cluster-app/                # Manifestos da Aplicação
    │   ├── api-deployment.yaml
    │   ├── ingress-api.yaml
    │   ├── otel-agent.yaml
    │   └── postgres.yaml
    ├── cluster-grafana/            # Manifestos da Camada de Visualização
    │   ├── grafana.yaml
    │   └── ingress-grafana.yaml
    └── cluster-obs/                # Manifestos dos Bancos de Telemetria
        ├── ingress-obs.yaml
        ├── loki.yaml
        ├── otel-collector.yaml
        ├── prometheus.yaml
        └── tempo.yaml
🚀 Como Executar o Projeto
Pré-requisitos
Certifique-se de que o arquivo hosts do seu sistema operacional (ex: C:\Windows\System32\drivers\etc\hosts) contém o apontamento local:
127.0.0.1 grafana.local

Passo 1: Construir a Infraestrutura Física
Crie os três clusters isolados utilizando o KinD:

Bash
kind create cluster --config infra/kind-cluster-app.yaml --name cluster-app
kind create cluster --config infra/kind-cluster-obs.yaml --name cluster-obs
kind create cluster --config infra/kind-cluster-grafana.yaml --name cluster-grafana
Passo 2: Instalar Controladores Ingress
Para suportar rotas via URL, instale o NGINX Ingress Controller nos clusters aplicáveis:

Bash
# No Cluster App
kubectl apply -f [https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml](https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml) --context kind-cluster-app

# No Cluster Grafana
kubectl apply -f [https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml](https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml) --context kind-cluster-grafana
Aguarde os pods do ingress-nginx ficarem com status "Running" antes de prosseguir.

Passo 3: Build e Deploy da Aplicação
Crie e carregue a imagem da API para o cluster de aplicação:

Bash
cd app
docker build -t minha-api-app:latest .
kind load docker-image minha-api-app:latest --name cluster-app
cd ..
Aplique os manifestos do cluster-app:

Bash
kubectl apply -f k8s/cluster-app/ --context kind-cluster-app
Passo 4: Subir o Backend de Observabilidade
Implante a stack técnica de recebimento de dados no cluster-obs:

Bash
kubectl apply -f k8s/cluster-obs/ --context kind-cluster-obs
kubectl rollout restart deployment otel-collector --context kind-cluster-obs
Passo 5: Subir a Camada de Visualização
Implante o Grafana e suas regras de roteamento no cluster-grafana:

Bash
kubectl apply -f k8s/cluster-grafana/ --context kind-cluster-grafana
🧪 Validação e Testes
1. Gerando Dados
Envie tráfego contínuo para a aplicação, alimentando as pipelines de monitoramento:

Bash
for i in {1..20}; do curl -s http://localhost:8080/health; echo ""; done
2. Acesso ao Painel
Abra o seu navegador e acesse a URL segura criada pelo Ingress: http://grafana.local (Credenciais padrão: admin / admin).

3. Explorando os Três Pilares (Menu Explore)
🔴 Traces (Tempo): Selecione Tempo, mude a aba para Search, filtre por api-app-python e clique em Run Query para analisar o diagrama de execução de cada requisição.

🟢 Métricas (Prometheus): Selecione Prometheus, e faça queries como http_server_duration_milliseconds_count (para volumetria de tráfego) ou system_cpu_utilization (para uso de hardware).

🔵 Logs (Loki): Selecione Loki, cole a LogQL {job="api-app-python"} na barra de busca e visualize todos os logs estruturados emitidos diretamente pela API, correlacionados no tempo.