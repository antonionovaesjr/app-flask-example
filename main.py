from flask import Flask, Response, request
import psutil
import socket
import threading
import jsonify
import time
import httpx
import prometheus_client
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)
# db = SQLAlchemy(app)
metrics = PrometheusMetrics(app, group_by='endpoint')
metrics.info('app_info', 'Application info', version='1.0.3')

app.config["DEBUG"] = True
app.config["ENV"] = "development"

UPDATE_PERIOD = 30
SYSTEM_USAGE = prometheus_client.Gauge('system_usage',
                                       'Hold current system resource usage',
                                       ['resource_type','device','hostname','ip'])
NETWORK_USAGE = prometheus_client.Gauge('network_usage',
                                       'Hold system resource usage',
                                       ['type','hostname','ip'])

REQUEST_LATENCY = prometheus_client.Gauge('http_request_time_ms',
                                       'Hold current system usage',
                                       ['method','path','hostname','ip'])

REQUEST_COUNT = prometheus_client.Counter('http_request_count',
                                       'Hold current system resource',
                                       ['method','path','hostname','ip'])

SWAP_USAGE = prometheus_client.Gauge('swap_usage',
                                       'Hold current system resource usage',
                                       ['resource_type'])

common_counter = metrics.counter(
    'by_endpoint_counter', 'Request count by endpoints',
    labels={'endpoint': lambda: request.endpoint}
)

metrics.register_default(
    metrics.counter(
        'by_path_counter', 'Request count by request paths',
        labels={'path': lambda: request.path}
    )
)
@app.route("/")
@common_counter
def home():
    return {"mensagem":"Ola mundo"}

@app.route("/cep/<id>",methods=["GET"])
@metrics.do_not_track()
@common_counter
def cep(id):
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)
    start_time = time.time()
    cep = id
    cep_response = httpx.get("https://viacep.com.br/ws/{}/json/".format(cep))
    print(cep_response.json())
    REQUEST_LATENCY.labels(method="GET",path="/cep/id",hostname=hostname,ip=ip).set(time.time() - start_time)
    print(time.time() - start_time)
    REQUEST_COUNT.labels(method="GET",path="/cep/id",hostname=hostname,ip=ip).inc()
    return cep_response.json()

@app.route("/ddd/<id>",methods=["GET"])
def ddd(id):
    ddd = id
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)
    start_time = time.time()
    ddd_response = httpx.get("https://brasilapi.com.br/api/ddd/v1/{}".format(ddd))
    REQUEST_LATENCY.labels(method="GET",path="/ddd/id",hostname=hostname,ip=ip).set(time.time() - start_time)
    print(time.time() - start_time)
    print(ddd_response.json())
    REQUEST_COUNT.labels(method="GET", path="/ddd/id", hostname=hostname, ip=ip).inc()
    return ddd_response.json()

def gen_metrics():
    while True:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        network = psutil.net_io_counters()
        NETWORK_USAGE.labels('bytes_sent',hostname,ip).set(network.bytes_sent)
        NETWORK_USAGE.labels('bytes_recv', hostname, ip).set(network.bytes_recv)
        NETWORK_USAGE.labels('err_in', hostname, ip).set(network.errin)
        NETWORK_USAGE.labels('err_out', hostname, ip).set(network.errout)
        NETWORK_USAGE.labels('drop_in', hostname, ip).set(network.dropin)
        NETWORK_USAGE.labels('drop_out', hostname, ip).set(network.dropout)
        NETWORK_USAGE.labels('packets_sent', hostname, ip).set(network.packets_sent)
        NETWORK_USAGE.labels('packets_recv', hostname, ip).set(network.packets_recv)
        SYSTEM_USAGE.labels('cpu','processor',hostname,ip).set(psutil.cpu_percent())
        SYSTEM_USAGE.labels('memory','memory',hostname,ip).set(psutil.virtual_memory()[2])
        root_disk_usage = psutil.disk_usage("/")
        SYSTEM_USAGE.labels('disk', '/',hostname,ip).set(root_disk_usage.percent)
        time.sleep(UPDATE_PERIOD)

if __name__ == '__main__':
    prometheus_client.start_http_server(9999)
    gen_metrics_thread = threading.Thread(target=gen_metrics, args=(),daemon=True)
    gen_metrics_thread.start()
    app.run(host='0.0.0.0', port=8080)