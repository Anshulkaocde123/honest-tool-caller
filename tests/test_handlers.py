"""
Tests for tool handlers. The calculator gets most of the love
because it's the one that could actually break things.
"""

from unittest.mock import patch, MagicMock
from tool_handlers import (
    execute_tool,
    handle_calculate,
    handle_get_weather,
    handle_search_wikipedia,
)


# ── calculator tests ────────────────────────────────────────────────────────

class TestCalculator:
    """Trust no math. Verify everything."""

    def test_basic_addition(self):
        assert handle_calculate("2 + 3") == "2 + 3 = 5"

    def test_basic_subtraction(self):
        assert handle_calculate("10 - 4") == "10 - 4 = 6"

    def test_multiplication(self):
        assert handle_calculate("7 * 6") == "7 * 6 = 42"

    def test_division(self):
        assert handle_calculate("10 / 4") == "10 / 4 = 2.5"

    def test_exponentiation(self):
        assert handle_calculate("2 ** 10") == "2 ** 10 = 1024"

    def test_order_of_operations(self):
        assert handle_calculate("2 + 3 * 4") == "2 + 3 * 4 = 14"

    def test_parentheses(self):
        assert handle_calculate("(2 + 3) * 4") == "(2 + 3) * 4 = 20"

    def test_negative_numbers(self):
        result = handle_calculate("-5 + 3")
        assert "= -2" in result

    def test_division_by_zero(self):
        result = handle_calculate("1 / 0")
        assert "Division by zero" in result

    def test_blocks_eval_injection(self):
        """The big one. If this fails, unplug the computer."""
        result = handle_calculate("__import__('os').system('echo pwned')")
        assert "Error" in result

    def test_blocks_function_calls(self):
        result = handle_calculate("print('hello')")
        assert "Error" in result

    def test_blocks_string_literals(self):
        result = handle_calculate("'hello' + 'world'")
        assert "Error" in result

    def test_invalid_syntax(self):
        result = handle_calculate("2 +* 3")  # actually invalid, unlike 2 + + 3 (unary plus)
        assert "Error" in result

    def test_empty_expression(self):
        result = handle_calculate("")
        assert "Error" in result


# ── dispatcher tests ────────────────────────────────────────────────────────

class TestDispatcher:
    """Make sure the traffic cop knows the routes."""

    def test_routes_to_calculator(self):
        result = execute_tool("calculate", {"expression": "1 + 1"})
        assert "= 2" in result

    def test_unknown_tool_returns_error(self):
        result = execute_tool("hack_the_planet", {})
        assert "Unknown tool" in result

    def test_bad_arguments_returns_error(self):
        # passing wrong args — should not crash
        result = execute_tool("calculate", {"wrong_param": "oops"})
        assert "Error" in result

    def test_all_three_tools_are_registered(self):
        # each should not return "Unknown tool"
        for name, args in [
            ("get_weather", {"city": "TestCity"}),
            ("calculate", {"expression": "1+1"}),
            ("search_wikipedia", {"query": "test"}),
        ]:
            result = execute_tool(name, args)
            assert "Unknown tool" not in result


# ── weather tests (mocked HTTP) ────────────────────────────────────────────

class TestWeather:
    """We mock the API because nobody wants flaky tests at 2 AM."""

    @patch("tool_handlers.requests.get")
    def test_successful_weather_response(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "current_condition": [{
                "temp_C": "33",
                "humidity": "62",
                "weatherDesc": [{"value": "Sunny"}],
            }]
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = handle_get_weather("Delhi")
        assert "Delhi" in result
        assert "33" in result
        assert "Sunny" in result

    @patch("tool_handlers.requests.get")
    def test_network_error(self, mock_get):
        import requests
        mock_get.side_effect = requests.RequestException("Connection refused")

        result = handle_get_weather("Atlantis")
        assert "Could not fetch" in result

    @patch("tool_handlers.requests.get")
    def test_weird_response_format(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"unexpected": "format"}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = handle_get_weather("Delhi")
        assert "weird" in result.lower() or "Error" in result or "Unexpected" in result


# ── wikipedia tests (mocked HTTP) ──────────────────────────────────────────

class TestWikipedia:
    """Wikipedia but make it deterministic."""

    @patch("tool_handlers.requests.get")
    def test_successful_search(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "title": "Python (programming language)",
            "extract": "Python is a high-level programming language.",
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = handle_search_wikipedia("Python programming")
        assert "Python" in result

    @patch("tool_handlers.requests.get")
    def test_article_not_found(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        result = handle_search_wikipedia("asdfghjkl123456")
        assert "No Wikipedia article found" in result

    @patch("tool_handlers.requests.get")
    def test_truncation_of_long_articles(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "title": "Long Article",
            "extract": "x" * 2000,  # way too long
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = handle_search_wikipedia("Long Article")
        assert "[truncated]" in result
        assert len(result) < 2000

    @patch("tool_handlers.requests.get")
    def test_network_failure(self, mock_get):
        import requests
        mock_get.side_effect = requests.RequestException("Timeout")

        result = handle_search_wikipedia("anything")
        assert "failed" in result.lower()
