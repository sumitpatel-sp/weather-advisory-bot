import os
import yaml

SEVERITY_ORDER = {"high": 3, "moderate": 2, "low": 1}

ACTIVITY_ALIASES = {
    "cycling": {"cycling", "cycle", "bike", "biking", "bicycle", "ride a bike"},
    "running": {"running", "run", "jog", "jogging"},
    "outdoor_exercise": {"exercise", "workout", "walking", "walk", "hiking", "hike"},
    "two_wheeler": {"two wheeler", "two-wheeler", "scooter", "motorcycle", "motorbike"},
    "travel": {"travel", "drive", "driving", "commute", "road trip"},
    "picnic": {"picnic", "barbecue", "bbq", "outdoor lunch"},
}


def load_sops():
    path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "policies",
        "sops.yaml",
    )

    with open(path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file) or []


def resolve_activities(activity, target_group):
    normalized = (activity or "").strip().lower()
    activities = set()

    for canonical, aliases in ACTIVITY_ALIASES.items():
        if normalized == canonical or normalized in aliases:
            activities.add(canonical)

    if normalized and not activities:
        activities.add(normalized)

    group = (target_group or "").lower()

    if group == "children":
        activities.add("children_outdoor")
    elif group == "elderly":
        activities.add("elderly_outdoor")
    elif group == "pets":
        activities.add("pets_outdoor")

    return activities


def is_relevant(sop_activity, activities):
    if sop_activity in activities:
        return True

    return (
        sop_activity == "outdoor_exercise"
        and bool(activities & {"cycling", "running", "outdoor_exercise"})
    )


def compare(actual, operator, expected):
    if operator == ">=":
        return actual >= expected
    if operator == ">":
        return actual > expected
    if operator == "<=":
        return actual <= expected
    if operator == "<":
        return actual < expected
    if operator == "==":
        return actual == expected

    return False


def condition_matches(sop, weather):
    condition_type = sop.get("condition_type")

    if condition_type == "always":
        return True

    if condition_type == "threshold":
        value = weather.get(sop.get("field"))
        return value is not None and compare(
            value,
            sop.get("operator"),
            sop.get("value"),
        )

    if condition_type == "composite":
        conditions = sop.get("conditions", [])
        minimum = sop.get("min_conditions", len(conditions))

        matched_count = sum(
            1
            for condition in conditions
            if weather.get(condition["field"]) is not None
            and compare(
                weather[condition["field"]],
                condition["operator"],
                condition["value"],
            )
        )

        return matched_count >= minimum

    return False


def match_sops(activity, target_group, weather, sops=None):
    sops = sops or load_sops()
    activities = resolve_activities(activity, target_group)

    matches = [
        sop
        for sop in sops
        if is_relevant(sop.get("activity", ""), activities)
        and condition_matches(sop, weather)
    ]

    matches.sort(
        key=lambda sop: SEVERITY_ORDER.get(sop.get("severity", "low"), 0),
        reverse=True,
    )

    return matches, matches[0] if matches else None