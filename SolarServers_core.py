import psutil as ps
import os
import ctypes
import platform
from typing import List, Dict
import numpy as np

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
    from ai_engine import AIEngine
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

class SolarServersCore:
    def __init__(self):
        self.pid = os.getpid()
        self.name_cache = {}
        self.meta = self._hardware_scan()
        if AI_AVAILABLE:
            try:
                self.ai = AIEngine()
                print("AI initialized")
            except Exception:
                self.ai = None
                print("AI failed to initialize")
        else:
            self.ai = None

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
                if platform.system() == "Windows":
                    is_admin = bool(ctypes.windll.shell32.IsUserAnAdmin())
                else:
                    is_admin = False
            except (AttributeError, OSError):
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
                "id": str(f"{app_name}_{c.pid}"),
                "app": str(app_name),
                "pid": int(c.pid),
                "ip": str(c.raddr.ip) if c.raddr and c.raddr.ip else "0.0.0.0",
                "port": int(c.raddr.port) if c.raddr and c.raddr.port else 0,
            }


            # AI classification
            if self.ai:
                try:
                    entry["is_threat"] = bool(np.array(self.ai.predict_threat(entry["ip"], entry["port"], "ESTABLISHED")).item())
                except Exception:
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
    core = SolarServersCore()
    pkt = core.get_packet()
    print(f"\nFound {len(pkt['connections'])} connections")
    for c in pkt["connections"][:10]:
        print(f"{c['app']} -> {c['ip']}:{c['port']}")
