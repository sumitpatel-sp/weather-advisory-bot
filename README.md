# Weather Advisory Support Bot

A Streamlit chatbot that provides outdoor activity safety recommendations using live Open-Meteo weather data and written Standard Operating Procedures (SOPs).

The bot does not invent safety advice. Every recommendation is linked to a specific SOP. If no written SOP applies, the bot clearly says that it cannot provide a policy-based recommendation.

## Features

- Streamlit chat interface
- LangGraph workflow with real branching
- Live city geocoding and weather data from Open-Meteo
- Gemini used only for intent extraction
- YAML-based SOP rules
- Deterministic SOP matching
- Session memory for follow-up questions
- Exact-hour weather support, such as “tomorrow at 12 PM”
- Automated evaluation suite

## Technology Stack

- Python
- Streamlit
- LangGraph
- Gemini through LangChain Google GenAI
- Open-Meteo API
- Requests
- PyYAML
- Python unittest

## Project Structure

```text
weather-advisory-bot/
├── backend/
│   ├── __init__.py
│   ├── graph.py
│   ├── state.py
│   ├── llm.py
│   ├── weather.py
│   └── policy.py
├── frontend/
│   └── app.py
├── policies/
│   └── sops.yaml
├── evals/
│   ├── test_cases.py
│   └── results.md
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Why YAML is Used for SOPs

SOPs are stored in YAML so that policies can be added or changed without editing the LangGraph workflow, weather API logic, frontend, or LLM code.

## Setup

### 1. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Configure Gemini

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your-gemini-api-key
```

Do not commit or submit `.env`.

Use `.env.example` in the submission:

```env
GEMINI_API_KEY=your-gemini-api-key-here
```

## Run the Application

From the project root:

```powershell
streamlit run frontend\app.py
```

Example questions:

```text
Is it safe to cycle in Bhopal today?
Can I walk in Bhopal tomorrow at 12 PM?
Should I take my child to the park in Delhi?
Is it a good day for a picnic in Mumbai?
What about this evening instead?
```

## LangGraph Workflow

```text
User question
    |
    v
understand_query
    |
    v
resolve_location
    |---------------- location failure ----------------> error_response
    v
fetch_weather
    |---------------- weather failure -----------------> error_response
    v
match_sop
    |---------------- no SOP match --------------------> no_guidance_response
    v
generate_response
    |
    v
END
```

The graph has separate paths for:

- Intent-extraction failure
- Missing or unresolved location
- Weather API failure
- No matching SOP
- Successful SOP-based response

## LLM Boundary

Gemini is used only to extract structured information from a natural-language question:

- Activity
- City
- Time period
- Exact hour, when supplied
- Target group

Gemini does not make the safety decision.

The final answer is generated deterministically from:

1. The selected SOP
2. The actual weather values returned by Open-Meteo

This prevents unsupported safety advice and invented weather values.

## Weather Data

The bot uses Open-Meteo for:

- City geocoding
- Current weather
- Hourly weather forecasts

The application requests and uses:

- Temperature
- Wind speed
- Precipitation
- Rain probability
- UV index

For an exact-time question such as “tomorrow at 12 PM,” the bot uses the corresponding hourly forecast. For a question such as “this evening,” it evaluates weather during the evening period.

## SOP Rules

SOPs are defined in `policies/sops.yaml`.

The project includes at least 10 SOPs across these categories:

- Outdoor exercise
- Travel
- Vulnerable groups
- Picnic planning

The rule set includes high, moderate, and low severity levels.

Examples include:

- High wind while cycling
- High UV during outdoor exercise
- High rain probability during travel
- Extreme heat for children, elderly people, and pets
- A fuzzy non-numeric picnic-planning SOP
- A low-severity cycling SOP for conditions below high-risk thresholds

## SOP Matching

The policy matcher:

1. Resolves activity paraphrases such as `cycle`, `bike`, `jogging`, and `walk`.
2. Finds relevant SOPs.
3. Checks written weather conditions.
4. Selects the highest-severity matching SOP.

Severity priority:

```text
high > moderate > low
```

Every successful response includes the SOP ID and actual weather values.

If no SOP applies, the bot does not invent generic advice. It clearly says that no written SOP applies.

## Session Memory

Conversation history is stored in Streamlit session state.

This supports follow-up questions such as:

```text
User: Is it safe to cycle in Bhopal today?
User: What about this evening instead?
```

Memory lasts only during the active Streamlit session.

## Evaluation Suite

Run the standard tests:

```powershell
Remove-Item Env:LIVE_SEVERE_CITY -ErrorAction SilentlyContinue
python -m unittest evals.test_cases -v
```

Current standard test result:

```text
Ran 10 tests in 0.120s

OK (skipped=1)
```

Summary:

- Passed: 9
- Failed: 0
- Skipped: 1

The test suite covers:

- High-wind cycling SOP selection
- High-UV jogging SOP selection
- Cycling paraphrase using “bike”
- Fuzzy picnic SOP
- No-SOP behavior
- Highest-severity SOP selection
- Adversarial input
- End-to-end SOP response containing an SOP ID and weather values
- Simulated weather API failure
- Live severe-weather evaluation

## Live Severe-Weather Evaluation

The assignment requires a genuine live severe-weather test.

Run it only with a city currently experiencing severe weather:

```powershell
$env:LIVE_SEVERE_CITY="CITY_NAME"
python -m unittest evals.test_cases.WeatherBotTests.test_live_severe_weather -v
```

The test passes only if a high-severity SOP is selected.

Bhopal and Mumbai were tested during development, but both had normal weather conditions. They selected low-severity SOP-014, so they correctly failed the severe-weather test.

This confirms that the test does not falsely classify normal weather as severe.

Before final submission, run this test again using a city under a genuine active weather warning. Record the city, weather values, selected SOP, date, and result in `evals/results.md`.

## Security

- `.env` is excluded through `.gitignore`.
- API keys must never be committed or included in the ZIP.
- The submission must not include `venv/`, `.env`, `__pycache__/`, or `.git/`.
- If an API key was exposed in a previous ZIP, it must be rotated and revoked.

## Adding an SOP

Add a new rule by editing only `policies/sops.yaml`.

Example:

```yaml
- id: SOP-015
  category: travel
  activity: travel
  severity: moderate
  condition_type: threshold
  field: wind_speed
  operator: ">="
  value: 35
  advice: "Travel only if necessary because strong wind may affect vehicle control."
```

No changes are needed in the graph, weather code, frontend, or LLM code.

## Limitations

- Open-Meteo availability can affect live requests.
- The first geocoding result is used for a city name.
- Session memory resets when the app restarts.
- The bot can provide advice only when a written SOP applies.
- A live severe-weather test depends on actual current weather and may not pass on a normal-weather day.

## Submission Checklist

Include:

- Source code
- `README.md`
- `requirements.txt`
- `.env.example`
- `.gitignore`
- `policies/sops.yaml`
- `evals/test_cases.py`
- Completed `evals/results.md`

Do not include:

- `.env`
- `venv`
- `__pycache__`
- API keys
- Python cache files