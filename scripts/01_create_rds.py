# Script para crear una instancia RDS MYSQL en AWS con parámetros específicos

# Importamos las librerías necesarias
import boto3
import os

# Parámetros de la instancia RDS
rds = boto3.client('rds')
DB_INSTANCE_ID = 'app-mysql'
DB_NAME = 'app'
DB_USER = 'admin'

# Configuramos la variable de entorno "RDS_ADMIN_PASSWORD" para la contraseña del admin
DB_PASS = os.environ.get('RDS_ADMIN_PASSWORD')

# Verificar que la variable de entorno esté definida
if not DB_PASS:
    raise Exception('Debes definir la variable de entorno RDS_ADMIN_PASSWORD con la contraseña del admin.')

# Crear la instancia RDS MYSQL, con manejo de excepcion si ya existe y con los parametros solicitados
try:
    rds.create_db_instance(
        DBInstanceIdentifier=DB_INSTANCE_ID,
        AllocatedStorage=20,
        DBInstanceClass='db.t3.micro',
        Engine='mysql',
        MasterUsername=DB_USER,
        MasterUserPassword=DB_PASS,
        DBName=DB_NAME,
        PubliclyAccessible=True,
        BackupRetentionPeriod=0
    )
    print(f'Instancia RDS {DB_INSTANCE_ID} creada correctamente.')
    
# Manejo de exepción si la instancia ya existe
    
except rds.exceptions.DBInstanceAlreadyExistsFault:
    print(f'La instancia {DB_INSTANCE_ID} ya existe.')
