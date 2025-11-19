import boto3

ec2 = boto3.client('ec2')

# Parámetro por defecto
image_id = 'ami-06b21ccaeff8cd686'
response = ec2.run_instances(
    ImageId=image_id,
    MinCount=1,
    MaxCount=1,
    InstanceType='t2.micro'
)
instance_id = response['Instances'][0]['InstanceId']
print(f"Instancia creada con ID: {instance_id}")