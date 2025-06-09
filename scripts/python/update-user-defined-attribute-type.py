from django.db.models import Q
from apps.workspaces.models import Workspace
from fyle_accounting_mappings.models import MappingSetting, DestinationAttribute
from apps.workspaces.models import SageIntacctCredential
from apps.sage_intacct.utils import SageIntacctConnector

default_destination_attributes = {
    'DEPARTMENT', 'LOCATION', 'PROJECT', 'EXPENSE_TYPE', 'CHARGE_CARD_NUMBER',
    'VENDOR', 'ACCOUNT', 'CCC_ACCOUNT', 'CUSTOMER', 'TASK', 'COST_TYPE', 'ALLOCATION', 'EMPLOYEE', 'CLASS',
    'ITEM', 'COSTTYPE'
}

workspaces = Workspace.objects.filter(~Q(name__icontains='fyle for') & ~Q(name__icontains='test')).order_by('id')

attributes_to_update = []
mapping_settings_to_update = []

for workspace in workspaces:
    sage_intacct_credentials = SageIntacctCredential.objects.filter(workspace_id=workspace.id).first()
    if sage_intacct_credentials:
        try:
            sage_intacct_connection = SageIntacctConnector(credentials_object=sage_intacct_credentials, workspace_id=workspace.id)
            dimensions = sage_intacct_connection.connection.dimensions.get_all()    
            for dimension in dimensions:
                if dimension['objectName'] not in default_destination_attributes and dimension['userDefinedDimension'] == 'true':
                    object_label = dimension['objectLabel'].replace(' ', '_').upper()
                    object_name = dimension['objectName'].replace(' ', '_').upper()
                    if object_name != object_label:
                        print("workspace_id",workspace.id)
                        print(f"Object Name: {dimension['objectName']}")
                        print(f"Object Label: {dimension['objectLabel']}")
                        print(f"Term Label: {dimension['termLabel']}")
                        attribute = DestinationAttribute.objects.filter(workspace_id=workspace.id, attribute_type=object_label).exists()
                        print(f"Object Label Exists: {attribute}")
                        if attribute:
                            print(f"Updating {object_label} in Destination Attributes to {dimension['objectName']}")
                            attributes_to_update.append({
                                    'workspace_id': workspace.id,
                                    'attribute_type': object_label,
                                    'new_attribute_type': object_name
                            })
                        mapping_settings_exists = MappingSetting.objects.filter(workspace_id=workspace.id, destination_field=object_label).exists()
                        print(f"Mapping Settings Exists: {mapping_settings_exists}")
                        if mapping_settings_exists:
                            mapping_settings_to_update.append({
                                'workspace_id': workspace.id,
                                'destination_field': object_label,
                                'new_destination_field': object_name
                            })
                        print("-" * 40)
        except Exception as e:
            print('Error while fetching dimensions', e)

print("Attributes to Update", attributes_to_update)
print("Mapping Settings to Update", mapping_settings_to_update)

if attributes_to_update:
    for attribute in attributes_to_update:  
        dest_attrs = DestinationAttribute.objects.filter(  
            workspace_id=attribute['workspace_id'],  
            attribute_type=attribute['attribute_type']  
        )  
        for dest_attr in dest_attrs:  
            dest_attr.attribute_type = attribute['new_attribute_type']  
        
        DestinationAttribute.objects.bulk_update(dest_attrs, ['attribute_type']) 

if mapping_settings_to_update:
    for mapping_setting in mapping_settings_to_update:  
        mapping_settings = MappingSetting.objects.filter(  
            workspace_id=mapping_setting['workspace_id'],  
            destination_field=mapping_setting['destination_field']  
        ) 
        for ms in mapping_settings:  
            ms.destination_field = mapping_setting['new_destination_field']  
    
        MappingSetting.objects.bulk_update(  
            mapping_settings,  
            ['destination_field']  
        )  