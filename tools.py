"""
Tool schemas — the menu we hand to Gemini.
"Here are functions you can ask me to run. Choose wisely."
"""

weather_tool = {
    "type": "function",
    "name": "get_weather",
    "description": (
        "Get the current weather for a given city. "
        "Returns temperature, weather condition (e.g., sunny, cloudy, rainy), "
        "and humidity. Use this when the user asks about weather, temperature, "
        "or climate conditions for a specific location."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "The city name, e.g., 'Delhi', 'London', 'New York'",
            }
        },
        "required": ["city"],
    },
}

calculate_tool = {
    "type": "function",
    "name": "calculate",
    "description": (
        "Evaluate a mathematical expression and return the numerical result. "
        "Supports basic arithmetic (+, -, *, /), exponentiation (**), "
        "and parentheses. Use this for any math that should be computed "
        "exactly rather than estimated."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "The math expression, e.g., '(2 + 3) * 4', '2 ** 10'",
            }
        },
        "required": ["expression"],
    },
}

wikipedia_tool = {
    "type": "function",
    "name": "search_wikipedia",
    "description": (
        "Search Wikipedia for information about a topic. Returns a summary "
        "of the most relevant article. Use this when the user asks factual "
        "questions about people, places, events, science, history, or any "
        "topic that would have a Wikipedia article."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query, e.g., 'Albert Einstein', 'quantum computing'",
            }
        },
        "required": ["query"],
    },
}

# all three, ready to ship
ALL_TOOLS = [weather_tool, calculate_tool, wikipedia_tool]
