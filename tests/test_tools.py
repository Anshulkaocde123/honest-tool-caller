"""Tests for tool schema structure. Because if the menu is wrong, the chef can't cook."""

from tools import ALL_TOOLS, weather_tool, calculate_tool, wikipedia_tool


class TestToolSchemaStructure:
    """Make sure every schema has the fields Gemini expects."""

    REQUIRED_TOP_KEYS = {"type", "name", "description", "parameters"}
    REQUIRED_PARAM_KEYS = {"type", "properties", "required"}

    def test_all_tools_has_three_tools(self):
        assert len(ALL_TOOLS) == 3, "We promised 3 tools. Deliver."

    def test_weather_schema_structure(self):
        self._validate_schema(weather_tool, "get_weather", ["city"])

    def test_calculate_schema_structure(self):
        self._validate_schema(calculate_tool, "calculate", ["expression"])

    def test_wikipedia_schema_structure(self):
        self._validate_schema(wikipedia_tool, "search_wikipedia", ["query"])

    def test_all_schemas_are_functions(self):
        for tool in ALL_TOOLS:
            assert tool["type"] == "function", f"{tool['name']} should be type 'function'"

    def test_descriptions_are_not_empty(self):
        for tool in ALL_TOOLS:
            desc = tool["description"]
            assert len(desc) > 20, f"{tool['name']} description is suspiciously short"

    def test_no_duplicate_names(self):
        names = [t["name"] for t in ALL_TOOLS]
        assert len(names) == len(set(names)), "Duplicate tool names detected"

    # helper
    def _validate_schema(self, tool, expected_name, expected_required):
        assert set(tool.keys()) >= self.REQUIRED_TOP_KEYS
        assert tool["name"] == expected_name
        params = tool["parameters"]
        assert set(params.keys()) >= self.REQUIRED_PARAM_KEYS
        assert params["type"] == "object"
        assert params["required"] == expected_required
        for prop_name in expected_required:
            assert prop_name in params["properties"]
