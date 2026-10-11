#!/usr/bin/env python3
"""Build the editable OpenBot ESP32 Fritzing sketch (stdlib only).

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
SOURCE = ROOT / "source-esp32"
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
        return f"OpenBot_DIY_ESP32_{self.key}_v2"

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


# Functional grouping; all 38 DevKit contacts are represented, with unused
# and flash-connected GPIOs explicitly marked NC.
left = ["GPIO4", "GPIO13", "GPIO12", "GPIO15", "GPIO2", "EN", "GPIO32",
        "GPIO33", "GPIO25", "GPIO26", "GPIO27", "GPIO14", "GPIO34",
        "GPIO36", "GPIO39", "GND2", "GND3", "GPIO0"]
right = ["GPIO35", "GPIO22", "GPIO5", "GPIO18", "GPIO19", "GPIO21", "GPIO23",
         "GPIO16", "GPIO17", "GPIO1", "GPIO3", "GPIO6", "GPIO7", "GPIO8",
         "GPIO9", "GPIO10", "GPIO11"]
captions = {"GPIO4": "GPIO4 · ADC", "GPIO13": "GPIO13 · IN1",
            "GPIO12": "GPIO12 · IN2 *", "GPIO15": "GPIO15 · IN3 *",
            "GPIO2": "GPIO2 · IN4 *", "GPIO35": "GPIO35 · ENC L",
            "GPIO22": "GPIO22 · ENC R", "GPIO5": "GPIO5 · Trig *",
            "GPIO18": "GPIO18 · Echo", "GND2": "GND", "GND3": "GND"}
for n in left + right:
    if n not in captions:
        captions[n] = n + (" · Flash / NC" if n in [f"GPIO{i}" for i in range(6, 12)] else " · NC")
add_part("esp32", "ESP32 DevKit", 900, 600, 350, 810,
         [pin(n, 0, 150 + i * 32, "left", captions[n]) for i, n in enumerate(left)] +
         [pin(n, 350, 150 + i * 32, "right", captions[n]) for i, n in enumerate(right)] +
         [pin("5V", 60, 0, "top", "5V / VIN *"),
          pin("3V3", 175, 0, "top"), pin("GND", 290, 0, "top")],
         color="#e6efff", subtitle="ESP-WROOM-32 · 38 pin · 3,3 В",
         buses=[["GND", "GND2", "GND3"]],
         notes=["Встроенный BLE → OpenBot", "USB: прошивка / один источник *"])
add_part("l298n", "L298N", 450, 696, 260, 350,
         [pin("OUT1", 0, 54, "left", "OUT1 (+ L)"),
          pin("OUT2", 0, 86, "left", "OUT2 (− L)"),
          pin("OUT3", 0, 150, "left", "OUT3 (− R)"),
          pin("OUT4", 0, 182, "left", "OUT4 (+ R)"),
          pin("IN1", 260, 86, "right"), pin("IN2", 260, 118, "right"),
          pin("IN3", 260, 150, "right"), pin("IN4", 260, 182, "right"),
          pin("+12V", 40, 0, "top", "+12V / VS"),
          pin("GND", 130, 0, "top"), pin("5V", 220, 0, "top", "5V · вход"),
          pin("ENA", 260, 230, "right"), pin("ENB", 260, 262, "right")],
         color="#ffe9e5", subtitle="Драйвер двигателей · логика 5 В",
         buses=[["5V", "ENA", "ENB"]],
         notes=["ENA / ENB: перемычки ON", "5V-EN: перемычка снята"])
for key, title, y in [("motor_lf", "M1 · левый передний", 690),
                      ("motor_lb", "M2 · левый задний", 900),
                      ("motor_rf", "M3 · правый передний", 1110),
                      ("motor_rb", "M4 · правый задний", 1320)]:
    add_part(key, title, 40, y, 170, 130,
             [pin("+", 170, 60, "right"), pin("−", 170, 100, "right")],
             color="#fff0b6", kind="motor", subtitle="Мотор-редуктор TT")
add_part("battery", "3 × 18650 · 3S", 450, 120, 180, 180,
         [pin("+", 180, 60, "right"), pin("GND", 180, 140, "right")],
         color="#f3f3f3", kind="battery", subtitle="До 12,6 В")
add_part("switch", "SW1 · питание", 720, 140, 160, 90,
         [pin("IN", 0, 40, "left"), pin("OUT", 160, 40, "right")],
         kind="switch", buses=[["IN", "OUT"]])
for key, title, x, y, w, value, note in [
        ("buck_logic", "DC/DC · логика", 1000, 120, 320, "5 В", "Выход: стабилизированные 5 В"),
        ("buck_motor", "DC/DC · моторы *", 350, 380, 350, "VMOT", "Выход: по номиналу TT; для 3–6 В ≤ 6 В")]:
    add_part(key, title, x, y, w, 200,
             [pin("IN+", 0, 90, "left"), pin("OUT+", w, 90, "right"),
              pin("GND", w / 2, 200, "bottom", "IN− / OUT− · GND")],
             color="#fff1dc", subtitle="Понижающий преобразователь",
             notes=[note])
for key, title, y in [("enc_l", "LM393 · левый", 590), ("enc_r", "LM393 · правый", 850)]:
    add_part(key, title, 1600, y, 320, 200,
             [pin("D0", 0, 90, "left", "D0 / DO"),
              pin("A0", 0, 122, "left", "A0 / AO · NC"),
              pin("VCC", 320, 80, "right", "VCC · 3,3 В *"),
              pin("GND", 320, 160, "right")],
             color="#e5f5ec", subtitle="Датчик частоты вращения",
             notes=["Только модуль, работающий от 3,3 В"])
add_part("sonar", "HC-SR04+", 1600, 1130, 320, 190,
         [pin("Trig", 0, 90, "left", "Trig / Trigger"), pin("Echo", 0, 122, "left"),
          pin("VCC", 320, 80, "right", "VCC · 5 В"), pin("GND", 320, 160, "right")],
         color="#e5f1fd", subtitle="Ультразвуковой дальномер")
add_part("r1", "R1", 620, 630, 140, 90,
         [pin("1", 0, 40, "left"), pin("2", 140, 40, "right")],
         kind="resistor", value="30 кОм")
add_part("r2", "R2", 750, 930, 140, 140,
         [pin("1", 50, 0, "top"), pin("2", 50, 140, "bottom")],
         kind="resistor_vertical", value="10 кОм")
add_part("r3", "R3", 1370, 1212, 140, 90,
         [pin("1", 0, 40, "left"), pin("2", 140, 40, "right")],
         kind="resistor", value="1 кОм")
add_part("r4", "R4", 1280, 1282, 140, 140,
         [pin("1", 50, 0, "top"), pin("2", 50, 140, "bottom")],
         kind="resistor_vertical", value="2 кОм")
for i, y in [(5, 540), (6, 790)]:
    add_part(f"r{i}", f"R{i}", 1410, y, 140, 140,
             [pin("1", 50, 0, "top"), pin("2", 50, 140, "bottom")],
             kind="resistor_vertical", value="10 кОм")
add_part("heading", "OpenBot DIY · ESP32", 40, 10, 2090, 85, [], kind="annotation",
         notes=["OpenBot DIY · ESP32 DevKit · ESP-WROOM-32, 38 pin · схема Fritzing",
                "GPIO — номера сигналов, не положение контактов. На платах находи выводы по маркировке."])
add_part("config", "Конфигурация прошивки", 980, 340, 1090, 160, [], kind="annotation",
         notes=["Прошивка: OPENBOT DIY_ESP32 · HAS_INDICATORS 0 (конфликт с дальномером)",
                "OLED не подключён: GPIO22 занят правым LM393. HAS_OLED 0.",
                "R1 / R2: батарея ÷ 4 → GPIO4 · R3 / R4: Echo × 2/3 → GPIO18",
                "R5 / R6: подтяжка D0 / DO к 3V3; у GPIO35 нет внутренней подтяжки."])
add_part("rail_labels", "Питание", 1840, 110, 300, 110, [], kind="annotation",
         notes=["Цвета — по назначению", "См. цветную легенду внизу", "GND — общий провод"])
add_part("footer", "Примечания", 300, 1510, 1810, 190, [], kind="annotation",
         notes=["* DC/DC моторы: подбери напряжение и ток по своим TT. Клемма +12V / VS не требует именно 12 В.",
                "* На ESP32 подавай только стабилизированные 5 В на подтверждённый вход 5V / VIN. 3S напрямую нельзя.",
                "* При USB-питании ESP32 отсоедини внешний источник от его 5V / VIN. GND всех узлов соединён.",
                "* LM393: питание 3,3 В только для совместимого модуля; модуль 5 В требует согласователя уровней.",
                "* GPIO2 / GPIO5 / GPIO12 / GPIO15 задают режим запуска; не допускай внешней подтяжки GPIO12 к 5 В.",
                "NC = не подключено · Поворотники и OLED здесь отключены · Файл схемы не меняет прошивку."])
add_part("legend", "Цвета проводов", 300, 1715, 1810, 185, [], kind="legend")


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
        ty = 219 if p.key == "l298n" else (90 if p.key == "esp32" else 43)
        out.append(text(p.width / 2, ty, p.title, 12 if p.kind == "motor" else (21 if p.key != "l298n" else 25),
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
vb = junction("VBAT", 950, 180)
route(("switch", "OUT"), vb, [], "VBAT")
route(vb, ("buck_logic", "IN+"), [(950, 210)], "VBAT")
route(vb, ("buck_motor", "IN+"), [(950, 340), (300, 340), (300, 470)], "VBAT")
route(vb, ("r1", "1"), [(760, 180), (760, 620), (600, 620), (600, 670)], "VBAT")
route(("buck_motor", "OUT+"), ("l298n", "+12V"), [(740, 470), (740, 610), (490, 610)], "VMOT")
adc = junction("ADC", 800, 670)
route(("r1", "2"), adc, [], "ADC")
route(adc, ("r2", "1"), [], "ADC")
route(adc, ("esp32", "GPIO4"), [(850, 670), (850, 750)], "ADC")

rails = {}
for name, x, ys in [("5V", 2050, [210, 530, 1210]),
                    ("3V3", 2000, [520, 570, 670, 790, 930]),
                    ("GND", 2110, [320, 550, 750, 1010, 1290, 1422])]:
    rail = rails[name] = {y: junction(f"{name}_{y}", x, y) for y in sorted(set(ys))}
    for a, b in zip(list(rail.values()), list(rail.values())[1:]):
        route(a, b, [], name)
route(("buck_logic", "OUT+"), rails["5V"][210], [], "5V")
v5 = junction("5V_main", 960, 530)
route(("esp32", "5V"), v5, [], "5V")
route(v5, rails["5V"][530], [], "5V")
route(("l298n", "5V"), v5, [(670, 690), (770, 690), (770, 530)], "5V")
route(("esp32", "3V3"), rails["3V3"][570], [(1075, 570)], "3V3")
gleft = junction("GND_left", 580, 550)
gesp = junction("GND_esp", 1190, 550)
route(gleft, gesp, [], "GND")
route(gesp, rails["GND"][550], [], "GND")
route(("esp32", "GND"), gesp, [], "GND")
route(("battery", "GND"), gleft, [(780, 260), (780, 550)], "GND")
route(("buck_logic", "GND"), rails["GND"][320], [], "GND")
route(("buck_motor", "GND"), gleft, [(525, 600), (580, 600)], "GND")
route(("l298n", "GND"), gleft, [], "GND")
route(("r2", "2"), rails["GND"][1422], [(800, 1422)], "GND")
for key in ("enc_l", "enc_r", "sonar"):
    net = "5V" if key == "sonar" else "3V3"
    route((key, "VCC"), rails[net][by_key[key].point("VCC")[1]], [], net)
    route((key, "GND"), rails["GND"][by_key[key].point("GND")[1]], [], "GND")
for n, i in [("GPIO13", "IN1"), ("GPIO12", "IN2"), ("GPIO15", "IN3"), ("GPIO2", "IN4")]:
    route(("l298n", i), ("esp32", n), [], "PWM")
for key in ("motor_lf", "motor_lb"):
    route((key, "+"), ("l298n", "OUT1"), [(250, by_key[key].point("+")[1]), (250, 750)], "motor")
    route((key, "−"), ("l298n", "OUT2"), [(280, by_key[key].point("−")[1]), (280, 782)], "motor")
for key in ("motor_rf", "motor_rb"):
    route((key, "+"), ("l298n", "OUT4"), [(310, by_key[key].point("+")[1]), (310, 878)], "motor")
    route((key, "−"), ("l298n", "OUT3"), [(340, by_key[key].point("−")[1]), (340, 846)], "motor")
for npin, key, rkey, lane, ysupply in [("GPIO35", "enc_l", "r5", 1330, 520),
                                     ("GPIO22", "enc_r", "r6", 1360, 790)]:
    y = by_key[key].point("D0")[1]
    node = junction(f"ENC_{key}", 1460, y)
    route(("esp32", npin), node, [(lane, by_key["esp32"].point(npin)[1]), (lane, y)], "encoder")
    route(node, (key, "D0"), [], "encoder")
    route((rkey, "2"), node, [], "encoder")
    route((rkey, "1"), rails["3V3"][ysupply], [(1460, ysupply)], "3V3")
route(("esp32", "GPIO5"), ("sonar", "Trig"), [(1390, 814), (1390, 1220)], "sonar")
route(("sonar", "Echo"), ("r3", "2"), [], "sonar")
echo = junction("ECHO_3V3", 1330, 1252)
route(("r3", "1"), echo, [], "sonar")
route(echo, ("r4", "1"), [], "sonar")
route(echo, ("esp32", "GPIO18"), [(1300, 1252), (1300, 846)], "sonar")
route(("r4", "2"), rails["GND"][1422], [], "GND")


def validate():
    """Verify independent firmware assignments, nets and voltage boundaries."""
    fw = (ROOT.parents[2] / "firmware/openbot/openbot.ino").read_text()
    diy = re.split(r"#elif\s+\(OPENBOT\s*==\s*DIY_ESP32\)", fw, maxsplit=1)[1].split("#endif", 1)[0]
    expected = {"PIN_PWM_LF1": "13", "PIN_PWM_LF2": "12", "PIN_PWM_RF1": "15",
                "PIN_PWM_RF2": "2", "PIN_PWM_LB1": "13", "PIN_PWM_LB2": "12",
                "PIN_PWM_RB1": "15", "PIN_PWM_RB2": "2", "PIN_SPEED_LF": "35",
                "PIN_SPEED_RF": "22", "PIN_VIN": "4", "PIN_TRIGGER": "5", "PIN_ECHO": "18"}
    for name, value in expected.items():
        assert re.search(rf"const int {name}\s*=\s*{value}\s*;", diy), name
    assert "(30 + 10) / 10" in diy
    # Source conflict is documented, not silently carried into the diagram.
    assert "const int PIN_LED_LI = 5;" in diy and "const int PIN_LED_RI = 18;" in diy
    assert len(by_key["esp32"].pins) == 38
    for wire in wires:
        a, b = positions[wire["a"]], positions[wire["b"]]
        assert a[0] == b[0] or a[1] == b[1], (wire, a, b)
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
    for gp, inp in [("GPIO13", "IN1"), ("GPIO12", "IN2"), ("GPIO15", "IN3"), ("GPIO2", "IN4")]:
        same(("esp32", gp), ("l298n", inp))
    for out, keys, contact in [("OUT1", ("motor_lf", "motor_lb"), "+"),
                                ("OUT2", ("motor_lf", "motor_lb"), "−"),
                                ("OUT4", ("motor_rf", "motor_rb"), "+"),
                                ("OUT3", ("motor_rf", "motor_rb"), "−")]:
        same(("l298n", out), *((k, contact) for k in keys))
    same(("battery", "+"), ("buck_logic", "IN+"), ("buck_motor", "IN+"), ("r1", "1"))
    same(("buck_motor", "OUT+"), ("l298n", "+12V"))
    same(("r1", "2"), ("r2", "1"), ("esp32", "GPIO4"))
    same(("esp32", "5V"), ("buck_logic", "OUT+"), ("l298n", "5V"),
         ("l298n", "ENA"), ("l298n", "ENB"), ("sonar", "VCC"))
    same(("esp32", "3V3"), ("enc_l", "VCC"), ("enc_r", "VCC"), ("r5", "1"), ("r6", "1"))
    same(("battery", "GND"), ("esp32", "GND"), ("esp32", "GND2"), ("esp32", "GND3"),
         ("r2", "2"), ("r4", "2"), *((k, "GND") for k in ("l298n", "buck_logic", "buck_motor", "enc_l", "enc_r", "sonar")))
    for gp, key, rkey in [("GPIO35", "enc_l", "r5"), ("GPIO22", "enc_r", "r6")]:
        same(("esp32", gp), (key, "D0"), (rkey, "2"))
        assert len(vertices[(key, "A0")]) == 1
    same(("esp32", "GPIO5"), ("sonar", "Trig"))
    same(("sonar", "Echo"), ("r3", "2"))
    same(("esp32", "GPIO18"), ("r3", "1"), ("r4", "1"))
    boundaries = [("battery", "+"), ("esp32", "5V"), ("esp32", "3V3"),
                  ("esp32", "GND"), ("esp32", "GPIO4"), ("esp32", "GPIO18"),
                  ("sonar", "Echo"), ("l298n", "+12V")]
    assert len({find(n) for n in boundaries}) == len(boundaries)
    used_gpio = {"GPIO4", "GPIO13", "GPIO12", "GPIO15", "GPIO2", "GPIO35", "GPIO22", "GPIO5", "GPIO18"}
    for c in by_key["esp32"].pins:
        if c.name.startswith("GPIO") and c.name not in used_gpio:
            assert len(vertices[("esp32", c.name)]) == 1, c.name
    assert by_key["r1"].value == "30 кОм" and by_key["r2"].value == "10 кОм"
    assert 12.6 * (10 * 1.01) / (30 * .99 + 10 * 1.01) < 3.3
    assert by_key["r3"].value == "1 кОм" and by_key["r4"].value == "2 кОм"
    assert 5.25 * (2 * 1.01) / (1 * .99 + 2 * 1.01) < 3.6
    grouped = defaultdict(list)
    for p in parts:
        for c in p.pins:
            grouped[str(find((p.key, c.name)))].append(f"{p.key}.{c.name}")
    return sorted(sorted(nodes) for nodes in grouped.values())


def save_sketch():
    sketch = ET.Element("module", fritzingVersion="1.0.8")
    sub(sketch, "title", "OpenBot DIY · ESP32")
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
    payload = {"openbot-diy-esp32.fz": save_sketch()}
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
    (SOURCE / "openbot-diy-esp32.fz").write_bytes(payload["openbot-diy-esp32.fz"])
    with ZipFile(ROOT / "openbot-diy-esp32.fzz", "w", ZIP_DEFLATED) as archive:
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
