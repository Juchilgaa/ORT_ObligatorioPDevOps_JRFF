#!/usr/bin/env python3
"""
automatismo_rrhh.py
Script lineal (sin funciones) que automatiza el despliegue RRHH en AWS.

Flujo:
- Crea / verifica bucket S3 global "jrff-rrhh-app-pdevops2k25"
- Pide al usuario que suba:
    - paquete_app_rrhh.zip
    - init_db.sql
  y espera un "OK" por stdin.
- Verifica que esos objetos estén en el bucket.
- Crea / reutiliza RDS MySQL.
- Crea / reutiliza Security Group web.
- Crea EC2 con Apache/PHP.
- Configura la app vía SSM usando los archivos del bucket.

"""

import os
import time
import boto3
from botocore.exceptions import ClientError


# ===============================
# VARIABLES DE ENTORNO
# ===============================

RDS_ADMIN_PASSWORD = os.environ.get("RDS_ADMIN_PASSWORD")
APP_USER = os.environ.get("APP_USER")
APP_PASS = os.environ.get("APP_PASS")

# ===========================================
# NOMBRE BUCKET S3
# ===========================================
RRHH_BUCKET = "jrff-rrhh-app-pdevops2k25"
APP_ZIP_KEY = "paquete_app_rrhh.zip"
SQL_KEY = "init_db.sql"

print("=======================================")
print(" BUCKET SELECCIONADO PARA DESPLIEGUE")
print("=======================================")
print(f" RRHH_BUCKET = {RRHH_BUCKET}")
print("=======================================\n")




# ==========
# CLIENTES BOTO3
# ==========

ec2 = boto3.client("ec2")
rds = boto3.client("rds")
ssm = boto3.client("ssm")
s3 = boto3.client("s3")



# ===============================
# CONSTANTES
# ===============================
DB_INSTANCE_ID = "rrhh-mysql"
DB_NAME = "rrhh_app"
DB_USER = "admin"
WEB_SG_NAME = "rrhh-web-sg"
EC2_NAME_TAG = "rrhh-webserver"
AMI_ID = "ami-06b21ccaeff8cd686"
INSTANCE_PROFILE_NAME = "LabInstanceProfile"

print("****** Automatismo RRHH – Inicio ******\n")


# ===========================================
# Crea y verifica S3
# ===========================================



print(f"[S3] Creando/verificando bucket S3 global: {RRHH_BUCKET}")

try:
    # Intentar crearlo. Si el nombre ya existe en otra cuenta → BucketAlreadyExists.
    s3.create_bucket(Bucket=RRHH_BUCKET)
    print(f"[S3] Bucket creado correctamente: {RRHH_BUCKET}")
except ClientError as e:
    code = e.response["Error"]["Code"]

    if code == "BucketAlreadyOwnedByYou":
        print(f"[S3] El bucket '{RRHH_BUCKET}' ya existe y es tuyo. Se reutiliza.")
    elif code == "BucketAlreadyExists":
        raise SystemExit(
            f"ERROR: El bucket '{RRHH_BUCKET}' ya está en uso en otra cuenta (AWS global).\n"
            "Debés elegir otro nombre de bucket para el despliegue."
        )
    else:
        raise SystemExit(f"[S3] Error inesperado al crear bucket: {e}")

# Verificar que realmente existe y es accesible
try:
    s3.head_bucket(Bucket=RRHH_BUCKET)
    print(f"[S3] Verificación OK. Bucket accesible: {RRHH_BUCKET}\n")
except ClientError as e:
    raise SystemExit(f"[S3] Error al verificar el bucket luego de crearlo: {e}")

# Mensaje para que el usuario suba los archivos
print("############################################################")
print("# ATENCIÓN – ACCIÓN REQUERIDA")
print("# Se creó/verificó el bucket S3:")
print(f"#   s3://{RRHH_BUCKET}")
print("# Ahora debés subir MANUALMENTE estos archivos al bucket:")
print(f"#   1) {APP_ZIP_KEY}  (ZIP con la aplicación PHP)")
print(f"#   2) {SQL_KEY}      (script SQL con estructura/datos)")
print("#")
print("# Cuando termines de subirlos, escribí OK y presioná Enter")
print("############################################################\n")

respuesta = input("Escribí OK cuando los archivos estén subidos al bucket: ").strip().lower()
if respuesta != "ok":
    raise SystemExit("Se aborta el despliegue porque no se confirmó 'OK'.")

print("\n[S3] Verificando que los archivos estén presentes en el bucket...")

# Verificar existencia de paquete_app_rrhh.zip
try:
    s3.head_object(Bucket=RRHH_BUCKET, Key=APP_ZIP_KEY)
    print(f"[S3] Encontrado: s3://{RRHH_BUCKET}/{APP_ZIP_KEY}")
except ClientError:
    raise SystemExit(
        f"ERROR: No se encontró el objeto '{APP_ZIP_KEY}' en el bucket '{RRHH_BUCKET}'.\n"
        "Verificá que el archivo esté subido con ese nombre exacto."
    )

# Verificar existencia de init_db.sql
try:
    s3.head_object(Bucket=RRHH_BUCKET, Key=SQL_KEY)
    print(f"[S3] Encontrado: s3://{RRHH_BUCKET}/{SQL_KEY}")
except ClientError:
    raise SystemExit(
        f"ERROR: No se encontró el objeto '{SQL_KEY}' en el bucket '{RRHH_BUCKET}'.\n"
        "Verificá que el archivo esté subido con ese nombre exacto."
    )

print("[S3] Archivos requeridos presentes. Continuando con el despliegue...\n")



# ===============================
# Crea RDS - Mysql
# ===============================

print("[RDS] Creando o recuperando RDS...")

try:
    rds.create_db_instance(
        DBInstanceIdentifier=DB_INSTANCE_ID,
        AllocatedStorage=20,
        DBName=DB_NAME,
        Engine="mysql",
        MasterUsername=DB_USER,
        MasterUserPassword=RDS_ADMIN_PASSWORD,
        DBInstanceClass="db.t3.micro",
    )
    print(f"[RDS] Creación iniciada: {DB_INSTANCE_ID}")
except ClientError as e:
    if e.response["Error"]["Code"] == "DBInstanceAlreadyExistsFault":
        print(f"[RDS] La instancia {DB_INSTANCE_ID} ya existe. Continuando...")
    else:
        print("[RDS] Error inesperado:", e)
        raise

print("[RDS] Esperando a que esté en estado 'available'...")

while True:
    info = rds.describe_db_instances(DBInstanceIdentifier=DB_INSTANCE_ID)
    status = info["DBInstances"][0]["DBInstanceStatus"]
    print(f"[RDS] Estado actual: {status}")

    if status == "available":
        DB_ENDPOINT = info["DBInstances"][0]["Endpoint"]["Address"]
        print(f"[RDS] Listo. Endpoint: {DB_ENDPOINT}")
        break

# Espera dinámica: consulta cada 3 segundos hasta que el estado sea 'available'

    time.sleep(3)

# ===============================
# Crea EC2 con la config del Apache
# ===============================

print("\n[EC2] Creando instancia EC2 web...")

user_data = """#!/bin/bash
yum update -y
yum install -y httpd php
systemctl enable httpd
systemctl start httpd

echo "<?php echo 'Servidor RRHH OK'; ?>" > /var/www/html/index.php
"""

response = ec2.run_instances(
    ImageId=AMI_ID,
    InstanceType="t2.micro",
    MinCount=1,
    MaxCount=1,
    IamInstanceProfile={"Name": INSTANCE_PROFILE_NAME},
    SecurityGroupIds=[sg_id],
    UserData=user_data
)

instance_id = response["Instances"][0]["InstanceId"]
print(f"[EC2] Instancia creada: {instance_id}")

ec2.create_tags(
    Resources=[instance_id],
    Tags=[{"Key": "Name", "Value": EC2_NAME_TAG}]
)

print("[EC2] Tag Name aplicado.")
print("[EC2] Esperando estado 'instance_status_ok'...")

waiter = ec2.get_waiter("instance_status_ok")
waiter.wait(InstanceIds=[instance_id])
print("[EC2] La instancia está lista.")

desc = ec2.describe_instances(InstanceIds=[instance_id])
public_ip = desc["Reservations"][0]["Instances"][0]["PublicIpAddress"]

print(f"[EC2] IP pública: {public_ip}")

# ===============================
# Config APP via SSM
# ===============================

print("[SSM] Configurando app RRHH dentro de EC2...")

env_file_cmd = f"""cat <<EOF >/var/www/.env
DB_HOST={DB_ENDPOINT}
DB_NAME={DB_NAME}
DB_USER={DB_USER}
DB_PASS={RDS_ADMIN_PASSWORD}

APP_USER={APP_USER}
APP_PASS={APP_PASS}
EOF
"""

commands = [
    # Paquetes necesarios: web, php, cliente MySQL, awscli, unzip
    "yum install -y httpd php awscli unzip mariadb105 || true",
    "systemctl enable httpd || true",
    "systemctl start httpd || true",

    # Descargar ZIP de la app y el SQL desde S3 a /tmp
    f"aws s3 cp s3://{RRHH_BUCKET}/{APP_ZIP_KEY} /tmp/{APP_ZIP_KEY}",
    f"aws s3 cp s3://{RRHH_BUCKET}/{SQL_KEY} /tmp/{SQL_KEY}",

    # Dejar la app en /var/www/html
    "rm -rf /var/www/html/*",
    f"unzip -o /tmp/{APP_ZIP_KEY} -d /var/www/html",

    # Mover init_db.sql FUERA del webroot, a /var/www
    f"mv /tmp/{SQL_KEY} /var/www/{SQL_KEY}",

    # Ejecutar el script SQL contra la RDS para crear tablas/datos
    # (usa el cliente mariadb/mysql y las credenciales que ya tenemos)
    f'mysql -h {DB_ENDPOINT} -u {DB_USER} -p"{RDS_ADMIN_PASSWORD}" {DB_NAME} < /var/www/{SQL_KEY}',

    # Crear archivo .env en /var/www (.env fuera del webroot)
    env_file_cmd,
    "chmod 600 /var/www/.env",
    "chown apache:apache /var/www/.env",

    # Asegurar permisos para que Apache pueda leer todo el código
    "chown -R apache:apache /var/www/html",

    # Reiniciar servicios web
    "systemctl restart httpd || true",
    "systemctl restart php-fpm || true",
]

response = ssm.send_command(
    InstanceIds=[instance_id],
    DocumentName="AWS-RunShellScript",
    Parameters={"commands": commands}
)

command_id = response["Command"]["CommandId"]
print(f"[SSM] Command ID: {command_id}")

while True:
    output = ssm.get_command_invocation(
        CommandId=command_id,
        InstanceId=instance_id
    )
    status = output["Status"]
    print(f"[SSM] Estado comando: {status}")

    if status in ["Success", "Failed", "TimedOut", "Cancelled"]:
        break

    time.sleep(5)

print("\n[SSM] OUTPUT:")
print(output.get("StandardOutputContent", ""))

print("\n=== DESPLIEGUE COMPLETADO EXITOSAMENTE ===")
if public_ip:
    print(f"URL de la aplicación: http://{public_ip}/index.php")
else:
    print("La instancia no tiene IP pública, revisar configuración de red.")
print(f"APP_USER: {APP_USER}")
print(f"APP_PASS: {APP_PASS}")