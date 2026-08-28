<p align="center">
  <img src="assets/banner.png" alt="The Honest Tool-Caller Banner" width="100%"/>
</p>

<p align="center">
  <strong>An AI assistant that refuses to hallucinate.</strong><br/>
  Weather. Math. Wikipedia. Powered by real APIs, not imagination.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10+-blue?style=flat-square&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/Gemini-Interactions_API-4285F4?style=flat-square&logo=google&logoColor=white" alt="Gemini"/>
  <img src="https://img.shields.io/badge/tests-32_passing-brightgreen?style=flat-square" alt="Tests"/>
  <img src="https://img.shields.io/badge/eval()-absolutely_not-red?style=flat-square" alt="No eval()"/>
  <img src="https://img.shields.io/badge/license-MIT-yellow?style=flat-square" alt="License"/>
</p>

---

## The Elevator Pitch

Most LLMs will confidently tell you it's 25 degrees in Delhi right now. They're lying. They don't know. They've never checked. They're just statistically predicting what a helpful answer looks like.

This project doesn't do that.

When you ask "What's the weather in Delhi?", it **actually calls a weather API**. When you ask "What's 2^10?", it **actually computes it** instead of guessing. When you ask about the Taj Mahal, it **actually searches Wikipedia** instead of regurgitating training data.

The model decides *what* to do. Your code decides *how* to do it. Nobody makes anything up. That's the deal.

Built with Google's Gemini Interactions API. No LangChain. No LlamaIndex. No frameworks. Just a human, an API, and a healthy distrust of neural networks doing arithmetic.

---

## Table of Contents

- [How It Works (The Architecture)](#how-it-works-the-architecture)
- [The Tool Roster](#the-tool-roster)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Architecture Deep Dive](#architecture-deep-dive)
  - [The Two-Round-Trip Pattern](#the-two-round-trip-pattern)
  - [The Dispatcher Pattern](#the-dispatcher-pattern)
  - [The ReAct Loop](#the-react-loop)
- [Design Decisions (And Why)](#design-decisions-and-why)
- [Security](#security)
- [Testing](#testing)
  - [Test Philosophy](#test-philosophy)
  - [Test Categories](#test-categories)
  - [Tips for Testing API-Dependent Code](#tips-for-testing-api-dependent-code)
- [Key Concepts Explained](#key-concepts-explained)
- [Built With](#built-with)
- [License](#license)

---

## How It Works (The Architecture)

```
                    THE HONEST TOOL-CALLING PIPELINE
                    ================================

                        Round 1                            Round 2
               (ask the brain)                    (feed it real data)

  ┌─────────┐      ┌─────────────┐      ┌─────────┐      ┌─────────────┐
  │         │      │             │      │         │      │             │
  │   You   │─────>│   Gemini    │─────>│   You   │─────>│   Gemini    │
  │         │      │             │      │         │      │             │
  │ "What's │      │ "I need to  │      │ *runs*  │      │ "It's 33°C  │
  │ the     │      │  call       │      │ the     │      │  and hazy   │
  │ weather │      │  get_weather│      │ actual  │      │  in Delhi   │
  │ in      │      │  with       │      │ weather │      │  right now."│
  │ Delhi?" │      │  city=Delhi"│      │ API     │      │             │
  │         │      │             │      │         │      │             │
  └─────────┘      └─────────────┘      └─────────┘      └─────────────┘
     INPUT           TOOL CALL           EXECUTION         REAL ANSWER
  (your question)  (model's plan)    (your code runs)    (grounded in data)
```

**Two API round trips. Zero hallucination.** The model never pretends to know something it doesn't. It asks you to look it up, you look it up, and then it speaks from the actual data.

---

## The Tool Roster

| Tool | Trigger | What It Actually Does | API |
|------|---------|----------------------|-----|
| **Weather** | "What's the weather in X?" | Fetches real-time weather data | [wttr.in](https://wttr.in) (free, no key) |
| **Calculator** | "What's (2+3)*4?" | Safely evaluates math via AST parsing | Python `ast` module (local) |
| **Wikipedia** | "Tell me about X" | Searches and returns article summaries | [Wikipedia REST API](https://en.wikipedia.org/api/rest_v1/) (free, no key) |

---

## Quick Start

```bash
# 1. clone it
git clone https://github.com/Anshulkaocde123/honest-tool-caller.git
cd honest-tool-caller

# 2. set up python
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. get your free gemini API key at:
#    https://aistudio.google.com/apikey
#    (sign in with gmail, click "Create API key", done)

# 4. create a .env file
echo "GEMINI_API_KEY=paste-your-key-here" > .env

# 5. run it
python main.py chat
```

That's it. No Docker. No Kubernetes. No YAML files that are longer than the actual code.

---

## Usage

```bash
# ask a single question and get out
python main.py ask "What's the weather in Mumbai?"

# interactive chat — keeps going until you say quit
python main.py chat

# smoke test — fires all 3 tools to make sure everything works
python main.py test
```

### Example Session

```
══════════════════════════════════════════════════
 The Honest Tool-Caller (Gemini Edition)
 Weather . Calculator . Wikipedia
 Type quit to exit.
══════════════════════════════════════════════════

> What's the weather in Delhi right now?
  sending to gemini...
  calling get_weather({'city': 'Delhi'})
    -> Weather in Delhi: Haze, 33°C, Humidity: 62%

  Assistant: The weather in Delhi right now is hazy with
  a temperature of 33°C and humidity at 62%.

> What's 2 to the power of 10?
  calling calculate({'expression': '2 ** 10'})
    -> 2 ** 10 = 1024

  Assistant: 2 to the power of 10 is 1024.

> quit
peace out
```

---

## Project Structure

```
honest-tool-caller/
│
├── main.py              # the conductor — CLI + orchestration
│                          argparse (ask/chat/test), Gemini API calls,
│                          two-round-trip pipeline, ANSI colored output
│
├── tools.py             # the menu — what Gemini sees
│                          three JSON Schema tool definitions that tell
│                          the model what functions exist and when to use them
│
├── tool_handlers.py     # the kitchen — what actually runs
│                          dispatcher (dict registry), weather handler (wttr.in),
│                          calculator (AST-safe, no eval), wikipedia handler
│
├── tests/
│   ├── test_tools.py    # schema structure validation (7 tests)
│   └── test_handlers.py # calculator, dispatcher, mocked HTTP (25 tests)
│
├── assets/
│   └── banner.png       # the pretty picture at the top
│
├── requirements.txt     # dependencies
├── .gitignore           # keeps .env and __pycache__ out of git
├── LICENSE              # MIT
└── README.md            # you are here
```

### Why This File Structure?

The separation isn't just organizational aesthetics — it's a design principle called **Separation of Concerns**:

- **`tools.py`** (Schema) can change without touching any logic. You can rename a parameter, rewrite a description, add a new tool — and nothing else breaks.
- **`tool_handlers.py`** (Logic) can swap API providers without touching schemas or orchestration. Switch from wttr.in to OpenWeatherMap? One file changes.
- **`main.py`** (Orchestration) can swap Gemini for Claude or GPT-4 without touching tools or handlers.

Every production agent system you'll ever see follows this pattern. Learn it now.

---

## Architecture Deep Dive

### The Two-Round-Trip Pattern

This is the core mechanism. Every tool-calling system — LangChain, LangGraph, CrewAI — uses this under the hood.

```python
# ROUND 1: "Hey Gemini, here's a question and here are tools you can use"
interaction = client.interactions.create(
    model="gemini-2.5-flash",
    input="What's the weather in Delhi?",
    tools=ALL_TOOLS,  # <-- the menu of available functions
)

# Gemini doesn't answer. Instead it says:
# "Call get_weather with city='Delhi'"
# interaction.steps contains a step with type="function_call"

# ROUND 2: "Here's what the tool returned. Now answer the question."
final = client.interactions.create(
    model="gemini-2.5-flash",
    input=function_results,                    # the real weather data
    tools=ALL_TOOLS,
    previous_interaction_id=interaction.id,    # links the turns together
)

print(final.output_text)  # "It's 33°C and hazy in Delhi."
```

**Key insight:** `previous_interaction_id` is what gives Gemini memory between rounds. Without it, Round 2 would have no idea what question was asked in Round 1.

### The Dispatcher Pattern

Instead of a wall of `if/elif/elif/elif` (which becomes unreadable at 10+ tools), we use a dictionary registry:

```python
registry = {
    "get_weather":      handle_get_weather,      # tool_name → function
    "calculate":        handle_calculate,
    "search_wikipedia": handle_search_wikipedia,
}

handler = registry.get(tool_name)  # O(1) lookup, no matter how many tools
handler(**arguments)               # call it with the model's arguments
```

Adding a new tool = adding one line to the dictionary + writing the handler function. No orchestration code changes. No schema code changes. Just plug and play.

### The ReAct Loop

What we've built is the **ReAct** (Reasoning + Acting) pattern, published in [Yao et al., 2022](https://arxiv.org/abs/2210.03629):

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│   REASON ──────> ACT ──────> OBSERVE ──────> ANSWER          │
│                                                              │
│   Gemini         Your        Gemini          Gemini          │
│   reads the      code        sees the        formulates      │
│   question and   executes    real data       a natural       │
│   picks a tool   the tool    and grounds     language        │
│   + arguments    locally     its response    answer          │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

This is the same loop that every agent framework runs:
- **LangChain's** `AgentExecutor` = this loop with extra middleware
- **LangGraph's** tool nodes = this loop as a state machine
- **CrewAI's** task execution = this loop with role-playing

We just built it with zero abstraction. That's the point.

---

## Design Decisions (And Why)

### "Why not use LangChain or some framework?"

Because frameworks hide the mechanism. If LangChain's `AgentExecutor` breaks, and you don't understand what it's doing under the hood, you're stuck Googling error messages at 2 AM with no mental model of what went wrong.

Build it raw first. Use frameworks later *knowing what they abstract*.

### "Why return errors as strings instead of raising exceptions?"

In agent systems, crashing is the worst possible outcome. If the weather API is down and your code throws an unhandled exception, the entire conversation dies.

Instead, we return `"Error: could not reach weather service"` as a string. The model receives this and can say: *"I'm sorry, the weather service is currently unavailable. Can I help with something else?"*

This is called **graceful degradation** — the system keeps running even when parts of it fail.

### "Why dict registry instead of if/elif?"

Three reasons:
1. **O(1) lookup** — constant time, no matter how many tools
2. **Extensibility** — adding a new tool = adding one line
3. **Testability** — you can inspect the registry programmatically

At 3 tools, if/elif works fine. At 15 tools, it's a nightmare. Build the right habit now.

### "Why truncate Wikipedia to 1000 characters?"

Three reasons that matter in production:
1. **Cost** — you pay per token. 5000 words of Wikipedia = expensive
2. **Signal-to-noise** — the model answers better with 200 relevant words than 5000 words where 90% is irrelevant
3. **Latency** — longer inputs take longer to process

Give the model the *minimum context* needed to answer well. This is the same principle behind RAG chunking strategies.

### "Why `gemini-2.5-flash` and not `pro`?"

Flash is fast, cheap, and good enough for tool-calling. The model isn't writing poetry — it's deciding which function to call and extracting arguments from natural language. Flash handles this perfectly. Save `pro` for tasks that need deeper reasoning.

---

## Security

### The Calculator Problem

The model sends us a string like `"2 + 3 * 4"`. We need to evaluate it.

**The tempting (catastrophic) way:**
```python
result = eval(expression)  # DO NOT DO THIS
```

**Why it's catastrophic:**
```python
# The model could be tricked into calling:
calculate(expression="__import__('os').system('rm -rf /')")
# eval() would happily execute this. Your filesystem is gone.
```

This attack is called **prompt injection** — a malicious user crafts input that makes the model generate dangerous tool arguments.

**Our approach: AST whitelisting**

```
   "2 + 3 * 4" ──parse──> Abstract Syntax Tree ──walk──> result

        BinOp(Add)
        /        \
      Num(2)    BinOp(Mult)      We walk each node.
                /        \       Only Num, Add, Sub, Mult, Div, Pow allowed.
              Num(3)    Num(4)   Everything else? Blocked.
```

This is a **whitelist** approach: we explicitly allow safe operations and block everything else. The alternative (blacklisting dangerous operations) always has gaps — there's always some creative exploit you forgot to block.

### API Key Safety

- Keys live in `.env` (which is in `.gitignore` — never committed)
- The code checks for placeholder values and exits with a helpful message
- Bots scan GitHub for leaked API keys within minutes. Treat them like passwords

### HTTP Timeouts

Every external HTTP call has `timeout=10`. Without this, a dead API server would hang your program forever. Always set timeouts. Always.

---

## Testing

### Running Tests

```bash
# activate your venv first
source venv/bin/activate

# run all 32 tests with verbose output
pytest tests/ -v

# run just calculator tests
pytest tests/test_handlers.py::TestCalculator -v

# run just security tests
pytest tests/test_handlers.py::TestCalculator::test_blocks_eval_injection -v
```

### Test Philosophy

> *"Tests exist to catch the bugs you don't think exist."*

Our tests follow three principles:

1. **No network calls.** Tests that hit real APIs are flaky, slow, and break on airplanes. We mock everything.
2. **Security tests are first-class citizens.** The eval injection test isn't a nice-to-have — it's the most important test in the suite.
3. **Test behavior, not implementation.** We test "does it return an error?" not "does it call a specific internal function?"

### Test Categories

| Category | Count | What's Being Tested |
|----------|-------|--------------------|
| **Calculator Math** | 8 | Addition, subtraction, multiplication, division, exponents, order of ops, parentheses, negatives |
| **Calculator Security** | 4 | eval injection, function calls, string literals, syntax errors |
| **Calculator Edge Cases** | 2 | Division by zero, empty expression |
| **Dispatcher Routing** | 4 | Known tools, unknown tools, bad arguments, all-registered check |
| **Weather (mocked)** | 3 | Success response, network error, malformed response |
| **Wikipedia (mocked)** | 4 | Success, 404 not found, truncation of long articles, network failure |
| **Schema Validation** | 7 | Structure, required fields, types, no duplicates, description length |
| **Total** | **32** | |

### Tips for Testing API-Dependent Code

These patterns apply to any project that calls external APIs:

**1. Mock at the boundary, not inside your code**
```python
# Good: mock requests.get (the external boundary)
@patch("tool_handlers.requests.get")
def test_weather(self, mock_get):
    mock_get.return_value = ...

# Bad: mock your own internal functions
# (you'd be testing the mock, not the code)
```

**2. Test the sad path harder than the happy path**

The happy path usually works. What breaks production is:
- Network timeouts
- Malformed JSON responses
- 404s and 500s
- Empty response bodies
- Rate limiting

Write a test for each of these.

**3. Never depend on external state in tests**

```python
# Bad: actually calls the weather API (fails without internet)
def test_weather():
    result = handle_get_weather("Delhi")
    assert "Delhi" in result

# Good: mocked, deterministic, works on an airplane
@patch("tool_handlers.requests.get")
def test_weather(self, mock_get):
    mock_get.return_value = fake_response(temp="33", desc="Sunny")
    result = handle_get_weather("Delhi")
    assert "33" in result
```

**4. Separate "does the API integration work?" from "does my code work?"**

- **Unit tests** (what we have): test your code with mocked APIs. Run on every commit.
- **Integration tests** (optional): test against real APIs. Run manually, not in CI. The `python main.py test` command serves this purpose.

---

## Key Concepts Explained

### Tool Schemas — The Contract Between You and the Model

A tool schema isn't just metadata. It's a **contract**:

```
"Here's a function called get_weather.
 It takes a city name as a string.
 Use it when someone asks about weather."
```

The model *reads* this description (literally, it's in the prompt) and uses it to decide:
1. **When** to use the tool (match user intent to description)
2. **What** arguments to pass (extract from the user's message)

If your description is vague ("does stuff with data"), the model will pick the wrong tool. If your parameter description is unclear ("input: string"), the model will send garbage arguments. Schema design is the #1 reason tool-calling "just doesn't work."

### Gemini Interactions API vs. OpenAI

| Feature | OpenAI | Gemini |
|---------|--------|--------|
| API call | `client.chat.completions.create()` | `client.interactions.create()` |
| Tool calls in response | `message.tool_calls` | `interaction.steps` (filter by `type`) |
| Arguments format | JSON **string** (must `json.loads()`) | Already a Python **dict** |
| Linking turns | Manually manage messages list | `previous_interaction_id` |
| Final answer | `message.content` | `interaction.output_text` |

Gemini's biggest convenience: `step.arguments` is already parsed. No `json.loads()`, no crash when the model produces invalid JSON. One less thing to screw up.

### Graceful Degradation

Every handler returns a string — even on failure:

```python
try:
    return f"Weather in {city}: {desc}, {temp}°C"
except requests.RequestException as e:
    return f"Could not fetch weather for '{city}': {e}"
    # ^ the model can work with this. it can't work with a dead process.
```

The model receives the error string and can say something helpful:
> "I wasn't able to reach the weather service right now. Want to try again?"

Crashing is never the answer. Return errors as data.

---

## Built With

| Component | What | Why |
|-----------|------|-----|
| [Google Gemini API](https://ai.google.dev/gemini-api/docs) | Interactions API with function calling | The brain — decides what tool to call |
| [wttr.in](https://wttr.in) | Free weather API | No signup, returns JSON, reliable enough |
| [Wikipedia REST API](https://en.wikipedia.org/api/rest_v1/) | Article summaries | Free knowledge, structured JSON |
| Python `ast` module | Safe math evaluation | Because `eval()` is a war crime |
| [pytest](https://docs.pytest.org/) | Test framework | 32 tests, zero network dependencies |

## Why Gemini Instead of Others?

If you're wondering why we chose Google's Gemini over OpenAI (GPT-4) or Anthropic (Claude) for this project:

1. **Free Tier Generosity:** Gemini's free tier (via AI Studio) is incredibly generous for developers building side projects and learning agentic patterns. You don't need to pull out a credit card to run these tests.
2. **Native Dict Arguments:** In Gemini's Interactions API, when the model requests a tool call, `step.arguments` is already parsed into a native Python dictionary. With OpenAI, `tool_call.function.arguments` is a raw JSON string that you have to parse yourself (and hope the model didn't hallucinate invalid JSON). Gemini handles the parsing safely for you.
3. **Speed:** `gemini-2.5-flash` is blisteringly fast, which is critical for tool-calling where you have multiple round-trips before answering the user.

---

## Is It Deployed? (Can Anyone Use It?)

**Yes, the code is public and ready to use!** 

Because this is a CLI (Command Line Interface) tool rather than a centralized web app, it runs locally on your machine. This is a feature, not a bug: it means you aren't sending your private data or API keys to our servers. You run the brain (Gemini) and the hands (the local Python scripts) entirely on your own hardware.

Anyone can use it right now by following these 3 steps:
1. Clone this repository to your local machine.
2. Get your own free Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey).
3. Run `python main.py chat` in your terminal.

---

## License

MIT — do whatever you want with it. Just don't use `eval()` in production and then blame me.

---

<p align="center">
  <sub>Built by <a href="https://github.com/Anshulkaocde123">Anshul Jain</a> — because someone had to teach AI to be honest.</sub>
</p>
