import requests
from envs import DASHBOARD_UID, GRAFANA_API_KEY, GRAFANA_API_URL

class GrafanaPanelManager:
    def __init__(self, grafana_url, api_key, dashboard_uid, max_panels=10):
        self.grafana_url = grafana_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.dashboard_uid = dashboard_uid
        self.max_panels = max_panels
        self.panels_dict = {}  # {title: panel_json}
        self._init_panels_dict()

    def _init_panels_dict(self):
        dashboard_json = self._fetch_dashboard()
        self.panels_dict.clear()
        for panel in dashboard_json.get("panels", []):
            self.panels_dict[panel["title"]] = panel
        print(f"Initialized panels_dict: {list(self.panels_dict.keys())}")

    def _fetch_dashboard(self):
        resp = requests.get(f"{self.grafana_url}/api/dashboards/uid/{self.dashboard_uid}",
                            headers=self.headers)
        resp.raise_for_status()
        return resp.json()["dashboard"]

    def _push_dashboard(self, dashboard_json):
        resp = requests.post(f"{self.grafana_url}/api/dashboards/db",
                             headers=self.headers,
                             json={"dashboard": dashboard_json, "overwrite": True})
        resp.raise_for_status()
        return resp.json()

    def add_or_update_panel(self, panel_template):
        title = panel_template.get("title")
        if not title:
            raise ValueError("panel_template must contain 'title'")

        # 1. 获取最新 Dashboard
        dashboard_json = self._fetch_dashboard()
        grafana_panels = dashboard_json.get("panels", [])

        # 2. 检查标题一致
        grafana_titles = {p["title"] for p in grafana_panels}
        dict_titles = set(self.panels_dict.keys())
        if grafana_titles != dict_titles:
            print("Title mismatch between local dictionary and Grafana. Aborting update.")
            return False

        # 3. 移除同名 Panel（无论是否存在）
        remaining_panels = [p for p in grafana_panels if p["title"] != title]

        # 4. 创建独立的新 Panel 对象
        new_panel = dict(panel_template)
        # 插入到最前面
        updated_panels = [new_panel] + remaining_panels

        # 5. 超过最大数量删除最后一个
        if len(updated_panels) > self.max_panels:
            removed_panel = updated_panels.pop(-1)
            print(f"Panel '{removed_panel['title']}' removed due to max_panels limit.")

        # 6. 更新 gridPos
        # for idx, panel in enumerate(updated_panels):
        #     panel["gridPos"] = {"x": 0, "y": idx * 8, "w": 24, "h": 8}

        # 7. 更新 Dashboard JSON
        dashboard_json["panels"] = updated_panels

        # 8. 推送到 Grafana
        try:
            resp = self._push_dashboard(dashboard_json)
            if resp.get("status") in ["success", "ok"]:
                # 成功才更新字典
                self.panels_dict.clear()
                for panel in updated_panels:
                    self.panels_dict[panel["title"]] = panel
                print(f"Dashboard updated successfully: {list(self.panels_dict.keys())}")
                return True
            else:
                print(f"Grafana update failed: {resp}")
                return False
        except requests.HTTPError as e:
            print(f"Failed to update Grafana: {e}")
            return False


    def delete_panel(self, title):
        dashboard_json = self._fetch_dashboard()
        grafana_titles = {p["title"] for p in dashboard_json.get("panels", [])}
        dict_titles = set(self.panels_dict.keys())
        if grafana_titles != dict_titles:
            print("Title mismatch between local dictionary and Grafana. Aborting deletion.")
            return False

        new_panels = [p for p in dashboard_json.get("panels", []) if p["title"] != title]

        if len(new_panels) == len(dashboard_json.get("panels", [])):
            print(f"Panel '{title}' not found in Grafana. Nothing to delete.")
            return False

        dashboard_json["panels"] = new_panels

        try:
            resp = self._push_dashboard(dashboard_json)
            if resp.get("status") in ["success", "ok"]:
                self.panels_dict.pop(title, None)
                print(f"Panel '{title}' deleted successfully.")
                return True
            else:
                print(f"Failed to delete panel on Grafana: {resp}")
                return False
        except requests.HTTPError as e:
            print(f"Failed to delete panel in Grafana: {e}")
            return False

manager = GrafanaPanelManager(
    grafana_url=GRAFANA_API_URL,
    api_key=GRAFANA_API_KEY,
    dashboard_uid=DASHBOARD_UID
)