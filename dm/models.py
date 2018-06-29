from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractUser
from django.conf import settings

from django.core.validators import MinValueValidator, MaxValueValidator

from .choices import *

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

import string
import random

channel_layer = get_channel_layer()


class User(AbstractUser):
    def __str__(self):
        return "%s %s" % (self.first_name, self.last_name)

    ws_channel = models.CharField(max_length=255, blank=True)

class oTreeInstance(models.Model):
    class Meta:
        permissions = (
            ('can_restart', "Can restart the oTree instance"),
            ('can_reset', "Can reset otree database"),
        )

    name = models.CharField(
        max_length=32, 
        validators=[
            RegexValidator(regex='^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$', 
                message='name is not suitable',
                code='invalid')
        ]
    )
    owned_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Experimenter")    
    
    deployed = models.BooleanField(default=False)
    git_sha = models.CharField(max_length=200, blank=True)
    deploy_source = models.CharField(max_length=200, blank=True)
    app_dir = models.CharField(max_length=200, blank=True)

    otree_admin_username = models.CharField(max_length=200, blank=True)
    otree_admin_password = models.CharField(max_length=200, blank=True)
    otree_auth_level = models.CharField(max_length=200, blank=True)
    otree_production = models.IntegerField(null=True, blank=True)

    web_dynos = models.PositiveSmallIntegerField(validators=[MinValueValidator(1),
                                       MaxValueValidator(settings.MAX_WEB)], default=1)
    worker_dynos = models.PositiveSmallIntegerField(validators=[MinValueValidator(settings.MIN_WORKERS),
                                       MaxValueValidator(settings.MAX_WORKERS)], default=1)

    def __str__(self):
        return self.name

    def git_url(self):
        git_url = "dokku@%s:%s" % (settings.DOKKU_DOMAIN, self.name)
        return git_url

    def url(self):
        return "http://%s.%s" % (self.name, settings.DOKKU_DOMAIN
)
    def refresh_from_dokku(self, user_id):
        async_to_sync(channel_layer.send)(
            "dokku_tasks",
            {
                "type": "update.app.report",
                "user_id": user_id,
                "instance_name": self.name
            },
        )

    def scale_dokku_app(self, user_id=-1):
        dyno_dict = {
            'web': str(self.web_dynos),
            'worker': str(self.worker_dynos),
        }
        async_to_sync(channel_layer.send)(
            "dokku_tasks", 
            {
                'type': 'scale_app',
                'instance_name': self.name,
                'user_id': user_id,
                'var_dict': dyno_dict,
            }
        )


    def create_dokku_app(self, user_id):
        async_to_sync(channel_layer.send)(
            "dokku_tasks",
            {
                "type": "create.app",
                "user_id": user_id,
                "instance_name": self.name
            },
        )

    def restart_dokku_app(self, user_id):
        async_to_sync(channel_layer.send)(
            "dokku_tasks",
            {
                "type": "restart.app",
                "user_id": user_id,
                "instance_name": self.name
            },
        )

    def destroy_dokku_app(self, user_id, delete_self=True):
        async_to_sync(channel_layer.send)(
            "dokku_tasks",
            {
                "type": "destroy.app",
                "user_id": user_id,
                "instance_name": self.name
            },
        )
        num_delete, _ = self.delete()
        
    def set_default_environment(self, user_id=-1):
        self.otree_production = 1
        self.otree_admin_username = "admin"
        self.otree_admin_password = self._get_random_password()
        self.otree_auth_level = "STUDY"
        self.save()

        self.set_environment(user_id)       


    def set_environment(self, user_id=-1):
        print('set env')
        env_vars_dict = {
            'OTREE_PRODUCTION': self.otree_production,
            'OTREE_ADMIN_USERNAME': self.otree_admin_username,
            'OTREE_ADMIN_PASSWORD': self.otree_admin_password,
            'OTREE_AUTH_LEVEL': self.otree_auth_level
        }

        async_to_sync(channel_layer.send)(
            "dokku_tasks",
            {
                "type": "set.env",
                "user_id": user_id,
                "instance_name": self.name,
                "var_dict": env_vars_dict
            },
        )


    def reset_database(self, user_id):
        async_to_sync(channel_layer.send)(
            "dokku_tasks",
            {
                "type": "reset.database",
                "user_id": user_id,
                "instance_name": self.name
            },
        )

       
    def _get_random_password(self, length=20, chars=string.ascii_letters + string.digits):
        return "".join(random.choice(chars) for i in range(length))
