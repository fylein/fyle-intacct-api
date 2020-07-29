from rest_framework import serializers

from .models import Bill, BillLineitem, ExpenseReport, ExpenseReportLineitem


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
