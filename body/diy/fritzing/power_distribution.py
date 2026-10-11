"""Native 6 x 2 power header, with two separately soldered buses on perfboard."""
from copy import deepcopy
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from library_artwork import ROOT
import generate as nano


def part():
    pins=[]
    for row,side,x in [('5V','left',20),('GND','right',320)]:
        for i in range(6):
            p=nano.Pin(f'{row}{i+1}',x,100+42*i,side,f'{row} · {i+1}',f'connector{len(pins)}');pins.append(p)
    p=nano.Part('power_dist','Распределитель 6 × 2',1870,250,340,380,pins,
                buses=[[f'{row}{i+1}'for i in range(6)]for row in ['5V','GND']],index=900)
    return p


def schematic(layer='schematic'):
    p=part()
    out=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{p.width/90}in" height="{p.height/90}in" viewBox="0 0 {p.width} {p.height}"><g id="{layer}">',
         '<rect x="10" y="12" width="320" height="352" rx="8" fill="#fff8e8" stroke="#715f41" stroke-width="2"/>',
         nano.text(170,43,p.title,20,anchor='middle'),nano.text(170,72,'Два ряда по 6 контактов',15,anchor='middle')]
    for row,x,color in [('5V',85,'#ef6c00'),('GND',255,'#202124')]:
        out.append(f'<path d="M{x} 100 V310" stroke="{color}" stroke-width="5" fill="none"/>')
        for i in range(6):
            pin=next(c for c in p.pins if c.name==f'{row}{i+1}')
            out.extend([f'<path d="M{pin.x} {pin.y} H{x}" stroke="{color}" stroke-width="3"/>',
                        f'<circle id="{pin.id}pin" cx="{pin.x}" cy="{pin.y}" r="6" fill="{color}"/>',
                        f'<rect id="{pin.id}terminal" x="{pin.x-.5}" y="{pin.y-.5}" width="1" height="1" fill="none"/>',
                        nano.text(110 if row=='5V' else 230,pin.y+5,str(i+1),14,color,'middle')])
    out.append(nano.text(170,345,'5V       │       GND',19,anchor='middle'))
    return ('\n'.join(out)+'</g></svg>').encode()


def breadboard_graphic():
    # The stock Fritzing header and perfboard templates supply the component art.
    w,h=340,480
    out=[nano.text(170,28,'Распределитель 6 × 2',20,anchor='middle'),
         nano.text(170,58,'5V',20,'#ef6c00','middle'),nano.text(265,58,'GND',20,'#202124','middle')]
    scale=0.048
    holes=''
    hole_art=[]
    for xx in range(4):
        for yy in range(8):
            cx=500+1000*xx;cy=500+1000*yy
            # Circular cutouts and copper annuli from the perfboard template.
            holes+=f'M{cx-200},{cy} a200,200 0 1,0 400,0 a200,200 0 1,0 -400,0z '
            t=(ROOT/'perfboard_connectorTemplate.txt').read_text()
            for a,b in [('%1',str(cx)),('%2',str(cy)),('%3',str(xx)),('%4',str(yy)),('%5',f'{xx}_{yy}')]:t=t.replace(a,b)
            hole_art.append(t.replace('connector','lib_perf_'))
    t=(ROOT/'perfboard_boardLayerTemplate.txt').read_text()
    for a,b in [('%1','4'),('%2','8'),('%3','4000'),('%4','8000'),('%5',holes),('%6','3996'),('%7','7996'),('%8',''.join(hole_art))]: t=t.replace(a,b)
    t=t[t.index('<g'):t.rindex('</svg>')].replace('breadboardbreadboard','lib_perfboard')
    out.append(f'<g transform="translate(120 76) scale({scale})">{t}</g>')
    pins={}
    # Rotate a native two-row, six-position male header to stand vertically.
    for i in range(6):
        for col,filename,row in [(0,'generic_male_pin_header_bread_template.txt','5V'),(1,'generic_male_pin_header_bread_2nd_template.txt','GND')]:
            t=(ROOT/filename).read_text().replace('%1',f'_stock_{col}_{i}')
            t=re.sub(r'\[([-\d.]+)\]',lambda m:str(float(m.group(1))+1000*i),t)
            out.append(f'<g transform="translate(168 124) scale({scale}) matrix(0 1 1 0 0 0)">{t}</g>')
            x=168+scale*(500+1000*col);y=124+scale*(500+1000*i)
            pins[f'{row}{i+1}']=(x,y,'none','')
            out.append(nano.text(149 if col==0 else 282,y+5,str(i+1),15,'#203040','middle'))
    # Colored traces are an annotated view of the solder links on the underside.
    for row,color in [('5V','#ef6c00'),('GND','#202124')]:
        x,y=pins[row+'1'][:2]; _,yy=pins[row+'6'][:2]
        out.append(f'<path d="M{x} {y} V{yy}" stroke="{color}" stroke-width="4" fill="none" stroke-dasharray="5,4"/>')
    out.extend([nano.text(170,451,'Пайка снизу: два отдельных ряда',15,anchor='middle'),nano.text(170,475,'5V и GND между собой не соединять',14,anchor='middle')])
    return w,h,pins,out
