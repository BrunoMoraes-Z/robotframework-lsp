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


import datetime

_BUILTIN_TYPES = [str, int, float, bool, list, tuple, dict, set, bytes, datetime.date]


def _gather_type_names(completion_context: ICompletionContext) -> List[str]:
    """Return only builtin type names."""
    return sorted({t.__name__ for t in _BUILTIN_TYPES})


def _matches_context(prefix: str) -> bool:
    import re

    if re.search(r"\$\{[^}:]+:\s+$", prefix):
        return True
    if re.search(r"\bVAR\s+[^:=]+:\s+$", prefix):
        return True
    return False


def complete(completion_context: ICompletionContext) -> List[CompletionItemTypedDict]:
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
                    start=Position(completion_context.sel.line, completion_context.sel.col),
                    end=Position(completion_context.sel.line, completion_context.sel.col),
                ),
                name,
            ),
            insertTextFormat=InsertTextFormat.PlainText,
        )
        ret.append(ci.to_dict())
    return ret
