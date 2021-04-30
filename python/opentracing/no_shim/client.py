# Set the following environment variables first before running this client:
#
# LS_ACCESS_TOKEN
# LS_SERVICE_NAME
#
# Spans will be exported to https://ingest.staging.lightstep.com:443
# NoShim

from requests import get
from os import environ

from opentelemetry.trace import (
    set_tracer_provider, get_tracer_provider
)
from opentelemetry.propagate import set_global_textmap
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.propagators.ot_trace import OTTracePropagator
from opentelemetry.launcher.tracer import LightstepOTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider, Resource
from grpc import ssl_channel_credentials
from opentelemetry.shim.opentracing_shim import create_tracer
from opentracing.propagation import Format
from random import randint
from opentelemetry.propagators.ot_trace import OT_BAGGAGE_PREFIX

set_tracer_provider(TracerProvider())

set_global_textmap(OTTracePropagator())

get_tracer_provider().add_span_processor(
    BatchSpanProcessor(
        LightstepOTLPSpanExporter(
            endpoint="https://ingest.staging.lightstep.com:443",
            credentials=ssl_channel_credentials(),
            headers=(("lightstep-access-token", environ["LS_ACCESS_TOKEN"]),)
        )
    )
)
get_tracer_provider()._resource = Resource(
    {"service.name": environ["LS_SERVICE_NAME"], "service.version": "1.2.3"}
)

tracer = create_tracer(get_tracer_provider())

random_int = randint(0, 100)

with tracer.start_active_span(
    "client {}".format(random_int), finish_on_close=True
) as scope:
    carrier = {}

    carrier["{}random_int".format(OT_BAGGAGE_PREFIX)] = str(random_int)

    tracer.inject(scope.span.context, Format.HTTP_HEADERS, carrier)

    print(get("http://localhost:5000/ping", headers=carrier).content)
