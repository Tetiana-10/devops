import boto3
from pathlib import Path
import time
import paramiko
from datetime import datetime
from io import StringIO

print("Enter your aws_user_id:")
id = input()
print("Enter your aws_user_password:")
password = input()
print("Enter your aws_region:")
aws_region = input()
home = str(Path.home())

#Creation of EC2 instance
print("Enter KeyName for new instance:")
keyName = input()
ec2 = boto3.resource('ec2', aws_access_key_id=id, aws_secret_access_key=password, region_name=aws_region)
client = boto3.client('ec2', region_name=aws_region)
ssh_key=client.create_key_pair(KeyName=keyName)

instances = ec2.create_instances(
     ImageId='ami-009c174642dba28e4',
     MinCount=1,
     MaxCount=1,
     InstanceType='t2.micro',
     KeyName=keyName
)

#Creation of security group
securityGroup = ec2.create_security_group(GroupName='tetiana/zubko'+datetime.now().strftime('%Y-%m-%d %H:%M:%S'),Description='for test task by Tetiana Zubko')
securityGroup.authorize_ingress(
   IpPermissions=[
        {'IpProtocol': 'tcp',
         'FromPort': 80,
         'ToPort': 80,
         'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
         {'IpProtocol': 'tcp',
         'FromPort': 22,
         'ToPort': 22,
         'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}
    ]
) 
instances[0].modify_attribute(Groups=[securityGroup.group_id])

#Creation of EBS volume
responses = client.describe_instances()
for response in responses['Reservations']:
      for instance in response['Instances']:
          if(instance['InstanceId']==instances[0].id):
              availability_zone = instance['Placement']['AvailabilityZone']
volume = ec2.create_volume(AvailabilityZone=availability_zone,VolumeType='standard', Size=1)
print("The instance is startig. Please wait ...")
instances[0].wait_until_running()
instances[0].attach_volume(VolumeId=volume.id, Device='/dev/xvdf')

#connect via ssh
print(ssh_key['KeyMaterial'])
#key = paramiko.RSAKey.from_private_key_file(sshFilePath)
key = paramiko.RSAKey.from_private_key(StringIO(ssh_key['KeyMaterial']))
sshClient = paramiko.SSHClient()
sshClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    print(instances[0].public_dns_name)
    sshClient.connect(hostname=instances[0].public_dns_name, username="ubuntu", pkey=key)
    stdin, stdout, stderr = sshClient.exec_command('sudo mkfs.ext4 /dev/xvdf')
    stdin, stdout, stderr = sshClient.exec_command('sudo mkdir /mnt/xvdf')
    stdin, stdout, stderr = sshClient.exec_command('sudo mount /dev/xvdf /mnt/xvdf')
    sshClient.close()
except Exception:
    print("SSH exception happened")
