# -*- coding: utf-8 -*-
"""
إنشاء شهادة CA محلية + شهادة سيرفر موثوقة
بعد التشغيل، يجب تثبيت ca.pem في الجهاز/الجوال
"""
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from datetime import datetime, timedelta
import ipaddress, os

cert_dir = os.path.dirname(os.path.abspath(__file__))

# === 1) إنشاء CA (Certificate Authority) ===
ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
ca_name = x509.Name([
    x509.NameAttribute(NameOID.COUNTRY_NAME, "YE"),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Supermarket Local CA"),
    x509.NameAttribute(NameOID.COMMON_NAME, "Supermarket Local CA"),
])
ca_cert = (
    x509.CertificateBuilder()
    .subject_name(ca_name)
    .issuer_name(ca_name)
    .public_key(ca_key.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(datetime.utcnow())
    .not_valid_after(datetime.utcnow() + timedelta(days=3650))
    .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
    .sign(ca_key, hashes.SHA256())
)

ca_cert_path = os.path.join(cert_dir, "ca.pem")
ca_key_path = os.path.join(cert_dir, "ca-key.pem")

with open(ca_cert_path, "wb") as f:
    f.write(ca_cert.public_bytes(serialization.Encoding.PEM))
with open(ca_key_path, "wb") as f:
    f.write(ca_key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.TraditionalOpenSSL, serialization.NoEncryption()))

print(f"CA cert: {ca_cert_path}")
print(f"CA key:  {ca_key_path}")

# === 2) إنشاء شهادة السيرفر ===
server_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
server_name = x509.Name([
    x509.NameAttribute(NameOID.COUNTRY_NAME, "YE"),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Supermarket"),
    x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
])

san = x509.SubjectAlternativeName([
    x509.DNSName("localhost"),
    x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
    x509.IPAddress(ipaddress.IPv4Address("192.168.8.38")),
])

server_cert = (
    x509.CertificateBuilder()
    .subject_name(server_name)
    .issuer_name(ca_name)
    .public_key(server_key.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(datetime.utcnow())
    .not_valid_after(datetime.utcnow() + timedelta(days=365))
    .add_extension(san, critical=False)
    .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
    .sign(ca_key, hashes.SHA256())
)

cert_path = os.path.join(cert_dir, "cert.pem")
key_path = os.path.join(cert_dir, "key.pem")

with open(cert_path, "wb") as f:
    f.write(server_cert.public_bytes(serialization.Encoding.PEM))
with open(key_path, "wb") as f:
    f.write(server_key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.TraditionalOpenSSL, serialization.NoEncryption()))

print(f"Server cert: {cert_path}")
print(f"Server key:  {key_path}")
print()
print("="*50)
print("الآن ثبّت ca.pem على جهازك:")
print("  Windows: انقر مزدوج على ca.pem -> Install Certificate -> Local Machine -> Trusted Root")
print("  Android: الإعدادات -> الأمان -> تثبيت شهادة -> CA certificate -> اختر ca.pem")
print("  iPhone:  انقل ca.pem للجوال -> الإعدادات -> عام -> VPN وإدارة الأجهزة -> ثبّت")
print("="*50)
