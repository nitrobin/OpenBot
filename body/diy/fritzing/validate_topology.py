#!/usr/bin/env python3
"""Independently compare native Fritzing connectivity with the saved Git baseline.

No generator imports: read FZZ, FZP buses and reciprocal connector references,
then traverse the resulting electrical graph. The comparison includes NC pins.
The Nano reference corrects one error in that generated baseline: its 5V pin
is externally unconnected in docs/images/wiring_diagram.png (USB power).
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
POWER_HUB_BASELINE = "8d51688"
VARIANTS = {
    "openbot-diy-nano": "nano",
    "openbot-diy-esp32": "esp32",
    "openbot-diy-nano-breadboard": "nano",
    "openbot-diy-esp32-breadboard": "esp32",
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

def project(components, allowed):
    return sorted(sorted(c & allowed) for c in components if c & allowed)


def validate_power_hub(shared_artwork):
    """Check the power board and the separate distribution board below it."""
    stem = "openbot-diy-power-hub"
    data = (ROOT/(stem+".fzz")).read_bytes()
    sketch = Sketch(data)
    names = ["BAT+", "GND BAT", "SW_IN", "SW_OUT", "VBAT L298N", "GND L298N", "5V L298N",
             "A7 NANO", "GND NANO", "5V periferial", "GND periferial", "VBAT R1", "GND R2"]
    dist_names = ["5V IN", "5V OLED", "5V HC-SR04", "5V FC-03 L", "5V FC-03 R", "5V spare",
                  "GND IN", "GND OLED", "GND HC-SR04", "GND FC-03 L", "GND FC-03 R", "GND spare"]
    for key, expected in [("power_hub", names), ("power_dist", dist_names)]:
        assert {cid: name for cid, name, _ in sketch.fingerprint(key)["connectors"]} == {
            f"connector{i}": name for i, name in enumerate(expected)}, f"Wrong pin order: {key}"
    buses = [[0, 2], [3, 4, 11], [1, 5, 8, 10, 12], [6, 9]]
    assert sketch.fingerprint("power_hub")["buses"] == sorted(
        sorted(f"connector{i}" for i in bus) for bus in buses), "Changed main-board buses"
    assert sketch.fingerprint("power_dist")["buses"] == sorted(
        sorted(f"connector{i}" for i in bus) for bus in [range(6), range(6, 12)]), "Joined peripheral 5V and GND"
    assert not any(target in name for name in names for target in ["OLED", "HC-SR04", "FC-03"]), "Distribution header remains on main board"
    assert sketch.fingerprint("switch")["buses"] == [["connector0", "connector1"]]
    assert {name for _, name, _ in sketch.fingerprint("l298n")["connectors"]} == {"+12V", "GND", "5V"}
    for key, value in [("r1", "20 кОм"), ("r2", "10 кОм")]:
        d = sketch.definition(sketch.parts[key])
        assert d.find("properties/property[@name='resistance']").text == value
        assert not d.findall("buses/bus"), f"Resistor bypass: {key}"
    raw = {"battery.+", "power_hub.BAT+", "power_hub.SW_IN", "switch.IN"}
    switched = {"switch.OUT", "power_hub.SW_OUT", "power_hub.VBAT L298N", "power_hub.VBAT R1", "l298n.+12V", "r1.1"}
    ground = {"battery.GND", "l298n.GND", "r2.2", *("power_hub."+n for n in names if n.startswith("GND ")),
              *("power_dist."+n for n in dist_names if n.startswith("GND "))}
    logic = {"l298n.5V", *("power_hub."+n for n in names if n.startswith("5V ")),
             *("power_dist."+n for n in dist_names if n.startswith("5V "))}
    adc = {"power_hub.A7 NANO", "r1.2", "r2.1"}
    allowed = raw | switched | ground | logic | adc
    actual_ports = {key+"."+n for key in sketch.parts for _, n, _ in sketch.fingerprint(key)["connectors"]}
    assert actual_ports == allowed
    for mid, d in sketch.definitions.items():
        for layers in d.findall("views/*/layers"):
            image = layers.get("image");art = sketch.files["svg."+image.replace("/", ".")]
            cache_key = mid, image.split("/")[0]
            if cache_key in shared_artwork:assert shared_artwork[cache_key] == art, f"Artwork cache conflict: {cache_key}"
            shared_artwork[cache_key] = art
    opened = Sketch(data)
    d = opened.definition(opened.parts["switch"]);d.remove(d.find("buses"))
    def unplug(cids):
        result = Sketch(data);idx = result.parts["power_hub"].get("modelIndex")
        for view in ["breadboardView", "schematicView"]:
            for cid in cids:
                links = result.parts["power_hub"].find(f"views/{view}/connectors/connector[@connectorId='{cid}']/connects")
                for ref in list(links):
                    reciprocal = result.instances[ref.get("modelIndex")].find(
                        f"views/{view}/connectors/connector[@connectorId='{ref.get('connectorId')}']/connects")
                    for back in list(reciprocal):
                        if back.get("modelIndex") == idx and back.get("connectorId") == cid:reciprocal.remove(back)
                    links.remove(ref)
        return result
    no_switch = unplug(["connector2", "connector3"])
    no_peripheral = unplug(["connector9", "connector10"])
    # Compare all old electrical ports after moving the eight load pads to the lower board.
    old = Sketch(git("show", f"{POWER_HUB_BASELINE}:{PREFIX}{stem}.fzz"))
    old_ports = {k+"."+n for k in old.parts for _, n, _ in old.fingerprint(k)["connectors"]}
    moved = {"power_dist."+n: "power_hub."+n for n in dist_names if n not in ["5V IN", "GND IN", "5V spare", "GND spare"]}
    for key in ["battery", "switch", "l298n", "r1", "r2"]:assert sketch.fingerprint(key) == old.fingerprint(key)
    views = {}
    for view in ["breadboardView", "schematicView"]:
        nets = sketch.graph(view)
        assert project(nets, allowed) == sorted(map(sorted, [raw | switched, ground, logic, adc]))
        assert project(opened.graph(view), allowed) == sorted(map(sorted, [raw, switched, ground, logic, adc]))
        assert project(no_switch.graph(view), allowed) == sorted(map(sorted, [
            raw - {"switch.IN"}, switched - {"switch.OUT"}, {"switch.IN", "switch.OUT"}, ground, logic, adc]))
        translated = [{moved.get(p, p) for p in net} for net in nets]
        assert project(translated, old_ports) == project(old.graph(view), old_ports), f"Topology changed beyond relocation: {view}"
        for supply in ["5V", "GND"]:
            assert not any({f"power_hub.{supply} periferial", f"power_dist.{supply} IN"} <= net
                           for net in no_peripheral.graph(view)), f"Peripheral remains connected after unplugging: {view}"
        for key, count in [("l298n", 3), ("power_dist", 2)]:
            links = sketch.parts[key].findall(f"views/{view}/connectors/connector/connects/connect")
            assert len(links) == count, f"Expected exactly {count} cable wires: {key}/{view}"
        for key in ["r1", "r2"]:
            assert not any({key+".1", key+".2"} <= net for net in nets)
            geo = sketch.parts[key].find(f"views/{view}/geometry")
            hub_geo = sketch.parts["power_hub"].find(f"views/{view}/geometry")
            x = float(geo.get("x"))-float(hub_geo.get("x"));y = float(geo.get("y"))-float(hub_geo.get("y"))
            assert 80 <= x <= 800 and 110 <= y <= 780, f"Resistor outside main power board: {key}/{view}"
        hub_geo = sketch.parts["power_hub"].find(f"views/{view}/geometry")
        dist_geo = sketch.parts["power_dist"].find(f"views/{view}/geometry")
        assert float(dist_geo.get("y")) >= float(hub_geo.get("y"))+980, f"Distribution board is not below main board: {view}"
        for key, instance in sketch.parts.items():
            d = sketch.definition(instance);image = d.find(f"views/{view}/layers").get("image")
            art = ET.fromstring(sketch.files["svg."+image.replace("/", ".")]);ids = {n.get("id") for n in art.iter() if n.get("id")}
            for c in d.findall("connectors/connector"):
                p = c.find(f"views/{view}/p");assert {p.get("svgId"), p.get("terminalId")} <= ids
                if key == "power_hub":
                    t = next(n for n in art.iter() if n.get("id") == p.get("terminalId"))
                    y = float(t.get("y"))+float(t.get("height"))/2
                    if c.get("id") in ["connector0", "connector1", "connector2", "connector3"]:assert y <= 110, "BAT/SW not at top"
                    if c.get("id") in ["connector9", "connector10"]:assert y >= 880, "periferial not at bottom"
        views[view] = {"status": "pass", "ports": len(allowed), "ON_nets": 4, "OFF_nets": 5,
                       "BAT_and_SW_at_top": True, "periferial_at_bottom": True,
                       "distribution_board_below_main_board": True, "peripheral_cable_wires": 2,
                       "unplugged_peripheral_isolated": True, "L298N_supply_wires": 3,
                       "switch_opens_VBAT_OUT": True, "unplugged_SW_opens_VBAT_OUT": True,
                       "original_topology_preserved_after_moving_load_pads": True,
                       "Nano_hub_connection": "A7 + GND (USB power)",
                       "divider": {"R1": "20 кОм", "R2": "10 кОм", "ratio": "1/3", "A7_net": sorted(adc),
                                   "resistors_inside_main_board": True, "no_resistor_bypass": True}}
    print(f"PASS {stem}.fzz: BAT/SW top, periferial bottom, separate header below with two wires, A7 divider, ON/OFF, both views")
    return {"file": stem+".fzz", "sha256": sha256(data).hexdigest(), "views": views,
            "reference_baseline_commit": git("rev-parse", POWER_HUB_BASELINE).decode().strip(),
            "method": "explicit connector contract + original hub topology mapped onto separate distribution board"}


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
        if board == "nano":
            # The Git baseline is an earlier redraw, not the source image.
            # It incorrectly connected Nano 5V to the L298N/sensor rail.
            # Keep every other original connection; require 5V to be NC.
            power_net = next(net for net in expected if "nano.5V" in net)
            assert "l298n.5V" in power_net
            expected = sorted(sorted(pin for pin in net if pin != "nano.5V") for net in expected)
            expected.append(["nano.5V"])
            expected.sort()
        baseline[board] = sketch, expected, ports
    report = {"baseline_commit": baseline_hash, "method": "FZZ connector references + FZP buses; independent graph traversal; all original ports including NC",
              "reference_corrections": [{"board": "nano", "port": "nano.5V", "expected": "externally unconnected (USB/OTG power)",
                                         "source": "docs/images/wiring_diagram.png; body/diy/README.md, DIY step 21",
                                         "reason": "Earlier generated baseline incorrectly joined Nano 5V to L298N/sensor power"}], "files": []}
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
            if board == "nano":
                assert {"nano.5V"} in groups, f"Nano 5V must be NC: {stem}/{view}"
                assert any({"nano.GND", "l298n.GND"} <= group for group in groups), f"Missing common GND: {stem}/{view}"
                assert not sketch.parts["nano"].findall(
                    f"views/{view}/connectors/connector[@connectorId='connector2']/connects/connect"), f"Wire on Nano 5V: {stem}/{view}"
            checks[view] = {"status": "pass", "reference_nets": len(actual), "original_ports": len(ports)}
            if board == "nano":
                checks[view]["Nano_5V_externally_unconnected"] = True
                checks[view]["common_GND_preserved"] = True
        result = {"file": stem+".fzz", "sha256": sha256(data).hexdigest(), "views": checks,
                  "pin_names_internal_buses_and_component_values": "unchanged"}
        report["files"].append(result)
        print(f"PASS {stem}.fzz: {len(expected)} nets, {len(ports)} original ports, Breadboard + Schematic")
    report["files"].append(validate_power_hub(shared_artwork))
    report["shared_module_artwork_conflicts"] = 0
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n")
    print(f"Baseline {baseline_hash}; report: {args.report.name}")


if __name__ == "__main__":
    main()
