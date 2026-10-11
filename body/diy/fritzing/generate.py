#!/usr/bin/env python3
"""Build the editable OpenBot Nano Fritzing sketch (stdlib only).

Parts, pins and wires are native Fritzing objects. The diagram groups module
pins by function; it is not a drawing of their physical header positions.
The generated FZZ includes every custom part and SVG.
"""
from collections import defaultdict
from dataclasses import dataclass, field
from html import escape
from pathlib import Path
import json
import re
import xml.etree.ElementTree as ET
from zipfile import ZipFile, ZIP_DEFLATED
from wire_colors import COLORS, legend_svg

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "source"
PARTS = SOURCE / "parts"
VIEWS = {"breadboardView": "breadboard", "schematicView": "schematic"}
DATE = "2026-10-11"


def sub(parent, tag, text=None, **attrs):
    item = ET.SubElement(parent, tag, {k: str(v) for k, v in attrs.items()})
    if text is not None:
        item.text = str(text)
    return item


def xml_bytes(root):
    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def text(x, y, content, size=16, color="#172433", anchor="start", weight="normal"):
    return (f'<text x="{x}" y="{y}" font-family="Noto Sans,Arial,sans-serif" '
            f'font-size="{size}" font-weight="{weight}" fill="{color}" '
            f'text-anchor="{anchor}">{escape(content)}</text>')


@dataclass
class Pin:
    name: str
    x: float
    y: float
    side: str
    caption: str = ""
    id: str = ""


@dataclass
class Part:
    key: str
    title: str
    x: float
    y: float
    width: float
    height: float
    pins: list
    color: str = "#eef4fa"
    subtitle: str = ""
    kind: str = "module"
    value: str = ""
    buses: list = field(default_factory=list)
    notes: list = field(default_factory=list)
    index: int = 0

    @property
    def module_id(self):
        return f"OpenBot_DIY_Nano_{self.key}_v2"

    def point(self, pin):
        p = next(p for p in self.pins if p.name == pin)
        return self.x + p.x, self.y + p.y

    def connector(self, pin):
        return next(p.id for p in self.pins if p.name == pin)


parts = []
by_key = {}


def add_part(*args, **kwargs):
    p = Part(*args, **kwargs, index=100 + len(parts))
    for i, pin in enumerate(p.pins):
        pin.id = f"connector{i}"
    parts.append(p)
    by_key[p.key] = p
    return p


def pin(name, x, y, side, caption=""):
    return Pin(name, x, y, side, caption)


left = ["VIN", "GND", "5V", "3V3", "AREF", "RST1", "RST2", "A7",
        "D5", "D6", "D9", "D10", "D4", "D7", "GND2"]
right = ["D2", "D3", "D12", "D11", "A5", "A4", "A0", "A1", "A2",
         "A3", "A6", "D8", "D13", "D0", "D1"]
captions = {"VIN": "VIN · не A7", "A7": "A7 · делитель", "D5": "D5 · IN1",
            "D6": "D6 · IN2", "D9": "D9 · IN3", "D10": "D10 · IN4",
            "D4": "D4 · LED L", "D7": "D7 · LED R", "D2": "D2 · ENC L",
            "D3": "D3 · ENC R", "D12": "D12 · Trig", "D11": "D11 · Echo",
            "A5": "A5 · SCL", "A4": "A4 · SDA", "D0": "D0 / RX0",
            "D1": "D1 / TX1", "GND2": "GND", "RST1": "RST", "RST2": "RST"}
add_part("nano", "Arduino Nano", 790, 280, 300, 620,
         [pin(n, 0, 80 + i * 32, "left", captions.get(n, n)) for i, n in enumerate(left)] +
         [pin(n, 300, 80 + i * 32, "right", captions.get(n, n)) for i, n in enumerate(right)],
         color="#e6efff", subtitle="ATmega328P · 5 В · DIY",
         buses=[["GND", "GND2"], ["RST1", "RST2"]],
         notes=["USB Mini-B → телефон / ПК", "VIN здесь не подключён"])
add_part("l298n", "L298N", 390, 530, 260, 350,
         [pin("OUT1", 0, 54, "left", "OUT1 (+ L)"),
          pin("OUT2", 0, 86, "left", "OUT2 (− L)"),
          pin("OUT3", 0, 150, "left", "OUT3 (− R)"),
          pin("OUT4", 0, 182, "left", "OUT4 (+ R)"),
          pin("IN1", 260, 86, "right"), pin("IN2", 260, 118, "right"),
          pin("IN3", 260, 150, "right"), pin("IN4", 260, 182, "right"),
          pin("+12V", 40, 0, "top"), pin("GND", 130, 0, "top"),
          pin("5V", 220, 0, "top", "5V *"),
          pin("ENA", 260, 230, "right"), pin("ENB", 260, 262, "right")],
         color="#ffe9e5", subtitle="Драйвер двигателей",
         buses=[["5V", "ENA", "ENB"]],
         notes=["ENA / ENB: перемычки ON", "5V-EN: см. питание *"])
for key, title, y in [("motor_lf", "M1 · левый передний", 530),
                      ("motor_lb", "M2 · левый задний", 720),
                      ("motor_rf", "M3 · правый передний", 920),
                      ("motor_rb", "M4 · правый задний", 1110)]:
    add_part(key, title, 40, y, 170, 130,
             [pin("+", 170, 60, "right"), pin("−", 170, 100, "right")],
             color="#fff0b6", kind="motor", subtitle="Мотор-редуктор TT")
add_part("battery", "3 × 18650 · 3S", 390, 90, 180, 180,
         [pin("+", 180, 60, "right"), pin("GND", 180, 140, "right")],
         color="#f3f3f3", kind="battery", subtitle="До 12,6 В *")
add_part("switch", "SW1 · питание", 650, 110, 160, 90,
         [pin("IN", 0, 40, "left"), pin("OUT", 160, 40, "right")],
         kind="switch", buses=[["IN", "OUT"]])
for key, title, y in [("enc_l", "LM393 · левый", 280), ("enc_r", "LM393 · правый", 490)]:
    add_part(key, title, 1450, y, 260, 165,
             [pin("D0", 0, 90, "left", "D0 / DO"),
              pin("A0", 0, 122, "left", "A0 / AO · NC"),
              pin("VCC", 260, 80, "right"), pin("GND", 260, 132, "right")],
             color="#e5f5ec", subtitle="Датчик частоты вращения")
add_part("sonar", "HC-SR04", 1450, 720, 260, 175,
         [pin("Trig", 0, 90, "left", "Trig / Trigger"), pin("Echo", 0, 122, "left"),
          pin("VCC", 260, 80, "right"), pin("GND", 260, 132, "right")],
         color="#e5f1fd", subtitle="Ультразвуковой дальномер")
add_part("oled", "OLED · SSD1306", 1450, 960, 260, 170,
         [pin("SCL", 0, 90, "left"), pin("SDA", 0, 122, "left"),
          pin("VCC", 260, 80, "right", "VCC / VIN *"), pin("GND", 260, 132, "right")],
         color="#f1eafa", subtitle="I2C · модуль с питанием 5 В")
add_part("r1", "R1", 500, 330, 140, 90,
         [pin("1", 0, 40, "left"), pin("2", 140, 40, "right")],
         kind="resistor", value="20 кОм")
add_part("r2", "R2", 630, 420, 140, 140,
         [pin("1", 50, 0, "top"), pin("2", 50, 140, "bottom")],
         kind="resistor_vertical", value="10 кОм")
for i, y, suffix in [(3, 1000, "L · левый"), (4, 1150, "R · правый")]:
    add_part(f"r{i}", f"R{i}", 830, y, 140, 90,
             [pin("1", 0, 40, "left"), pin("2", 140, 40, "right")],
             kind="resistor", value="150 Ом")
    add_part(f"led_{suffix[0].lower()}", f"LED {suffix}", 1080, y, 160, 120,
             [pin("A", 0, 40, "left", "A (+)"), pin("K", 160, 40, "right", "K (−)")],
             kind="led", color="#fff1dc")
add_part("heading", "OpenBot DIY · Arduino Nano", 40, 10, 1800, 70, [], kind="annotation",
         notes=["OpenBot DIY · Arduino Nano · редактируемая схема Fritzing",
                "Выводы сгруппированы по функции; положение контакта на плате определяй по его маркировке."])
add_part("footer", "Примечания", 300, 1310, 1500, 165, [], kind="annotation",
         notes=["* Питание 5V показано как в исходной схеме. Для 3S (12,6 В) проверь модуль L298N и питание TT.",
                "При внешних стабилизированных 5 В отключи 5V-EN; ENA / ENB остаются включены.",
                "Проверь допустимое питание OLED VCC / VIN. USB-питание Nano не объединяй со вторым источником 5V.",
                "Цвет проводов обозначает назначение; см. цветную легенду ниже.",
                "R1 = 20 кОм · R2 = 10 кОм · R3 = R4 = 150 Ом · A7 = VBAT / 3 · NC = не подключено."])
add_part("legend", "Цвета проводов", 300, 1495, 1500, 185, [], kind="legend")


def svg_for(p, layer):
    if p.kind == "legend":
        return legend_svg(p.width, p.height, layer)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{p.width / 90:.8f}in" '
           f'height="{p.height / 90:.8f}in" viewBox="0 0 {p.width} {p.height}">', f'<g id="{layer}">']
    if p.kind == "annotation":
        for i, line in enumerate(p.notes):
            out.append(text(8, 27 + i * 27, line, 23 if p.key == "heading" and i == 0 else 16,
                            weight="bold" if i == 0 and p.key == "heading" else "normal"))
    elif p.kind in ("resistor", "resistor_vertical", "led", "switch"):
        if p.kind == "resistor":
            out += ['<line x1="0" y1="40" x2="140" y2="40" stroke="#333" stroke-width="2"/>',
                    '<rect x="48" y="30" width="44" height="20" fill="#fff" stroke="#333" stroke-width="2"/>',
                    text(70, 21, f"{p.title} · {p.value}", 20, anchor="middle", weight="bold")]
        elif p.kind == "resistor_vertical":
            out += ['<line x1="50" y1="0" x2="50" y2="140" stroke="#333" stroke-width="2"/>',
                    '<rect x="40" y="48" width="20" height="44" fill="#fff" stroke="#333" stroke-width="2"/>',
                    text(67, 61, p.title, 17), text(67, 85, p.value, 17)]
        elif p.kind == "led":
            out += [text(80, 107, p.title, 19, anchor="middle", weight="bold"),
                    '<line x1="0" y1="40" x2="160" y2="40" stroke="#333" stroke-width="2"/>',
                    '<path d="M60 26 L60 54 L86 40 Z M86 26 L86 54" fill="#f5a623" stroke="#333" stroke-width="2"/>',
                    '<path d="M81 22 L96 7 M95 15 L96 7 L88 8 M93 27 L108 12 M107 20 L108 12 L100 13" fill="none" stroke="#333" stroke-width="2"/>',
                    text(4, 72, "A (+)", 16), text(156, 72, "K (−)", 16, anchor="end")]
        else:
            out += [text(80, 21, p.title, 18, anchor="middle", weight="bold"),
                    '<path d="M0 40 L48 40 L112 40 L160 40" fill="none" stroke="#333" stroke-width="2"/>',
                    '<circle cx="48" cy="40" r="4" fill="#fff" stroke="#333"/>',
                    '<circle cx="112" cy="40" r="4" fill="#fff" stroke="#333"/>',
                    text(80, 73, "ON", 16, anchor="middle")]
    else:
        out.append(f'<rect x="20" y="20" width="{p.width - 40}" height="{p.height - 40}" rx="8" fill="{p.color}" stroke="#426077" stroke-width="1.6"/>')
        # Driver title is lower down to leave space for the three power terminals.
        ty = 219 if p.key == "l298n" else 43
        out.append(text(p.width / 2, ty, p.title, 13 if p.kind == "motor" else (21 if p.key != "l298n" else 25),
                        anchor="middle", weight="bold"))
        if p.subtitle:
            out.append(text(p.width / 2, ty + 24, p.subtitle, 11 if p.key == "l298n" else 13, anchor="middle"))
        for i, note in enumerate(p.notes):
            out.append(text(p.width / 2, p.height - 47 + 22 * i, note, 13, anchor="middle"))
        if p.kind == "motor":
            out += ['<circle cx="75" cy="92" r="22" fill="#fff" stroke="#426077" stroke-width="2"/>',
                    text(75, 100, "M", 23, anchor="middle")]
        if p.kind == "battery":
            for x in (35, 65, 95):
                out.append(f'<rect x="{x}" y="85" width="22" height="60" rx="5" fill="#d1e7db" stroke="#426077"/>')
    for c in p.pins:
        px, py = c.x, c.y
        dx, dy = {"left": (20, 0), "right": (-20, 0), "top": (0, 20), "bottom": (0, -20)}[c.side]
        out.append(f'<line id="{c.id}pin" x1="{px}" y1="{py}" x2="{px + dx}" y2="{py + dy}" stroke="#555" stroke-width="2"/>')
        out.append(f'<rect id="{c.id}terminal" x="{px - .5}" y="{py - .5}" width="1" height="1" fill="none" stroke="none"/>')
        if p.kind not in ("resistor", "resistor_vertical", "led", "switch"):
            label = c.caption or c.name
            if c.side == "left":
                out.append(text(px + 26, py + 5, label, 15))
            elif c.side == "right":
                out.append(text(px - 26, py + 5, label, 15, anchor="end"))
            else:
                out.append(text(px, py + 42 if c.side == "top" else py - 25,
                                label, 15, anchor="middle"))
    out += ["</g></svg>"]
    return "\n".join(out).encode()


def part_xml(p):
    root = ET.Element("module", moduleId=p.module_id, fritzingVersion="1.0.8")
    for tag, value in [("version", "1"), ("date", DATE), ("author", "nitrobin / OpenBot fork"),
                       ("title", p.title), ("label", p.title),
                       ("description", "OpenBot DIY functional wiring symbol. Pin names identify contacts; positions are schematic. License: CC BY-SA 3.0.")]:
        sub(root, tag, value)
    props = sub(root, "properties")
    sub(props, "property", "OpenBot DIY wiring", name="family")
    sub(props, "property", p.title, name="part number")
    if p.value:
        sub(props, "property", p.value, name="resistance")
    views = sub(root, "views")
    for view, layer in {**VIEWS, "iconView": "icon"}.items():
        layers = sub(sub(views, view), "layers", image=f"{layer}/{p.key}.svg")
        sub(layers, "layer", layerId=layer)
    connectors = sub(root, "connectors")
    for c in p.pins:
        ce = sub(connectors, "connector", id=c.id, name=c.name, type="male")
        sub(ce, "description", c.caption or c.name)
        cvs = sub(ce, "views")
        for view, layer in VIEWS.items():
            sub(sub(cvs, view), "p", layer=layer, svgId=f"{c.id}pin", terminalId=f"{c.id}terminal")
    buses = sub(root, "buses")
    for i, bus in enumerate(p.buses):
        b = sub(buses, "bus", id=f"bus{i}")
        for name in bus:
            sub(b, "nodeMember", connectorId=p.connector(name))
    return xml_bytes(root)


# Each graph vertex is either a module terminal or a real wire junction. Wire
# bends are separate Fritzing wire objects with reciprocal connector references.
positions, vertices, wires, connections = {}, defaultdict(list), [], []
for p in parts:
    for c in p.pins:
        key = (p.key, c.name)
        positions[key] = p.point(c.name)
        vertices[key].append((p.index, c.id, "part"))


def junction(key, x, y):
    node = ("junction", key)
    positions[node] = (x, y)
    return node


def route(start, end, bends, net):
    coords = [positions[start], *bends, positions[end]]
    coords = [p for i, p in enumerate(coords) if i == 0 or p != coords[i-1]]
    nodes = [start]
    for x, y in coords[1:-1]:
        nodes.append(junction(f"bend_{len(wires)}_{len(nodes)}", x, y))
    nodes.append(end)
    for a, b in zip(nodes, nodes[1:]):
        index = 1000 + len(wires)
        wires.append({"index": index, "a": a, "b": b, "net": net})
        vertices[a].append((index, "connector0", "wire"))
        vertices[b].append((index, "connector1", "wire"))
    connections.append({"from": list(start), "to": list(end), "net": net})


route(("battery", "+"), ("switch", "IN"), [], "VBAT")
vb = junction("VBAT", 720, 305)
route(("switch", "OUT"), vb, [(850, 150), (850, 305)], "VBAT")
route(vb, ("l298n", "+12V"), [(720, 490), (430, 490)], "VBAT")
route(vb, ("r1", "1"), [(470, 305), (470, 370)], "VBAT")
adc = junction("A7", 680, 370)
route(("r1", "2"), adc, [], "ADC")
route(adc, ("r2", "1"), [], "ADC")
route(adc, ("nano", "A7"), [(745, 370), (745, 584)], "ADC")

# Two continuous supply rails, with explicit junctions at every branch.
rail5 = {}
railg = {}
sensor_keys = ("enc_l", "enc_r", "sonar", "oled")
for y in sorted({200, *(by_key[key].point("VCC")[1] for key in sensor_keys)}):
    rail5[y] = junction(f"5V_{y}", 1780, y)
for y in sorted({220, 230, 392, 560, 1240, *(by_key[key].point("GND")[1] for key in sensor_keys)}):
    railg[y] = junction(f"GND_{y}", 1820, y)
for rail, net in ((rail5, "5V"), (railg, "GND")):
    vals = list(rail.values())
    for a, b in zip(vals, vals[1:]):
        route(a, b, [], net)
route(("l298n", "5V"), rail5[200], [(610, 200)], "5V")
route(("nano", "5V"), rail5[200], [(760, 424), (760, 200)], "5V")
route(("l298n", "GND"), railg[220], [(520, 220)], "GND")
route(("battery", "GND"), railg[230], [(600, 230)], "GND")
route(("nano", "GND"), railg[392], [(730, 392), (730, 220), (1820, 220)], "GND")
route(("r2", "2"), railg[560], [(700, 560), (700, 240), (1820, 240)], "GND")
for key in sensor_keys:
    y5 = by_key[key].point("VCC")[1]
    yg = by_key[key].point("GND")[1]
    route((key, "VCC"), rail5[y5], [], "5V")
    route((key, "GND"), railg[yg], [], "GND")

for n, i in (("D5", "IN1"), ("D6", "IN2"), ("D9", "IN3"), ("D10", "IN4")):
    route(("l298n", i), ("nano", n), [], "PWM")
for key in ("motor_lf", "motor_lb"):
    yplus = by_key[key].point("+")[1]
    yminus = by_key[key].point("−")[1]
    route((key, "+"), ("l298n", "OUT1"), [(250, yplus), (250, 584)], "motor")
    route((key, "−"), ("l298n", "OUT2"), [(280, yminus), (280, 616)], "motor")
for key in ("motor_rf", "motor_rb"):
    yplus = by_key[key].point("+")[1]
    yminus = by_key[key].point("−")[1]
    route((key, "+"), ("l298n", "OUT4"), [(310, yplus), (310, 712)], "motor")
    route((key, "−"), ("l298n", "OUT3"), [(340, yminus), (340, 680)], "motor")
for npin, key, mpin, lane, net in [("D2", "enc_l", "D0", 1160, "encoder"),
                                 ("D3", "enc_r", "D0", 1190, "encoder"),
                                 ("D12", "sonar", "Trig", 1250, "sonar"),
                                 ("D11", "sonar", "Echo", 1280, "sonar"),
                                 ("A5", "oled", "SCL", 1320, "I2C"),
                                 ("A4", "oled", "SDA", 1350, "I2C")]:
    route(("nano", npin), (key, mpin),
          [(lane, by_key["nano"].point(npin)[1]), (lane, by_key[key].point(mpin)[1])], net)
for npin, rkey, ledkey, lane, y in [("D4", "r3", "led_l", 735, 1040),
                                  ("D7", "r4", "led_r", 715, 1190)]:
    route(("nano", npin), (rkey, "1"),
          [(lane, by_key["nano"].point(npin)[1]), (lane, y)], "LED")
    route((rkey, "2"), (ledkey, "A"), [], "LED")
    route((ledkey, "K"), railg[1240], [(1270 if ledkey == "led_l" else 1300, y),
                                     (1270 if ledkey == "led_l" else 1300, 1240)], "GND")


def validate():
    """Check against the independent firmware pin definitions and circuit rules."""
    fw = (ROOT.parents[2] / "firmware/openbot/openbot.ino").read_text()
    diy = re.split(r"#if\s+\(?OPENBOT\s*==\s*DIY\)?", fw, maxsplit=1)[1].split("#elif", 1)[0]
    expected = {"PIN_PWM_L1": "5", "PIN_PWM_L2": "6", "PIN_PWM_R1": "9",
                "PIN_PWM_R2": "10", "PIN_SPEED_LF": "2", "PIN_SPEED_RF": "3",
                "PIN_VIN": "A7", "PIN_TRIGGER": "12", "PIN_ECHO": "11",
                "PIN_LED_LI": "4", "PIN_LED_RI": "7"}
    for name, value in expected.items():
        assert re.search(rf"const int {name}\s*=\s*{value}\s*;", diy), name
    assert "(20 + 10) / 10" in diy or "(20+10)/10" in diy
    for wire in wires:
        a, b = positions[wire["a"]], positions[wire["b"]]
        assert a[0] == b[0] or a[1] == b[1], (wire, a, b)
    # Conductive wires and configured jumpers form nets. Resistors and motors
    # are components, so their terminals must not be merged here.
    parent = {}
    def find(a):
        parent.setdefault(a, a)
        if parent[a] != a:
            parent[a] = find(parent[a])
        return parent[a]
    def union(a, b):
        parent[find(a)] = find(b)
    for wire in wires:
        union(wire["a"], wire["b"])
    for p in parts:
        for bus in p.buses:
            for name in bus[1:]:
                union((p.key, bus[0]), (p.key, name))
    def same(*nodes):
        assert len({find(n) for n in nodes}) == 1, nodes
    for npin, i in (("D5", "IN1"), ("D6", "IN2"), ("D9", "IN3"), ("D10", "IN4")):
        same(("nano", npin), ("l298n", i))
    same(("l298n", "OUT1"), ("motor_lf", "+"), ("motor_lb", "+"))
    same(("l298n", "OUT2"), ("motor_lf", "−"), ("motor_lb", "−"))
    same(("l298n", "OUT4"), ("motor_rf", "+"), ("motor_rb", "+"))
    same(("l298n", "OUT3"), ("motor_rf", "−"), ("motor_rb", "−"))
    same(("nano", "A7"), ("r1", "2"), ("r2", "1"))
    same(("battery", "+"), ("l298n", "+12V"), ("r1", "1"))
    same(("battery", "GND"), ("nano", "GND"), ("r2", "2"),
         ("led_l", "K"), ("led_r", "K"), *((k, "GND") for k in ("l298n", "enc_l", "enc_r", "sonar", "oled")))
    same(("nano", "5V"), ("l298n", "5V"), ("l298n", "ENA"), ("l298n", "ENB"),
         *((k, "VCC") for k in ("enc_l", "enc_r", "sonar", "oled")))
    assert len({find(n) for n in [("nano", "5V"), ("nano", "GND"),
                                  ("nano", "A7"), ("battery", "+")]}) == 4
    for key, npin in (("enc_l", "D2"), ("enc_r", "D3")):
        same((key, "D0"), ("nano", npin))
        assert len(vertices[(key, "A0")]) == 1
    for mpin, npin in (("Trig", "D12"), ("Echo", "D11")):
        same(("sonar", mpin), ("nano", npin))
    for mpin, npin in (("SCL", "A5"), ("SDA", "A4")):
        same(("oled", mpin), ("nano", npin))
    for npin, rkey, ledkey in (("D4", "r3", "led_l"), ("D7", "r4", "led_r")):
        same(("nano", npin), (rkey, "1"))
        same((rkey, "2"), (ledkey, "A"))
        assert find((ledkey, "A")) != find((ledkey, "K"))
    assert len(vertices[("nano", "VIN")]) == 1
    grouped = defaultdict(list)
    for p in parts:
        for c in p.pins:
            grouped[str(find((p.key, c.name)))].append(f"{p.key}.{c.name}")
    return sorted(sorted(nodes) for nodes in grouped.values())


def save_sketch():
    sketch = ET.Element("module", fritzingVersion="1.0.8")
    sub(sketch, "title", "OpenBot DIY · Arduino Nano")
    sub(sketch, "author", "nitrobin / OpenBot fork")
    sub(sketch, "date", DATE)
    viewsettings = sub(sketch, "views")
    for view in VIEWS:
        sub(viewsettings, "view", name=view, backgroundColor="#ffffff", gridSize="0.1in",
            showGrid="0", alignToGrid="0", viewFromBelow="0")
    instances = sub(sketch, "instances")
    element_views = {}
    for p in parts:
        item = sub(instances, "instance", moduleIdRef=p.module_id,
                   modelIndex=p.index, path=f"{p.key}.fzp")
        sub(item, "title", p.title)
        if p.value:
            sub(item, "property", name="resistance", value=p.value)
        views = sub(item, "views")
        for view, layer in VIEWS.items():
            v = sub(views, view, layer=layer)
            sub(v, "geometry", x=p.x, y=p.y, z="2.5")
            element_views[p.index, view] = sub(v, "connectors")
    for wire in wires:
        item = sub(instances, "instance", moduleIdRef="WireModuleID", modelIndex=wire["index"], path="wire.fzp")
        sub(item, "title", f'{wire["net"]} · {wire["index"]}')
        views = sub(item, "views")
        x, y = positions[wire["a"]]
        x2, y2 = positions[wire["b"]]
        for view, layer in VIEWS.items():
            wl = "breadboardWire" if view == "breadboardView" else "schematicTrace"
            v = sub(views, view, layer=wl)
            sub(v, "geometry", x=x, y=y, x1="0", y1="0", x2=x2-x, y2=y2-y,
                z="3.5" if view == "breadboardView" else "5.5",
                wireFlags="64" if view == "breadboardView" else "128")
            sub(v, "wireExtras", mils="24" if wire["net"] in ("VBAT", "GND", "5V", "motor") else "16",
                color=COLORS[wire["net"]], opacity="1", banded="0")
            element_views[wire["index"], view] = sub(v, "connectors")
    for refs in vertices.values():
        for index, connector, kind in refs:
            for view, layer in VIEWS.items():
                own_layer = layer if kind == "part" else ("breadboardWire" if view == "breadboardView" else "schematicTrace")
                c = sub(element_views[index, view], "connector", connectorId=connector, layer=own_layer)
                sub(c, "geometry", x="0", y="0")
                connects = sub(c, "connects")
                for target_index, target_connector, target_kind in refs:
                    if target_index == index and target_connector == connector:
                        continue
                    target_layer = layer if target_kind == "part" else ("breadboardWire" if view == "breadboardView" else "schematicTrace")
                    sub(connects, "connect", modelIndex=target_index,
                        connectorId=target_connector, layer=target_layer)
    return xml_bytes(sketch)


def main():
    nets = validate()
    SOURCE.mkdir(exist_ok=True)
    PARTS.mkdir(exist_ok=True)
    payload = {"openbot-diy-nano.fz": save_sketch()}
    for p in parts:
        definition = part_xml(p)
        (PARTS / f"{p.key}.fzp").write_bytes(definition)
        payload[f"part.{p.key}.fzp"] = definition
        for layer in [*VIEWS.values(), "icon"]:
            folder = PARTS / "svg" / layer
            folder.mkdir(parents=True, exist_ok=True)
            svg = svg_for(p, layer)
            (folder / f"{p.key}.svg").write_bytes(svg)
            payload[f"svg.{layer}.{p.key}.svg"] = svg
    (SOURCE / "openbot-diy-nano.fz").write_bytes(payload["openbot-diy-nano.fz"])
    with ZipFile(ROOT / "openbot-diy-nano.fzz", "w", ZIP_DEFLATED) as archive:
        for name, content in payload.items():
            # Fixed timestamps make regeneration deterministic.
            from zipfile import ZipInfo
            info = ZipInfo(name, (2026, 10, 11, 12, 0, 0))
            info.compress_type = ZIP_DEFLATED
            archive.writestr(info, content)
    (SOURCE / "nets.json").write_text(json.dumps(nets, ensure_ascii=False, indent=2) + "\n")
    print(f"Saved {len(parts)} parts, {len(wires)} wire segments; {len(nets)} verified nets.")


if __name__ == "__main__":
    main()
