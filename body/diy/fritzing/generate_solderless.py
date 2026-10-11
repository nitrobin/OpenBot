#!/usr/bin/env python3
"""Nano variant: real solderless breadboard buses, four resistors and two LEDs."""
import xml.etree.ElementTree as ET
from library_artwork import Artwork,point,matrix_text
import generate as nano
from generate_breadboard import Physical,Wiring,txt,build

MOUNT={
 'r1':{'1':'B3','2':'B9'},'r2':{'1':'B12','2':'B18'},
 'r3':{'1':'H3','2':'H9'},'r4':{'1':'H12','2':'H18'},
 'led_l':{'K':'E22','A':'E23'},'led_r':{'K':'E26','A':'E27'},
}


def prepare(parts):
    del parts['power_dist']
    a=Artwork('breadboard');scale=4;bx,by=1000,1320
    mat,art=a.fit(0,0,a.box[2]*scale,a.box[3]*scale)
    pins={c.get('id'):(*point(mat,*a.pin(c.get('id'))),'none','')for c in a.definition.findall('connectors/connector')}
    p=nano.Part('breadboard','Беспаечная макетная плата',bx,by,a.box[2]*scale,a.box[3]*scale,
                [nano.Pin(cid,x,y,side,id=cid)for cid,(x,y,side,_)in pins.items()],index=900)
    graphic=[art]
    for row,label,color in [('W','5V','#ef6c00'),('X','GND','#202124'),('Y','GND','#202124'),('Z','5V','#ef6c00')]:
        y=pins[row+'1'][1]
        graphic.append(f'<path d="M20 {y-12} H{p.width-20}" stroke="{color}" stroke-width="2" fill="none"/>')
        graphic.append(txt(12,y+5,row+' · '+label,14,color))
    parts['breadboard']=Physical(p,bx,by,p.width,p.height,pins,graphic)
    for key,holes in MOUNT.items():
        old=parts[key];artwork=Artwork('led'if key.startswith('led')else'resistor')
        if key.startswith('r'):artwork.resistance(old.part.value)
        cidmap={'1':'connector0','2':'connector1'}if key.startswith('r')else{'K':'connector0','A':'connector1'}
        names=list(holes);p1=parts['breadboard'].point(holes[names[0]]);p2=parts['breadboard'].point(holes[names[1]])
        q1=artwork.pin(cidmap[names[0]]);q2=artwork.pin(cidmap[names[1]])
        factor=(p2[0]-p1[0])/(q2[0]-q1[0]);assert factor>0
        x=min(p1[0],p2[0])-25;y=p1[1]-factor*artwork.box[3]-35
        m=(factor,0,0,factor,p1[0]-x-factor*q1[0],p1[1]-y-factor*q1[1])
        image='<g transform="'+matrix_text(m)+'">'+''.join(ET.tostring(n,encoding='unicode')for n in artwork.flat)+'</g>'
        pp={name:(*point(m,*artwork.pin(cidmap[name])),'none','')for name in holes}
        ww=factor*artwork.box[2]+50;hh=factor*artwork.box[3]+70
        label=('LED L'if key=='led_l'else'LED R')if key.startswith('led')else old.part.title+' · '+old.part.value
        # Resistor names sit near their row; LEDs have separate A/K labels.
        graphic=[image,txt(ww/2,25 if key.startswith('led')else pp['1'][1]-34,label,17,anchor='middle',bold=True)]
        if key.startswith('led'):
            for name,(px,py,*_)in pp.items():graphic.append(txt(px,py+22,'A (+)'if name=='A'else'K (−)',12,anchor='middle'))
        parts[key]=Physical(old.part,x,y,ww,hh,pp,graphic);parts[key].library='led'if key.startswith('led')else'resistor'
        for name,hole in holes.items():assert all(abs(a-b)<1e-6 for a,b in zip(parts[key].point(name),parts['breadboard'].point(hole)))
    parts['sonar'].x=2120;parts['oled'].x=2120
    parts['footer'].y=2140
    parts['footer'].graphic=[txt(8,26+28*i,t,18)for i,t in enumerate([
      'Обычная беспаечная макетная плата: R1–R4 и LED L / LED R установлены в её отверстия.',
      'В каждой колонке A–E соединены; F–J соединены отдельно. Через центральный паз соединения нет.',
      'Верхние шины: 5V и GND. Нижние шины соединены с верхними двумя перемычками.',
      'Цвет = назначение провода. Пересечения без точки не соединены. Контакты сверяй по маркировке.',
      'Питание двигателей подключено к L298N отдельными проводами; через макетную плату оно не проходит.',
      'Номиналы, питание Nano и настройки — см. README.nano-on-breadboard.ru-RU.md.',
    ])]
    parts['legend'].y=2350
    parts['heading'].graphic=[txt(10,28,'OpenBot DIY · Arduino Nano · обычная макетная плата',30,bold=True),txt(10,61,'Резисторы и светодиоды установлены в отверстия; питание распределяется по шинам 5V / GND.',20)]
    w=Wiring(parts)
    def r(a,b,net,bends=()):w.route(a,b,net,bends)
    def bb(hole):return ('breadboard',hole)
    def p(key,pin):return w.point(key,pin)
    def exit_point(key,pin):
        x,y=p(key,pin);q=parts[key];side=q.pins[pin][2]
        return (q.x-40,y)if side=='left'else(q.x+q.w+40,y)if side=='right'else(x,q.y+q.h+25)if side=='bottom'else(x,q.y+35)
    r(('battery','+'),('switch','IN'),'VBAT',[(445,p('battery','+')[1]),(445,p('switch','IN')[1])])
    vb=w.junction('VBAT',710,350);r(('switch','OUT'),vb,'VBAT',[exit_point('switch','OUT'),(710,parts['switch'].y+parts['switch'].h+25)])
    qx,qy=p('l298n','+12V');r(vb,('l298n','+12V'),'VBAT',[(710,520),(990,520),(990,1095),(qx,1095)])
    tx,ty=w.positions[bb('A3')];r(vb,bb('A3'),'VBAT',[(850,350),(850,ty-30),(tx,ty-30)])
    x,y=w.positions[bb('A9')];xx,yy=w.positions[bb('A12')];r(bb('A9'),bb('A12'),'ADC',[(x,y-25),(xx,yy-25)])
    x,y=p('nano','A7');tx,ty=w.positions[bb('C9')];r(('nano','A7'),bb('C9'),'ADC',[(920,y),(920,ty),(tx,ty)])
    r(bb('A18'),bb('X17'),'GND')
    r(bb('W5'),bb('Z5'),'5V',[(bx-60,by+28),(bx-60,by+576)])
    r(bb('X5'),bb('Y5'),'GND',[(bx-30,by+58),(bx-30,by+547)])
    for i,(key,pin,slot)in enumerate([('l298n','5V','W1'),('nano','5V','W7'),('enc_l','VCC','W13'),('enc_r','VCC','W19'),('sonar','VCC','W25'),('oled','VCC','W29')]):
        x,y=p(key,pin);tx,ty=w.positions[bb(slot)]
        if key in ('nano','l298n'):
            yy=1210-25*i;lane=940-25*i
            bends=[exit_point(key,pin),(lane,exit_point(key,pin)[1]),(lane,yy),(tx,yy)]
        else:
            lane=2480+25*i;yy=1210-25*i
            bends=[exit_point(key,pin),(lane,exit_point(key,pin)[1]),(lane,yy),(tx,yy)]
        r((key,pin),bb(slot),'5V',bends)
    for i,(key,pin,slot)in enumerate([('l298n','GND','X1'),('nano','GND','X7'),('enc_l','GND','X13'),('enc_r','GND','X19'),('sonar','GND','X25'),('oled','GND','X29'),('battery','GND','X3')]):
        x,y=p(key,pin);tx,ty=w.positions[bb(slot)];yy=1240-25*i
        if key in ('nano','l298n','battery'):
            lane=880-25*i;bends=[exit_point(key,pin),(lane,exit_point(key,pin)[1]),(lane,yy),(tx,yy)]
        else:
            lane=2700+25*i;bends=[exit_point(key,pin),(lane,exit_point(key,pin)[1]),(lane,yy),(tx,yy)]
        r((key,pin),bb(slot),'GND',bends)
    for npin,rhole,lane,yy in [('D4','J3',1580,1990),('D7','J12',1620,2020)]:
        x,y=p('nano',npin);tx,ty=w.positions[bb(rhole)];r(('nano',npin),bb(rhole),'LED',[(lane,y),(lane,yy),(tx,yy)])
    for a,b in [('J9','D23'),('J18','D27')]:
        x,y=w.positions[bb(a)];xx,yy=w.positions[bb(b)];r(bb(a),bb(b),'LED',[(x,by+302),(xx,by+302)])
    for a,b,offset in [('D22','Y25',30),('D26','Y29',60)]:
        x,y=w.positions[bb(a)];xx,yy=w.positions[bb(b)];r(bb(a),bb(b),'GND',[(x+offset,y),(x+offset,by+650),(xx,by+650)])
    for i,npin in enumerate(['D5','D6','D9','D10']):
        x,y=p('nano',npin);qx,qy=p('l298n',f'IN{i+1}');lane=1460+30*i;yy=1160+25*i
        r(('nano',npin),('l298n',f'IN{i+1}'),'PWM',[(lane,y),(lane,yy),(qx,yy)])
    for npin,key,mpin,lane,net in [('D2','enc_l','D0',1560,'encoder'),('D3','enc_r','D0',1600,'encoder'),('D12','sonar','Trig',1660,'sonar'),('D11','sonar','Echo',1700,'sonar')]:
        x,y=p('nano',npin);qx,qy=p(key,mpin);r(('nano',npin),(key,mpin),net,[(lane,y),(lane,qy+65),(qx,qy+65)])
    for npin,mpin,lane,yy in [('A5','SCL',1770,440),('A4','SDA',1810,465)]:
        x,y=p('nano',npin);qx,qy=p('oled',mpin);r(('nano',npin),('oled',mpin),'I2C',[(1080 if npin=='A5'else 1050,y),(1080 if npin=='A5'else 1050,yy),(lane,yy),(lane,1485),(qx,1485)])
    for key,out,lane in [('motor_lf','OUT1',320),('motor_lb','OUT1',320),('motor_lf','OUT2',345),('motor_lb','OUT2',345),('motor_rf','OUT4',880),('motor_rb','OUT4',880),('motor_rf','OUT3',910),('motor_rb','OUT3',910)]:
        pin='+'if out in ('OUT1','OUT4')else'−';x,y=p(key,pin);qx,qy=p('l298n',out);r((key,pin),('l298n',out),'motor',[(lane,y),(lane,qy)])
    attachments=[((key,name),bb(hole))for key,holes in MOUNT.items()for name,hole in holes.items()]
    return parts,w,attachments

if __name__=='__main__':
    nano.validate();build(nano,'nano',variant='solderless')
