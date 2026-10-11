#!/usr/bin/env python3
"""Build Breadboard variants from bundled Fritzing library artwork.

The original Schematic views and electrical connections are preserved.
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
            out += [f'<rect id="{c.id}pin" x="{x-6}" y="{y-6}" width="12" height="12" fill="none" stroke="none"/>',
                    f'<rect id="{c.id}terminal" x="{x-.5}" y="{y-.5}" width="1" height="1" fill="none" stroke="none"/>']
        out += ["</g></svg>"]
        return "\n".join(out).encode()


def physical_parts(module, board):
    from library_artwork import Artwork, point
    from power_distribution import part as distribution_part, breadboard_graphic
    parts = {}

    def ready(key, art_name, mapping, x, y, w, h, rotation=0, sides=None, note=''):
        p=module.by_key[key];a=Artwork(art_name)
        if art_name=='resistor': a.resistance(p.value)
        if art_name=='resistor':mat,art=a.fit(10,48,160,45,rotation)
        elif art_name=='led':mat,art=a.fit(35,42,110,125,rotation)
        else:mat,art=a.fit(45 if key in ('nano','esp32') else 12,65,
                          w-90 if key in ('nano','esp32') else w-24,h-100,rotation)
        pins={}
        for name,cid in mapping.items():
            px,py=point(mat,*a.pin(cid))
            side=(sides or {}).get(name,'none')
            pins[name]=(px,py,'none','')
        graphic=[txt(w/2,28,p.title+(f' · {p.value}'if p.value else ''),20,anchor='middle',bold=True),art]
        if key in ('nano','esp32'):
            # The stock silkscreen rotates with the board. Add upright labels.
            for name,(px,py,*_)in pins.items():
                left=px<w/2;label={'RST1':'RST','RST2':'RST','GND2':'GND','GND3':'GND','D0':'RX0','D1':'TX1','EN':'EN / RST'}.get(name,name.replace('GPIO','IO'))
                graphic.append(txt(px-15 if left else px+15,py+5,label,15,'#172433','end'if left else'start'))
                pins[name]=(px,py,'left'if left else'right',label)
        elif art_name=='led':
            for name,(px,py,*_)in pins.items():graphic.append(txt(px,py+25,'A (+)'if name=='A'else'K (−)',13,anchor='middle'))
        elif art_name=='switch':
            for name,(px,py,*_)in pins.items():graphic.append(txt(px,py+20,name,15,anchor='middle'))
            graphic.append(txt(w-15,h-10,'L2 · NC',13,anchor='end'))
        elif key=='l298n':
            graphic.append(txt(w/2,h-9,'ENA / ENB: ON · 5V-EN: '+('снять'if board=='esp32'else'см. README'),16,anchor='middle'))
        if note:graphic.append(txt(w/2,h-9,note,14,anchor='middle'))
        for name,side in (sides or {}).items():
            px,py,*_=pins[name];pins[name]=(px,py,side,name)
        physical=Physical(p,x,y,w,h,pins,graphic)
        physical.library=art_name
        parts[key]=physical

    if board=='nano':
        mapping=dict(zip(['D1','D0','RST2','GND2','D2','D3','D4','D5','D6','D7','D8','D9','D10','D11','D12','VIN','GND','RST1','5V','A7','A6','A5','A4','A3','A2','A1','A0','AREF','3V3','D13'],[f'connector{i}'for i in range(16,46)]))
        ready('nano','nano',mapping,1115,410,340,740,180)
    else:
        left=['3V3','EN','GPIO36','GPIO39','GPIO34','GPIO35','GPIO32','GPIO33','GPIO25','GPIO26','GPIO27','GPIO14','GPIO12','GND2','GPIO13','GPIO9','GPIO10','GPIO11','5V']
        right=['GND','GPIO23','GPIO22','GPIO1','GPIO3','GPIO21','GND3','GPIO19','GPIO18','GPIO5','GPIO17','GPIO16','GPIO4','GPIO0','GPIO2','GPIO15','GPIO8','GPIO7','GPIO6']
        ready('esp32','esp32',dict(zip(left+right,[f'connector{i}'for i in range(45,83)])),1095,400,440,920,-90)
    mapping={'OUT1':'connector0','OUT2':'connector1','OUT3':'connector2','OUT4':'connector4','+12V':'connector5','GND':'connector6','5V':'connector7','ENA':'connector11','ENB':'connector12','IN1':'connector13','IN2':'connector14','IN3':'connector15','IN4':'connector16'}
    ready('l298n','l298n',mapping,380,650 if board=='esp32'else 600,440,470,
          sides={**{n:'left'for n in ['OUT1','OUT2']},**{n:'right'for n in ['OUT3','OUT4']},**{n:'bottom'for n in ['+12V','GND','5V','ENA','ENB','IN1','IN2','IN3','IN4']}})
    for key,y in [('motor_lf',570),('motor_lb',835),('motor_rf',1270),('motor_rb',1535)]:
        ready(key,'motor',{'+':'connector1','−':'connector0'},40,y,250,245,180,sides={'+':'right','−':'right'})
    ready('battery','battery',{'+':'connector1','GND':'connector0'},60,130,350,275,sides={'+':'right','GND':'right'},note='3S · до 12,6 В')
    ready('switch','switch',{'IN':'connector1','OUT':'connector0'},480,185,180,160,sides={'IN':'bottom','OUT':'bottom'})
    for key,y in [('enc_l',470),('enc_r',825)]:
        ready(key,'fc03',{'VCC':'connector0','GND':'connector1','D0':'connector2','A0':'connector3'},2070 if board=='esp32'else 1900,y,290,280,90,
              sides={n:'bottom'for n in ['VCC','GND','D0','A0']})
    ready('sonar','sonar',{'VCC':'connector0','Trig':'connector1','Echo':'connector2','GND':'connector3'},2010 if board=='esp32'else 1860,1170,340,270,
          sides={n:'bottom'for n in ['VCC','Trig','Echo','GND']})
    if board=='nano':
        ready('oled','oled',{'GND':'connector1','VCC':'connector2','SCL':'connector3','SDA':'connector4'},1900,1510,290,260,sides={n:'top'for n in ['GND','VCC','SCL','SDA']})
    else:
        for key,x,y,note in [('buck_logic',900,115,'Настроить OUT+ на 5 В'),('buck_motor',470,390,'OUT+ = VMOT по номиналу TT')]:
            ready(key,'buck',{'IN+':'connector0','GND':'connector1','OUT+':'connector2'},x,y,320,245,sides={'IN+':'left','GND':'left','OUT+':'right'},note=note)
            a=Artwork('buck');mat,_=a.fit(12,65,296,145)
            gx,gy=point(mat,*a.pin('connector3'))
            # Both negative pads of this non-isolated module are common GND.
            parts[key].graphic.append(txt(gx-10,gy+15,'OUT− = GND',12,anchor='end'))
    positions={'r1':(780,170),'r2':(990,170),'r3':(1020,1280),'r4':(1020,1510)}if board=='nano'else{'r1':(810,380),'r2':(810,520),'r3':(1730,1430),'r4':(1930,1530),'r5':(1740,680),'r6':(1740,980)}
    for key,(x,y)in positions.items():ready(key,'resistor',{'1':'connector0','2':'connector1'},x,y,180,110)
    if board=='nano':
        for key,y in [('led_l',1250),('led_r',1480)]:ready(key,'led',{'A':'connector1','K':'connector0'},1350,y,180,195)
    width=2950 if board=='esp32'else 2750
    def annotation(key,x,y,w,h,graphic):parts[key]=Physical(module.by_key[key],x,y,w,h,{},graphic)
    annotation('heading',30,10,width,85,[txt(10,28,f"OpenBot DIY · {'ESP32'if board=='esp32'else'Arduino Nano'} · Breadboard",30,bold=True),txt(10,61,'Готовые компоненты Fritzing · цвет = назначение провода · контакты по маркировке',20)])
    notes=['Колодка 6 × 2: припаять каждый ряд отдельно; один ряд 5V, второй GND. Между рядами нет соединения.',
           'Провода и контакты редактируются в Fritzing. Точки = соединения; пересечения без точки не соединены.',
           'LM393 / OLED / L298N: сверяй маркировку своей платы; корпуса из готовых библиотек Fritzing.',
           'Номиналы и условия питания — см. README. NC = не подключено.']
    notes+=['ESP32: USB снизу. Датчики LM393 питаются от 3V3, отдельно от колодки 5V.',
            '5V-EN L298N снять; ENA / ENB включены. Echo: 1 кОм + 2 кОм; HAS_INDICATORS = 0.']if board=='esp32'else['Nano: USB сверху. VIN свободен; батарея → делитель 20 кОм + 10 кОм → A7.',
            'Nano: исходное питание. Для батареи 3S проверь регулятор L298N и допустимое питание TT.']
    annotation('footer',330,1840,width-350,185,[txt(8,26+28*i,n,18)for i,n in enumerate(notes)])
    if board=='esp32':
        annotation('config',1270,150,1280,155,[txt(8,26+28*i,n,18)for i,n in enumerate(module.by_key['config'].notes)])
        annotation('rail_labels',2800,95,300,80,[txt(8,26,'3V3 отдельно от 5V',18)])
    p=distribution_part();w,h,pins,art=breadboard_graphic()
    parts['power_dist']=Physical(p,2490 if board=='esp32'else 2300,470,w,h,pins,art)
    legend=Physical(module.by_key['legend'],330,2040,width-350,185,{},[])
    legend.svg=lambda layer='breadboard':legend_svg(legend.w,legend.h,layer)
    parts['legend']=legend
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
        requested=[self.positions[a],*bends,self.positions[b]]
        pts=[requested[0]]
        for n,p in enumerate(requested[1:]):
            q=pts[-1]
            if abs(q[0]-p[0])>0.001 and abs(q[1]-p[1])>0.001:
                side=self.parts[b[0]].pins[b[1]][2] if n==len(requested)-2 and b[0]in self.parts else ""
                pts.append((q[0],p[1]) if side in ("left","right") else (p[0],q[1]))
            if p!=pts[-1]:pts.append(p)
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
        distribution=name in ("5V","GND")
        if distribution:
            # One source and five destinations; extra local GND branches share
            # the source contact. The two rows remain separate native buses.
            order=["l298n","nano","enc_l","enc_r","sonar","oled"] if "nano"in self.parts else ["buck_logic","esp32","l298n","enc_l","enc_r","sonar"]
            targets={key:("power_dist",f"{name}{i+1}") for i,key in enumerate(order)}
        else:
            ys=sorted({y for _,_,y in items})
            nodes={y:self.junction(f"{name}_{y}",x,y)for y in ys}
            for a,b in zip(ys,ys[1:]):self.route(nodes[a],nodes[b],name)
        for i,(key,pin,y)in enumerate(items):
            px,py=self.point(key,pin);p=self.parts[key];side=p.pins[pin][2]
            if key=="l298n" and name in ("5V","GND"):
                lane=950 if name=="5V"else 920
                below=p.y+p.h+55 if name=="5V"else p.y+p.h+80
                bends=[(px,below),(lane,below),(lane,y)]
            elif side=="left":bends=[(p.x-45,py),(p.x-45,y)]
            elif side=="right":bends=[(p.x+p.w+45,py),(p.x+p.w+45,y)]
            elif side=="top":bends=[(px,p.y+45),(p.x+p.w+45,p.y+45),(p.x+p.w+45,y)]
            elif key.startswith("r"):
                lane=p.x-45 if pin=="1"else p.x+p.w+70
                bends=[(lane,py),(lane,y)]
            else:bends=[(px,y)]
            if distribution:
                target=targets.get(key,targets[order[0]])
                tx,ty=self.positions[target]
                # Parallel approach channels keep wires outside the header.
                lane=self.parts["power_dist"].x+(80-15*i if name=="5V"else 390+15*i)
                bends += [(lane,y),(lane,ty)]
                self.route((key,pin),target,name,bends)
            else:self.route((key,pin),nodes[y],name,bends)


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
                if not key.startswith("junction_") and key!="breadboard":named[node]=key+"."+c.get("name")
            for bus in definition.findall("buses/bus"):
                ids=[n.get("connectorId") for n in bus.findall("nodeMember")]
                for c in ids[1:]:union((idx,ids[0]),(idx,c))
        for c in inst.findall(f"views/{view}/connectors/connector"):
            for ref in c.findall("connects/connect"):
                union((idx,c.get("connectorId")),(ref.get("modelIndex"),ref.get("connectorId")))
    grouped=defaultdict(list)
    for n,label in named.items():grouped[find(n)].append(label)
    return sorted(sorted(v) for v in grouped.values())


def build(module,board,variant=None):
    stem=f"openbot-diy-{board}"
    with ZipFile(ROOT/(stem+".fzz")) as z: payload={n:z.read(n) for n in z.namelist()}
    fzname=next(n for n in payload if n.endswith(".fz"))
    sketch=ET.fromstring(payload.pop(fzname))
    original=deepcopy(sketch)
    parts=physical_parts(module,board)
    attachments=[];removed=set()
    if variant=="solderless":
        from generate_solderless import prepare
        parts,w,attachments=prepare(parts)
        removed={int(i.get("modelIndex"))for i in sketch.findall("instances/instance")if Path(i.get("path")).stem=="power_dist" or 30000<=int(i.get("modelIndex"))<30200}
        for inst in list(sketch.find("instances")):
            if int(inst.get("modelIndex"))in removed:sketch.find("instances").remove(inst)
            else:
                for connects in inst.findall("views/*/connectors/connector/connects"):
                    for ref in list(connects):
                        if int(ref.get("modelIndex"))in removed:connects.remove(ref)
        for name in list(payload):
            if name=="part.power_dist.fzp" or name.endswith(".power_dist.svg"):del payload[name]
        assert set(parts)==set(module.by_key)|{"breadboard"}
    else:
        w=wiring(parts,board)
        assert set(parts)==set(module.by_key)|{"power_dist"}
    definitions={}
    for key,physical in parts.items():
        name=f"part.{key}.fzp"
        if key=="breadboard":
            from library_artwork import ROOT as LIBRARY
            definition=ET.parse(LIBRARY/"breadboard.fzp").getroot()
            for item in list(definition.find("views")):definition.find("views").remove(item)
            for view,layer in [("breadboardView","breadboard"),("iconView","icon")]:
                sub(sub(sub(definition.find("views"),view),"layers",image=f"{layer}/breadboard.svg"),"layer",layerId=layer)
            for c in definition.findall("connectors/connector"):
                for v in list(c.find("views")):c.find("views").remove(v)
                sub(sub(c.find("views"),"breadboardView"),"p",layer="breadboard",svgId=c.get("id")+"pin",terminalId=c.get("id")+"terminal")
            payload["svg.icon.breadboard.svg"]=physical.svg("icon")
        else:definition=ET.fromstring(payload[name])
        # Solderless parts have different images and terminal positions. Fritzing
        # caches artwork by moduleId across documents, including batch exports.
        old_id=definition.get("moduleId")
        new_id=old_id+("_solderless_library_v1"if variant=="solderless"else"_library_v1")
        definition.set("moduleId",new_id)
        definition.find("description").text="OpenBot DIY: bundled Fritzing library artwork adapted to the existing connector IDs. Original author and license: library-parts/sources.json. See README.breadboard.ru-RU.md."
        if hasattr(physical,"library"):
            from library_artwork import ROOT as LIBRARY
            credits=json.loads((LIBRARY/"sources.json").read_text())[physical.library]
            definition.find("author").text=credits["author"]
            definition.find("description").text+=" Source: "+credits["source"]+"; "+credits["license"]
        definitions[new_id]=definition
        payload[name]=xml(definition)
        payload[f"svg.breadboard.{key}.svg"]=physical.svg()
        # Separate identifiers prevent replacing an original part in the cache.
        if key=="breadboard":
            inst=sub(sketch.find("instances"),"instance",moduleIdRef=old_id,modelIndex=physical.part.index,path="breadboard.fzp")
            sub(inst,"title").text=physical.part.title
            sub(sub(inst,"views"),"breadboardView",layer="breadboard")
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
    for a,b in attachments:
        for source,target in [(a,b),(b,a)]:
            sp=parts[source[0]].part;tp=parts[target[0]].part
            cid=sp.connector(source[1]);tid=tp.connector(target[1]);con=views[sp.index]
            c=con.find(f"connector[@connectorId='{cid}']")
            if c is None:
                c=sub(con,"connector",connectorId=cid,layer="breadboard");sub(c,"geometry",x=0,y=0);sub(c,"connects")
            sub(c.find("connects"),"connect",modelIndex=tp.index,connectorId=tid,layer="breadboard")
    expected=json.loads((ROOT/("source" if board=="nano" else "source-esp32")/"nets.json").read_text())
    if variant=="solderless":expected=sorted(sorted(n for n in group if not n.startswith("power_dist."))for group in expected)
    for definition in definitions.values():
        assert definition.find("properties/property[@name='family']") is not None
    for view in ("breadboardView","schematicView"):
        assert graph_nets(sketch,definitions,view)==expected,(board,view,"net mismatch")
    # Preserve component positions and Schematic connections, except the
    # distribution header explicitly replaced in the solderless variant.
    by_index={i.get("modelIndex"):i for i in sketch.findall("instances/instance")}
    for a in original.findall("instances/instance"):
        if int(a.get("modelIndex"))in removed:continue
        b=by_index[a.get("modelIndex")]
        aa=deepcopy(a.find("views/schematicView"));bb=deepcopy(b.find("views/schematicView"))
        if removed and aa is not None:
            for connects in aa.findall("connectors/connector/connects"):
                for ref in list(connects):
                    if int(ref.get("modelIndex"))in removed:connects.remove(ref)
        assert (ET.tostring(aa)if aa is not None else None)==(ET.tostring(bb)if bb is not None else None)
    newstem=stem+("-on-breadboard"if variant=="solderless"else"-breadboard")
    payload[newstem+".fz"]=xml(sketch)
    outdir=ROOT/("source-nano-on-breadboard"if variant=="solderless"else"source-breadboard-"+board)
    outdir.mkdir(exist_ok=True)
    current_paths=set()
    for name,content in payload.items():
        if name.endswith(".fz"):path=outdir/name
        elif name.startswith("part."):path=outdir/"parts"/name.removeprefix("part.")
        elif name.startswith("svg."):
            _,layer,filename=name.split(".",2);path=outdir/"parts/svg"/layer/filename
        else:raise ValueError(name)
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(content);current_paths.add(path)
    for path in (outdir/"parts").rglob("junction_*"):
        if path.is_file() and path not in current_paths:path.unlink()
    (outdir/"nets.json").write_text(json.dumps(expected,ensure_ascii=False,indent=2)+"\n")
    with ZipFile(ROOT/(newstem+".fzz"),"w",ZIP_DEFLATED) as z:
        for name,content in payload.items():
            info=ZipInfo(name,(2026,10,11,12,0,0));info.compress_type=ZIP_DEFLATED;z.writestr(info,content)
    print(f"{newstem}: {len(parts)} parts + {marker_count} native junctions, {len(w.wires)} Breadboard wires, {len(expected)} nets; Schematic preserved.")


if __name__=="__main__":
    nano.validate();esp.validate()
    build(nano,"nano");build(esp,"esp32")
