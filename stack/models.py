from __future__ import unicode_literals

from django.db import models

# Create your models here.
class Queue(models.Model):
	id = models.AutoField(primary_key=True)
	name = models.TextField(max_length=100)
	url = models.TextField(max_length=512)
	arn = models.TextField(max_length=512)

class IAM(models.Model):
	id = models.AutoField(primary_key=True)
	name = models.TextField(max_length=100)
	access_key_id = models.TextField(max_length=512)
	secret_key = models.TextField(max_length=512)

class Topic(models.Model):
	id = models.AutoField(primary_key=True)
	name = models.TextField(max_length=100)
	arn = models.TextField(max_length=512)

class Stack(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    topic = models.ForeignKey(Topic)
    queue = models.ForeignKey(Queue, related_name="queue_fk")
    dl_queue = models.ForeignKey(Queue, related_name="dl_queue_fk")
    poster = models.ForeignKey(IAM, related_name="poster_fk")
    retriever = models.ForeignKey(IAM, related_name="retriever_fk")

