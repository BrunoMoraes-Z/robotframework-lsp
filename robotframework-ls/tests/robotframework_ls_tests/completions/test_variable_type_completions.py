import pytest

from robotframework_ls.impl.completion_context import CompletionContext
from robotframework_ls.server_api.server import complete_all


def _get_completion_labels(completions):
    return {c["label"] for c in completions}


def test_type_completion_after_colon(workspace, libspec_manager):
    workspace.set_root("case_vars_file", libspec_manager=libspec_manager)
    doc, selected = workspace.put_doc_get_line_col(
        "typed.robot",
        "*** Test Cases ***\nTest\n    ${var:|}\n",
    )
    line, col = selected.get_end_line_col()
    completions = complete_all(
        CompletionContext(doc, workspace=workspace.ws, line=line, col=col)
    )
    labels = _get_completion_labels(completions)
    assert "str" in labels
    assert "MyVars" not in labels


