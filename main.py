#!/usr/bin/env python3
"""
The Honest Tool-Caller Orchestrator.

A CLI assistant that refuses to hallucinate. It checks weather, does math,
and searches Wikipedia by actually calling real APIs instead of making stuff up.
Uses Google's Gemini Interactions API to implement a ReAct loop.

Usage:
  python main.py ask "What's the weather in Delhi?"
  python main.py chat
  python main.py test
"""

import argparse
import os
import sys
from typing import Optional, List, Dict, Any

from dotenv import load_dotenv
from google import genai

from tools import ALL_TOOLS
from tool_handlers import execute_tool

load_dotenv()

# ── ANSI Color Codes ────────────────────────────────────────────────────────
# Because black and white text is for barbarians.

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"


def get_client() -> genai.Client:
    """
    Create and authenticate a Gemini client.
    Dies gracefully if the API key is missing.

    Returns:
        genai.Client: The authenticated client.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "paste-your-gemini-api-key-here":
        print(f"{RED}✗ No API key found.{RESET}")
        print(f"  Get one free at: {CYAN}https://aistudio.google.com/apikey{RESET}")
        print(f"  Then put it in .env: GEMINI_API_KEY=your-key-here")
        sys.exit(1)

    return genai.Client(api_key=api_key)


def ask(query: str, client: Optional[genai.Client] = None, verbose: bool = True) -> str:
    """
    Send a query through the full tool-calling pipeline (ReAct pattern).
    Performs two round trips:
      1. Ask → Model requests tool call
      2. Execute tool locally → Feed result back → Model generates final answer

    Args:
        query (str): The user's question.
        client (Optional[genai.Client]): The Gemini client. Created if None.
        verbose (bool): Whether to print the interactions to stdout.

    Returns:
        str: The final answer from the model.
    """
    if client is None:
        client = get_client()

    if verbose:
        print(f"\n{BOLD}You:{RESET} {query}")
        print(f"{DIM}  ↳ sending to gemini...{RESET}")

    # Round 1: Send the question with our tool schemas
    interaction = client.interactions.create(
        model="gemini-2.5-flash",
        input=query,
        tools=ALL_TOOLS,
    )

    # Check if Gemini wants to call a tool (identifying function_call steps)
    tool_calls = [s for s in interaction.steps if s.type == "function_call"]

    if not tool_calls:
        # No tool needed — Gemini answered directly
        answer = interaction.output_text
        if verbose:
            print(f"\n{GREEN}🤖 Assistant:{RESET} {answer}")
        return answer

    # Execute each tool call locally and gather results
    results: List[Dict[str, Any]] = []
    for step in tool_calls:
        if verbose:
            print(f"  {YELLOW}⚡ calling {step.name}({step.arguments}){RESET}")

        result = execute_tool(step.name, step.arguments)

        if verbose:
            print(f"  {DIM}  → {result}{RESET}")

        results.append({
            "type": "function_result",
            "name": step.name,
            "call_id": step.id,
            "result": [{"type": "text", "text": str(result)}],
        })

    # Round 2: Feed the tool results back (linked via previous_interaction_id)
    final = client.interactions.create(
        model="gemini-2.5-flash",
        input=results,
        tools=ALL_TOOLS,
        previous_interaction_id=interaction.id,
    )

    answer = final.output_text
    if verbose:
        print(f"\n{GREEN}🤖 Assistant:{RESET} {answer}")
    return answer


def chat_loop() -> None:
    """
    Start an interactive chat loop.
    Type 'quit', 'exit', or 'q' to escape.
    """
    print(f"\n{BOLD}{'═' * 50}{RESET}")
    print(f"{BOLD} The Honest Tool-Caller{RESET} {DIM}(Gemini Edition){RESET}")
    print(f" Weather • Calculator • Wikipedia")
    print(f" Type {CYAN}quit{RESET} to exit.")
    print(f"{BOLD}{'═' * 50}{RESET}")

    client = get_client()

    while True:
        try:
            user_input = input(f"\n{CYAN}▸ {RESET}").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n{DIM}bye 👋{RESET}")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print(f"{DIM}peace out ✌️{RESET}")
            break

        ask(user_input, client=client)


def run_tests() -> None:
    """
    Fire all 3 tools with test queries to ensure the pipeline is operational.
    A simple smoke test suite for the CLI.
    """
    test_queries = [
        ("Weather", "What's the weather in Delhi right now?"),
        ("Calculator", "What is (2 + 3) * 4 - 1?"),
        ("Wikipedia", "Tell me about the Taj Mahal."),
    ]

    print(f"\n{BOLD}{'═' * 50}{RESET}")
    print(f"{BOLD} Smoke Test — firing all 3 tools{RESET}")
    print(f"{BOLD}{'═' * 50}{RESET}")

    client = get_client()

    for label, query in test_queries:
        print(f"\n{BOLD}── {label} {'─' * (40 - len(label))}{RESET}")
        ask(query, client=client)

    print(f"\n{GREEN}✓ All tests fired.{RESET}\n")


def main() -> None:
    """
    CLI Entrypoint.
    Parses arguments and delegates to the appropriate command.
    """
    parser = argparse.ArgumentParser(
        prog="honest-tool-caller",
        description="A CLI assistant that refuses to hallucinate. Uses real tools.",
    )
    subparsers = parser.add_subparsers(dest="command")

    # `ask` subcommand
    ask_parser = subparsers.add_parser("ask", help="Ask a single question")
    ask_parser.add_argument("query", type=str, help="Your question")

    # `chat` subcommand
    subparsers.add_parser("chat", help="Interactive chat loop")

    # `test` subcommand
    subparsers.add_parser("test", help="Run smoke tests for all 3 tools")

    args = parser.parse_args()

    if args.command == "ask":
        ask(args.query)
    elif args.command == "chat":
        chat_loop()
    elif args.command == "test":
        run_tests()
    else:
        parser.print_help()
        print(f"\n{DIM}Try: python main.py chat{RESET}")


if __name__ == "__main__":
    main()
