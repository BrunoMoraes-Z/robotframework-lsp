from typing import List, Set
import ast

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


_BUILTIN_TYPES = [str, int, float, bool, list, tuple, dict, set, bytes]


def _gather_type_names(completion_context: ICompletionContext) -> List[str]:
    names: Set[str] = {t.__name__ for t in _BUILTIN_TYPES}
    ws = completion_context.workspace
    if ws is not None:
        for uri in ws.iter_all_doc_uris_in_workspace((".py",)):
            doc = ws.get_document(uri, accept_from_file=True)
            if not doc:
                continue
            try:
                tree = ast.parse(doc.source)
            except Exception:
                continue
            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    names.add(node.name)
    return sorted(names)


def _matches_context(prefix: str) -> bool:
    import re

    if re.search(r"\$\{[^}:]+:$", prefix):
        return True
    if re.search(r"\bVAR\s+[^:=]+:$", prefix):
        return True
    return False


def complete(completion_context: ICompletionContext) -> List[CompletionItemTypedDict]:
    line = completion_context.doc.get_line(completion_context.sel.line)
    prefix = line[: completion_context.sel.col]
    if not prefix.endswith(":"):
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
