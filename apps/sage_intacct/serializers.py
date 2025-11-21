from fyle_accounting_mappings.models import DestinationAttribute
from rest_framework import serializers

from apps.sage_intacct.models import (
    Bill,
    BillLineitem,
    ChargeCardTransaction,
    ChargeCardTransactionLineitem,
    ExpenseReport,
    ExpenseReportLineitem,
    SageIntacctAttributesCount,
)


class BillSerializer(serializers.ModelSerializer):
    """
    Sage Intacct Bill serializer
    """
    class Meta:
        model = Bill
        fields = '__all__'


class BillLineitemsSerializer(serializers.ModelSerializer):
    """
    Sage Intacct Bill Lineitems serializer
    """
    class Meta:
        model = BillLineitem
        fields = '__all__'


class ExpenseReportSerializer(serializers.ModelSerializer):
    """
    Sage Intacct ExpenseReport serializer
    """
    class Meta:
        model = ExpenseReport
        fields = '__all__'


class ExpenseReportLineitemsSerializer(serializers.ModelSerializer):
    """
    Sage Intacct ExpenseReport Lineitems serializer
    """
    class Meta:
        model = ExpenseReportLineitem
        fields = '__all__'


class ChargeCardTransactionSerializer(serializers.ModelSerializer):
    """
    Sage Intacct ChargeCardTransaction serializer
    """
    class Meta:
        model = ChargeCardTransaction
        fields = '__all__'


class ChargeCardTransactionLineitemsSerializer(serializers.ModelSerializer):
    """
    Sage Intacct ChargeCardTransaction Lineitems serializer
    """
    class Meta:
        model = ChargeCardTransactionLineitem
        fields = '__all__'


class SageIntacctFieldSerializer(serializers.ModelSerializer):
    """
    Expense Fields Serializer
    """
    class Meta:
        model = DestinationAttribute
        fields = ['attribute_type', 'display_name']


class SageIntacctAttributesCountSerializer(serializers.ModelSerializer):
    """
    Serializer for Sage Intacct Attributes Count
    """
    class Meta:
        model = SageIntacctAttributesCount
        exclude = ['user_defined_dimensions_details']
