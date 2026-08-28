# 🤖 The Honest Tool-Caller

> A CLI assistant that refuses to hallucinate. It checks weather, does math, and searches Wikipedia by actually calling real APIs instead of making stuff up. What a concept.

Built with Google's **Gemini API** — no LangChain, no LlamaIndex, no frameworks. Just raw tool-calling, the way the gods intended.

## What It Does

| Tool | What It Handles | How |
|------|----------------|-----|
| 🌤️ **Weather** | "What's the weather in Delhi?" | [wttr.in](https://wttr.in) — free, no key |
| 🔢 **Calculator** | "What's (2 + 3) * 4?" | Safe AST parsing (not `eval()`, we're not animals) |
| 📚 **Wikipedia** | "Tell me about quantum computing" | Wikipedia REST API — free, no key |

## How It Works

```
You → Gemini → "call get_weather(city='Delhi')" → Your code runs it → Result → Gemini → "It's 35°C and sunny"
```

The model **decides** which tool to use. **You** execute it. The model **reads** the real data and answers honestly. Two API round trips, zero hallucination.

This is the **ReAct pattern** (Reason → Act → Observe) — the same loop that powers every AI agent framework under the hood.

## Quick Start

```bash
# 1. clone it
git clone https://github.com/Anshulkaocde123/honest-tool-caller.git
cd honest-tool-caller

# 2. set up python env
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. get your free gemini API key
#    → https://aistudio.google.com/apikey

# 4. configure
cp .env.example .env
# edit .env and paste your key

# 5. run it
python main.py chat
```

## Usage

```bash
# ask a single question
python main.py ask "What's 2 ** 10?"

# interactive chat
python main.py chat

# smoke test all 3 tools
python main.py test
```

## Running Tests

```bash
pytest tests/ -v
```

## Project Structure

```
honest-tool-caller/
├── main.py            # CLI entry point (argparse, the whole pipeline)
├── tools.py           # Tool schemas (what Gemini sees)
├── tool_handlers.py   # Tool implementations (what actually runs)
├── tests/
│   ├── test_tools.py      # Schema structure validation
│   └── test_handlers.py   # Calculator, dispatcher, mocked HTTP
├── requirements.txt
├── .env.example
└── .gitignore
```

## Why "Honest"?

Most LLMs will confidently tell you the weather is 25°C in Delhi right now. They're making it up. This tool-caller **actually checks** — and if the API is down, it says so instead of inventing data.

Honesty > confidence.

## Security

- API keys stored in `.env` (never committed)
- Calculator uses **AST whitelisting** — only numbers and `+`, `-`, `*`, `/`, `**` allowed
- No `eval()`. Ever. [Here's why](https://xkcd.com/327/).
- HTTP timeouts on all external calls

## Built With

- [Google Gemini API](https://ai.google.dev/gemini-api/docs) — Interactions API with function calling
- [wttr.in](https://wttr.in) — Free weather data
- [Wikipedia REST API](https://en.wikipedia.org/api/rest_v1/) — Free knowledge
- Python 3.10+

## License

MIT — do whatever you want, just don't blame me.
