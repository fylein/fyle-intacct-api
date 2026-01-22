from apps.workspaces.enums import (
    SystemCommentEntityTypeEnum,
    SystemCommentIntentEnum,
    SystemCommentReasonEnum,
    SystemCommentSourceEnum
)


class SystemCommentHelper:
    """
    Helper class for creating system comments with domain-specific methods
    """

    @staticmethod
    def _create_comment(
        workspace_id: int,
        source: SystemCommentSourceEnum,
        intent: SystemCommentIntentEnum,
        entity_type: SystemCommentEntityTypeEnum,
        entity_id: int = None,
        reason: SystemCommentReasonEnum | str = None,
        info: dict = None
    ) -> dict:
        """
        Create a system comment dict
        :param workspace_id: Workspace ID
        :param source: Source function that generated the comment
        :param intent: Intent describing the action taken
        :param entity_type: Type of entity the comment is associated with
        :param entity_id: ID of the entity
        :param reason: Human readable reason (enum or string)
        :param info: Additional info dict
        :return: System comment dict
        """
        reason_value = reason.value if isinstance(reason, SystemCommentReasonEnum) else reason
        return {
            'workspace_id': workspace_id,
            'source': source,
            'intent': intent,
            'entity_type': entity_type,
            'entity_id': entity_id,
            'detail': {
                'reason': reason_value,
                'info': info or {}
            }
        }

    @staticmethod
    def _add(system_comments: list | None, comment: dict) -> None:
        """
        Add comment to list if not None
        :param system_comments: List to append comment to
        :param comment: Comment dict to append
        :return: None
        """
        if system_comments is not None:
            system_comments.append(comment)

    # Default values applied
    @classmethod
    def add_default_project_applied(
        cls,
        system_comments: list | None,
        workspace_id: int,
        expense_id: int,
        default_project_id: str,
        default_project_name: str
    ) -> None:
        """
        Add system comment for default project applied
        """
        cls._add(system_comments, cls._create_comment(
            workspace_id=workspace_id,
            source=SystemCommentSourceEnum.GET_PROJECT_ID,
            intent=SystemCommentIntentEnum.DEFAULT_VALUE_APPLIED,
            entity_type=SystemCommentEntityTypeEnum.EXPENSE,
            entity_id=expense_id,
            reason=SystemCommentReasonEnum.DEFAULT_PROJECT_APPLIED,
            info={
                'default_project_id': default_project_id,
                'default_project_name': default_project_name
            }
        ))

    @classmethod
    def add_default_department_applied(
        cls,
        system_comments: list | None,
        workspace_id: int,
        expense_id: int,
        default_department_id: str,
        default_department_name: str
    ) -> None:
        """
        Add system comment for default department applied
        """
        cls._add(system_comments, cls._create_comment(
            workspace_id=workspace_id,
            source=SystemCommentSourceEnum.GET_DEPARTMENT_ID,
            intent=SystemCommentIntentEnum.DEFAULT_VALUE_APPLIED,
            entity_type=SystemCommentEntityTypeEnum.EXPENSE,
            entity_id=expense_id,
            reason=SystemCommentReasonEnum.DEFAULT_DEPARTMENT_APPLIED,
            info={
                'default_department_id': default_department_id,
                'default_department_name': default_department_name
            }
        ))

    @classmethod
    def add_default_location_applied(
        cls,
        system_comments: list | None,
        workspace_id: int,
        expense_id: int,
        default_location_id: str,
        default_location_name: str
    ) -> None:
        """
        Add system comment for default location applied
        """
        cls._add(system_comments, cls._create_comment(
            workspace_id=workspace_id,
            source=SystemCommentSourceEnum.GET_LOCATION_ID,
            intent=SystemCommentIntentEnum.DEFAULT_VALUE_APPLIED,
            entity_type=SystemCommentEntityTypeEnum.EXPENSE,
            entity_id=expense_id,
            reason=SystemCommentReasonEnum.DEFAULT_LOCATION_APPLIED,
            info={
                'default_location_id': default_location_id,
                'default_location_name': default_location_name
            }
        ))

    @classmethod
    def add_default_item_applied(
        cls,
        system_comments: list | None,
        workspace_id: int,
        expense_id: int,
        default_item_id: str,
        default_item_name: str
    ) -> None:
        """
        Add system comment for default item applied
        """
        cls._add(system_comments, cls._create_comment(
            workspace_id=workspace_id,
            source=SystemCommentSourceEnum.GET_ITEM_ID,
            intent=SystemCommentIntentEnum.DEFAULT_VALUE_APPLIED,
            entity_type=SystemCommentEntityTypeEnum.EXPENSE,
            entity_id=expense_id,
            reason=SystemCommentReasonEnum.DEFAULT_ITEM_APPLIED,
            info={
                'default_item_id': default_item_id,
                'default_item_name': default_item_name
            }
        ))

    @classmethod
    def add_default_class_applied(
        cls,
        system_comments: list | None,
        workspace_id: int,
        expense_id: int,
        default_class_id: str,
        default_class_name: str
    ) -> None:
        """
        Add system comment for default class applied
        """
        cls._add(system_comments, cls._create_comment(
            workspace_id=workspace_id,
            source=SystemCommentSourceEnum.GET_CLASS_ID,
            intent=SystemCommentIntentEnum.DEFAULT_VALUE_APPLIED,
            entity_type=SystemCommentEntityTypeEnum.EXPENSE,
            entity_id=expense_id,
            reason=SystemCommentReasonEnum.DEFAULT_CLASS_APPLIED,
            info={
                'default_class_id': default_class_id,
                'default_class_name': default_class_name
            }
        ))

    @classmethod
    def add_default_tax_code_applied(
        cls,
        system_comments: list | None,
        workspace_id: int,
        expense_id: int,
        default_tax_code_id: str,
        default_tax_code_name: str
    ) -> None:
        """
        Add system comment for default tax code applied
        """
        cls._add(system_comments, cls._create_comment(
            workspace_id=workspace_id,
            source=SystemCommentSourceEnum.GET_TAX_CODE_ID,
            intent=SystemCommentIntentEnum.DEFAULT_VALUE_APPLIED,
            entity_type=SystemCommentEntityTypeEnum.EXPENSE,
            entity_id=expense_id,
            reason=SystemCommentReasonEnum.DEFAULT_TAX_CODE_APPLIED,
            info={
                'default_tax_code_id': default_tax_code_id,
                'default_tax_code_name': default_tax_code_name
            }
        ))

    @classmethod
    def add_default_ccc_vendor_applied(
        cls,
        system_comments: list | None,
        workspace_id: int,
        expense_group_id: int,
        default_ccc_vendor_id: str,
        default_ccc_vendor_name: str
    ) -> None:
        """
        Add system comment for default CCC vendor applied in bill creation
        """
        cls._add(system_comments, cls._create_comment(
            workspace_id=workspace_id,
            source=SystemCommentSourceEnum.CREATE_BILL,
            intent=SystemCommentIntentEnum.DEFAULT_VALUE_APPLIED,
            entity_type=SystemCommentEntityTypeEnum.EXPENSE_GROUP,
            entity_id=expense_group_id,
            reason=SystemCommentReasonEnum.DEFAULT_CCC_VENDOR_APPLIED,
            info={
                'default_ccc_vendor_id': default_ccc_vendor_id,
                'default_ccc_vendor_name': default_ccc_vendor_name
            }
        ))

    @classmethod
    def add_default_credit_card_applied(
        cls,
        system_comments: list | None,
        workspace_id: int,
        expense_id: int,
        default_charge_card_id: str,
        default_charge_card_name: str
    ) -> None:
        """
        Add system comment for default credit card applied
        """
        cls._add(system_comments, cls._create_comment(
            workspace_id=workspace_id,
            source=SystemCommentSourceEnum.GET_CCC_ACCOUNT_ID,
            intent=SystemCommentIntentEnum.DEFAULT_VALUE_APPLIED,
            entity_type=SystemCommentEntityTypeEnum.EXPENSE,
            entity_id=expense_id,
            reason=SystemCommentReasonEnum.DEFAULT_CREDIT_CARD_APPLIED,
            info={
                'default_charge_card_id': default_charge_card_id,
                'default_charge_card_name': default_charge_card_name
            }
        ))

    # Employee fallback values
    @classmethod
    def add_employee_location_applied(
        cls,
        system_comments: list | None,
        workspace_id: int,
        expense_id: int,
        employee_location_id: str,
        employee_location_name: str
    ) -> None:
        """
        Add system comment for employee location fallback applied
        """
        cls._add(system_comments, cls._create_comment(
            workspace_id=workspace_id,
            source=SystemCommentSourceEnum.GET_LOCATION_ID,
            intent=SystemCommentIntentEnum.EMPLOYEE_DEFAULT_VALUE_APPLIED,
            entity_type=SystemCommentEntityTypeEnum.EXPENSE,
            entity_id=expense_id,
            reason=SystemCommentReasonEnum.EMPLOYEE_LOCATION_APPLIED,
            info={
                'employee_location_id': employee_location_id,
                'employee_location_name': employee_location_name
            }
        ))

    @classmethod
    def add_employee_department_applied(
        cls,
        system_comments: list | None,
        workspace_id: int,
        expense_id: int,
        employee_department_id: str,
        employee_department_name: str
    ) -> None:
        """
        Add system comment for employee department fallback applied
        """
        cls._add(system_comments, cls._create_comment(
            workspace_id=workspace_id,
            source=SystemCommentSourceEnum.GET_DEPARTMENT_ID,
            intent=SystemCommentIntentEnum.EMPLOYEE_DEFAULT_VALUE_APPLIED,
            entity_type=SystemCommentEntityTypeEnum.EXPENSE,
            entity_id=expense_id,
            reason=SystemCommentReasonEnum.EMPLOYEE_DEPARTMENT_APPLIED,
            info={
                'employee_department_id': employee_department_id,
                'employee_department_name': employee_department_name
            }
        ))

    # Fund source & report changes
    @classmethod
    def add_fund_source_changed(
        cls,
        system_comments: list | None,
        workspace_id: int,
        expense_id: int,
        old_fund_source: str,
        new_fund_source: str
    ) -> None:
        """
        Add system comment for expense fund source changed
        """
        reason = SystemCommentReasonEnum.FUND_SOURCE_CHANGED.value.format(
            old=old_fund_source,
            new=new_fund_source
        )
        cls._add(system_comments, cls._create_comment(
            workspace_id=workspace_id,
            source=SystemCommentSourceEnum.HANDLE_FUND_SOURCE_CHANGE,
            intent=SystemCommentIntentEnum.UPDATE_EXPENSE_FUND_SOURCE,
            entity_type=SystemCommentEntityTypeEnum.EXPENSE,
            entity_id=expense_id,
            reason=reason,
            info={
                'old_fund_source': old_fund_source,
                'new_fund_source': new_fund_source
            }
        ))

    @classmethod
    def add_category_changed(
        cls,
        system_comments: list | None,
        workspace_id: int,
        expense_id: int,
        old_category: str,
        new_category: str
    ) -> None:
        """
        Add system comment for expense category changed
        """
        reason = SystemCommentReasonEnum.CATEGORY_CHANGED.value.format(
            old=old_category,
            new=new_category
        )
        cls._add(system_comments, cls._create_comment(
            workspace_id=workspace_id,
            source=SystemCommentSourceEnum.HANDLE_CATEGORY_CHANGE,
            intent=SystemCommentIntentEnum.UPDATE_EXPENSE_CATEGORY,
            entity_type=SystemCommentEntityTypeEnum.EXPENSE,
            entity_id=expense_id,
            reason=reason,
            info={
                'old_category': old_category,
                'new_category': new_category
            }
        ))

    @classmethod
    def add_expense_added_to_report(
        cls,
        system_comments: list | None,
        workspace_id: int,
        report_id: str,
        fyle_expense_id: str = None
    ) -> None:
        """
        Add system comment for expense added to report
        """
        info = {'report_id': report_id}
        if fyle_expense_id:
            info['expense_id'] = fyle_expense_id
        cls._add(system_comments, cls._create_comment(
            workspace_id=workspace_id,
            source=SystemCommentSourceEnum.HANDLE_REPORT_CHANGE,
            intent=SystemCommentIntentEnum.UPDATE_EXPENSE_REPORT,
            entity_type=SystemCommentEntityTypeEnum.EXPENSE,
            entity_id=None,
            reason=SystemCommentReasonEnum.EXPENSE_ADDED_TO_REPORT,
            info=info
        ))

    @classmethod
    def add_expense_ejected_from_report(
        cls,
        system_comments: list | None,
        workspace_id: int,
        expense_id: int,
        report_id: str,
        is_expense_group_deleted: bool = False
    ) -> None:
        """
        Add system comment for expense ejected from report
        """
        cls._add(system_comments, cls._create_comment(
            workspace_id=workspace_id,
            source=SystemCommentSourceEnum.HANDLE_REPORT_CHANGE,
            intent=SystemCommentIntentEnum.UPDATE_EXPENSE_REPORT,
            entity_type=SystemCommentEntityTypeEnum.EXPENSE,
            entity_id=expense_id,
            reason=SystemCommentReasonEnum.EXPENSE_EJECTED_FROM_REPORT,
            info={
                'report_id': report_id,
                'is_expense_group_deleted': is_expense_group_deleted
            }
        ))

    @classmethod
    def add_expense_groups_recreated(
        cls,
        system_comments: list | None,
        workspace_id: int,
        expense_count: int,
        expense_ids: list,
        skipped_expense_ids: list
    ) -> None:
        """
        Add system comment for expense groups recreated
        """
        cls._add(system_comments, cls._create_comment(
            workspace_id=workspace_id,
            source=SystemCommentSourceEnum.RECREATE_EXPENSE_GROUPS,
            intent=SystemCommentIntentEnum.RECREATE_EXPENSE_GROUPS,
            entity_type=SystemCommentEntityTypeEnum.EXPENSE_GROUP,
            entity_id=None,
            reason=SystemCommentReasonEnum.EXPENSE_GROUPS_RECREATED,
            info={
                'expense_count': expense_count,
                'expense_ids': expense_ids,
                'skipped_expense_ids': skipped_expense_ids
            }
        ))

    @classmethod
    def add_expense_group_deleted(
        cls,
        system_comments: list | None,
        workspace_id: int,
        expense_group_id: int
    ) -> None:
        """
        Add system comment for expense group deleted
        """
        cls._add(system_comments, cls._create_comment(
            workspace_id=workspace_id,
            source=SystemCommentSourceEnum.DELETE_EXPENSE_GROUP_AND_RELATED_DATA,
            intent=SystemCommentIntentEnum.DELETE_EXPENSE_GROUP,
            entity_type=SystemCommentEntityTypeEnum.EXPENSE_GROUP,
            entity_id=expense_group_id,
            reason=SystemCommentReasonEnum.EXPENSE_GROUP_AND_RELATED_DATA_DELETED,
            info={}
        ))

    @classmethod
    def add_expenses_deleted(
        cls,
        system_comments: list | None,
        workspace_id: int,
        expense_ids: list,
        fund_source: str = None
    ) -> None:
        """
        Add system comment for expenses deleted due to no export setting
        """
        info = {'expense_ids': expense_ids}
        if fund_source:
            info['fund_source'] = fund_source
        cls._add(system_comments, cls._create_comment(
            workspace_id=workspace_id,
            source=SystemCommentSourceEnum.DELETE_EXPENSES,
            intent=SystemCommentIntentEnum.DELETE_EXPENSES,
            entity_type=SystemCommentEntityTypeEnum.EXPENSE,
            entity_id=None,
            reason=SystemCommentReasonEnum.EXPENSES_DELETED_NO_EXPORT_SETTING,
            info=info
        ))

    # Vendor handling
    @classmethod
    def add_credit_card_misc_vendor_applied(
        cls,
        system_comments: list | None,
        workspace_id: int,
        expense_id: int,
        source: SystemCommentSourceEnum,
        original_merchant: str
    ) -> None:
        """
        Add system comment for Credit Card Misc vendor fallback applied
        """
        cls._add(system_comments, cls._create_comment(
            workspace_id=workspace_id,
            source=source,
            intent=SystemCommentIntentEnum.DEFAULT_VALUE_APPLIED,
            entity_type=SystemCommentEntityTypeEnum.EXPENSE,
            entity_id=expense_id,
            reason=SystemCommentReasonEnum.CREDIT_CARD_MISC_VENDOR_APPLIED,
            info={
                'original_merchant': original_merchant,
                'vendor_used': 'Credit Card Misc'
            }
        ))

    @classmethod
    def add_vendor_not_found_for_reimbursable(
        cls,
        system_comments: list | None,
        workspace_id: int,
        expense_id: int,
        merchant: str
    ) -> None:
        """
        Add system comment for vendor not found for reimbursable expense
        """
        cls._add(system_comments, cls._create_comment(
            workspace_id=workspace_id,
            source=SystemCommentSourceEnum.CREATE_EXPENSE_REPORT_LINEITEMS,
            intent=SystemCommentIntentEnum.VENDOR_NOT_FOUND,
            entity_type=SystemCommentEntityTypeEnum.EXPENSE,
            entity_id=expense_id,
            reason=SystemCommentReasonEnum.VENDOR_NOT_FOUND_FOR_REIMBURSABLE,
            info={
                'merchant': merchant
            }
        ))

    # Expense skipping & filtering
    @classmethod
    def add_negative_expense_skipped(
        cls,
        system_comments: list | None,
        workspace_id: int,
        expense_id: int,
        amount: float,
        is_grouped_by_expense: bool
    ) -> None:
        """
        Add system comment for negative expense skipped
        """
        reason = SystemCommentReasonEnum.NEGATIVE_EXPENSE_SKIPPED if is_grouped_by_expense else SystemCommentReasonEnum.NEGATIVE_REPORT_TOTAL_SKIPPED
        cls._add(system_comments, cls._create_comment(
            workspace_id=workspace_id,
            source=SystemCommentSourceEnum.FILTER_EXPENSE_GROUPS,
            intent=SystemCommentIntentEnum.SKIP_EXPENSE,
            entity_type=SystemCommentEntityTypeEnum.EXPENSE,
            entity_id=expense_id,
            reason=reason,
            info={
                'amount': amount,
                'is_grouped_by_expense': is_grouped_by_expense
            }
        ))

    @classmethod
    def add_expense_filter_rule_applied(
        cls,
        system_comments: list | None,
        workspace_id: int,
        expense_id: int
    ) -> None:
        """
        Add system comment for expense skipped due to filter rules
        """
        cls._add(system_comments, cls._create_comment(
            workspace_id=workspace_id,
            source=SystemCommentSourceEnum.GROUP_EXPENSES_AND_SAVE,
            intent=SystemCommentIntentEnum.SKIP_EXPENSE,
            entity_type=SystemCommentEntityTypeEnum.EXPENSE,
            entity_id=expense_id,
            reason=SystemCommentReasonEnum.EXPENSE_SKIPPED_AFTER_IMPORT,
            info={}
        ))

    @classmethod
    def add_reimbursable_expense_not_configured(
        cls,
        system_comments: list | None,
        workspace_id: int,
        expense_id: int
    ) -> None:
        """
        Add system comment for reimbursable expense skipped due to settings not configured
        """
        cls._add(system_comments, cls._create_comment(
            workspace_id=workspace_id,
            source=SystemCommentSourceEnum.GROUP_EXPENSES_AND_SAVE,
            intent=SystemCommentIntentEnum.SKIP_EXPENSE,
            entity_type=SystemCommentEntityTypeEnum.EXPENSE,
            entity_id=expense_id,
            reason=SystemCommentReasonEnum.REIMBURSABLE_EXPENSE_NOT_CONFIGURED,
            info={}
        ))

    @classmethod
    def add_ccc_expense_not_configured(
        cls,
        system_comments: list | None,
        workspace_id: int,
        expense_id: int
    ) -> None:
        """
        Add system comment for CCC expense skipped due to settings not configured
        """
        cls._add(system_comments, cls._create_comment(
            workspace_id=workspace_id,
            source=SystemCommentSourceEnum.GROUP_EXPENSES_AND_SAVE,
            intent=SystemCommentIntentEnum.SKIP_EXPENSE,
            entity_type=SystemCommentEntityTypeEnum.EXPENSE,
            entity_id=expense_id,
            reason=SystemCommentReasonEnum.CCC_EXPENSE_NOT_CONFIGURED,
            info={}
        ))

    @classmethod
    def add_export_skipped_mapping_errors(
        cls,
        system_comments: list | None,
        workspace_id: int,
        expense_group_id: int,
        error_id: int = None,
        error_type: str = None
    ) -> None:
        """
        Add system comment for export skipped due to unresolved mapping errors
        """
        info = {}
        if error_id:
            info['error_id'] = error_id
        if error_type:
            info['error_type'] = error_type

        cls._add(system_comments, cls._create_comment(
            workspace_id=workspace_id,
            source=SystemCommentSourceEnum.VALIDATE_FAILING_EXPORT,
            intent=SystemCommentIntentEnum.SKIP_EXPORT,
            entity_type=SystemCommentEntityTypeEnum.EXPENSE_GROUP,
            entity_id=expense_group_id,
            reason=SystemCommentReasonEnum.UNRESOLVED_MAPPING_ERRORS,
            info=info
        ))
