import logging
import time

from rest_framework_bulk import BulkListSerializer, BulkSerializerMixin
from rest_framework_mongoengine.serializers import DocumentSerializer, EmbeddedDocumentSerializer
from workflows.models import Action, TaskAction, TaskActionParameters, Prep, Site, Task, TaskSiteStatus, Reason, \
    TaskPrep, Workflow

logger = logging.getLogger(__name__)


# Actions

def get_list_values(key, data):
    return sorted(data.get(key, []))


def save_action(data):
    action = None

    if 'id' in data:
        # Get action by id (currently frontend does not send id, but it will be used in the future)
        action = Action.objects(id=data['id']).first()
    else:
        # If no action, then try to find equal entry
        action = Action.objects(
            action=data.action,
            xrootd=data.xrootd,
            cores=data.cores,
            secondary=data.secondary,
            splitting=data.splitting,
            group=data.group,
            sites=data.sites,
            reasons=data.reasons,
        ).first()

    # If no similar entry exist, then create new one
    if not action:
        action = Action(
            action=data.action,
            xrootd=data.xrootd,
            cores=data.cores,
            secondary=data.secondary,
            splitting=data.splitting,
            group=data.group,
            sites=data.sites,
            reasons=data.reasons,
        )
        action.save()

    return action


def save_new_reasons(reasons):
    for text in reasons:
        reason = Reason.objects(text=text)

        if not reason:
            Reason(text=text).save()


class TaskActionParametersSerializer(EmbeddedDocumentSerializer):
    class Meta:
        model = TaskActionParameters
        fields = '__all__'


def set_action_to_task(filter_task_name, task, task_action):
    if (task.name == filter_task_name):
        task.task_action = task_action
    return task

def set_action_to_tasks(filter_task_name, workflow, task_action):
    workflow.tasks = list(map(lambda task: set_action_to_task(filter_task_name, task, task_action), workflow.tasks))
    return workflow


class TaskActionSerializer(BulkSerializerMixin, DocumentSerializer):
    parameters = TaskActionParametersSerializer()

    class Meta:
        model = TaskAction
        fields = '__all__'
        depth = 1
        list_serializer_class = BulkListSerializer

    def create(self, validated_data):
        action_data = validated_data.pop('parameters')
        action = save_action(action_data)

        task_action = TaskAction(
            acted=0,
            timestamp=time.time(),
            parameters=action_data,
            **validated_data
        )
        task_action.save()
        save_new_reasons(action.reasons)

        # Ugly task action reference insert as mongo does not support multiple positional args ($)
        preps = Prep.objects(workflows__tasks__name=task_action.name)
        for prep in preps:
            prep.workflows = list(map(lambda wf: set_action_to_tasks(task_action.name, wf, task_action), prep.workflows))
            prep.save()

        return task_action


# Tasks

class TaskSiteStatusSerializer(EmbeddedDocumentSerializer):
    class Meta:
        model = TaskSiteStatus
        fields = '__all__'


class TaskPrepSerializer(EmbeddedDocumentSerializer):
    class Meta:
        model = TaskPrep
        fields = '__all__'


class TaskSerializer(EmbeddedDocumentSerializer):
    prep = TaskPrepSerializer()
    statuses = TaskSiteStatusSerializer(many=True)
    task_action = TaskActionSerializer()

    class Meta:
        model = Task
        fields = '__all__'
        depth = 1


class WorkflowSerializer(EmbeddedDocumentSerializer):
    tasks = TaskSerializer(many=True)

    class Meta:
        model = Workflow
        fields = '__all__'


class PrepSerializer(EmbeddedDocumentSerializer):
    workflows = WorkflowSerializer(many=True)

    class Meta:
        model = Prep
        fields = '__all__'


# Sites

class SiteSerializer(DocumentSerializer):
    class Meta:
        model = Site
        fields = '__all__'
