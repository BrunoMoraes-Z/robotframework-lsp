import pytest

from robotframework_ls.impl.robot_version import robot_version_supports_variable_types

from robotframework_ls.impl.completion_context import CompletionContext
from robotframework_ls.server_api.server import complete_all


def _get_completion_labels(completions):
    return {c["label"] for c in completions}


@pytest.mark.skipif(
    not robot_version_supports_variable_types(),
    reason="Test requires RF typed variable support.",
)
def test_type_completion_after_colon(workspace, libspec_manager):
    workspace.set_root("case_vars_file", libspec_manager=libspec_manager)
    doc, selected = workspace.put_doc_get_line_col(
        "typed.robot",
        "*** Test Cases ***\nTest\n    ${var: |}\n",
    )
    line, col = selected.get_end_line_col()
    completions = complete_all(
        CompletionContext(doc, workspace=workspace.ws, line=line, col=col)
    )
    labels = _get_completion_labels(completions)
    assert "str" in labels
    assert "datetime" in labels
    assert "MyVars" not in labels


def test_type_completion_disabled_for_old_version(
    workspace, libspec_manager, monkeypatch
):
    from robotframework_ls.impl import robot_version

    monkeypatch.setattr(robot_version, "get_robot_major_minor_version", lambda: (7, 2))

    workspace.set_root("case_vars_file", libspec_manager=libspec_manager)
    doc, selected = workspace.put_doc_get_line_col(
        "typed.robot",
        "*** Test Cases ***\nTest\n    ${var: |}\n",
    )
    line, col = selected.get_end_line_col()
    completions = complete_all(
        CompletionContext(doc, workspace=workspace.ws, line=line, col=col)
    )
    assert completions == []


@pytest.mark.skipif(
    not robot_version_supports_variable_types(),
    reason="Test requires RF typed variable support.",
)
def test_secret_type_completion_for_newer_versions(
    workspace, libspec_manager, monkeypatch
):
    from robotframework_ls.impl import robot_version

    monkeypatch.setattr(robot_version, "get_robot_major_minor_version", lambda: (7, 4))

    workspace.set_root("case_vars_file", libspec_manager=libspec_manager)
    doc, selected = workspace.put_doc_get_line_col(
        "typed.robot",
        "*** Test Cases ***\nTest\n    ${token: Secret|}\n",
    )
    line, col = selected.get_end_line_col()
    completions = complete_all(
        CompletionContext(doc, workspace=workspace.ws, line=line, col=col)
    )
    labels = _get_completion_labels(completions)
    assert "Secret" in labels


@pytest.mark.skipif(
    not robot_version_supports_variable_types(),
    reason="Test requires RF typed variable support.",
)
def test_secret_type_not_available_for_older_versions(
    workspace, libspec_manager, monkeypatch
):
    from robotframework_ls.impl import robot_version

    monkeypatch.setattr(robot_version, "get_robot_major_minor_version", lambda: (7, 3))

    workspace.set_root("case_vars_file", libspec_manager=libspec_manager)
    doc, selected = workspace.put_doc_get_line_col(
        "typed.robot",
        "*** Test Cases ***\nTest\n    ${token: Sec|}\n",
    )
    line, col = selected.get_end_line_col()
    completions = complete_all(
        CompletionContext(doc, workspace=workspace.ws, line=line, col=col)
    )
    labels = _get_completion_labels(completions)
    assert "Secret" not in labels


@pytest.mark.skipif(
    not robot_version_supports_variable_types(),
    reason="Test requires RF typed variable support.",
)
def test_secret_value_completion(monkeypatch, workspace, libspec_manager):
    from robotframework_ls.impl import robot_version

    monkeypatch.setattr(robot_version, "get_robot_major_minor_version", lambda: (7, 4))

    workspace.set_root("case_vars_file", libspec_manager=libspec_manager)
    doc, selected = workspace.put_doc_get_line_col(
        "secret_value.robot",
        """*** Variables ***
${NORMAL: Secret}    %{=teste}

*** Test Cases ***
Test
    Log    ${NORMAL.|}
""",
    )
    line, col = selected.get_end_line_col()
    completions = complete_all(
        CompletionContext(doc, workspace=workspace.ws, line=line, col=col)
    )
    labels = _get_completion_labels(completions)
    assert "value" in labels


@pytest.mark.skipif(
    not robot_version_supports_variable_types(),
    reason="Test requires RF typed variable support.",
)
def test_secret_value_completion_keeps_dict_keys(
    monkeypatch, workspace, libspec_manager
):
    from robotframework_ls.impl import robot_version

    monkeypatch.setattr(robot_version, "get_robot_major_minor_version", lambda: (7, 4))

    workspace.set_root("case_vars_file", libspec_manager=libspec_manager)
    doc, selected = workspace.put_doc_get_line_col(
        "secret_value_dict.robot",
        """*** Variables ***
&{DICT: Secret}    key1=%{=var1}    key2=%{=var2}

*** Test Cases ***
Test
    Log    ${DICT.|}
""",
    )
    line, col = selected.get_end_line_col()
    completions = complete_all(
        CompletionContext(doc, workspace=workspace.ws, line=line, col=col)
    )
    labels = _get_completion_labels(completions)
    assert "value" in labels
    assert "key1" in labels


@pytest.mark.skipif(
    not robot_version_supports_variable_types(),
    reason="Test requires RF typed variable support.",
)
def test_secret_value_completion_not_offered_for_non_secret(
    monkeypatch, workspace, libspec_manager
):
    from robotframework_ls.impl import robot_version

    monkeypatch.setattr(robot_version, "get_robot_major_minor_version", lambda: (7, 4))

    workspace.set_root("case_vars_file", libspec_manager=libspec_manager)
    doc, selected = workspace.put_doc_get_line_col(
        "secret_value.robot",
        """*** Variables ***
${NORMAL: str}    value

*** Test Cases ***
Test
    Log    ${NORMAL.|}
""",
    )
    line, col = selected.get_end_line_col()
    completions = complete_all(
        CompletionContext(doc, workspace=workspace.ws, line=line, col=col)
    )
    labels = _get_completion_labels(completions)
    assert "value" not in labels
