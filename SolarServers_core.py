import psutil as ps
import os as o
import ctypes as c
ig = [
    'svchost.exe','system','searchhost.exe','runtimebroker.exe',
    'smartscreen.exe','spoolsv.exe','lsass.exe','services.exe',
    'wininit.exe','csrss.exe','dwm.exe','sihost.exe',
    'taskhostw.exe','ctfmon.exe','conhost.exe','dllhost.exe',
    'backgroundtaskhost.exe','systemsettings.exe','settingsynchost.exe',
    'microsoftedgeupdate.exe','windowsupdatebox.exe',
    'msmpeng.exe','nissrv.exe','securityhealthservice.exe',
    'msseces.exe','avgnt.exe','avp.exe','ekrn.exe',
    'mbamservice.exe','norton*.exe','mcafee*.exe',
    'onedrive.exe','dropbox.exe','googledrivesync.exe',
    'wuauclt.exe','trustedinstaller.exe','msiexec.exe',
    'system/hidden'
]
wl = [
    'chrome.exe','firefox.exe','brave.exe','msedge.exe',
    'discord.exe','slack.exe','telegram.exe',
    'spotify.exe','vlc.exe',
    'steam.exe','epicgameslauncher.exe'
]
class SS:
    def __init__(self):
        self.ig = ig
        self.wl = wl
        self.nc = {}
        self.pid = o.getpid()
        self.hw = self.hw_scan()
        self.a
        print(f"SYSTEMSERVERS READY | PID {self.pid}")
        print(f"HARDWARE {self.hw}")
    def hw_scan(self):
        try:
            ram = ps.virtual_memory().total / (1024**3)
        except:
            ram = 2.0
        try:
            adm = o.getuid() == 0
        except:
            try:
                adm = c.windll.shell32.IsUserAnAdmin() != 0
            except:
                adm = False
        self.a = {"tier": "POTATO" if ram <= 2 else ("STANDARD" if ram<= 8 else ("HIGH" if ram <= 16 else "PEAK")),
            "ram": round(ram,2),
            "admin": adm}
        return self.a
    def scan(self):
        out = []
        try:
            con = ps.net_connections(kind="inet")
        except:
            return [{"err":"admin needed"}]
        for x in con:
            if x.pid in (None,self.pid):
                continue
            if x.status != "ESTABLISHED":
                continue
            if not x.raddr:
                continue
            if x.pid not in self.nc:
                try:
                    self.nc[x.pid] = ps.Process(x.pid).name()
                except:
                    self.nc[x.pid] = "System/Hidden"
            n = self.nc[x.pid]
            if n.lower() in [i.lower() for i in self.ig]:
                continue
            out.append({
                "app": n,
                "lp": x.laddr.port,
                "rip": x.raddr.ip,
                "rp": x.raddr.port,
                "st": x.status
            })
        return out
e = SS()
print("\nScanning...\n")
d = e.scan()
print(f"Found {len(d)} connections\n")
for i,v in enumerate(d[:10]):
    print(f"[{i+1}] {v['app']} -> {v['rip']}:{v['rp']}")
if len(d) > 10:
    print(f"... +{len(d)-10} more")
