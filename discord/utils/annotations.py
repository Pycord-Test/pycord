"""
The MIT License (MIT)

Copyright (c) 2021-present Pycord Development

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

import ast
import functools
import inspect
import textwrap
from typing import Any, overload

from ..errors import AnnotationMismatch


def _param_spans(obj: Any) -> dict[str, tuple[int, int, int, int, str]]:
    """
    Get the source code spans for each parameter's annotation in a function.
    Returns a mapping of parameter name to a tuple of
    (start_line, start_col_1b, end_line, end_col_1b, line_text).
    1b = 1-based column offset.

    Parameters
    ----------
    obj:
        The function or method to analyze.

    Returns
    -------
    dict[str, tuple[int, int, int, int, str]]
        Mapping of parameter names to their annotation spans.
    """
    src, start_line = inspect.getsourcelines(obj)  # original (indented) lines
    filename = inspect.getsourcefile(obj) or "<unknown>"

    # Compute common indent that dedent will remove
    non_empty = [l for l in src if l.strip()]
    common_indent = min((len(l) - len(l.lstrip(" "))) for l in non_empty) if non_empty else 0

    # Parse a DEDENTED copy to get stable AST coords
    dedented = textwrap.dedent("".join(src))
    mod = ast.parse(dedented, filename=filename, mode="exec", type_comments=True)

    fn = next((n for n in mod.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))), None)
    if fn is None:
        return {}

    def _collect_args(a: ast.arguments) -> list[tuple[ast.arg, ast.expr | None]]:
        out: list[tuple[ast.arg, ast.expr | None]] = []
        for ar in getattr(a, "posonlyargs", []):
            out.append((ar, ar.annotation))
        for ar in a.args:
            out.append((ar, ar.annotation))
        if a.vararg:
            out.append((a.vararg, a.vararg.annotation))
        for ar in a.kwonlyargs:
            out.append((ar, ar.annotation))
        if a.kwarg:
            out.append((a.kwarg, a.kwarg.annotation))
        return out

    args = _collect_args(fn.args)

    def _line_text_file(lineno_file: int) -> str:
        idx = lineno_file - start_line
        if 0 <= idx < len(src):
            return src[idx].rstrip("\n")
        return ""

    spans: dict[str, tuple[int, int, int, int, str]] = {}

    for ar, ann in args:
        name = ar.arg

        # AST positions are snippet-relative: lineno 1-based, col_offset 0-based
        ln_snip = getattr(ar, "lineno", 1)
        col0_snip = getattr(ar, "col_offset", 0)

        # Prefer annotation end if present; otherwise end at end of the name
        if ann is not None and hasattr(ann, "end_lineno") and hasattr(ann, "end_col_offset"):
            end_ln_snip = ann.end_lineno
            end_col0_snip = ann.end_col_offset
        else:
            end_ln_snip = ln_snip
            end_col0_snip = col0_snip + len(name)

        # Convert SNIPPET positions -> FILE positions
        ln_file = start_line + (ln_snip - 1)
        end_ln_file = start_line + (end_ln_snip - 1)

        # Add back the common indent that dedent removed; convert to 1-based
        col_1b_file = col0_snip + 1 + common_indent
        end_col_1b_file = end_col0_snip + 1 + common_indent

        line_text = _line_text_file(ln_file)
        # Guard: keep columns within the line
        line_len_1b = len(line_text) + 1
        col_1b_file = max(1, min(col_1b_file, line_len_1b))
        end_col_1b_file = max(col_1b_file, min(end_col_1b_file, line_len_1b))

        spans[name] = (ln_file, col_1b_file, end_ln_file, end_col_1b_file, line_text)

    return spans


def _unwrap_partial(func: Any) -> Any:
    while isinstance(func, functools.partial):
        func = func.func
    return func


@overload
def get_annotations(
    obj: Any,
    *,
    globals: dict[str, Any] | None = None,
    locals: dict[str, Any] | None = None,
    eval_str: bool = False,
    expected_types: None = None,
    custom_error: None = None,
) -> dict[str, Any]: ...


@overload
def get_annotations(
    obj: Any,
    *,
    globals: dict[str, Any] | None = None,
    locals: dict[str, Any] | None = None,
    eval_str: bool = False,
    expected_types: dict[int, type],
    custom_error: str | None = None,
) -> dict[str, Any]: ...


def get_annotations(
    obj: Any,
    *,
    globals: dict[str, Any] | None = None,
    locals: dict[str, Any] | None = None,
    eval_str: bool = False,
    expected_types: dict[int, type] | None = None,
    custom_error: str | None = None,
) -> dict[str, Any]:
    """
    Get the type annotations of a function or method, with optional type checking.

    This function unwraps `functools.partial` objects to access the original function.

    This function is a modified version of `inspect.get_annotations` that adds the ability to check parameter types.

    .. note::
        This function is not intended to be used by end-users.

    Parameters
    ----------
    obj:
        The function or method to inspect.
    globals:
        The global namespace to use for evaluating string annotations.
    locals:
        The local namespace to use for evaluating string annotations.
    eval_str:
        Whether to evaluate string annotations.
    expected_types:
        A mapping of parameter index to expected type for type checking.
    custom_error:
        A custom error message format for type mismatches. Supports the following format fields:
        - parameter: The name of the parameter with the mismatch.
        - expected: The expected type.
        - got: The actual type found.

    Returns
    -------
    dict[str, Any]
        A mapping of parameter names to their type annotations.
    """
    unwrapped_obj = _unwrap_partial(obj)
    r = inspect.get_annotations(unwrapped_obj, globals=globals, locals=locals, eval_str=eval_str)

    if expected_types is not None:
        for i, (k, v) in enumerate(r.items()):
            if i in expected_types and not isinstance(v, expected_types[i]):
                error = AnnotationMismatch(
                    (
                        custom_error
                        or 'Type annotation mismatch for parameter "{parameter}": expected {expected}, got {got}'
                    ).format(
                        parameter=k,
                        expected=repr(expected_types[i]),
                        got=repr(r[k]),
                    )
                )
                spans = _param_spans(unwrapped_obj)

                if k in spans:
                    ln, col_1b, end_ln, end_col_1b, line_text = spans[k]
                else:
                    ln = unwrapped_obj.__code__.co_firstlineno
                    line_text = inspect.getsource(unwrapped_obj).splitlines()[0]
                    col_1b, end_ln, end_col_1b = 1, ln, len(line_text) + 1
                error.filename = unwrapped_obj.__code__.co_filename
                error.lineno = ln
                error.offset = col_1b
                error.end_lineno = end_ln
                error.end_offset = end_col_1b
                error.text = line_text
                raise error

    return r


__all__ = ("get_annotations", "AnnotationMismatch")
