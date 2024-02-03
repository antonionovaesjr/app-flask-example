import prometheus_client
import time
import psutil

UPDATE_PERIOD = 5
SYSTEM_USAGE = prometheus_client.Gauge('system_usage',
                                       'Hold current system resource usage',
                                       ['resource_type'])
SWAP_USAGE = prometheus_client.Gauge('swap_usage',
                                       'Hold current system resource usage',
                                       ['resource_type'])

if __name__ == '__main__':
    prometheus_client.start_http_server(9999)

while True:
    SYSTEM_USAGE.labels('CPU').set(psutil.cpu_percent())
    SYSTEM_USAGE.labels('Memory').set(psutil.virtual_memory()[2])
    print(psutil.cpu_percent())
    disk_usage = psutil.disk_usage("/")
    print(disk_usage)
    memory = psutil.virtual_memory()
    print(round(((memory.used / memory.total )* 100),2 ))
    SWAP_USAGE.labels('DISK').set(disk_usage.percent)
    time.sleep(UPDATE_PERIOD)