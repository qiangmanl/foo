# server_async.py
import os
import time
from typing import List, Optional
from utils import gen_panel_info
from fastapi import FastAPI
from pydantic import BaseModel
import httpx  # 异步 HTTP 客户端
import logging
from panelmanage import manager
from envs import GRAFANA_API_URL, METRICS_NAME, VICTORIA_URL, GRAFANA_API_KEY, DASHBOARD_UID, DATASOURCE_UID
app = FastAPI(title="Client Traffic Collector")

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


if not GRAFANA_API_KEY:
    logger.error(" GRAFANA_API_KEY not set")
    exit(1)
if not DASHBOARD_UID:
    logger.error(" DASHBOARD_UID not set")
    exit(1)
if not DATASOURCE_UID:
    logger.error(" DATASOURCE_UID not set")
    exit(1)

if not GRAFANA_API_URL:
    logger.error(" GRAFANA_API_URL not set")
    exit(1)

target_counts = {}

def target_traffic_continuous(target: str, count: int)-> bool:
    global target_counts
    if target in target_counts:
        if target_counts[target] == count - 1:
            traffic_continuous = True
        else:
            traffic_continuous = False
    else:
        traffic_continuous = True
    target_counts[target] = count
    return traffic_continuous
    

# ---------------------------
# 数据模型
# ---------------------------
class PortTraffic(BaseModel):
    port: str
    in_bytes: int
    out_bytes: int
    counts: int

class ClientTraffic(BaseModel):
    client_id: str
    ip: str
    ports: List[PortTraffic]

class ResponseData(BaseModel):
    lines_written: int=0

class Response(BaseModel):
    type: str           # success / error
    title: str
    status: int
    detail: Optional[str] = None
    instance: Optional[str] = None
    data: Optional[ResponseData] = None

# ---------------------------
# 接收客户端上报 API
# ---------------------------
@app.post("/report_traffic", response_model=Response)
async def report_traffic(client_data: ClientTraffic):
    timestamp = int(time.time() * 1000)  # 毫秒
    lines = []
    payload = ""
    for port_stat in client_data.ports:
        
        if target_traffic_continuous(f"{client_data.ip}:{port_stat.port}", port_stat.counts):
            lines.append(
                f'{METRICS_NAME}{{client_id="{client_data.client_id}",ip="{client_data.ip}",port="{port_stat.port}",direction="in"}} {port_stat.in_bytes} {timestamp}'
            )
            lines.append(
                f'{METRICS_NAME}{{client_id="{client_data.client_id}",ip="{client_data.ip}",port="{port_stat.port}",direction="out"}} {port_stat.out_bytes} {timestamp}'
            )
            payload = "\n".join(lines)
            # 
        else:
            # 非连续上报
            manager.add_or_update_panel(gen_panel_info(client_data.ip, port_stat.port))
    if payload:
        # 异步写入 VictoriaMetrics
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(VICTORIA_URL, content=payload)
                if resp.status_code != 200:
                    if resp.status_code == 204:
                        return Response(
                            type="success",
                            title="VictoriaMetrics write QL succeeded with no content header",
                            status=204,
                            data=ResponseData(lines_written=len(lines)),
                        )
                    else:
                        return Response(
                            type="error",
                            title="VictoriaMetrics write QL failed",
                            status=resp.status_code,
                            detail=resp.text,
                            data=None,
                        )
            except Exception as e:
                return Response(
                    type="error",
                    title="VictoriaMetrics write QL but threw an exception",
                    status=500,
                    detail=str(e),
                    data=None,
                )
        return Response(
            type="success",
            title="VictoriaMetrics write QL succeeded",
            status=200,
            data=ResponseData(lines_written=len(lines)),
        )
    else:
        
        return Response(
        type="success",
        title="writen VictoriaMetrics with zero lines",
        status=200,
        data=ResponseData(lines_written=0),
    )
