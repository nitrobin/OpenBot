#!/usr/bin/env python3
"""Independently compare native Fritzing connectivity with the saved Git baseline.

No generator imports: read FZZ, FZP buses and reciprocal connector references,
then traverse the resulting electrical graph. The comparison includes NC pins.
"""
import argparse
from collections import defaultdict
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parent
PREFIX = "body/diy/fritzing/"
BASELINE = "12c12e5"
VARIANTS = {
    "openbot-diy-nano": "nano",
    "openbot-diy-esp32": "esp32",
    "openbot-diy-nano-breadboard": "nano",
    "openbot-diy-esp32-breadboard": "esp32",
    "openbot-diy-nano-on-breadboard": "nano",
}
MOUNT = {
    "r1": {"1": "B3", "2": "B9"},
    "r2": {"1": "B12", "2": "B18"},
    "r3": {"1": "H3", "2": "H9"},
    "r4": {"1": "H12", "2": "H18"},
    "led_l": {"K": "E22", "A": "E23"},
    "led_r": {"K": "E26", "A": "E27"},
}


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


class Sketch:
    def __init__(self, data):
        with ZipFile(BytesIO(data)) as archive:
            self.files = {name: archive.read(name) for name in archive.namelist()}
        self.root = ET.fromstring(next(data for name, data in self.files.items() if name.endswith(".fz")))
        self.definitions = {}
        for name, data in self.files.items():
            if name.endswith(".fzp"):
                part = ET.fromstring(data)
                self.definitions[part.get("moduleId")] = part
        self.instances = {}
        self.parts = {}
        for item in self.root.findall("instances/instance"):
            index = item.get("modelIndex")
            assert index not in self.instances, f"Duplicate modelIndex: {index}"
            self.instances[index] = item
            if item.get("moduleIdRef") != "WireModuleID":
                key = Path(item.get("path")).stem
                assert key not in self.parts or key.startswith("junction_"), key
                self.parts[key] = item

    def definition(self, instance):
        return self.definitions[instance.get("moduleIdRef")]

    def fingerprint(self, key):
        definition = self.definition(self.parts[key])
        return {
            "connectors": sorted((c.get("id"), c.get("name"), c.get("type"))
                                 for c in definition.findall("connectors/connector")),
            "buses": sorted(sorted(n.get("connectorId") for n in bus.findall("nodeMember"))
                            for bus in definition.findall("buses/bus")),
            "properties": sorted((p.get("name"), p.text or "")
                                 for p in definition.findall("properties/property")),
        }

    def graph(self, view):
        adjacent = defaultdict(set)
        labels = {}
        legal = {}

        def connect(a, b):
            adjacent[a].add(b)
            adjacent[b].add(a)

        for index, item in self.instances.items():
            if item.get("moduleIdRef") == "WireModuleID":
                legal[index] = {"connector0", "connector1"}
                if item.find(f"views/{view}") is not None:
                    connect((index, "connector0"), (index, "connector1"))
            else:
                definition = self.definition(item)
                key = Path(item.get("path")).stem
                legal[index] = set()
                for c in definition.findall("connectors/connector"):
                    cid = c.get("id")
                    legal[index].add(cid)
                    node = (index, cid)
                    adjacent[node]
                    labels[node] = key + "." + c.get("name")
                for bus in definition.findall("buses/bus"):
                    pins = [n.get("connectorId") for n in bus.findall("nodeMember")]
                    assert set(pins) <= legal[index], (key, bus.get("id"))
                    for pin in pins[1:]:
                        connect((index, pins[0]), (index, pin))
        for index, item in self.instances.items():
            for c in item.findall(f"views/{view}/connectors/connector"):
                cid = c.get("connectorId")
                assert cid in legal[index], (index, cid)
                for ref in c.findall("connects/connect"):
                    target = (ref.get("modelIndex"), ref.get("connectorId"))
                    assert target[0] in legal and target[1] in legal[target[0]], target
                    reciprocal = self.instances[target[0]].find(
                        f"views/{view}/connectors/connector[@connectorId='{target[1]}']/connects/"
                        f"connect[@modelIndex='{index}'][@connectorId='{cid}']")
                    assert reciprocal is not None, f"Missing reciprocal reference: {index}.{cid} -> {target}"
                    connect((index, cid), target)
        seen, components = set(), []
        for start in adjacent:
            if start in seen:
                continue
            pending, component = [start], set()
            while pending:
                node = pending.pop()
                if node in seen:
                    continue
                seen.add(node)
                component.add(node)
                pending.extend(adjacent[node] - seen)
            components.append({labels[n] for n in component if n in labels})
        return components

    def terminal_position(self, key, name):
        instance = self.parts[key]
        definition = self.definition(instance)
        pin = definition.find(f"connectors/connector[@name='{name}']/views/breadboardView/p")
        image = definition.find("views/breadboardView/layers").get("image")
        svg = ET.fromstring(self.files["svg." + image.replace("/", ".")])
        node = next(n for n in svg.iter() if n.get("id") == pin.get("terminalId"))
        assert node.tag.endswith("rect"), (key, name)
        geometry = instance.find("views/breadboardView/geometry")
        return (float(geometry.get("x")) + float(node.get("x")) + float(node.get("width"))/2,
                float(geometry.get("y")) + float(node.get("y")) + float(node.get("height"))/2)


def project(components, allowed):
    return sorted(sorted(c & allowed) for c in components if c & allowed)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=ROOT/"topology-validation.json")
    args = parser.parse_args()
    baseline_hash = git("rev-parse", BASELINE).decode().strip()
    baseline = {}
    for board, source in [("nano", "source"), ("esp32", "source-esp32")]:
        sketch = Sketch(git("show", f"{baseline_hash}:{PREFIX}openbot-diy-{board}.fzz"))
        expected = json.loads(git("show", f"{baseline_hash}:{PREFIX}{source}/nets.json"))
        ports = {p for net in expected for p in net}
        for view in ["breadboardView", "schematicView"]:
            assert project(sketch.graph(view), ports) == expected, f"Baseline mismatch: {board}/{view}"
        baseline[board] = sketch, expected, ports
    report = {"baseline_commit": baseline_hash, "method": "FZZ connector references + FZP buses; independent graph traversal; all original ports including NC", "files": []}
    shared_artwork = {}
    for stem, board in VARIANTS.items():
        data = (ROOT/(stem+".fzz")).read_bytes()
        sketch = Sketch(data)
        original, expected, ports = baseline[board]
        # Fritzing shares its part cache between documents. A shared identifier
        # must never refer to different artwork/terminal positions.
        for module_id, definition in sketch.definitions.items():
            for layers in definition.findall("views/*/layers"):
                image = layers.get("image")
                if not image:
                    continue
                svg = sketch.files["svg."+image.replace("/", ".")]
                cache_key = module_id, image.split("/")[0]
                if cache_key in shared_artwork:
                    assert shared_artwork[cache_key] == svg, f"Fritzing artwork cache conflict: {stem}/{cache_key}"
                shared_artwork[cache_key] = svg
        for key in original.parts:
            assert sketch.fingerprint(key) == original.fingerprint(key), f"Changed pins, buses or values: {stem}/{key}"
        actual_ports = {key+"."+name for key in sketch.parts
                        if key in original.parts
                        for _, name, _ in sketch.fingerprint(key)["connectors"]}
        assert actual_ports == ports, f"Changed port set: {stem}"
        checks = {}
        for view in ["breadboardView", "schematicView"]:
            groups = sketch.graph(view)
            actual = project(groups, ports)
            assert actual == expected, json.dumps({"file": stem, "view": view,
                "missing": [n for n in expected if n not in actual],
                "unexpected": [n for n in actual if n not in expected]}, ensure_ascii=False)
            for key in original.parts:
                if key.startswith("r") and key[1:].isdigit():
                    assert not any({key+".1", key+".2"} <= group for group in groups), f"Bypassed resistor: {stem}/{view}/{key}"
            assert not any({"l298n.5V", "l298n.GND"} <= group for group in groups), f"Power short: {stem}/{view}"
            checks[view] = {"status": "pass", "original_nets": len(actual), "original_ports": len(ports)}
        result = {"file": stem+".fzz", "sha256": sha256(data).hexdigest(), "views": checks,
                  "pin_names_internal_buses_and_component_values": "unchanged"}
        if "breadboard" in sketch.parts:
            stock = ET.parse(ROOT/"library-parts/breadboard.fzp").getroot()
            definition = sketch.definition(sketch.parts["breadboard"])
            stock_buses = sorted(sorted(n.get("connectorId") for n in bus.findall("nodeMember")) for bus in stock.findall("buses/bus"))
            assert sketch.fingerprint("breadboard")["buses"] == stock_buses, "Changed breadboard buses"
            mounted = 0
            for key, pairs in MOUNT.items():
                for name, hole in pairs.items():
                    a = sketch.terminal_position(key, name)
                    b = sketch.terminal_position("breadboard", hole)
                    assert max(abs(x-y) for x, y in zip(a, b)) < 1e-5, (key, name, hole, a, b)
                    inst = sketch.parts[key]
                    cid = sketch.definition(inst).find(f"connectors/connector[@name='{name}']").get("id")
                    assert inst.find(f"views/breadboardView/connectors/connector[@connectorId='{cid}']/connects/connect[@modelIndex='900'][@connectorId='{hole}']") is not None, (key, name, hole)
                    mounted += 1
            result["breadboard"] = {"stock_internal_buses": len(stock_buses), "buses_unchanged": True, "mounted_pins_verified": mounted, "resistors_bypassed": False, "5V_GND_short": False}
        report["files"].append(result)
        print(f"PASS {stem}.fzz: {len(expected)} nets, {len(ports)} original ports, Breadboard + Schematic")
    report["shared_module_artwork_conflicts"] = 0
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n")
    print(f"Baseline {baseline_hash}; report: {args.report.name}")


if __name__ == "__main__":
    main()
