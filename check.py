import json
import sys
from pathlib import Path
from uuid import UUID


ROOT = Path(__file__).resolve().parent
PIPELINES = [
    ROOT / "clip_index.pipe",
    ROOT / "tactics_upload.pipe",
    ROOT / ".github" / "demo.pipe",
]
CATALOG_PATH = ROOT / ".rocketride" / "services-catalog.json"


def fail(message):
    print(f"ERROR: {message}")
    return False


def load_catalog():
    with CATALOG_PATH.open("r", encoding="utf-8") as file:
        services = json.load(file)
    return {service["name"]: service for service in services}


def first_key(path):
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file, object_pairs_hook=dict)
    return next(iter(data.keys())), data


def provider_outputs(provider, lane):
    lanes = provider.get("lanes", {})
    outputs = []
    for output_lanes in lanes.values():
        outputs.extend(output_lanes)
    return lane in outputs


def validate_pipeline(path, catalog):
    ok = True
    relative = path.relative_to(ROOT)
    first, pipeline = first_key(path)

    if first != "components":
        ok = fail(f"{relative}: components must be the first top-level field") and ok

    components = pipeline.get("components")
    if not isinstance(components, list) or not components:
        return fail(f"{relative}: components must be a non-empty list")

    try:
        UUID(pipeline.get("project_id", ""))
    except ValueError:
        ok = fail(f"{relative}: project_id must be a literal UUID") and ok

    if pipeline.get("version") != 1:
        ok = fail(f"{relative}: version must be 1") and ok

    by_id = {}
    for component in components:
        component_id = component.get("id")
        provider_name = component.get("provider")
        if not component_id or not provider_name:
            ok = fail(f"{relative}: every component needs id and provider") and ok
            continue
        if component_id in by_id:
            ok = fail(f"{relative}: duplicate component id {component_id}") and ok
        by_id[component_id] = component
        if provider_name not in catalog:
            ok = fail(f"{relative}: unknown provider {provider_name} on {component_id}") and ok

    source_count = 0
    for component in components:
        provider = catalog.get(component.get("provider"), {})
        if "source" in provider.get("classType", []):
            source_count += 1
    if source_count != 1:
        ok = fail(f"{relative}: expected exactly one source component, found {source_count}") and ok

    for component in components:
        component_id = component.get("id")
        provider = catalog.get(component.get("provider"), {})
        target_lanes = provider.get("lanes", {})
        for connection in component.get("input", []):
            lane = connection.get("lane")
            source_id = connection.get("from")
            source_component = by_id.get(source_id)
            if not source_component:
                ok = fail(f"{relative}: {component_id} references missing input {source_id}") and ok
                continue
            source_provider = catalog.get(source_component.get("provider"), {})
            if lane not in target_lanes:
                ok = fail(f"{relative}: {component_id} does not accept lane {lane}") and ok
            if not provider_outputs(source_provider, lane):
                ok = fail(f"{relative}: {source_id} does not output lane {lane} for {component_id}") and ok

    controls_by_invoker = {}
    for component in components:
        component_id = component.get("id")
        provider = catalog.get(component.get("provider"), {})
        controlled_classes = set(provider.get("classType", []))
        for control in component.get("control", []):
            class_type = control.get("classType")
            invoker_id = control.get("from")
            invoker = by_id.get(invoker_id)
            invoker_provider = catalog.get(invoker.get("provider"), {}) if invoker else {}
            if not invoker:
                ok = fail(f"{relative}: {component_id} control references missing invoker {invoker_id}") and ok
                continue
            if class_type not in controlled_classes:
                ok = fail(f"{relative}: {component_id} is not a {class_type} control target") and ok
            if class_type not in invoker_provider.get("invoke", {}):
                ok = fail(f"{relative}: {invoker_id} does not invoke {class_type} controls") and ok
            controls_by_invoker.setdefault(invoker_id, {}).setdefault(class_type, 0)
            controls_by_invoker[invoker_id][class_type] += 1

    for component in components:
        component_id = component.get("id")
        provider = catalog.get(component.get("provider"), {})
        for class_type, requirement in provider.get("invoke", {}).items():
            minimum = requirement.get("min", 0)
            maximum = requirement.get("max")
            count = controls_by_invoker.get(component_id, {}).get(class_type, 0)
            if count < minimum:
                ok = fail(f"{relative}: {component_id} needs at least {minimum} {class_type} control(s), found {count}") and ok
            if maximum is not None and count > maximum:
                ok = fail(f"{relative}: {component_id} allows at most {maximum} {class_type} control(s), found {count}") and ok

    if ok:
        print(f"OK: {relative}")
    return ok


def validate_supporting_files():
    required = [
        ROOT / "env.example",
        ROOT / "video-data" / "clip-summaries" / "clip_000_005_positional_patience.txt",
        ROOT / "video-data" / "sample-uploads" / "possession_and_rest_defense_tactics.txt",
    ]
    ok = True
    for path in required:
        if not path.exists():
            ok = fail(f"missing supporting file {path.relative_to(ROOT)}") and ok
    if ok:
        print("OK: supporting demo files")
    return ok


def main():
    if not CATALOG_PATH.exists():
        print("ERROR: .rocketride/services-catalog.json is missing")
        return 1

    catalog = load_catalog()
    ok = validate_supporting_files()
    for path in PIPELINES:
        if not path.exists():
            ok = fail(f"missing pipeline {path.relative_to(ROOT)}") and ok
            continue
        ok = validate_pipeline(path, catalog) and ok

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())