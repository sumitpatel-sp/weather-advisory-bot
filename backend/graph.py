from langgraph.graph import END, START, StateGraph

from backend.llm import build_sop_response, extract_intent
from backend.policy import match_sops
from backend.state import BotState
from backend.weather import fetch_weather, geocode_city, get_weather_for_period


def understand_query(state):
    try:
        intent = extract_intent(
            state["user_input"],
            state.get("messages", []),
        )
        state.update(intent)

    except Exception as error:
        state["error"] = f"Could not understand the request: {error}"

    return state


def resolve_location(state):
    if not state.get("location"):
        state["error"] = "No location was mentioned. Please specify a city."
        return state

    latitude, longitude, error = geocode_city(state["location"])

    if error:
        state["error"] = error
    else:
        state["latitude"] = latitude
        state["longitude"] = longitude

    return state


def fetch_weather_node(state):
    weather, error = fetch_weather(
        state["latitude"],
        state["longitude"],
    )

    if error:
        state["error"] = error
        return state

    selected_weather, error = get_weather_for_period(
        weather,
        state.get("time_period", "now"),
        state.get("target_hour"),
    )

    if error:
        state["error"] = error
    elif any(value is None for value in selected_weather.values()):
        state["error"] = "Weather API returned incomplete data for that time."
    else:
        state["weather"] = selected_weather

    return state


def match_sop_node(state):
    matched_sops, selected_sop = match_sops(
        state.get("activity", ""),
        state.get("target_group", "general"),
        state["weather"],
    )

    state["matched_sops"] = matched_sops
    state["selected_sop"] = selected_sop
    return state


def generate_response(state):
    state["response"] = build_sop_response(
        state["selected_sop"],
        state["weather"],
    )
    return state


def no_guidance_response(state):
    activity = state.get("activity") or "that activity"

    state["response"] = (
        f"I found no written safety SOP that applies to {activity} under the "
        "available weather conditions. I cannot give a policy-based recommendation."
    )
    return state


def error_response(state):
    error = state.get("error", "")
    error_lower = error.lower()

    if "understand" in error_lower or "api_key" in error_lower or "quota" in error_lower or "gemini" in error_lower:
        state["response"] = f"Unable to process query with AI: {error}"
    elif "location" in error_lower or "geocod" in error_lower or "resolve" in error_lower:
        state["response"] = "I could not resolve that location. Please specify a valid city."
    else:
        state["response"] = f"Live weather data is temporarily unavailable: {error}"

    return state


def route_error_or_location(state):
    return "error_response" if state.get("error") else "resolve_location"


def route_error_or_weather(state):
    return "error_response" if state.get("error") else "fetch_weather"


def route_error_or_sop(state):
    return "error_response" if state.get("error") else "match_sop"


def route_sop(state):
    if state.get("selected_sop"):
        return "generate_response"

    return "no_guidance_response"


def build_graph():
    graph = StateGraph(BotState)

    graph.add_node("understand_query", understand_query)
    graph.add_node("resolve_location", resolve_location)
    graph.add_node("fetch_weather", fetch_weather_node)
    graph.add_node("match_sop", match_sop_node)
    graph.add_node("generate_response", generate_response)
    graph.add_node("no_guidance_response", no_guidance_response)
    graph.add_node("error_response", error_response)

    graph.add_edge(START, "understand_query")

    graph.add_conditional_edges(
        "understand_query",
        route_error_or_location,
        {
            "resolve_location": "resolve_location",
            "error_response": "error_response",
        },
    )

    graph.add_conditional_edges(
        "resolve_location",
        route_error_or_weather,
        {
            "fetch_weather": "fetch_weather",
            "error_response": "error_response",
        },
    )

    graph.add_conditional_edges(
        "fetch_weather",
        route_error_or_sop,
        {
            "match_sop": "match_sop",
            "error_response": "error_response",
        },
    )

    graph.add_conditional_edges(
        "match_sop",
        route_sop,
        {
            "generate_response": "generate_response",
            "no_guidance_response": "no_guidance_response",
        },
    )

    graph.add_edge("generate_response", END)
    graph.add_edge("no_guidance_response", END)
    graph.add_edge("error_response", END)

    return graph.compile()


agent = build_graph()


def run_agent(user_input, messages):
    initial_state = {
        "messages": messages,
        "user_input": user_input,
        "activity": "",
        "location": "",
        "time_period": "now",
        "target_hour": None,
        "target_group": "general",
        "weather": {},
        "matched_sops": [],
        "selected_sop": None,
        "error": "",
        "response": "",
    }

    result = agent.invoke(initial_state)
    return result["response"]