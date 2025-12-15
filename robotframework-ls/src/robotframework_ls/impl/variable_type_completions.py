from typing import List, Set

from robocorp_ls_core.lsp import (
    CompletionItem,
    CompletionItemKind,
    InsertTextFormat,
    Position,
    Range,
    TextEdit,
    CompletionItemTypedDict,
)
from robotframework_ls.impl.protocols import ICompletionContext
from robotframework_ls.impl.robot_version import (
    robot_version_supports_secret_variables,
    robot_version_supports_variable_types,
)


import datetime

_BUILTIN_TYPES = [
    str,
    int,
    float,
    bool,
    list,
    tuple,
    dict,
    set,
    bytes,
    bytearray,
    object,
    datetime.date,
    datetime.datetime,
]


def _gather_type_names(completion_context: ICompletionContext) -> List[str]:
    """Return only builtin type names."""
    type_names = {t.__name__ for t in _BUILTIN_TYPES}

    if robot_version_supports_secret_variables():
        try:
            from robot.api.types import Secret
        except Exception:
            # If Robot Framework is not available or is older than 7.4, just skip it.
            pass
        else:
            type_names.add(Secret.__name__)

    return sorted(type_names)


def _matches_context(prefix: str) -> bool:
    import re

    if re.search(r"\$\{[^}:]+:\s+$", prefix):
        return True
    if re.search(r"\bVAR\s+[^:=]+:\s+$", prefix):
        return True
    return False


def complete(completion_context: ICompletionContext) -> List[CompletionItemTypedDict]:
    if not robot_version_supports_variable_types():
        return []
    line = completion_context.doc.get_line(completion_context.sel.line)
    prefix = line[: completion_context.sel.col]
    if ":" not in prefix:
        return []

    if not _matches_context(prefix):
        return []

    type_names = _gather_type_names(completion_context)
    ret: List[CompletionItemTypedDict] = []
    for name in type_names:
        ci = CompletionItem(
            label=name,
            kind=CompletionItemKind.Class,
            text_edit=TextEdit(
                Range(
                    start=Position(
                        completion_context.sel.line, completion_context.sel.col
                    ),
                    end=Position(
                        completion_context.sel.line, completion_context.sel.col
                    ),
                ),
                name,
            ),
            insertTextFormat=InsertTextFormat.PlainText,
        )
        ret.append(ci.to_dict())
    return ret
