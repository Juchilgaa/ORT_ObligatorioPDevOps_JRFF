import boto3
import os

# Parámetros
rds = boto3.client('rds')
DB_INSTANCE_ID = 'app-mysql'
DB_NAME = 'app'
DB_USER = 'admin'
# La password debe venir de una variable de entorno
DB_PASS = os.environ.get('RDS_ADMIN_PASSWORD')

if not DB_PASS:
    raise Exception('Debes definir la variable de entorno RDS_ADMIN_PASSWORD con la contraseña del admin.')

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
except rds.exceptions.DBInstanceAlreadyExistsFault:
    print(f'La instancia {DB_INSTANCE_ID} ya existe.')
