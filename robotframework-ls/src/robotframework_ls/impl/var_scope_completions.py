from typing import List
from robocorp_ls_core.lsp import CompletionItem, CompletionItemKind, InsertTextFormat, Position, Range, TextEdit
from robotframework_ls.impl.protocols import ICompletionContext

_SCOPES = ("GLOBAL", "SUITE", "TEST", "TASK", "LOCAL")


def complete(completion_context: ICompletionContext) -> List[dict]:
    sel = completion_context.sel
    doc = completion_context.doc
    line = doc.get_line(sel.line)
    prefix = line[: sel.col]

    # Activate only if line starts with VAR after stripping leading spaces
    stripped = prefix.lstrip()
    if not stripped.upper().startswith("VAR"):
        return []

    idx = prefix.rfind("scope=")
    if idx == -1:
        return []

    current = prefix[idx + len("scope=") :].strip()

    ret: List[dict] = []
    for scope in _SCOPES:
        if scope.startswith(current.upper()):
            text_edit = TextEdit(
                Range(
                    start=Position(sel.line, idx + len("scope=")),
                    end=Position(sel.line, sel.col),
                ),
                scope,
            )
            ret.append(
                CompletionItem(
                    label=scope,
                    kind=CompletionItemKind.EnumMember,
                    text_edit=text_edit,
                    insertText=scope,
                    insertTextFormat=InsertTextFormat.PlainText,
                ).to_dict()
            )
    return ret
