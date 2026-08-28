"""
Tool handlers — the functions that actually do things.
The model decides what to call. We do the heavy lifting.
Errors come back as strings because crashing is for amateurs.
"""

import ast
import operator
import requests


# ── dispatcher ──────────────────────────────────────────────────────────────

def execute_tool(tool_name: str, arguments: dict) -> str:
    """Route a tool call to the right handler. Returns result as a string."""

    registry = {
        "get_weather": handle_get_weather,
        "calculate": handle_calculate,
        "search_wikipedia": handle_search_wikipedia,
    }

    handler = registry.get(tool_name)
    if handler is None:
        return f"Error: Unknown tool '{tool_name}'. I know: {list(registry.keys())}"

    try:
        return handler(**arguments)
    except Exception as e:
        return f"Error executing {tool_name}: {e}"


# ── weather ─────────────────────────────────────────────────────────────────

def handle_get_weather(city: str) -> str:
    """Fetch weather from wttr.in — free, no API key, no drama."""

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
    except (KeyError, IndexError) as e:
        return f"Weather API returned something weird for '{city}': {e}"


# ── calculator ──────────────────────────────────────────────────────────────
# Uses AST parsing because eval() is basically handing a stranger your keys.

_SAFE_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _walk_ast(node):
    """Recursively evaluate an AST node. Only numbers and basic math allowed."""

    if isinstance(node, ast.Expression):
        return _walk_ast(node.body)

    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
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
    """Safely evaluate a math expression. No eval(), we're not animals."""

    try:
        tree = ast.parse(expression, mode="eval")
        result = _walk_ast(tree)
        return f"{expression} = {result}"
    except ZeroDivisionError:
        return f"Error: Division by zero in '{expression}'"
    except (ValueError, SyntaxError) as e:
        return f"Error evaluating '{expression}': {e}"


# ── wikipedia ───────────────────────────────────────────────────────────────

def handle_search_wikipedia(query: str) -> str:
    """Search Wikipedia. Truncates to 1000 chars because tokens cost money."""

    try:
        url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + query.replace(" ", "_")
        resp = requests.get(url, timeout=10)

        if resp.status_code == 404:
            return f"No Wikipedia article found for '{query}'"

        resp.raise_for_status()
        data = resp.json()

        title = data.get("title", query)
        summary = data.get("extract", "No summary available.")

        if len(summary) > 1000:
            summary = summary[:1000] + "... [truncated]"

        return f"Wikipedia — {title}:\n{summary}"

    except requests.RequestException as e:
        return f"Wikipedia search failed for '{query}': {e}"
