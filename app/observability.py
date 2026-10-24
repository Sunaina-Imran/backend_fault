"""OpenTelemetry setup for Fault IQ."""
import logging
import os
from threading import Lock

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import (
    OTLPLogExporter,
)
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
    OTLPMetricExporter,
)
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
    OTLPSpanExporter,
)
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from app.core.config import settings

logger = logging.getLogger(__name__)

_configured = False
_initialization_attempted = False
_lock = Lock()

_tracer_provider = None
_meter_provider = None
_logger_provider = None


def configure_observability(app, db_engine) -> None:
    """Configure OTLP exporters and instrument the application once."""
    global _configured, _initialization_attempted, _tracer_provider, _meter_provider, _logger_provider

    with _lock:
        if _configured or _initialization_attempted:
            return

        _initialization_attempted = True

        endpoint = os.getenv(
            "OTEL_EXPORTER_OTLP_ENDPOINT",
            "http://otel-collector:4317",
        )
        insecure = endpoint.startswith("http://")

        resource = Resource.create(
            {
                "service.name": "fault-iq-backend",
                "service.version": settings.VERSION,
                "deployment.environment": settings.ENVIRONMENT,
            }
        )

        try:
            # Distributed traces
            tracer_provider = TracerProvider(resource=resource)
            _tracer_provider = tracer_provider
            tracer_provider.add_span_processor(
                BatchSpanProcessor(
                    OTLPSpanExporter(
                        endpoint=endpoint,
                        insecure=insecure,
                    )
                )
            )

            # Application metrics
            metric_reader = PeriodicExportingMetricReader(
                OTLPMetricExporter(
                    endpoint=endpoint,
                    insecure=insecure,
                    timeout=10,
                ),
                export_interval_millis=15000,
            )
            meter_provider = MeterProvider(
                resource=resource,
                metric_readers=[metric_reader],
            )
            _meter_provider = meter_provider

            # Application logs
            logger_provider = LoggerProvider(resource=resource)
            _logger_provider = logger_provider
            logger_provider.add_log_record_processor(
                BatchLogRecordProcessor(
                    OTLPLogExporter(endpoint=endpoint, insecure=insecure)
                )
            )

            # Register global providers.
            trace.set_tracer_provider(tracer_provider)
            metrics.set_meter_provider(meter_provider)
            from opentelemetry._logs import set_logger_provider
            set_logger_provider(logger_provider)

            # Add the OTLP handler only to the Fault IQ application logger.
            otel_handler = LoggingHandler(
                level=logging.INFO,
                logger_provider=logger_provider,
            )
            logging.getLogger("app").addHandler(otel_handler)

            LoggingInstrumentor().instrument(
                set_logging_format=False,
                inject_trace_context=True,
            )
            SQLAlchemyInstrumentor().instrument(engine=db_engine)

            _configured = True
            logger.info("Fault IQ OpenTelemetry configured.")

        except Exception:
            logger.exception("Failed to initialize OpenTelemetry; cleaning up providers.")
            for name, provider in (
                ("traces", _tracer_provider),
                ("metrics", _meter_provider),
                ("logs", _logger_provider),
            ):
                if provider is None:
                    continue
                shutdown = getattr(provider, "shutdown", None)
                if callable(shutdown):
                    try:
                        shutdown()
                    except Exception:
                        logger.exception(
                            "Error shutting down OpenTelemetry %s provider during cleanup.",
                            name,
                        )
            raise
