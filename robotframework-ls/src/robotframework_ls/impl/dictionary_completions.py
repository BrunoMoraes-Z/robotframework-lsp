from typing import Dict, Tuple, Sequence, Iterator, List, Optional, NamedTuple
from robocorp_ls_core.robotframework_log import get_logger
from robotframework_ls.impl.protocols import ICompletionContext
from robocorp_ls_core.lsp import (
    CompletionItem,
    CompletionItemKind,
    InsertTextFormat,
    Position,
    Range,
    TextEdit,
    CompletionItemTypedDict,
)

log = get_logger(__name__)


def _iter_normalized_variables_and_values(
    completion_context: ICompletionContext,
) -> Iterator[Tuple[str, Tuple[str, ...]]]:
    from robot.api import Token
    from robotframework_ls.impl.variable_resolve import (
        extract_variable_base,
    )
    from robotframework_ls.impl.text_utilities import normalize_robot_name

    for node_info in completion_context.get_all_variables():
        node = node_info.node
        token = node.get_token(Token.VARIABLE)
        if token is None:
            continue
        var_name = token.value
        base_name = extract_variable_base(var_name)
        if base_name:
            var_value: Tuple[str, ...] = node.value
            yield (normalize_robot_name(base_name), var_value)


def _as_dictionary(
    dict_tokens: Sequence[str], normalize=False, filter_token: str = ""
) -> Dict[str, str]:
    """
    Parse ["key1=val1", "key2=val2",...] as a dictionary
    """
    from robotframework_ls.impl.text_utilities import normalize_robot_name

    dictionary = {}
    for token in dict_tokens:
        key, sep, val = token.partition("=")
        if not sep:
            continue
        key = key.strip()
        val = val.strip()

        if normalize:
            key = normalize_robot_name(key)
        if filter_token and filter_token not in normalize_robot_name(key):
            continue
        dictionary.update({key: val})
    return dictionary


def _completion_items(
    dictionary: Dict[str, str], editor_range: Range
) -> List[CompletionItemTypedDict]:
    return [
        CompletionItem(
            key,
            kind=CompletionItemKind.Variable,
            text_edit=TextEdit(editor_range, key),
            insertText=key,
            detail=value,
            documentation=value,
            insertTextFormat=InsertTextFormat.Snippet,
        ).to_dict()
        for key, value in dictionary.items()
    ]


class _BracketCompletionInfo(NamedTuple):
    base_name: str
    path_items: List[str]
    filter_token: str
    start_offset: int
    end_offset: int


def _get_bracket_completion_info_from_robot(
    token,
    value: str,
    col: int,
) -> Optional[_BracketCompletionInfo]:
    from robotframework_ls.impl.variable_resolve import iter_robot_variable_matches
    from robotframework_ls.impl.ast_utils import iter_robot_match_as_tokens
    from robotframework_ls.impl.text_utilities import normalize_robot_name

    last_opening_bracket_column = -1

    items_seen = []

    prev_rtoken = None
    for robot_match, relative_index in iter_robot_variable_matches(value):
        robot_match_start = token.col_offset + relative_index + robot_match.start
        robot_match_end = token.col_offset + relative_index + robot_match.end

        if robot_match.base and robot_match_start < col < robot_match_end:
            for rtoken in iter_robot_match_as_tokens(
                robot_match, relative_index=robot_match_start, lineno=token.lineno
            ):
                if rtoken.type == "[":
                    last_opening_bracket_column = rtoken.col_offset

                if rtoken.col_offset >= col:
                    if (
                        rtoken.type == "item"
                        and rtoken.col_offset == rtoken.end_col_offset
                    ):
                        prev_rtoken = rtoken
                        items_seen.append(rtoken)

                    break

                if rtoken.type == "item":
                    items_seen.append(rtoken)

                prev_rtoken = rtoken

            break
    else:
        return None

    if prev_rtoken is None:
        return None

    if prev_rtoken.type not in ("[", "item"):
        return None

    if last_opening_bracket_column == -1:
        return None

    search_items = []
    if len(items_seen) > 1:
        for item in items_seen[:-1]:
            search_items.append(item.value)

    if prev_rtoken.type == "[":
        start_offset = end_offset = prev_rtoken.col_offset
        filter_token = ""
    else:
        start_offset = prev_rtoken.col_offset
        end_offset = prev_rtoken.end_col_offset
        filter_token = normalize_robot_name(prev_rtoken.value)

    return _BracketCompletionInfo(
        base_name=robot_match.base,
        path_items=search_items,
        filter_token=filter_token,
        start_offset=start_offset,
        end_offset=end_offset,
    )


def _get_bracket_completion_info_inside_braces(
    token,
    value: str,
    col: int,
) -> Optional[_BracketCompletionInfo]:
    from robotframework_ls.impl.text_utilities import normalize_robot_name

    offset = col - token.col_offset
    if offset < 0:
        return None

    prefixes = ("${", "@{", "&{")
    var_start = -1
    for prefix in prefixes:
        idx = value.rfind(prefix, 0, offset)
        if idx > var_start:
            var_start = idx
    if var_start == -1:
        return None

    first_close_brace = value.find("}", var_start)
    first_open_bracket = value.find("[", var_start)
    if (
        first_open_bracket == -1
        or first_close_brace == -1
        or first_open_bracket > first_close_brace
    ):
        return None

    base_section = value[var_start + 2 : first_open_bracket]
    colon_i = base_section.find(":")
    if colon_i != -1:
        base_name = base_section[:colon_i].rstrip()
    else:
        base_name = base_section
    base_name = base_name.strip()
    if not base_name:
        return None

    items: List[str] = []
    current = ""
    current_start: Optional[int] = None
    in_bracket = False
    in_string = False
    string_char = ""

    i = first_open_bracket
    while i < offset and i < len(value):
        ch = value[i]
        if not in_bracket:
            if ch == "[":
                in_bracket = True
                current = ""
                current_start = i + 1
                in_string = False
                string_char = ""
            elif ch == "}":
                break
        else:
            if in_string:
                if ch == string_char:
                    in_string = False
                else:
                    current += ch
            else:
                if ch in ("'", '"') and current == "":
                    in_string = True
                    string_char = ch
                    current_start = i + 1
                elif ch == "]":
                    items.append(current.strip())
                    current = ""
                    current_start = None
                    in_bracket = False
                elif ch == "[":
                    items.append(current.strip())
                    current = ""
                    current_start = i + 1
                    in_string = False
                    string_char = ""
                elif ch.isspace() and current == "":
                    current_start = i + 1
                else:
                    current += ch
        i += 1

    if not in_bracket:
        return None

    filter_token = normalize_robot_name(current.strip())
    start_offset = token.col_offset + (current_start or offset)
    end_offset = token.col_offset + offset

    path_items = [item for item in items if item]

    return _BracketCompletionInfo(
        base_name=base_name,
        path_items=path_items,
        filter_token=filter_token,
        start_offset=start_offset,
        end_offset=end_offset,
    )


def _iter_all_normalized_variables_and_values(
    completion_context: ICompletionContext,
) -> Iterator[Tuple[str, Tuple[str, ...]]]:
    yield from _iter_normalized_variables_and_values(completion_context)

    dependency_graph = completion_context.collect_dependency_graph()
    for resource_doc in completion_context.iter_dependency_and_init_resource_docs(
        dependency_graph
    ):
        new_ctx = completion_context.create_copy(resource_doc)
        yield from _iter_normalized_variables_and_values(new_ctx)


def _resolve_dictionary_for_path(
    normalized_variables: Dict[str, Tuple[str, ...]],
    base_name: str,
    path_items: List[str],
) -> Tuple[str, ...] | None:
    from robotframework_ls.impl.text_utilities import normalize_robot_name
    from robotframework_ls.impl.variable_resolve import robot_search_variable

    search_items = [normalize_robot_name(base_name)]
    search_items.extend(normalize_robot_name(p) for p in path_items)
    log.debug("resolve path %s -> %s", base_name, search_items)

    count = 0
    while search_items:
        count += 1
        if count > 10:
            log.info(
                "Breaking recursion on dot dictionary completions: %s", search_items
            )
            return None

        search_name = search_items.pop(0)
        variable_values = normalized_variables.get(search_name)
        log.debug("search %s -> %s", search_name, variable_values)
        if not variable_values:
            return None

        if not search_items:
            return variable_values

        dictionary = _as_dictionary(variable_values, normalize=True)
        next_search_key = search_items.pop(0)
        next_search = dictionary.get(next_search_key)
        if not next_search or not next_search.startswith("&{"):
            return None

        new_match = robot_search_variable(next_search)
        if not new_match or not new_match.base:
            return None

        for item in reversed(new_match.items):
            search_items.insert(0, normalize_robot_name(item))
        search_items.insert(0, normalize_robot_name(new_match.base))

    return None


def complete(completion_context: ICompletionContext) -> List[CompletionItemTypedDict]:
    from robotframework_ls.impl.text_utilities import normalize_robot_name
    from robotframework_ls.impl.variable_resolve import robot_search_variable
    from robotframework_ls.impl.robot_generated_lsp_constants import (
        OPTION_ROBOT_COMPLETIONS_DICTIONARY_ENTRIES_ENABLE,
    )

    config = completion_context.config
    if config is not None and not config.get_setting(
        OPTION_ROBOT_COMPLETIONS_DICTIONARY_ENTRIES_ENABLE, bool, True
    ):
        return []

    token_info = completion_context.get_current_token()
    if token_info is None:
        return []
    token = token_info.token
    value = token.value

    col = completion_context.sel.col

    prefix_before_col = value[: col - token.col_offset]
    prefix = prefix_before_col
    if prefix.endswith("}"):
        prefix = prefix[:-1]

    if prefix.startswith(("${", "@{", "&{")) and "." in prefix:
        inside = prefix[2:]
        parts = inside.split(".")
        base_part = parts[0]
        colon_i = base_part.find(":")
        if colon_i != -1:
            base_name = base_part[:colon_i].rstrip()
        else:
            base_name = base_part

        path_items = parts[1:]
        if prefix.endswith("."):
            if path_items and path_items[-1] == "":
                path_items = path_items[:-1]
            filter_token = ""
        else:
            filter_token = normalize_robot_name(path_items[-1]) if path_items else ""
            path_items = path_items[:-1]

        start_offset = token.col_offset + len(prefix_before_col) - len(filter_token)
        end_offset = col

        normalized_vars = dict(
            _iter_all_normalized_variables_and_values(completion_context)
        )
        variable_values = _resolve_dictionary_for_path(
            normalized_vars, base_name, path_items
        )
        if not variable_values:
            return []

        try:
            dictionary = _as_dictionary(variable_values, filter_token=filter_token)
        except Exception:
            return []

        log.debug("dot completion dictionary %s", dictionary)

        editor_range = Range(
            start=Position(completion_context.sel.line, start_offset),
            end=Position(completion_context.sel.line, end_offset),
        )
        return _completion_items(dictionary, editor_range)

    bracket_info = _get_bracket_completion_info_from_robot(
        token, value, col
    )
    if bracket_info is None:
        bracket_info = _get_bracket_completion_info_inside_braces(
            token, value, col
        )
    if bracket_info is None:
        return []

    base_name, path_items, filter_token, start_offset, end_offset = bracket_info

    normalized_variables_and_values = dict(
        _iter_all_normalized_variables_and_values(completion_context)
    )

    selection = completion_context.sel

    search_items_normalized = [normalize_robot_name(base_name)]
    for item in path_items:
        search_items_normalized.append(normalize_robot_name(item))

    count = 0
    while search_items_normalized:
        count += 1
        if count > 10:
            log.info(
                "Breaking up possible recursion on dictionary completions. Stack: %s",
                search_items_normalized,
            )
            return []

        search_name_normalized = search_items_normalized.pop(0)

        variable_values = normalized_variables_and_values.get(search_name_normalized)
        if not variable_values:
            return []
        if not search_items_normalized:
            dictionary = _as_dictionary(variable_values, filter_token=filter_token)
            editor_range = Range(
                start=Position(selection.line, start_offset),
                end=Position(selection.line, end_offset),
            )
            return _completion_items(dictionary, editor_range)

        last_dict = _as_dictionary(variable_values, normalize=True)

        next_search = search_items_normalized.pop(0)
        next_value = last_dict.get(next_search)
        if not next_value:
            return []

        if not next_value.startswith("&{"):
            return []

        new_match = robot_search_variable(next_value)
        if not new_match or not new_match.base:
            return []

        for it in reversed(new_match.items):
            search_items_normalized.insert(0, normalize_robot_name(it))
        search_items_normalized.insert(0, normalize_robot_name(new_match.base))

    return []
