from enum import Enum
from typing import Union


def add_system_comment(
    system_comments: list | None,
    source: Union[Enum, str],
    intent: Union[Enum, str],
    entity_type: Union[Enum, str],
    workspace_id: int,
    entity_id: int = None,
    export_type: Union[Enum, str] = None,
    is_user_visible: bool = False,
    reason: Union[Enum, str] = None,
    info: dict = None
) -> None:
    """
    Add a system comment to the list

    :param system_comments: list of system comments
    :param source: source of the system comment
    :param intent: intent of the system comment
    :param entity_type: entity type of the system comment
    :param workspace_id: workspace id
    :param entity_id: entity id
    :param export_type: export type of the system comment
    :param is_user_visible: whether the system comment is user visible
    :param reason: reason of the system comment
    :param info: info of the system comment
    :return: None
    """
    if system_comments is None:
        return

    system_comments.append({
        'workspace_id': workspace_id,
        'source': source.value if isinstance(source, Enum) else source,
        'intent': intent.value if isinstance(intent, Enum) else intent,
        'entity_type': entity_type.value if isinstance(entity_type, Enum) else entity_type,
        'entity_id': entity_id,
        'export_type': export_type.value if isinstance(export_type, Enum) else export_type,
        'is_user_visible': is_user_visible,
        'detail': {
            'reason': reason.value if isinstance(reason, Enum) else reason,
            'info': info or {}
        }
    })
