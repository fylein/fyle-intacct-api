from django.db.models import Q
from apps.workspaces.models import Workspace
from fyle_accounting_mappings.models import DestinationAttribute, MappingSetting


wrong_attributes = {
    254: {
        "objectName": "WORK_LOCATION_UDD",
        "objectLabel": "Work Location",
    },
    255: {
        "objectName": "WORK_LOCATION_UDD",
        "objectLabel": "Work Location",
    },
    256: {
        "objectName": "WORK_LOCATION_UDD",
        "objectLabel": "Work Location",
    },
    537: {
        "objectName": "UDD_RESTRICTION",
        "objectLabel": "Restriction",
    },
    635: {
        "objectName": "RESTRICTION_UDD",
        "objectLabel": "Restriction",
    },
    640: {
        "objectName": "RESTRICTION_UDD",
        "objectLabel": "Restriction",
    },
}

for workspace_id, attributes in wrong_attributes.items():
    formatted_attribute_type = attributes["objectLabel"].upper().replace(" ", "_")

    DestinationAttribute.objects.filter(
        workspace_id=workspace_id, attribute_type=attributes["objectName"]
    ).update(
        attribute_type=formatted_attribute_type, display_name=attributes["objectLabel"]
    )

    MappingSetting.objects.filter(
        workspace_id=workspace_id, destination_field=attributes["objectName"]
    ).update(destination_field=formatted_attribute_type)
