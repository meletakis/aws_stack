import boto3
from botocore.exceptions import ClientError
import json


class AccessManagement:

	def __init__(self):
		self.iam_client = boto3.client('iam', region_name='eu-central-1')

	def create_user_keys(self, name, user_type):
		username = name+user_type
		try:
			new_user = self.iam_client.create_user(UserName=username)			
		except ClientError as e:
			if e.response['Error']['Code'] == 'EntityAlreadyExists':
				print "\nUser "+username+" already exists"
				return self.get_access_keys(username)
			else:
				print "Could not create User with name: "+username
			return False
		else:
			print "\nUser "+username+" created successfully"
			return self.get_access_keys(username)

	def get_access_keys(self, username):
		try:
			access_key = self.iam_client.create_access_key(UserName=username)
		except ClientError as e:
			print "User "+username+" exceeded the access key quota"
			return False
		else:
			print "SecretAccessKey:"+access_key['AccessKey']['SecretAccessKey']+"\t"+"AccessKeyId:"+access_key['AccessKey']['AccessKeyId']
			return access_key['AccessKey']


class Notification:

	def __init__(self):
		self.sns_client = boto3.client('sns', region_name='eu-central-1')

	def create_topic(self, name):
		try:
			new_topic = self.sns_client.create_topic(Name=name+'_topic')
		except ClientError as e:
			print "Could not create Topic with name: "+name+"_topic"
			return False
		else:
			print "Topic "+name+"_topic created successfully"
			return new_topic['TopicArn']

	def subscribe(self, topic, queue):
		try:
			new_subscription = self.sns_client.subscribe(
			    TopicArn=topic,
			    Protocol='sqs',
			    Endpoint= queue )
		except ClientError as e:
			print "Could not Subscribe Queue to SNS Topic"
			return False
		else:
			print "Queue subscribed to SNS Topic successfully"
			return new_subscription['SubscriptionArn']

	def set_raw_delivary(self, SubscriptionArn):
		try:
			raw_delivary = self.sns_client.set_subscription_attributes(
				SubscriptionArn=SubscriptionArn,
				AttributeName='RawMessageDelivery',
				AttributeValue='true')
		except ClientError as e:
			print "Could not sepcify Raw Message Delivery"
			return False
		else:
			print "Raw Delivery specified successfully"
			return True

	def add_publish_permision(self, topic, access_key, secret_key):
		try:
			account_id = get_account_id(access_key, secret_key)
			new_permission = self.sns_client.add_permission(
			    TopicArn=topic,
			    Label=str(topic)+":"+str(account_id)+":sns:publish",
			    AWSAccountId=[account_id],
			    ActionName=['Publish'])
		except ClientError as e:
			print "Could not give publish permissions to topic", e
			return False  
		else:
			print "Publish permissions given successfully to "+topic
			return True


class SimpleQueue:

	def __init__(self):
		self.sqs_client = boto3.client('sqs', region_name='eu-central-1')

	def create(self, name):
		try:
			new_queue = self.sqs_client.create_queue( QueueName = name+'_queue')
			queue_url = new_queue['QueueUrl']
			new_queue_attrs = self.sqs_client.get_queue_attributes(
    			QueueUrl=queue_url,
    			AttributeNames=['QueueArn'])
		except ClientError as e:
			print "Could not create Queue with name: "+name+"_queue"
			return False
		else:
			print "Queue "+name+"_queue created successfully"
			return {"queue_url":queue_url, "queue_arn": new_queue_attrs['Attributes']['QueueArn']}

	def create_dead_letter(self, name, associated_queue):
		try:
			new_dl_queue = self.sqs_client.create_queue(
			    QueueName = name+'_dl_queue',
			    Attributes={
			        'RedrivePolicy': json.dumps({ 'maxReceiveCount': 100, 'deadLetterTargetArn': associated_queue })
			    })
			queue_url = new_dl_queue['QueueUrl']
			new_queue_attrs = self.sqs_client.get_queue_attributes(
    			QueueUrl=queue_url,
    			AttributeNames=['QueueArn'])
		except ClientError as e:
			print "Could not create Dead Letter Queue with name: "+name+"_dl_queue"
			return False			
		else:
			print "Dead Letter Queue "+name+"_queue created successfully"
			return {"queue_url":queue_url, "queue_arn": new_queue_attrs['Attributes']['QueueArn']}

	def add_retrieve_delete_permision(self, queue, access_key, secret_key):
		
		try:
			account_id = get_account_id(access_key, secret_key)
			new_permission = self.sqs_client.add_permission(
			    QueueUrl=queue,
			    Label=str(queue)+":"+str(account_id)+":sqs:retrieve:delete",
			    AWSAccountIds=[account_id],
			    Actions=['ReceiveMessage', 'DeleteMessage'])
		except ClientError as e:
			print "Could not give retrieve/delete permissions to "+queue  
		else:
			print "Retrieve/Delete permissions given successfully to "+queue

def get_account_id(access_key, secret_key):

	try:
		client = boto3.client("sts", region_name='eu-central-1', 
			aws_access_key_id=access_key, aws_secret_access_key=secret_key)
	except ClientError as e:
		print "Could not retrieve AWS Acoount ID"
		return False
	else:
		return client.get_caller_identity()["Account"]