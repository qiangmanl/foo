from envs import DATASOURCE_UID, METRICS_EXPR_PREF

def format_target(ip: str, port: str):
    key = f"{ip}:{port}"
    return key

def gen_panel_info(ip: str, port: str):
    expr = METRICS_EXPR_PREF%(ip, port)
    return {
        "type": "timeseries",
        "title": f'{format_target(ip, port)}',
        "gridPos": {"x": 0, "y": 0, "w": 24, "h": 8},
        "targets": [
            {
                "refId": "A",
                "expr": expr,
                "legendFormat": "in/out",
                "datasource": {"type": "prometheus", "uid": f"{DATASOURCE_UID}"}
            }
        ],
        "options": {
            "legend": {"displayMode": "list", "placement": "bottom"},
            "tooltip": {"mode": "all", "sort": "none"},
        },
        "fieldConfig": {
            "defaults": {
                "unit": "bytes",
                "decimals": 2,
                "min": 0,
            },
            "overrides": []
        }
    }

