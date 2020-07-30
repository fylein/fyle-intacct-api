from typing import Dict

from .models import GeneralMapping


class MappingUtils:
    def __init__(self, workspace_id):
        self.__workspace_id = workspace_id

    def create_or_update_general_mapping(self, general_mapping: Dict):
        """
        Create or update general mapping
        :param general_mapping: general mapping payload
        :return:
        """
        general_mapping, _ = GeneralMapping.objects.update_or_create(
            workspace_id=self.__workspace_id,
            defaults={
                'default_location_name': general_mapping.get('default_location_name') \
                    if general_mapping.get('default_location_name') else None,
                'default_location_id': general_mapping.get('default_location_id') \
                    if general_mapping.get('default_location_id') else None,
                'default_department_name': general_mapping.get('default_department_name') \
                    if general_mapping.get('default_department_name') else None,
                'default_department_id': general_mapping.get('default_department_id') \
                    if general_mapping.get('default_department_id') else None,
                'default_project_name': general_mapping.get('default_project_name') \
                    if general_mapping.get('default_project_name') else None,
                'default_project_id': general_mapping.get('default_project_id') \
                    if general_mapping.get('default_project_id') else None
            }
        )
        return general_mapping
