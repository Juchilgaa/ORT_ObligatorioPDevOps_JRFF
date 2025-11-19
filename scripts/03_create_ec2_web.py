#Importo el SDK de AWS para Python
import boto3
#Importo time para poder hacer esperas (sleep)
import time

#Defino constantes para no repetir el mismo valor varias veces
ami_id = 'ami-06b21ccaeff8cd686'
instance_type = 't2.micro'
instance_profile_name = 'LabInstanceProfile' 

# Creo un único cliente EC2 y un único cliente SSM para reutilizar en todo el script
ec2 = boto3.client('ec2')
ssm = boto3.client('ssm')

# Parte 1: Crear una instancia EC2 asociada al Instance Profile del rol LabRole

# Uso las constantes definidas arriba para que sea más fácil cambiar parámetros
response = ec2.run_instances(
    ImageId=ami_id,
    MinCount=1,
    MaxCount=1,
    InstanceType=instance_type,
    IamInstanceProfile={'Name': instance_profile_name},
)

# Tomo el ID de la instancia creada
instance_id = response['Instances'][0]['InstanceId']
print(f"Instancia creada con ID: {instance_id}")

# Esperar a que la instancia esté en estado running
ec2.get_waiter('instance_status_ok').wait(InstanceIds=[instance_id])

# Parte 2: Enviar comando y extraer resultado usando SSM

command = 'echo "Prueba SSM sobre instancia de RRHH"'
response = ssm.send_command(
    InstanceIds=[instance_id],
    DocumentName="AWS-RunShellScript",
    Parameters={'commands': [command]}
)
command_id = response['Command']['CommandId']

# Esperar resultado del comando SSM
while True:
    output = ssm.get_command_invocation(CommandId=command_id, InstanceId=instance_id)
    if output['Status'] in ['Success', 'Failed', 'Cancelled', 'TimedOut']:
        break
    time.sleep(2)
    
print("Output:")
print(output['StandardOutputContent']) # Muestra la salida estándar del comando que se ejeutó


# Segunda parte del ejercicio: crear otra instancia con user_data

# Script de user data que se ejecuta al iniciar la instancia
user_data = '''#!/bin/bash
yum update -y
yum install -y httpd
systemctl start httpd
systemctl enable httpd
echo "Sitio RRHH desplegado correctamente" > /var/www/html/index.html
'''

# Creo otra instancia EC2, esta vez con user_data para levantar un Apache simple
response = ec2.run_instances(
    ImageId= ami_id,
    InstanceType= instance_type,
    MinCount=1,
    MaxCount=1,
    IamInstanceProfile={'Name': instance_profile_name},
    UserData=user_data
)

# Agregar tag Name: webserver-devops
instance_id = response['Instances'][0]['InstanceId']
ec2.create_tags(
    Resources=[instance_id],
    Tags=[{'Key': 'Name', 'Value': 'webserver-devops'}]
)
print(f"Instancia creada con ID: {instance_id} y tag 'webserver-devops'")

