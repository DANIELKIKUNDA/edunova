from __future__ import annotations
import base64,hashlib,hmac,secrets,struct,time
from cryptography.fernet import Fernet,InvalidToken
class MfaVault:
 def __init__(self,key:str):
  if len(key)<32: raise ValueError('MFA_ENCRYPTION_KEY must have at least 32 characters')
  material=base64.urlsafe_b64encode(hashlib.sha256(key.encode()).digest()); self.f=Fernet(material)
 def encrypt(self,secret:str)->str: return self.f.encrypt(secret.encode()).decode()
 def decrypt(self,value:str)->str: return self.f.decrypt(value.encode()).decode()
def new_totp_secret()->str: return base64.b32encode(secrets.token_bytes(20)).decode().rstrip('=')
def totp(secret:str,at:int|None=None,step:int=30,digits:int=6)->str:
 at=int(time.time() if at is None else at); counter=at//step; padded=secret+'='*((8-len(secret)%8)%8); key=base64.b32decode(padded); digest=hmac.new(key,struct.pack('>Q',counter),hashlib.sha1).digest(); off=digest[-1]&15; code=(struct.unpack('>I',digest[off:off+4])[0]&0x7fffffff)%(10**digits); return str(code).zfill(digits)
def verify_totp(secret:str,code:str,at:int|None=None,window:int=1)->bool:
 now=int(time.time() if at is None else at); return any(hmac.compare_digest(totp(secret,now+i*30),code.strip()) for i in range(-window,window+1))
