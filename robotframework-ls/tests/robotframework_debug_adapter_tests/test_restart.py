import json
from robotframework_debug_adapter_tests.fixtures import _DebuggerAPI


def test_restart_session(debugger_api: _DebuggerAPI):
    from robocorp_ls_core.debug_adapter_core.dap.dap_schema import InitializedEvent
    debugger_api.initialize()
    target = debugger_api.get_dap_case_file("case_log.robot")
    debugger_api.launch(target, debug=True)
    bp = debugger_api.get_line_index_with_content("check that log works", target)
    debugger_api.set_breakpoints(target, bp)
    debugger_api.configuration_done()

    hit = debugger_api.wait_for_thread_stopped(file="case_log.robot")
    debugger_api.continue_event(hit.thread_id, accept_terminated=True)

    restart_response = debugger_api.restart()
    assert restart_response.success

    debugger_api.set_breakpoints(target, bp)
    debugger_api.configuration_done()
    hit = debugger_api.wait_for_thread_stopped(file="case_log.robot")
    debugger_api.continue_event(hit.thread_id, accept_terminated=True)
