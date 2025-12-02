#!/usr/bin/env python3

# Import de las librerias necesarias

import os
import time
import zipfile
import tempfile
import shutil
import random
import boto3
from botocore.exceptions import ClientError

# VARIABLES DE ENTORNO

RDS_ADMIN_PASSWORD = os.environ.get("RDS_ADMIN_PASSWORD")
APP_USER = os.environ.get("APP_USER")
APP_PASS = os.environ.get("APP_PASS")

if not RDS_ADMIN_PASSWORD or not APP_USER or not APP_PASS:
    raise SystemExit(
        "ERROR: Debés definir las variables de entorno RDS_ADMIN_PASSWORD, APP_USER y APP_PASS.\n"
        "Ejemplo:\n"
        "  export RDS_ADMIN_PASSWORD='tu_pass_admin'\n"
        "  export APP_USER='admin'\n"
        "  export APP_PASS='admin123'\n"
    )

# ARCHIVOS / NOMBRES EN S3

BUCKET_PREFIX = "jrff-rrhh-app"
RRHH_BUCKET = None
APP_ZIP_KEY = "paquete_app_rrhh.zip"
SQL_KEY = "init_db.sql"

# Rutas locales (directorio del script)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OBLIG_ZIP_NAME = "obligatorio-main.zip"
OBLIG_ZIP_PATH = os.path.join(SCRIPT_DIR, OBLIG_ZIP_NAME)


#  CLIENTES BOTO3 

ec2 = boto3.client("ec2")
rds = boto3.client("rds")
ssm = boto3.client("ssm")
s3 = boto3.client("s3")

# CONSTANTES

DB_INSTANCE_ID = "rrhh-mysql"
DB_NAME = "demo_db"  # Nombre de la BD creada por el archivo init_db.sql
DB_USER = "admin"
WEB_SG_NAME = "rrhh-web-sg"
DB_SG_NAME = "rrhh-db-sg"
EC2_NAME_TAG = "rrhh-webserver"
AMI_ID = "ami-06b21ccaeff8cd686"
INSTANCE_PROFILE_NAME = "LabInstanceProfile"


print("****** Automatismo RRHH – Inicio ******\n")

# Crear bucket S3 dinámicamente

print(f"[S3] Generando el bucket S3.... Nombre: '{BUCKET_PREFIX}'...")

while True:
    sufijo = f"{random.randint(0, 9999):04d}"
    bucket_name = f"{BUCKET_PREFIX}{sufijo}"
    print(f"[S3] Probando crear bucket: {bucket_name}")

    try:
        s3.create_bucket(Bucket=bucket_name)
        RRHH_BUCKET = bucket_name
        print(f"[S3] Bucket creado correctamente: {RRHH_BUCKET}")
        break

    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code in ("BucketAlreadyExists", "BucketAlreadyOwnedByYou"):
            print(f"[S3] '{bucket_name}' ya existe. Probando otro...")
            continue
        else:
            raise SystemExit(f"[S3] Error inesperado al crear bucket: {e}")

if RRHH_BUCKET is None:
    raise SystemExit("ERROR: No se pudo crear un bucket S3. Abortando.")

try:
    s3.head_bucket(Bucket=RRHH_BUCKET)
    print(f"[S3] Verificación OK. Bucket accesible: {RRHH_BUCKET}\n")
except ClientError as e:
    raise SystemExit(f"[S3] Error al verificar el bucket luego de crearlo: {e}")

print("=======================================")
print(" BUCKET SELECCIONADO PARA DESPLIEGUE")
print("=======================================")
print(f" RRHH_BUCKET = {RRHH_BUCKET}")
print("=======================================\n")

# Preparar ZIP de la app y SQL desde obligatorio-main.zip

print("[S3] Preparando archivos a partir de obligatorio-main.zip...")

if not os.path.isfile(OBLIG_ZIP_PATH):
    raise SystemExit(
        f"ERROR: No se encontró '{OBLIG_ZIP_NAME}' en el directorio del script:\n"
        f"  {SCRIPT_DIR}\n"
        "Copiá o descarga obligatorio-main.zip allí y volvé a ejecutar."
    )

temp_dir = tempfile.mkdtemp(prefix="rrhh_")
print(f"[TMP] Directorio temporal: {temp_dir}")

try:
# Descomprimir obligatorio-main.zip
    print(f"[ZIP] Descomprimiendo {OBLIG_ZIP_PATH} ...")
    with zipfile.ZipFile(OBLIG_ZIP_PATH, "r") as z:
        z.extractall(temp_dir)

    app_root = os.path.join(temp_dir, "obligatorio-main")
    if not os.path.isdir(app_root):
        raise SystemExit(
            "ERROR: No se encontró la carpeta 'obligatorio-main' dentro del ZIP.\n"
            "Revisá la estructura de obligatorio-main.zip."
        )

#  Ubicar el SQL (init_db.sql en la raíz de obligatorio-main)
    local_sql_path = os.path.join(app_root, SQL_KEY)
    if not os.path.isfile(local_sql_path):
        raise SystemExit(
            f"ERROR: No se encontró '{SQL_KEY}' dentro de obligatorio-main.\n"
            "Asegurate de que el SQL esté con ese nombre en la raíz de la app."
        )

# Crea paquete_app_rrhh.zip con solo la app
    local_app_zip_path = os.path.join(temp_dir, APP_ZIP_KEY)
    print(f"[ZIP] Creando {local_app_zip_path} desde {app_root} (sin incluir .sql)...")

    with zipfile.ZipFile(local_app_zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(app_root):
            for fname in files:
                if fname.lower().endswith(".sql"):
                    continue  # NO incluimos .sql en el ZIP de la app
                full = os.path.join(root, fname)
                rel = os.path.relpath(full, app_root)
                z.write(full, rel)

    print("[ZIP] paquete_app_rrhh.zip creado correctamente.")

# Subir paquete_app_rrhh.zip e init_db.sql a S3
    print(f"[S3] Subiendo {local_app_zip_path} a s3://{RRHH_BUCKET}/{APP_ZIP_KEY} ...")
    s3.upload_file(local_app_zip_path, RRHH_BUCKET, APP_ZIP_KEY)
    print("[S3] Upload paquete_app_rrhh.zip OK.")

    print(f"[S3] Subiendo {local_sql_path} a s3://{RRHH_BUCKET}/{SQL_KEY} ...")
    s3.upload_file(local_sql_path, RRHH_BUCKET, SQL_KEY)
    print("[S3] Upload init_db.sql OK.\n")

finally:
    shutil.rmtree(temp_dir, ignore_errors=True)
    print(f"[TMP] Directorio temporal eliminado: {temp_dir}\n")

# Verificar existencia de objetos en S3
print("[S3] Verificando que los archivos estén presentes en el bucket...")

try:
    s3.head_object(Bucket=RRHH_BUCKET, Key=APP_ZIP_KEY)
    print(f"[S3] Encontrado: s3://{RRHH_BUCKET}/{APP_ZIP_KEY}")
except ClientError:
    raise SystemExit(
        f"ERROR: No se encontró el objeto '{APP_ZIP_KEY}' en el bucket '{RRHH_BUCKET}'.\n"
        "Algo falló durante la subida automática."
    )

try:
    s3.head_object(Bucket=RRHH_BUCKET, Key=SQL_KEY)
    print(f"[S3] Encontrado: s3://{RRHH_BUCKET}/{SQL_KEY}")
except ClientError:
    raise SystemExit(
        f"ERROR: No se encontró el objeto '{SQL_KEY}' en el bucket '{RRHH_BUCKET}'.\n"
        "Algo falló durante la subida automática."
    )

print("[S3] Archivos requeridos presentes. Continuando con el despliegue...\n")

# Crea RDS - Mysql

print("[RDS] Creando o recuperando RDS...")

try:
    info = rds.describe_db_instances(DBInstanceIdentifier=DB_INSTANCE_ID)
    print(f"[RDS] La instancia {DB_INSTANCE_ID} ya existe. Se reutiliza.")
except ClientError as e:
    code = e.response["Error"]["Code"]

    if code in ("DBInstanceNotFound", "DBInstanceNotFoundFault"):
        print(f"[RDS] La instancia {DB_INSTANCE_ID} no existe. Creándola...")

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
    else:
        print("[RDS] Error inesperado al verificar/crear la instancia:", e)
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

    time.sleep(3)



# Crea SGs (web y BD) y luego EC2


print("[SG] Creando o recuperando Security Group web...")

vpcs = ec2.describe_vpcs()
vpc_id = vpcs["Vpcs"][0]["VpcId"]

sg_id = None  # SG de la web (EC2)

# SG WEB (HTTP) 
try:
    response = ec2.create_security_group(
        GroupName=WEB_SG_NAME,
        Description="Security Group HTTP para app RRHH",
        VpcId=vpc_id
    )
    sg_id = response["GroupId"]
    print(f"[SG] SG web creado: {sg_id}")

    ec2.authorize_security_group_ingress(
        GroupId=sg_id,
        IpPermissions=[
            {
                "IpProtocol": "tcp",
                "FromPort": 80,
                "ToPort": 80,
                "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
            }
        ]
    )
    print("[SG] Regla HTTP 80/tcp configurada.\n")

except ClientError as e:
    code = e.response["Error"]["Code"]
    if code == "InvalidGroup.Duplicate":
        print(f"[SG] SG web '{WEB_SG_NAME}' ya existe. Recuperando ID...")
        sgs = ec2.describe_security_groups(
            Filters=[
                {"Name": "group-name", "Values": [WEB_SG_NAME]},
                {"Name": "vpc-id", "Values": [vpc_id]},
            ]
        )
        sg_id = sgs["SecurityGroups"][0]["GroupId"]
        print(f"[SG] Usando SG web existente: {sg_id}\n")
    else:
        print("[SG] Error inesperado creando SG web:", e)
        raise

if sg_id is None:
    raise SystemExit("ERROR: No se pudo determinar el ID del Security Group web (sg_id).")


#  SG BD (RDS MySQL) 

print("[SG] Creando o recuperando Security Group de base de datos...")

db_sg_id = None  # SG de la RDS

try:
    response = ec2.create_security_group(
        GroupName=DB_SG_NAME,
        Description="Security Group MySQL para RDS RRHH",
        VpcId=vpc_id
    )
    db_sg_id = response["GroupId"]
    print(f"[SG] SG BD creado: {db_sg_id}")

# Permitir 3306 solo desde el SG web
    ec2.authorize_security_group_ingress(
        GroupId=db_sg_id,
        IpPermissions=[
            {
                "IpProtocol": "tcp",
                "FromPort": 3306,
                "ToPort": 3306,
                "UserIdGroupPairs": [
                    {"GroupId": sg_id}
                ],
            }
        ]
    )
    print("[SG] Regla MySQL 3306/tcp desde SG web configurada.\n")

except ClientError as e:
    code = e.response["Error"]["Code"]
    if code == "InvalidGroup.Duplicate":
        print(f"[SG] SG BD '{DB_SG_NAME}' ya existe. Recuperando ID...")
        sgs = ec2.describe_security_groups(
            Filters=[
                {"Name": "group-name", "Values": [DB_SG_NAME]},
                {"Name": "vpc-id", "Values": [vpc_id]},
            ]
        )
        db_sg_id = sgs["SecurityGroups"][0]["GroupId"]
        print(f"[SG] Usando SG BD existente: {db_sg_id}\n")
    else:
        print("[SG] Error inesperado creando SG BD:", e)
        raise

if db_sg_id is None:
    raise SystemExit("ERROR: No se pudo determinar el ID del Security Group de BD (db_sg_id).")


# Asocia SG BD a la instancia RDS

print("[RDS] Asociando Security Group de BD a la instancia RDS...")

info = rds.describe_db_instances(DBInstanceIdentifier=DB_INSTANCE_ID)
current_sg_ids = [
    sg["VpcSecurityGroupId"] for sg in info["DBInstances"][0]["VpcSecurityGroups"]
]

if db_sg_id not in current_sg_ids:
    new_sg_ids = current_sg_ids + [db_sg_id]

    rds.modify_db_instance(
        DBInstanceIdentifier=DB_INSTANCE_ID,
        VpcSecurityGroupIds=new_sg_ids,
        ApplyImmediately=True,
    )
    print(f"[RDS] SGs actualizados para RDS: {new_sg_ids}")
    print("[RDS] Esperando a que la instancia vuelva a 'available' tras el cambio de SG...")

    while True:
        info = rds.describe_db_instances(DBInstanceIdentifier=DB_INSTANCE_ID)
        status = info["DBInstances"][0]["DBInstanceStatus"]
        print(f"[RDS] Estado actual tras cambio de SG: {status}")
        if status == "available":
            break
        time.sleep(5)
else:
    print("[RDS] El SG de BD ya estaba asociado al RDS.\n")

print(f"[SG] Usando Security Group web: {sg_id}")
print(f"[SG] Usando Security Group BD : {db_sg_id}\n")



# Creación de la EC2


print("\n[EC2] Creando instancia EC2 web...")

response = ec2.run_instances(
    ImageId=AMI_ID,
    InstanceType="t2.micro",
    MinCount=1,
    MaxCount=1,
    IamInstanceProfile={"Name": INSTANCE_PROFILE_NAME},
    SecurityGroupIds=[sg_id],
)

instance_id = response["Instances"][0]["InstanceId"]
print(f"[EC2] La Instancia creada es: {instance_id}")

ec2.create_tags(
    Resources=[instance_id],
    Tags=[{"Key": "Name", "Value": EC2_NAME_TAG}]
)
print("[EC2] Esperando estado... 'instance_status_ok'...")

waiter = ec2.get_waiter("instance_status_ok")
waiter.wait(InstanceIds=[instance_id])
print("[EC2] La instancia está lista.")

desc = ec2.describe_instances(InstanceIds=[instance_id])
public_ip = desc["Reservations"][0]["Instances"][0]["PublicIpAddress"]

print(f"[EC2] La IP pública asignada es: {public_ip}")

# Config APP via SSM

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
    "dnf clean all || yum clean all",
    "dnf makecache || true",
    "dnf -y update || yum -y update || true",
    "dnf -y install httpd php php-cli php-fpm php-common php-mysqlnd mariadb105 awscli unzip || "
    "yum -y install httpd php php-cli php-fpm php-common php-mysqlnd mariadb105 awscli unzip",
    "systemctl enable --now httpd || true",
    "systemctl enable --now php-fpm || true",
    "echo '<FilesMatch \\.php$>' > /etc/httpd/conf.d/php-fpm.conf",
    "echo '  SetHandler \"proxy:unix:/run/php-fpm/www.sock|fcgi://localhost/\"' >> /etc/httpd/conf.d/php-fpm.conf",
    "echo '</FilesMatch>' >> /etc/httpd/conf.d/php-fpm.conf",
    # 4) Descargar ZIP de la app y el SQL desde S3 a /tmp
    f"aws s3 cp s3://{RRHH_BUCKET}/{APP_ZIP_KEY} /tmp/{APP_ZIP_KEY}",
    f"aws s3 cp s3://{RRHH_BUCKET}/{SQL_KEY} /tmp/{SQL_KEY}",
    "rm -rf /var/www/html/*",
    f"unzip -o /tmp/{APP_ZIP_KEY} -d /var/www/html",
    f"mv /tmp/{SQL_KEY} /var/www/{SQL_KEY}",
    f'mysql -h {DB_ENDPOINT} -u {DB_USER} -p"{RDS_ADMIN_PASSWORD}" {DB_NAME} < /var/www/{SQL_KEY}',
    env_file_cmd,
    "chmod 600 /var/www/.env",
    "chown apache:apache /var/www/.env",
    "chown -R apache:apache /var/www/html",
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

print("\n=== DESPLIEGUE COMPLETADO  ===")
if public_ip:
    print(f"URL de la aplicación: http://{public_ip}/index.php")
print(f"APP_USER: {APP_USER}")
print(f"APP_PASS: {APP_PASS}")
