# Evaluation Results

## Standard Test Suite

Command run:

```powershell
Remove-Item Env:LIVE_SEVERE_CITY -ErrorAction SilentlyContinue
python -m unittest evals.test_cases -v
```

Result:

```text
Ran 10 tests in 0.120s

OK (skipped=1)
```

Summary:

- Passed: 9
- Failed: 0
- Skipped: 1

## Passed Tests

| Test | What it verifies | Result |
|---|---|---|
| High-wind cycling SOP | Cycling with wind speed of 45 km/h selects SOP-001 | Passed |
| High-UV jogging SOP | Jogging with high UV selects SOP-002 | Passed |
| Cycling paraphrase | “Bike” is matched to cycling policy | Passed |
| Fuzzy picnic SOP | Picnic question matches a qualitative/non-numeric SOP | Passed |
| No-SOP response | Unknown activity receives no invented guidance | Passed |
| Severity selection | A high-severity SOP wins over a low-severity SOP | Passed |
| Adversarial input | User text cannot override policy matching | Passed |
| End-to-end SOP response | Response contains SOP ID and weather values | Passed |
| Weather API failure | Bot returns an honest weather-unavailable response | Passed |

## Live Severe-Weather Test

The live severe-weather test is skipped during the standard suite unless `LIVE_SEVERE_CITY` is set.

Two live attempts were made:

### Attempt 1: Bhopal

```text
Temperature: 24.0°C
Wind speed: 3.2 km/h
Precipitation: 0.0 mm
Rain probability: 0%
UV index: 0.0
Selected SOP: SOP-014
Severity: low
```

Result: Failed as expected. Bhopal had normal weather conditions and did not trigger a high-severity SOP.

### Attempt 2: Mumbai

```text
Temperature: 29.2°C
Wind speed: 6.0 km/h
Precipitation: 0.0 mm
Rain probability: 0%
UV index: 0.0
Selected SOP: SOP-014
Severity: low
```

Result: Failed as expected. Mumbai had normal weather conditions and did not trigger a high-severity SOP.

## Honest Limitation

The live severe-weather test has not yet passed because no tested city had active severe weather at the time of testing.

The test is designed to pass only when live weather selects a high-severity SOP. This avoids falsely treating normal weather as severe.

To rerun the live severe-weather test during an active weather event:

```powershell
$env:LIVE_SEVERE_CITY="CITY_NAME"
python -m unittest evals.test_cases.WeatherBotTests.test_live_severe_weather -v
```

The resulting city, weather values, selected SOP, and pass/fail result should be added to this file.