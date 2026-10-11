#!/usr/bin/env python3
"""Create physical Breadboard variants; preserve the existing Schematic views.

No dependency on the Fritzing parts database: all artwork and connectors are
embedded. Board artwork is illustrative, not a dimensional CAD model.
"""
from collections import defaultdict
from copy import deepcopy
from html import escape
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

import generate as nano
import generate_esp32 as esp
from wire_colors import COLORS, legend_svg

ROOT = Path(__file__).resolve().parent


def xml(root):
    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def sub(parent, tag, **attrs):
    return ET.SubElement(parent, tag, {k: str(v) for k, v in attrs.items()})


def txt(x, y, value, size=18, color="#203040", anchor="start", bold=False):
    return (f'<text x="{x}" y="{y}" font-family="Noto Sans,Arial,sans-serif" '
            f'font-size="{size}" fill="{color}" text-anchor="{anchor}" '
            f'font-weight="{"bold" if bold else "normal"}">{escape(value)}</text>')


def rect(x, y, w, h, fill, stroke="#495463", radius=0):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'


def circle(x, y, r, fill, stroke="#495463", width=2):
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>'


class Physical:
    def __init__(self, part, x, y, w, h, pins, graphic):
        self.part, self.x, self.y, self.w, self.h = part, x, y, w, h
        self.pins, self.graphic = pins, graphic
        assert set(pins) == {c.name for c in part.pins}, part.key

    def point(self, name):
        x, y, *_ = self.pins[name]
        return self.x + x, self.y + y

    def svg(self, layer="breadboard"):
        out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w / 90:.8f}in" height="{self.h / 90:.8f}in" viewBox="0 0 {self.w} {self.h}">', f'<g id="{layer}">', *self.graphic]
        for c in self.part.pins:
            x, y, side, label = self.pins[c.name]
            out += [f'<circle id="{c.id}pin" cx="{x}" cy="{y}" r="7" fill="#d3b36c" stroke="#68532b" stroke-width="2"/>',
                    f'<rect id="{c.id}terminal" x="{x-.5}" y="{y-.5}" width="1" height="1" fill="none" stroke="none"/>']
            if side == "left":
                out.append(txt(x+15, y+6, label, 17, "#ffffff"))
            elif side == "right":
                out.append(txt(x-15, y+6, label, 17, "#ffffff", "end"))
            elif side == "top":
                out.append(txt(x, y-15, label, 16, "#ffffff", "middle"))
            elif side == "bottom":
                # Rotated silkscreen keeps closely spaced module headers legible.
                out.append(f'<g transform="translate({x+5} {y-15}) rotate(-90)">{txt(0,0,label,16,"#ffffff")}</g>')
        out += ["</g></svg>"]
        return "\n".join(out).encode()


def physical_parts(module, board):
    parts = {}
    def add(key, x, y, w, h, pins, graphic):
        parts[key] = Physical(module.by_key[key], x, y, w, h, pins, graphic)
    def holes(w, h):
        return [circle(x, y, 9, "#d2d7da") for x, y in ((35,80),(w-35,80),(35,h-30),(w-35,h-30))]
    def pcb(w, h, color):
        return [rect(10,60,w-20,h-70,color,radius=12), *holes(w,h)]
    def cap(x, y):
        return [circle(x,y,24,"#6e7781"),circle(x,y,18,"#d7dade"),f'<path d="M{x-12} {y} H{x+12} M{x} {y-12} V{y+12}" stroke="#7b8188" stroke-width="2"/>']

    if board == "nano":
        left = ["D13","3V3","AREF","A0","A1","A2","A3","A4","A5","A6","A7","5V","RST1","GND","VIN"]
        right = ["D12","D11","D10","D9","D8","D7","D6","D5","D4","D3","D2","GND2","RST2","D0","D1"]
        pins = {n:(20,155+36*i,"left",{"RST1":"RST"}.get(n,n)) for i,n in enumerate(left)}
        pins.update({n:(260,155+36*i,"right",{"RST2":"RST","GND2":"GND","D0":"RX0","D1":"TX1"}.get(n,n)) for i,n in enumerate(right)})
        art = [*pcb(280,740,"#146395"),
               rect(99,60,82,84,"#bbc3ca",radius=4),rect(107,63,66,51,"#38424c"),txt(140,134,"USB Mini-B",14,"#ffffff","middle"),
               rect(105,310,70,70,"#282e35",radius=3),txt(140,353,"328P",13,"#ffffff","middle"),
               rect(105,205,70,65,"#252c33"),txt(140,244,"FT232",11,"#ffffff","middle"),
               rect(113,475,54,40,"#ddd9cb"),txt(140,500,"RESET",10,anchor="middle"),
               txt(140,425,"Arduino Nano",18,"#ffffff","middle",True)]
        for y in range(320,375,10):
            art += [rect(98,y,7,4,"#aeb3b6"),rect(175,y,7,4,"#aeb3b6")]
        for y in (555,580,605):
            art += [rect(117,y,12,7,"#decd80"),rect(151,y,12,7,"#9be490")]
        add("nano",1150,410,280,740,pins,art)
    else:
        left = ["3V3","EN","GPIO36","GPIO39","GPIO34","GPIO35","GPIO32","GPIO33","GPIO25","GPIO26","GPIO27","GPIO14","GPIO12","GND2","GPIO13","GPIO9","GPIO10","GPIO11","5V"]
        right = ["GND","GPIO23","GPIO22","GPIO1","GPIO3","GPIO21","GND3","GPIO19","GPIO18","GPIO5","GPIO17","GPIO16","GPIO4","GPIO0","GPIO2","GPIO15","GPIO8","GPIO7","GPIO6"]
        labels = {"GPIO36":"VP / 36","GPIO39":"VN / 39","GPIO1":"TX / 1","GPIO3":"RX / 3","GPIO9":"SD2 / 9","GPIO10":"SD3 / 10","GPIO11":"CMD / 11","GPIO8":"SD1 / 8","GPIO7":"SD0 / 7","GPIO6":"CLK / 6","GND2":"GND","GND3":"GND","5V":"5V / VIN"}
        def label(n): return labels.get(n,n.replace("GPIO","IO"))
        pins = {n:(20,140+34*i,"left",label(n)) for i,n in enumerate(left)}
        pins.update({n:(320,140+34*i,"right",label(n)) for i,n in enumerate(right)})
        art = [txt(170,28,"ESP32 · 38 pin",24,anchor="middle",bold=True), *pcb(340,920,"#263438"),
               rect(105,76,130,85,"#354947"),'<path d="M110 145 V92 H133 V133 H156 V92 H179 V133 H202 V92 H229" fill="none" stroke="#c6b16f" stroke-width="5"/>',
               rect(105,170,130,235,"#b8c0c6",radius=3),txt(170,245,"ESP-WROOM",14,anchor="middle"),txt(170,267,"32",24,anchor="middle",bold=True),
               rect(131,535,78,65,"#22282e"),txt(170,575,"USB UART",10,"#ffffff","middle"),
               rect(80,820,42,35,"#d9d9d9"),rect(218,820,42,35,"#d9d9d9"),txt(101,811,"EN",13,"#ffffff","middle"),txt(239,811,"BOOT",13,"#ffffff","middle"),
               rect(133,842,74,73,"#b9c1c6",radius=4),rect(140,865,60,42,"#343c44"),txt(170,835,"USB",14,"#ffffff","middle")]
        add("esp32",1150,400,340,920,pins,art)

    # Heatsink at the top. Screw terminals are separate native connectors.
    pins = {"OUT1":(25,180,"left","OUT1"),"OUT2":(25,240,"left","OUT2"),"OUT3":(415,180,"right","OUT3"),"OUT4":(415,240,"right","OUT4"),
            "5V":(70,420,"bottom","5V"),"GND":(130,420,"bottom","GND"),"+12V":(190,420,"bottom","+12V / VS"),
            "ENA":(240,420,"bottom","ENA"),"IN1":(270,420,"bottom","IN1"),"IN2":(300,420,"bottom","IN2"),"IN3":(330,420,"bottom","IN3"),"IN4":(360,420,"bottom","IN4"),"ENB":(390,420,"bottom","ENB")}
    art = [txt(220,28,"L298N",26,anchor="middle",bold=True),*pcb(440,470,"#b33336"),rect(85,78,270,120,"#333a40"),
           *[rect(x,78,9,120,"#606970") for x in range(95,350,22)],rect(162,164,116,25,"#c0c8ce"),
           rect(10,145,45,130,"#1680bc"),rect(385,145,45,130,"#1680bc"),rect(35,393,181,52,"#1680bc"),
           *cap(102,290),*cap(208,290),rect(293,265,60,55,"#30353a"),txt(220,340,"ENA / ENB: ON",17,"#ffffff","middle",True),
           rect(231,407,18,26,"#151c20"),rect(381,407,18,26,"#151c20"),
           rect(48,290,18,29,"#161d20"),txt(40,284,"5V-EN",13,"#ffffff"),
           txt(220,225,"5V-EN: снять" if board=="esp32" else "5V-EN: см. README",15,"#ffffff","middle")]
    add("l298n",380,650 if board=="esp32" else 600,440,470,pins,art)

    for key,y in (("motor_lf",570),("motor_lb",835),("motor_rf",1270),("motor_rb",1535)):
        p=module.by_key[key]
        pins={"+":(230,110,"none",""),"−":(230,170,"none","")}
        art=[txt(120,28,p.title,17,anchor="middle",bold=True),rect(15,62,145,147,"#f5c72f",radius=18),rect(148,88,77,104,"#b2b8bc",radius=12),
             circle(75,135,38,"#f2d96c"),circle(75,135,13,"#ffffff"),rect(3,121,32,28,"#ffffff"),txt(217,94,"+",18),txt(217,203,"−",18),txt(90,231,"TT",16,anchor="middle")]
        add(key,40,y,250,245,pins,art)

    pins={"+":(335,110,"none",""),"GND":(335,200,"none","")}
    art=[txt(175,28,"Батарея · 3 × 18650 · 3S",22,anchor="middle",bold=True),rect(10,63,305,170,"#2d3339",radius=10)]
    for y in (86,133,180):
        art += [rect(33,y,244,35,"#5caa84",radius=14),rect(271,y+7,15,21,"#cbd4cf"),txt(53,y+24,"−",20,"#ffffff"),txt(249,y+24,"+",20,"#ffffff")]
    art += [txt(318,88,"+",23),txt(318,230,"GND",17,"#202124","end"),txt(175,261,"До 12,6 В",18,anchor="middle")]
    add("battery",60,130,350,275,pins,art)
    add("switch",480,185,180,145,{"IN":(45,117,"none",""),"OUT":(135,117,"none","")},
        [txt(90,27,"SW1 · питание",18,anchor="middle",bold=True),rect(30,52,120,55,"#292e34",radius=5),rect(93,60,47,39,"#cf4444",radius=3),txt(109,85,"ON",15,"#ffffff"),txt(45,140,"IN",15,anchor="middle"),txt(135,140,"OUT",15,anchor="middle")])

    for key,y in (("enc_l",470),("enc_r",825)):
        p=module.by_key[key]
        pins={"VCC":(45,240,"bottom","VCC"),"GND":(110,240,"bottom","GND"),"D0":(175,240,"bottom","DO"),"A0":(240,240,"bottom","AO · NC")}
        art=[txt(145,28,p.title,22,anchor="middle",bold=True),*pcb(290,280,"#165c9e"),rect(115,92,60,71,"#272b30"),
             rect(18,170,35,48,"#30353a"),rect(18,133,87,35,"#30353a"),rect(53,180,34,37,"#ffffff","#ffffff"),
             circle(228,111,24,"#3278b8"),rect(210,106,36,8,"#c9d4da"),txt(145,193,"LM393",16,"#ffffff","middle"),
             ]
        add(key,2070 if board=="esp32" else 1900,y,290,280,pins,art)
    pins={"VCC":(80,230,"bottom","VCC"),"Trig":(140,230,"bottom","Trig"),"Echo":(200,230,"bottom","Echo"),"GND":(260,230,"bottom","GND")}
    art=[txt(170,28,"HC-SR04+" if board=="esp32" else "HC-SR04",24,anchor="middle",bold=True),*pcb(340,270,"#185b9a")]
    for x in (95,245):
        art += [circle(x,127,61,"#c4cbd0"),circle(x,127,50,"#576773"),circle(x,127,41,"#b0b9c0"),
                *[f'<path d="M{x-30} {y} H{x+30}" stroke="#727f8c" stroke-width="2"/>' for y in range(105,155,8)]]
    add("sonar",2010 if board=="esp32" else 1860,1170,340,270,pins,art)
    if board=="nano":
        pins={"GND":(45,105,"top","GND"),"VCC":(110,105,"top","VCC"),"SCL":(175,105,"top","SCL"),"SDA":(240,105,"top","SDA")}
        add("oled",1900,1510,290,260,pins,[txt(145,28,"OLED · SSD1306",22,anchor="middle",bold=True),*pcb(290,260,"#195992"),rect(33,130,224,96,"#131a24"),rect(48,144,194,66,"#0f1f2e"),txt(145,184,"OpenBot",23,"#73c4ed","middle")])
    else:
        for key,x,y,label in (("buck_logic",900,115,"5 В · логика"),("buck_motor",470,390,"VMOT · по номиналу TT")):
            pins={"IN+":(25,115,"left","IN+"),"GND":(25,195,"left","GND"),"OUT+":(295,115,"right","OUT+")}
            add(key,x,y,320,245,pins,[txt(160,28,label,20,anchor="middle",bold=True),*pcb(320,245,"#1c6896"),
                 rect(124,96,65,65,"#434a52",radius=5),txt(156,137,"470",20,"#e2e7ea","middle"),*cap(91,179),*cap(252,179),
                 rect(212,92,37,45,"#377bb9"),rect(222,106,16,8,"#aab6c3"),txt(160,234,"DC/DC · корпус условный",14,anchor="middle")])

    resistor_positions={"r1":(780,170),"r2":(990,170),"r3":(1020,1280),"r4":(1020,1510)} if board=="nano" else {"r1":(810,380),"r2":(810,520),"r3":(1730,1430),"r4":(1930,1530),"r5":(1740,680),"r6":(1740,980)}
    band_colors={"20 кОм":["#c62828","#202124","#ef6c00"],"30 кОм":["#ef6c00","#202124","#ef6c00"],"10 кОм":["#795548","#202124","#ef6c00"],"150 Ом":["#795548","#228833","#795548"],"1 кОм":["#795548","#202124","#c62828"],"2 кОм":["#c62828","#202124","#c62828"]}
    for key,(x,y) in resistor_positions.items():
        p=module.by_key[key]
        art=[txt(90,28,f"{p.title} · {p.value}",20,anchor="middle",bold=True),'<path d="M10 60 H170" stroke="#9da4ac" stroke-width="5"/>',rect(48,44,84,32,"#d7bc83",radius=10)]
        for bx,c in zip((59,76,93),band_colors[p.value]): art.append(rect(bx,45,7,30,c,c))
        art.append(rect(116,45,5,30,"#795548","#795548"))
        add(key,x,y,180,100,{"1":(10,60,"none",""),"2":(170,60,"none","")},art)
    if board=="nano":
        for key,y in (("led_l",1250),("led_r",1480)):
            p=module.by_key[key]
            art=[txt(85,27,p.title,18,anchor="middle",bold=True),'<path d="M45 90 V160 M110 90 V160" stroke="#a6acb1" stroke-width="5"/>',
                 '<path d="M37 100 V78 A42 42 0 0 1 84 37 Q119 43 119 78 V100 Z" fill="#e79b1e" stroke="#965e12" stroke-width="2"/>',
                 circle(70,66,10,"#f9cb68","#f9cb68"),txt(45,183,"A (+)",16,anchor="middle"),txt(110,183,"K (−)",16,anchor="middle")]
            add(key,1350,y,180,195,{"A":(45,160,"none",""),"K":(110,160,"none","")},art)
    width=2700 if board=="esp32" else 2500
    heading=[txt(10,28,f"OpenBot DIY · {'ESP32' if board=='esp32' else 'Arduino Nano'} · Breadboard",30,bold=True),txt(10,61,"Вид сверху: соединяй контакты по маркировке. Цвет = назначение провода.",20)]
    add("heading",30,10,width,85,{},heading)
    notes=["Модули LM393 / OLED / L298N: показан пример — сверяй маркировку на своей плате.",
           "Линии питания — монтажные провода; точки обозначают соединения. Пересечения без точки не соединены.",
           "Номиналы и условия питания сохранены из соответствующей схемы; см. README. NC = не подключено."]
    if board=="esp32": notes += ["ESP32: 38 контактов, USB снизу. GPIO6–GPIO11 (SDx / CMD / CLK) оставить свободными.","5V-EN L298N снята; ENA / ENB включены. Echo: делитель 1 кОм + 2 кОм; HAS_INDICATORS = 0."]
    else: notes += ["Nano: USB сверху. VIN свободен; измерение батареи идёт через 20 кОм + 10 кОм на A7.","Nano: питание как в исходной схеме. Для батареи 3S проверь регулятор L298N и допустимое питание TT."]
    add("footer",330,1840,width-350,170,{},[txt(8,26+28*i,n,18) for i,n in enumerate(notes)])
    if board=="esp32":
        add("config",1270,150,1280,155,{},[txt(8,26+28*i,n,18) for i,n in enumerate(module.by_key["config"].notes)])
        add("rail_labels",2350,95,340,80,{},[txt(8,26,"Питание: 5V / 3V3 / GND",18)])
    legend = Physical(module.by_key["legend"],330,2040,width-350,185,{},[])
    legend.svg = lambda layer="breadboard": legend_svg(legend.w,legend.h,layer)
    parts["legend"] = legend
    return parts


class Wiring:
    def __init__(self, parts):
        self.parts=parts
        self.positions={}
        self.vertices=defaultdict(list)
        self.wires=[]
        for key,p in parts.items():
            for c in p.part.pins:
                self.positions[key,c.name]=p.point(c.name)
                self.vertices[key,c.name].append((p.part.index,c.id,"part"))

    def junction(self, name, x, y):
        key=("junction",name)
        assert key not in self.positions
        self.positions[key]=(x,y)
        return key

    def route(self, a, b, net, bends=()):
        pts=[self.positions[a],*bends,self.positions[b]]
        pts=[p for i,p in enumerate(pts) if not i or p!=pts[i-1]]
        nodes=[a]
        for x,y in pts[1:-1]: nodes.append(self.junction(f"bend_{len(self.wires)}_{len(nodes)}",x,y))
        nodes.append(b)
        for aa,bb in zip(nodes,nodes[1:]):
            idx=10000+len(self.wires)
            self.wires.append((idx,aa,bb,net))
            self.vertices[aa].append((idx,"connector0","wire"))
            self.vertices[bb].append((idx,"connector1","wire"))

    def point(self,key,pin): return self.positions[key,pin]

    def rail(self,name,x,items):
        # Every branch gets a native connected junction, including repeated y.
        ys=sorted({y for _,_,y in items})
        nodes={y:self.junction(f"{name}_{y}",x,y) for y in ys}
        for a,b in zip(ys,ys[1:]): self.route(nodes[a],nodes[b],name)
        for key,pin,y in items:
            px,py=self.point(key,pin)
            p=self.parts[key]
            _,_,side,_=p.pins[pin]
            if key=="l298n" and name in ("5V","GND"):
                lane=950 if name=="5V" else 920
                below=p.y+p.h+55 if name=="5V" else p.y+p.h+80
                bends=[(px,below),(lane,below),(lane,y)]
            elif side=="left": bends=[(p.x-45,py),(p.x-45,y)]
            elif side=="right": bends=[(p.x+p.w+45,py),(p.x+p.w+45,y)]
            elif side=="top": bends=[(px,p.y+45),(p.x+p.w+45,p.y+45),(p.x+p.w+45,y)]
            elif key.startswith("r"):
                lane=p.x-45 if pin=="1" else p.x+p.w+70
                bends=[(lane,py),(lane,y)]
            else: bends=[(px,y)]
            self.route((key,pin),nodes[y],name,bends)


def wiring(parts,board):
    w=Wiring(parts)
    def route(a,b,net,bends=()): w.route(a,b,net,bends)
    route(("battery","+"),("switch","IN"),"VBAT",[(445,240),(445,302)])
    vb=w.junction("VBAT",710,350)
    route(("switch","OUT"),vb,"VBAT",[(710,302)])
    if board=="nano":
        route(vb,("l298n","+12V"),"VBAT",[(710,520),(990,520),(990,1095),(570,1095)])
        route(vb,("r1","1"),"VBAT",[(710,230)])
        adc=w.junction("ADC",975,230)
        route(("r1","2"),adc,"ADC")
        route(adc,("r2","1"),"ADC")
        route(adc,("nano","A7"),"ADC",[(975,295),(1120,295),(1120,w.point("nano","A7")[1])])
        gnd=[("battery","GND",330),("nano","GND",350),("l298n","GND",300),("r2","2",260),("led_l","K",1470),("led_r","K",1810)]
        supply=[("nano","5V",380),("l298n","5V",410)]
        for key,y5,yg in (("enc_l",765,790),("enc_r",1125,1150),("sonar",1460,1485),("oled",1500,1475)):
            supply.append((key,"VCC",y5));gnd.append((key,"GND",yg))
        w.rail("5V",2410,supply);w.rail("GND",2470,gnd)
        mcu="nano"
        pwm=["D5","D6","D9","D10"]
        signals=[("D2","enc_l","D0",1560,"encoder"),("D3","enc_r","D0",1600,"encoder"),("D12","sonar","Trig",1660,"sonar"),("D11","sonar","Echo",1700,"sonar")]
        for npin,key,mpin,lane,net in signals:
            px,py=w.point(mcu,npin);qx,qy=w.point(key,mpin)
            route((mcu,npin),(key,mpin),net,[(lane,py),(lane,qy+65),(qx,qy+65)])
        for npin,mpin,lane,yy in (("A5","SCL",1770,440),("A4","SDA",1810,465)):
            px,py=w.point(mcu,npin);qx,qy=w.point("oled",mpin)
            route((mcu,npin),("oled",mpin),"I2C",[(1080 if npin=="A5" else 1050,py),(1080 if npin=="A5" else 1050,yy),(lane,yy),(lane,1485),(qx,1485)])
        for npin,rkey,lkey,lane,yy in (("D4","r3","led_l",1510,1375),("D7","r4","led_r",1540,1605)):
            px,py=w.point(mcu,npin);qx,qy=w.point(rkey,"1");lx,ly=w.point(lkey,"A")
            route((mcu,npin),(rkey,"1"),"LED",[(lane,py),(lane,yy),(980,yy),(980,qy)])
            route((rkey,"2"),(lkey,"A"),"LED",[(1250,qy),(1250,ly)])
    else:
        for key in ("buck_logic","buck_motor"):
            px,py=w.point(key,"IN+")
            lane=425 if key=="buck_motor" else 850
            route(vb,(key,"IN+"),"VBAT",[(lane,350),(lane,py)])
        route(vb,("r1","1"),"VBAT",[(740,350),(740,440)])
        adc=w.junction("ADC",1030,440)
        route(("r1","2"),adc,"ADC")
        route(adc,("r2","1"),"ADC",[(1030,510),(775,510),(775,580)])
        px,py=w.point("esp32","GPIO4")
        route(adc,("esp32","GPIO4"),"ADC",[(1070,440),(1070,1340),(1540,1340),(1540,py)])
        route(("buck_motor","OUT+"),("l298n","+12V"),"VMOT",[(845,505),(845,1155),(570,1155)])
        gnd=[("battery","GND",330),("buck_logic","GND",350),("buck_motor","GND",360),("esp32","GND",370),("l298n","GND",390),("r2","2",365),("r4","2",1660)]
        supply=[("buck_logic","OUT+",310),("esp32","5V",1510),("l298n","5V",415),("sonar","VCC",1460)]
        v3=[("esp32","3V3",395),("enc_l","VCC",765),("enc_r","VCC",1125),("r5","1",440),("r6","1",1110)]
        for key,y in (("enc_l",790),("enc_r",1150),("sonar",1485)):gnd.append((key,"GND",y))
        w.rail("5V",2650,supply);w.rail("3V3",2590,v3);w.rail("GND",2710,gnd)
        mcu="esp32";pwm=["GPIO13","GPIO12","GPIO15","GPIO2"]
        for npin,key,rkey,lane in (("GPIO35","enc_l","r5",1610),("GPIO22","enc_r","r6",1650)):
            qx,qy=w.point(key,"D0")
            node=w.junction(key+"_DO",1970,qy+65)
            px,py=w.point(mcu,npin)
            route((mcu,npin),node,"encoder",[(1100,py),(1100,340),(lane,340),(lane,qy+65)] if npin=="GPIO35" else [(lane,py),(lane,qy+65)])
            route(node,(key,"D0"),"encoder",[(qx,qy+65)])
            route((rkey,"2"),node,"encoder",[(1970,w.point(rkey,"2")[1])])
        px,py=w.point(mcu,"GPIO5");qx,qy=w.point("sonar","Trig")
        route((mcu,"GPIO5"),("sonar","Trig"),"sonar",[(1690,py),(1690,1410),(qx,1410)])
        px,py=w.point(mcu,"GPIO18")
        echo=w.junction("Echo_3V3",1700,1490)
        route((mcu,"GPIO18"),echo,"sonar",[(1730,py),(1730,1385),(1700,1385)])
        route(echo,("r3","1"),"sonar")
        route(echo,("r4","1"),"sonar",[(1700,1590)])
        qx,qy=w.point("sonar","Echo")
        route(("r3","2"),("sonar","Echo"),"sonar",[(qx,1490)])

    # Driver input wires leave the physical header below the board.
    for i,npin in enumerate(pwm):
        key=f"IN{i+1}";px,py=w.point(mcu,npin);qx,qy=w.point("l298n",key)
        lane=1460+30*i if board=="nano" else 1560+30*i
        yy=1160+25*i if board=="nano" else 1360+25*i
        if px < parts[mcu].x+100:
            bends=[(1120-25*i,py),(1120-25*i,yy),(qx,yy)]
        else:bends=[(lane,py),(lane,yy),(qx,yy)]
        route((mcu,npin),("l298n",key),"PWM",bends)
    for key,out,lane in (("motor_lf","OUT1",320),("motor_lb","OUT1",320),("motor_lf","OUT2",345),("motor_lb","OUT2",345),("motor_rf","OUT4",880),("motor_rb","OUT4",880),("motor_rf","OUT3",910),("motor_rb","OUT3",910)):
        pin="+" if out in ("OUT1","OUT4") else "−"
        px,py=w.point(key,pin);qx,qy=w.point("l298n",out)
        if key.startswith("motor_r"):
            yy=parts[key].y+(110 if pin=="+" else 170)
            route((key,pin),("l298n",out),"motor",[(lane,yy),(lane,qy)])
        else: route((key,pin),("l298n",out),"motor",[(lane,py),(lane,qy)])
    return w


def graph_nets(sketch,definitions,view):
    parent={}
    def find(n):
        parent.setdefault(n,n)
        if parent[n]!=n:parent[n]=find(parent[n])
        return parent[n]
    def union(a,b):parent[find(a)]=find(b)
    named={}
    for inst in sketch.findall("instances/instance"):
        idx=inst.get("modelIndex");module=inst.get("moduleIdRef")
        if module=="WireModuleID":
            if inst.find(f"views/{view}") is not None:union((idx,"connector0"),(idx,"connector1"))
        else:
            definition=definitions[module];key=Path(inst.get("path")).stem
            for c in definition.findall("connectors/connector"):
                node=(idx,c.get("id"));find(node)
                if not key.startswith("junction_"):named[node]=key+"."+c.get("name")
            for bus in definition.findall("buses/bus"):
                ids=[n.get("connectorId") for n in bus.findall("nodeMember")]
                for c in ids[1:]:union((idx,ids[0]),(idx,c))
        for c in inst.findall(f"views/{view}/connectors/connector"):
            for ref in c.findall("connects/connect"):
                union((idx,c.get("connectorId")),(ref.get("modelIndex"),ref.get("connectorId")))
    grouped=defaultdict(list)
    for n,label in named.items():grouped[find(n)].append(label)
    return sorted(sorted(v) for v in grouped.values())


def build(module,board):
    stem=f"openbot-diy-{board}"
    with ZipFile(ROOT/(stem+".fzz")) as z: payload={n:z.read(n) for n in z.namelist()}
    fzname=next(n for n in payload if n.endswith(".fz"))
    sketch=ET.fromstring(payload.pop(fzname))
    original=deepcopy(sketch)
    parts=physical_parts(module,board);w=wiring(parts,board)
    assert set(parts)==set(module.by_key)
    definitions={}
    for key,physical in parts.items():
        name=f"part.{key}.fzp";definition=ET.fromstring(payload[name])
        old_id=definition.get("moduleId");new_id=old_id+"_physical_v1"
        definition.set("moduleId",new_id)
        definition.find("description").text="OpenBot DIY physical Breadboard illustration; pin order is board-specific. See README.breadboard.ru-RU.md. License: CC BY-SA 3.0."
        definitions[new_id]=definition
        payload[name]=xml(definition)
        payload[f"svg.breadboard.{key}.svg"]=physical.svg()
        # Separate identifiers prevent replacing an original part in the cache.
        for inst in sketch.findall("instances/instance"):
            if inst.get("moduleIdRef")!=old_id:continue
            inst.set("moduleIdRef",new_id)
            view=inst.find("views/breadboardView")
            view.clear();view.set("layer","breadboard")
            sub(view,"geometry",x=physical.x,y=physical.y,z="2.5")
            sub(view,"connectors")
    instances=sketch.find("instances")
    for inst in instances:
        if inst.get("moduleIdRef")=="WireModuleID":
            view=inst.find("views/breadboardView")
            if view is not None:inst.find("views").remove(view)
    views={int(i.get("modelIndex")):i.find("views/breadboardView/connectors") for i in instances if i.get("moduleIdRef")!="WireModuleID"}
    for idx,a,b,net in w.wires:
        inst=sub(instances,"instance",moduleIdRef="WireModuleID",modelIndex=idx,path="wire.fzp")
        sub(inst,"title").text=f"{net} · {idx}"
        v=sub(sub(inst,"views"),"breadboardView",layer="breadboardWire")
        x,y=w.positions[a];xx,yy=w.positions[b]
        sub(v,"geometry",x=x,y=y,x1=0,y1=0,x2=xx-x,y2=yy-y,z="3.5",wireFlags=64)
        sub(v,"wireExtras",mils=24 if net in ("VBAT","5V","3V3","VMOT","GND","motor") else 16,color=COLORS[net],opacity=1,banded=0)
        views[idx]=sub(v,"connectors")
    # Each branch dot is a small native one-contact part attached to its wires.
    # Moving it in Fritzing therefore moves the wire endpoints with it.
    net_by_idx={idx:net for idx,_,_,net in w.wires}
    marker_count=0
    for key,refs in w.vertices.items():
        if key[0]!="junction" or len(refs)<3:continue
        net=net_by_idx[refs[0][0]]
        marker_id=f"OpenBot_DIY_{board}_junction_{net}_v1"
        filename=f"junction_{net}"
        if marker_id not in definitions:
            marker=ET.Element("module",moduleId=marker_id,fritzingVersion="1.0.8")
            for tag,value in (("title",f"Соединение {net}"),("version","1"),("author","nitrobin / OpenBot fork"),("description","Native electrical branch contact; CC BY-SA 3.0.")):
                sub(marker,tag).text=value
            props=sub(marker,"properties")
            sub(props,"property",name="family").text="OpenBot wiring junction"
            sub(props,"property",name="part number").text=net
            mv=sub(marker,"views")
            cv=sub(sub(sub(marker,"connectors"),"connector",id="connector0",type="male",name="junction"),"views")
            for view,layer in (("breadboardView","breadboard"),("iconView","icon")):
                sub(sub(sub(mv,view),"layers",image=f"{layer}/{filename}.svg"),"layer",layerId=layer)
                if layer=="breadboard":sub(sub(cv,view),"p",layer=layer,svgId="connector0pin",terminalId="connector0terminal")
                payload[f"svg.{layer}.{filename}.svg"]=(f'<svg xmlns="http://www.w3.org/2000/svg" width="{10/90:.8f}in" height="{10/90:.8f}in" viewBox="0 0 10 10"><g id="{layer}"><circle id="connector0pin" cx="5" cy="5" r="4.5" fill="{COLORS[net]}"/><rect id="connector0terminal" x="4.5" y="4.5" width="1" height="1" fill="none" stroke="none"/></g></svg>').encode()
            definitions[marker_id]=marker;payload[f"part.{filename}.fzp"]=xml(marker)
        x,y=w.positions[key];idx=20000+marker_count;marker_count+=1
        inst=sub(instances,"instance",moduleIdRef=marker_id,modelIndex=idx,path=filename+".fzp")
        sub(inst,"title").text=f"Соединение {net}"
        v=sub(sub(inst,"views"),"breadboardView",layer="breadboard")
        sub(v,"geometry",x=x-5,y=y-5,z="3.4")
        views[idx]=sub(v,"connectors")
        refs.append((idx,"connector0","part"))
    for refs in w.vertices.values():
        for idx,cid,kind in refs:
            layer="breadboard" if kind=="part" else "breadboardWire"
            c=sub(views[idx],"connector",connectorId=cid,layer=layer)
            sub(c,"geometry",x=0,y=0)
            connects=sub(c,"connects")
            for ii,cc,kk in refs:
                if (idx,cid)==(ii,cc):continue
                sub(connects,"connect",modelIndex=ii,connectorId=cc,layer="breadboard" if kk=="part" else "breadboardWire")
    expected=json.loads((ROOT/("source" if board=="nano" else "source-esp32")/"nets.json").read_text())
    for definition in definitions.values():
        assert definition.find("properties/property[@name='family']") is not None
    for view in ("breadboardView","schematicView"):
        assert graph_nets(sketch,definitions,view)==expected,(board,view,"net mismatch")
    # Preserve every existing Schematic instance/view, including manual work.
    for a,b in zip(original.findall("instances/instance"),sketch.findall("instances/instance")):
        assert ET.tostring(a.find("views/schematicView"))==ET.tostring(b.find("views/schematicView"))
    newstem=stem+"-breadboard"
    payload[newstem+".fz"]=xml(sketch)
    outdir=ROOT/("source-breadboard-"+board)
    outdir.mkdir(exist_ok=True)
    for name,content in payload.items():
        if name.endswith(".fz"):path=outdir/name
        elif name.startswith("part."):path=outdir/"parts"/name.removeprefix("part.")
        elif name.startswith("svg."):
            _,layer,filename=name.split(".",2);path=outdir/"parts/svg"/layer/filename
        else:raise ValueError(name)
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(content)
    (outdir/"nets.json").write_text(json.dumps(expected,ensure_ascii=False,indent=2)+"\n")
    with ZipFile(ROOT/(newstem+".fzz"),"w",ZIP_DEFLATED) as z:
        for name,content in payload.items():
            info=ZipInfo(name,(2026,10,11,12,0,0));info.compress_type=ZIP_DEFLATED;z.writestr(info,content)
    print(f"{newstem}: {len(parts)} parts + {marker_count} native junctions, {len(w.wires)} Breadboard wires, {len(expected)} nets; Schematic preserved.")


if __name__=="__main__":
    nano.validate();esp.validate()
    build(nano,"nano");build(esp,"esp32")
