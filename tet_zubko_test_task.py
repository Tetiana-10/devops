import boto3
from pathlib import Path
import paramiko
from datetime import datetime
import os

print("Enter your AWS access key ID:")
id = input()
print("Enter your AWS secret access key:")
password = input()
print("Enter your AWS region:")
aws_region = input()
home = str(Path.home())

#Creation of EC2 instance
print("Enter KeyName for a new instance:")
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
print("The instance is starting. Please wait ...")
instances[0].wait_until_running()
instances[0].attach_volume(VolumeId=volume.id, Device='/dev/xvdf')

#Connection via ssh
print("Connecting to the instance via SSH")
sshFile = open(home+"/sshKey.pom", "wt")
sshFile.write(str(ssh_key['KeyMaterial']))
sshFile.close()

key = paramiko.RSAKey.from_private_key_file(home+"/sshKey.pom")
sshClient = paramiko.SSHClient()
sshClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sshClient.connect(hostname=instances[0].public_dns_name, username="ubuntu", pkey=key)
stdin, stdout, stderr = sshClient.exec_command('sudo mkfs.ext4 /dev/xvdf')
stdin, stdout, stderr = sshClient.exec_command('sudo mkdir /mnt/xvdf')
stdin, stdout, stderr = sshClient.exec_command('sudo mount /dev/xvdf /mnt/xvdf')
sshClient.close()
os.remove(home+"/sshKey.pom")
print("The script was executed successfully!")
