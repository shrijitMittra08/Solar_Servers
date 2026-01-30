import psutil as ps
import os
import ctypes
from typing import List, Dict

IGNORE_APPS = [
    'svchost.exe','system','searchhost.exe','runtimebroker.exe',
    'smartscreen.exe','spoolsv.exe','lsass.exe','services.exe',
    'wininit.exe','csrss.exe','dwm.exe','sihost.exe',
    'taskhostw.exe','ctfmon.exe','conhost.exe','dllhost.exe',
    'backgroundtaskhost.exe','systemsettings.exe','settingsynchost.exe',
    'microsoftedgeupdate.exe','windowsupdatebox.exe',
    'msmpeng.exe','nissrv.exe','securityhealthservice.exe'
]

try:
    from ai_engine import predict
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

class SolarServerCore:
    def __init__(self):
        self.pid = os.getpid()
        self.name_cache = {}
        self.meta = self._hardware_scan()
        print(f"SolarServers Core Online | PID {self.pid}")
        print(f"Meta: {self.meta}")

    def _hardware_scan(self) -> Dict:
        try:
            ram = ps.virtual_memory().total / (1024 ** 3)
        except:
            ram = 2.0

        try:
            is_admin = os.getuid() == 0
        except:
            try:
                is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
            except:
                is_admin = False

        tier = "HIGH_END" if ram >= 8 else "LOW_END"

        return {
            "tier": tier,
            "is_admin": is_admin,
            "ram_gb": round(ram, 2)
        }
    def _scan_connections(self) -> List[Dict]:
        results = []

        try:
            connections = ps.net_connections(kind="inet")
        except Exception:
            return results  # Always safe fallback

        for c in connections:
            if not c.pid or not c.raddr:
                continue
            if c.pid == self.pid:
                continue
            if c.status != "ESTABLISHED":
                continue

            if c.pid not in self.name_cache:
                try:
                    self.name_cache[c.pid] = ps.Process(c.pid).name()
                except:
                    self.name_cache[c.pid] = "System/Hidden"

            app_name = self.name_cache[c.pid]

            if app_name.lower() in [i.lower() for i in IGNORE_APPS]:
                continue

            entry = {
                "id": f"{app_name}_{c.pid}",
                "app": app_name,
                "pid": c.pid,
                "ip": c.raddr.ip,
                "port": c.raddr.port,
            }

            # AI classification
            if AI_AVAILABLE:
                try:
                    entry["is_threat"] = bool(predict(entry))
                except:
                    entry["is_threat"] = False
            else:
                entry["is_threat"] = False

            results.append(entry)

        return results
    def get_packet(self) -> Dict:
        return {
            "meta": {
                "tier": self.meta["tier"],
                "is_admin": self.meta["is_admin"]
            },
            "connections": self._scan_connections()
        }

if __name__ == "__main__":
    core = SolarServerCore()
    pkt = core.get_packet()
    print(f"\nFound {len(pkt['connections'])} connections")
    for c in pkt["connections"][:10]:
        print(f"{c['app']} -> {c['ip']}:{c['port']}")
