import psutil as ps
import os
import ctypes
import platform
from typing import List, Dict
import numpy as np
import socket

IGNORE_APPS = [
    'svchost.exe','system','searchhost.exe','runtimebroker.exe',
    'smartscreen.exe','spoolsv.exe','lsass.exe','services.exe',
    'wininit.exe','csrss.exe','dwm.exe','sihost.exe',
    'taskhostw.exe','ctfmon.exe','conhost.exe','dllhost.exe',
    'backgroundtaskhost.exe','systemsettings.exe','settingsynchost.exe',
    'microsoftedgeupdate.exe','windowsupdatebox.exe',
    'msmpeng.exe','nissrv.exe','securityhealthservice.exe'
]

BROWSERS = [
    "chrome.exe",
    "firefox.exe",
    "msedge.exe",
    "brave.exe",
    "opera.exe"
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
        self.dns_cache = {}
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
            return results

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

            isBrowser = app_name.lower() in BROWSERS
            domain = None

            if isBrowser:
                domain = self._resolve_domain(c.raddr.ip)

            entry = {
                "id": (
                    f"{app_name}_{domain}_{c.raddr.ip}_{c.raddr.port}"
                    if isBrowser and domain
                    else f"{app_name}_{c.pid}_{c.raddr.ip}_{c.raddr.port}"
                ),
                "app": str(app_name),
                "pid": int(c.pid),
                "ip": str(c.raddr.ip) if c.raddr and c.raddr.ip else "0.0.0.0",
                "port": int(c.raddr.port) if c.raddr and c.raddr.port else 0,
                "type": "browser" if isBrowser else "process",
                "domain": domain,
            }

            if self.ai:
                try:
                    entry["is_threat"] = bool(np.array(self.ai.predict_threat(entry["ip"], entry["port"], "ESTABLISHED", entry.get("domain"))).item())
                except Exception:
                    entry["is_threat"] = False
            else:
                entry["is_threat"] = False

            if entry.get("type") == "browser":
                entry["risk_weight"] = 0.5
            else:
                entry["risk_weight"] = 1.0

            results.append(entry)

        return results
    
    def _resolve_domain(self, ip: str) -> str:
        if ip in self.dns_cache:
            return self.dns_cache[ip]

        try:
            domain = socket.gethostbyaddr(ip)[0]
        except Exception:
            domain = None

        # Clean up the domain to show more user-friendly names
        if domain:
            domain = domain.lower()
            
            # Skip generic hosting/infrastructure names
            generic_patterns = [
                'ec2-', 'compute-', 'server-', 'host-', 'node-',
                'ip-', 'static-', 'dynamic-', 'dhcp-', 'nat-',
                'gateway-', 'router-', 'switch-', 'proxy-',
                'cdn-', 'edge-', 'cache-', 'lb-', 'loadbalancer-',
                'aws-', 'gcp-', 'azure-', 'cloud-', 'vm-',
                'container-', 'pod-', 'k8s-', 'docker-'
            ]
            
            if any(pattern in domain for pattern in generic_patterns):
                domain = None
            
            # Try to extract actual domain from subdomains
            if domain:
                parts = domain.split('.')
                # For patterns like "something.google.com" -> try "google.com"
                if len(parts) >= 3:
                    # Check if the last two parts form a known TLD + domain
                    potential_domain = '.'.join(parts[-2:])
                    if potential_domain in ['google.com', 'facebook.com', 'amazon.com', 'microsoft.com', 
                                          'apple.com', 'youtube.com', 'twitter.com', 'instagram.com',
                                          'linkedin.com', 'github.com', 'stackoverflow.com', 'reddit.com']:
                        domain = potential_domain
                    # For .com, .org, .net, .edu, etc.
                    elif len(parts) >= 2 and parts[-1] in ['com', 'org', 'net', 'edu', 'gov', 'io', 'co', 'ai']:
                        domain = '.'.join(parts[-2:])

        self.dns_cache[ip] = domain
        return domain

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
