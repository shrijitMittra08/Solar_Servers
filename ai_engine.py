import joblib
import os
import numpy as np
import pandas as pd
import re
import warnings
warnings.filterwarnings("ignore", message=".*sklearn.utils.parallel.delayed.*")
class AIEngine:
    def __init__(self):
        self.model = None
        self.sc = None
        self.encoders = {}
        self.selector = None
        # Known malicious patterns - expanded
        self.malicious_patterns = [
            # Suspicious TLDs
            r'\.onion$', r'\.ru$', r'\.cn$', r'\.tk$', r'\.ml$', r'\.ga$', 
            r'\.cf$', r'\.gq$', r'\.xyz$', r'\.top$', r'\.club$', r'\.online$',
            r'\.site$', r'\.space$', r'\.website$', r'\.tech$', r'\.store$',
            # Malware-related keywords
            r'bopsecrets', r'rexroth', r'secrets', r'hack', r'exploit', 
            r'malware', r'virus', r'trojan', r'ransomware', r'phishing', 
            r'scam', r'fake', r'spyware', r'adware', r'keygen', r'crack', 
            r'warez', r'pirate', r'torrent', r'bittorrent', r'utorrent',
            r'piracy', r'illegal', r'free-download', r'full-version',
            r'activation', r'serial', r'license', r'patch', r'cheat',
            r'hacktool', r'rootkit', r'backdoor', r'botnet', r'worm',
            r'\d{4,}', 
            r'-{2,}',
            r'xxx', 
            r'porn', r'adult', r'sex',
            r'bit\.ly', r'tinyurl', r'goo\.gl',
            r'pastebin', r'githubusercontent',
        ]
        if os.path.exists("SolarServer_model.pkl"):
            self.model = joblib.load("SolarServer_model.pkl")
            print("AI Engine: Online")
        else:
            print("AI Engine: Offline")
        if os.path.exists("SolarServer_scaler.pkl"):
            self.sc = joblib.load("SolarServer_scaler.pkl")
        if os.path.exists("SolarServer_encoders.pkl"):
            self.encoders = joblib.load("SolarServer_encoders.pkl")
        if os.path.exists("SolarServer_selector.pkl"):
            self.selector = joblib.load("SolarServer_selector.pkl")
    
    def check_url_threat(self, url):
        """Check if URL contains suspicious patterns"""
        if not url:
            return False
        
        url_lower = url.lower()
        for pattern in self.malicious_patterns:
            if re.search(pattern, url_lower):
                return True
        return False
    
    def predict_threat(self, ip, port, status="ESTABLISHED", domain=None):
        if not self.model:
            return False
        
        # First check URL/domain patterns
        if domain and self.check_url_threat(domain):
            return True  # Known malicious pattern
        
        # Create feature dict with defaults
        features = {
            'duration': 0,
            'protocol_type': 'tcp',  # Assume TCP
            'service': 'http' if port in [80, 443] else 'private',  # Guess service
            'flag': 'SF' if status == 'ESTABLISHED' else 'S0',  # Assume SF for established
            'src_bytes': 1000,  # Default
            'dst_bytes': 5000,  # Default
            'land': 0,
            'wrong_fragment': 0,
            'urgent': 0,
            'hot': 0,
            'num_failed_logins': 0,
            'logged_in': 1 if port in [80, 443] else 0,  # Assume logged in for web
            'num_compromised': 0,
            'root_shell': 0,
            'su_attempted': 0,
            'num_root': 0,
            'num_file_creations': 0,
            'num_shells': 0,
            'num_access_files': 0,
            'num_outbound_cmds': 0,
            'is_host_login': 0,
            'is_guest_login': 0,
            'count': 10,
            'srv_count': 10,
            'serror_rate': 0.0,
            'srv_serror_rate': 0.0,
            'rerror_rate': 0.0,
            'srv_rerror_rate': 0.0,
            'same_srv_rate': 1.0,
            'diff_srv_rate': 0.0,
            'srv_diff_host_rate': 0.0,
            'dst_host_count': 1,
            'dst_host_srv_count': 1,
            'dst_host_same_srv_rate': 1.0,
            'dst_host_diff_srv_rate': 0.0,
            'dst_host_same_src_port_rate': 1.0,
            'dst_host_srv_diff_host_rate': 0.0,
            'dst_host_serror_rate': 0.0,
            'dst_host_srv_serror_rate': 0.0,
            'dst_host_rerror_rate': 0.0,
            'dst_host_srv_rerror_rate': 0.0
        }
        
        # Preprocess
        df_sample = pd.DataFrame([features])
        for col, enc in self.encoders.items():
            if col in df_sample.columns:
                df_sample[col] = enc.transform(df_sample[col])
        X_sample = df_sample.values
        if self.sc:
            X_sample = self.sc.transform(X_sample)
        if self.selector:
            X_sample = self.selector.transform(X_sample)
        pred = self.model.predict(X_sample)[0]
        return pred == 0  # 0 is attack
    
    def get_threat_score(self, ip, port, status="ESTABLISHED", domain=None):
        if not self.model:
            return 0.0
        
        # URL pattern check
        if domain and self.check_url_threat(domain):
            return 1.0  # Maximum threat score
        
        # Similar to predict_threat
        features = {
            'duration': 0,
            'protocol_type': 'tcp',
            'service': 'http' if port in [80, 443] else 'private',
            'flag': 'SF' if status == 'ESTABLISHED' else 'S0',
            'src_bytes': 1000,
            'dst_bytes': 5000,
            'land': 0,
            'wrong_fragment': 0,
            'urgent': 0,
            'hot': 0,
            'num_failed_logins': 0,
            'logged_in': 1 if port in [80, 443] else 0,
            'num_compromised': 0,
            'root_shell': 0,
            'su_attempted': 0,
            'num_root': 0,
            'num_file_creations': 0,
            'num_shells': 0,
            'num_access_files': 0,
            'num_outbound_cmds': 0,
            'is_host_login': 0,
            'is_guest_login': 0,
            'count': 10,
            'srv_count': 10,
            'serror_rate': 0.0,
            'srv_serror_rate': 0.0,
            'rerror_rate': 0.0,
            'srv_rerror_rate': 0.0,
            'same_srv_rate': 1.0,
            'diff_srv_rate': 0.0,
            'srv_diff_host_rate': 0.0,
            'dst_host_count': 1,
            'dst_host_srv_count': 1,
            'dst_host_same_srv_rate': 1.0,
            'dst_host_diff_srv_rate': 0.0,
            'dst_host_same_src_port_rate': 1.0,
            'dst_host_srv_diff_host_rate': 0.0,
            'dst_host_serror_rate': 0.0,
            'dst_host_srv_serror_rate': 0.0,
            'dst_host_rerror_rate': 0.0,
            'dst_host_srv_rerror_rate': 0.0
        }
        
        df_sample = pd.DataFrame([features])
        for col, enc in self.encoders.items():
            if col in df_sample.columns:
                df_sample[col] = enc.transform(df_sample[col])
        X_sample = df_sample.values
        if self.sc:
            X_sample = self.sc.transform(X_sample)
        if self.selector:
            X_sample = self.selector.transform(X_sample)
        if hasattr(self.model, 'predict_proba'):
            prob = self.model.predict_proba(X_sample)[0]
            return float(prob[0])  # Probability of attack
        else:
            return 0.0
    
    def get_stats(self):
        return {"model_loaded": self.model is not None}

e = AIEngine()
test_urls = [
    "https://bopsecrets.org/rexroth/cr/1.htm",
    "yourbittorrent.com",
    "https://google.com",
    "https://github.com",
    "https://malware.ru",
    "https://hack.cn",
    "crackwarez.xyz",
    "torrentdownload.site",
    "freekeygen.top",
    "warezdownload.club",
    "http://www.824555.com/app/member/SportOption.php?uid=guest&langx=gb"
]

print("URL Threat Detection Test:")
for url in test_urls:
    domain = url.split('/')[2] if '//' in url else url.split('/')[0] if '/' in url else url
    is_threat = e.check_url_threat(domain)
    print(f"{domain}: {'THREAT' if is_threat else 'SAFE'}")

print("\nPort Tests:")
print(f"Port 443: {'THREAT' if e.predict_threat('', 443) else 'SAFE'}")
print(f"Port 4444: {'THREAT' if e.predict_threat('', 4444) else 'SAFE'}")
print(f"Port 6666: {'THREAT' if e.predict_threat('', 6666) else 'SAFE'}")

