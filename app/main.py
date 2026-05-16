from fastapi import FastAPI
from pydantic import BaseModel
import os
import logging

# --- IMPORTAÇÕES DO OPENTELEMETRY ---
# Traces (Já existia no seu código)
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

# Métricas (NOVO!)
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter

# Logs (NOVO!)
from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter

# Instrumentação
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
# -----------------------------------

# 1. Configuração do Recurso Base (O nome que aparece no Grafana)
resource = Resource.create({"service.name": "api-app-python"})

# 2. Configuração do Endpoint HTTP (Apontando para o seu Collector local via Ingress ou Service)
otlp_endpoint_traces = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4318/v1/traces")
# Endpoints específicos para métricas e logs baseados no padrão OTLP HTTP
otlp_endpoint_metrics = otlp_endpoint_traces.replace("/v1/traces", "/v1/metrics")
otlp_endpoint_logs = otlp_endpoint_traces.replace("/v1/traces", "/v1/logs")


# --- INÍCIO DA CONFIGURAÇÃO DOS PROVIDERS ---

# 3. Provider de TRACES (O que desenha o gráfico de Gantt)
trace_provider = TracerProvider(resource=resource)
trace_exporter = OTLPSpanExporter(endpoint=otlp_endpoint_traces)
trace_provider.add_span_processor(BatchSpanProcessor(trace_exporter))
trace.set_tracer_provider(trace_provider)

# 4. Provider de MÉTRICAS (Uso de CPU, qtd de requisições, etc)
metric_exporter = OTLPMetricExporter(endpoint=otlp_endpoint_metrics)
metric_reader = PeriodicExportingMetricReader(metric_exporter, export_interval_millis=5000) # Envia a cada 5s
metric_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
metrics.set_meter_provider(metric_provider)

# 5. Provider de LOGS (Para capturar os prints e erros da aplicação)
logger_provider = LoggerProvider(resource=resource)
log_exporter = OTLPLogExporter(endpoint=otlp_endpoint_logs)
logger_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))
set_logger_provider(logger_provider)

# Cria um handler padrão do Python para enviar logs para o OTel
handler = LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider)
logging.getLogger().addHandler(handler)
# -------------------------------------------

# --- INICIALIZAÇÃO DA API ---
app = FastAPI(title="App Desafio Observabilidade")

# Instrumenta o FastAPI para traces e métricas HTTP automáticas
FastAPIInstrumentor.instrument_app(app)
# Instrumenta a biblioteca de logging padrão do Python
LoggingInstrumentor().instrument(set_logging_format=True)

class User(BaseModel):
    name: str

@app.post("/users")
def create_user(user: User):
    # Isso agora vai ser enviado para o OTel!
    logging.info(f"Recebido o usuário: {user.name}") 
    return {"status": "success", "message": f"Usuário {user.name} processado!", "data": user.name}

@app.get("/health")
def health_check():
    # Adicionando um log aqui também para podermos testar
    logging.info("Health check endpoint chamado!")
    return {"status": "healthy"}