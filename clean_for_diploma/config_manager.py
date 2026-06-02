import os
import sys
import json
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
class ConfigManager:
    def __init__(self):
        if getattr(sys, 'frozen', False):
            self.config_path = os.path.join(os.path.dirname(sys.executable), 'db_config.enc')
        else:
            self.config_path = 'db_config.enc'
        self.key = self._get_or_create_key()
    def _get_or_create_key(self):
        password = b"my_super_secret_app_salt_do_not_share"
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=password, iterations=100000)
        return base64.urlsafe_b64encode(kdf.derive(password))
    def save_config(self, host, port, dbname, user, password):
        data = {"host": host, "port": port, "dbname": dbname, "user": user, "password": password}
        f = Fernet(self.key)
        token = f.encrypt(json.dumps(data).encode('utf-8'))
        with open(self.config_path, 'wb') as file:
            file.write(token)
    def load_config(self):
        if not os.path.exists(self.config_path):
            return None
        try:
            with open(self.config_path, 'rb') as file:
                token = file.read()
            f = Fernet(self.key)
            decrypted_data = f.decrypt(token).decode('utf-8')
            return json.loads(decrypted_data)
        except Exception:
            return None