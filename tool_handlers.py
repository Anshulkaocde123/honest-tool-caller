"""
Tool Handlers (The Kitchen).

The model decides what to call, but this module does the actual heavy lifting.
All handlers return strings because crashing the agent loop on a network error
is a rookie mistake. Graceful degradation over tracebacks.
"""

import ast
import operator
import requests
from typing import Dict, Any, Callable


# ── Dispatcher ──────────────────────────────────────────────────────────────

def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> str:
    """
    Route a tool call to the appropriate handler function.

    Args:
        tool_name (str): The name of the tool requested by the model.
        arguments (Dict[str, Any]): The arguments parsed by the model.

    Returns:
        str: The result of the execution, or a graceful error message if things go south.
    """
    registry: Dict[str, Callable[..., str]] = {
        "get_weather": handle_get_weather,
        "calculate": handle_calculate,
        "search_wikipedia": handle_search_wikipedia,
    }

    handler = registry.get(tool_name)
    if handler is None:
        return f"Error: Unknown tool '{tool_name}'. I only know: {list(registry.keys())}"

    try:
        return handler(**arguments)
    except Exception as e:
        return f"Error executing {tool_name}: {e}"


# ── Weather ─────────────────────────────────────────────────────────────────

def handle_get_weather(city: str) -> str:
    """
    Fetch weather from wttr.in. Free, no API key, no drama.

    Args:
        city (str): The city to get weather for.

    Returns:
        str: A formatted string with weather details, or an error.
    """
    try:
        url = f"https://wttr.in/{city}?format=j1"
        resp = requests.get(url, timeout=10)  # no timeout = infinite sadness
        resp.raise_for_status()

        current = resp.json()["current_condition"][0]
        temp = current["temp_C"]
        humidity = current["humidity"]
        desc = current["weatherDesc"][0]["value"]

        return f"Weather in {city}: {desc}, {temp}°C, Humidity: {humidity}%"

    except requests.RequestException as e:
        return f"Could not fetch weather for '{city}': {e}"
    except (KeyError, IndexError, ValueError) as e:
        return f"Weather API returned something weird for '{city}': {e}"


# ── Calculator ──────────────────────────────────────────────────────────────
# We use AST parsing because using eval() is basically handing a stranger the
# keys to your server and hoping they don't rm -rf /.

_SAFE_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _walk_ast(node: ast.AST) -> float:
    """
    Recursively evaluate an AST node. Only allows numbers and basic math.

    Args:
        node (ast.AST): The parsed AST node.

    Raises:
        ValueError: If a disallowed operation or node type is encountered.

    Returns:
        float: The computed numerical value.
    """
    if isinstance(node, ast.Expression):
        return _walk_ast(node.body)

    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return float(node.value)
        raise ValueError(f"Nice try: {node.value}")

    if isinstance(node, ast.BinOp):
        op = _SAFE_OPS.get(type(node.op))
        if op is None:
            raise ValueError(f"Nope, '{type(node.op).__name__}' is not allowed")
        return op(_walk_ast(node.left), _walk_ast(node.right))

    if isinstance(node, ast.UnaryOp):
        op = _SAFE_OPS.get(type(node.op))
        if op is None:
            raise ValueError(f"Blocked unary op: {type(node.op).__name__}")
        return op(_walk_ast(node.operand))

    raise ValueError(f"Blocked: {type(node).__name__}. This isn't eval().")


def handle_calculate(expression: str) -> str:
    """
    Safely evaluate a math expression using AST parsing.
    No eval(), we're not animals.

    Args:
        expression (str): The mathematical expression to solve.

    Returns:
        str: The solution or an error string.
    """
    try:
        tree = ast.parse(expression, mode="eval")
        result = _walk_ast(tree)
        # Format cleanly, removing unnecessary decimals for integers
        if result.is_integer():
            result = int(result)
        return f"{expression} = {result}"
    except ZeroDivisionError:
        return f"Error: Division by zero in '{expression}'"
    except (ValueError, SyntaxError) as e:
        return f"Error evaluating '{expression}': {e}"


# ── Wikipedia ───────────────────────────────────────────────────────────────

def handle_search_wikipedia(query: str) -> str:
    """
    Search Wikipedia using their free REST API.
    Truncates the summary to 1000 chars because token context costs money.

    Args:
        query (str): The topic to search for.

    Returns:
        str: The summary of the Wikipedia article, or an error.
    """
    try:
        url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + query.replace(" ", "_")
        resp = requests.get(url, timeout=10)

        if resp.status_code == 404:
            return f"No Wikipedia article found for '{query}'"

        resp.raise_for_status()
        data = resp.json()

        title = data.get("title", query)
        summary = data.get("extract", "No summary available.")

        # Truncate to save tokens and avoid flooding context
        if len(summary) > 1000:
            summary = summary[:1000] + "... [truncated]"

        return f"Wikipedia — {title}:\n{summary}"

    except requests.RequestException as e:
        return f"Wikipedia search failed for '{query}': {e}"
