"""
Mapping Models
"""
from django.db import models

from apps.workspaces.models import Workspace


class GeneralMapping(models.Model):
    """
    General Mappings
    """
    id = models.AutoField(primary_key=True)
    default_location_name = models.CharField(max_length=255, help_text='Default location name', null=True)
    default_location_id = models.CharField(max_length=255, help_text='Default location ID', null=True)
    default_department_name = models.CharField(max_length=255, help_text='Default department name', null=True)
    default_department_id = models.CharField(max_length=255, help_text='Default department ID', null=True)
    default_project_name = models.CharField(max_length=255, help_text='Default project name', null=True)
    default_project_id = models.CharField(max_length=255, help_text='Default project ID', null=True)
    workspace = models.ForeignKey(Workspace, on_delete=models.PROTECT, help_text='Reference to Workspace model')
    created_at = models.DateTimeField(auto_now_add=True, help_text='Created at datetime')
    updated_at = models.DateTimeField(auto_now=True, help_text='Updated at datetime')

    class Meta:
        db_table = 'general_mappings'
