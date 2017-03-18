from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.views.generic.detail import DetailView

from forms import StackForm
from models import Queue, IAM, Topic, Stack

from aws import Notification, SimpleQueue, AccessManagement


class StackDetailView(DetailView):

    model = Stack

def index(request):
	stack_objs = Stack.objects.all()
	context = {'stacks' : stack_objs}
	return render(request, 'all_stacks.html', context)

def get(request, stackid):
	print "get"

def form(request):
	if request.method == 'GET':
		form = StackForm()
	else:
		form = StackForm(request.POST)
	if form.is_valid():
		name = form.cleaned_data['name']
		if new_stack(request, name):
			messages.success(request, "Stack created succesfully!")
		return HttpResponseRedirect("/");
	# post = Posts.objects.create(title=title,body=body,userId = request.user)
	# return HttpResponseRedirect("/posts/"+str(post.id))
	return render(request, 'new_stack.html', {'form': form})

def new_stack(request, stack_name):
	queue = SimpleQueue()
	notification = Notification()
	access_mng = AccessManagement()

	queue_info = queue.create(stack_name)
	topic_arn = notification.create_topic(stack_name)

	if queue and topic_arn:
		topic_obj = Topic.objects.create(name=stack_name+'_topic', arn=topic_arn)
		queue_obj = Queue.objects.create(name=stack_name+'_queue', arn=queue_info['queue_arn'], url=queue_info['queue_url'])

		dl_queue_info = queue.create_dead_letter(stack_name, queue_info['queue_arn'])
		subscription = notification.subscribe(topic_arn, queue_info['queue_arn'])

		if subscription:
			dl_queue_obj = Queue.objects.create(name=stack_name+'_dl_queue', 
				arn=dl_queue_info['queue_arn'], url=dl_queue_info['queue_url'])

			notification.set_raw_delivary(subscription)
			poster = access_mng.create_user_keys(stack_name, "_sns_poster")
			retriever = access_mng.create_user_keys(stack_name, "_sqs_retriever")
			
			if poster and retriever:
				notification.add_publish_permision(topic_arn, poster['AccessKeyId'], poster['SecretAccessKey'])
				poster_obj = IAM.objects.create(name=stack_name+'_poster', 
					access_key_id=poster['AccessKeyId'], secret_key=poster['SecretAccessKey'])

				queue.add_retrieve_delete_permision(queue_info['queue_url'], retriever['AccessKeyId'], retriever['SecretAccessKey'])
				queue.add_retrieve_delete_permision(dl_queue_info['queue_url'], retriever['AccessKeyId'], retriever['SecretAccessKey'])
				retriever_obj = IAM.objects.create(name=stack_name+'_retriever', 
					access_key_id=retriever['AccessKeyId'], secret_key=retriever['SecretAccessKey'])

				new_stack = Stack.objects.create(name=stack_name, topic=topic_obj,
					queue=queue_obj, dl_queue=dl_queue_obj, poster=poster_obj, retriever=retriever_obj)
				return True
			else:
				messages.warning(request, "Could not create users!")
		else:
			messages.warning(request, "Could not create subscribe Queue to Topic!")
	else:
		messages.warning(request, "Could not create queue or topic!")

	return False