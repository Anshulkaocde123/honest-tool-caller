#!/usr/bin/env python3
"""
The Honest Tool-Caller — a CLI assistant that refuses to hallucinate.
It checks weather, does math, and searches Wikipedia by actually calling
real APIs instead of making stuff up. What a concept.

Usage:
  python main.py ask "What's the weather in Delhi?"
  python main.py chat
  python main.py test
"""

import argparse
import json
import os
import sys

from dotenv import load_dotenv
from google import genai

from tools import ALL_TOOLS
from tool_handlers import execute_tool

load_dotenv()

# ── pretty colors (no extra deps, just ANSI) ────────────────────────────────

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"


def get_client():
    """Create a Gemini client or die trying."""

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "paste-your-gemini-api-key-here":
        print(f"{RED}✗ No API key found.{RESET}")
        print(f"  Get one free at: {CYAN}https://aistudio.google.com/apikey{RESET}")
        print(f"  Then put it in .env: GEMINI_API_KEY=your-key-here")
        sys.exit(1)

    return genai.Client(api_key=api_key)


def ask(query: str, client=None, verbose: bool = True):
    """
    Send a query through the full tool-calling pipeline.
    Two round trips: ask → tool call → execute → feed back → final answer.
    """

    if client is None:
        client = get_client()

    if verbose:
        print(f"\n{BOLD}You:{RESET} {query}")
        print(f"{DIM}  ↳ sending to gemini...{RESET}")

    # round 1: send the question with our tool schemas
    interaction = client.interactions.create(
        model="gemini-2.5-flash",
        input=query,
        tools=ALL_TOOLS,
    )

    # check if gemini wants to call a tool
    tool_calls = [s for s in interaction.steps if s.type == "function_call"]

    if not tool_calls:
        # no tool needed — gemini answered directly
        answer = interaction.output_text
        if verbose:
            print(f"\n{GREEN}🤖 Assistant:{RESET} {answer}")
        return answer

    # execute each tool call locally
    results = []
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

    # round 2: feed the tool results back
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


def chat_loop():
    """Interactive chat. Type 'quit' or 'exit' when you've had enough."""

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


def run_tests():
    """Fire all 3 tools with test queries to make sure everything works."""

    test_queries = [
        ("🌤️  Weather", "What's the weather in Delhi right now?"),
        ("🔢 Calculator", "What is (2 + 3) * 4 - 1?"),
        ("📚 Wikipedia", "Tell me about the Taj Mahal."),
    ]

    print(f"\n{BOLD}{'═' * 50}{RESET}")
    print(f"{BOLD} Smoke Test — firing all 3 tools{RESET}")
    print(f"{BOLD}{'═' * 50}{RESET}")

    client = get_client()

    for label, query in test_queries:
        print(f"\n{BOLD}── {label} {'─' * (40 - len(label))}{RESET}")
        ask(query, client=client)

    print(f"\n{GREEN}✓ All tests fired.{RESET}\n")


def main():
    parser = argparse.ArgumentParser(
        prog="honest-tool-caller",
        description="A CLI assistant that refuses to hallucinate. Uses real tools.",
    )
    subparsers = parser.add_subparsers(dest="command")

    # ask subcommand
    ask_parser = subparsers.add_parser("ask", help="Ask a single question")
    ask_parser.add_argument("query", type=str, help="Your question")

    # chat subcommand
    subparsers.add_parser("chat", help="Interactive chat loop")

    # test subcommand
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
