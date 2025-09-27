import os
VICTORIA_URL = os.getenv(
    "VICTORIA_URL", "http://victoriametrics:8428/api/v1/import/prometheus"
)  # 替换为你的 VictoriaMetrics 地址

GRAFANA_API_KEY = os.getenv("GRAFANA_API_KEY")

DASHBOARD_UID = os.getenv("DASHBOARD_UID")

DATASOURCE_UID = os.getenv("DATASOURCE_UID")

GRAFANA_API_URL = os.getenv("GRAFANA_API_URL")

METRICS_NAME = "client_traffic_bytes"

METRICS_EXPR_PREF =  f'{METRICS_NAME}{{ip="%s",port="%s"}})'