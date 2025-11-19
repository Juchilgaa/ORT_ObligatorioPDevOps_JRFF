import boto3
import botocore.exceptions as ClientError
ec2 = boto3.client('ec2')
# 1. Crear un Security Group que permita tráfico web desde cualquier IP
sg_name = 'web-sg-boto3'
try:
    response = ec2.create_security_group(
        GroupName=sg_name,
        Description='Permitir trafico web desde cualquier IP'
    )
    sg_id = response['GroupId']
    print(f"Security Group creado: {sg_id}")
    ec2.authorize_security_group_ingress(
        GroupId=sg_id,
        IpPermissions=[
            {
                'IpProtocol': 'tcp',
                'FromPort': 80,
                'ToPort': 80,
                'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
            }
        ]
    )
except ClientError as e:
    if 'InvalidGroup.Duplicate' in str(e):
        sg_id = ec2.describe_security_groups(GroupNames=[sg_name])['SecurityGroups'][0]['GroupId']
        print(f"Security Group ya existe: {sg_id}")
    else:
        raise

# 2. Asociar el SG a la instancia EC2 creada anteriormente

# Obtener la primera instancia EC2 cuyo tag Name sea 'webserver-devops'
instances = ec2.describe_instances(Filters=[{'Name': 'tag:Name', 'Values': ['webserver-devops']}])
instance_id = None
for reservation in instances['Reservations']:
    for instance in reservation['Instances']:
        instance_id = instance['InstanceId']
        break
    if instance_id:
        break
if not instance_id:
    raise Exception("No se encontró ninguna instancia con el tag 'webserver-devops'.")

ec2.modify_instance_attribute(InstanceId=instance_id, Groups=[sg_id])
print(f"SG {sg_id} asociado a la instancia {instance_id}")

print("Ahora navegue a la IP pública de la instancia para verificar el acceso web.")
