#!/usr/bin/env python3
"""Add the distribution header to existing sketches without moving existing parts."""
from copy import deepcopy
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from zipfile import ZipFile,ZipInfo,ZIP_DEFLATED
import generate as nano
import generate_esp32 as esp
from generate_breadboard import graph_nets,sub,xml
from power_distribution import part,schematic
from wire_colors import COLORS

ROOT=Path(__file__).resolve().parent
ID='OpenBot_DIY_6x2_power_distribution_v1'


def patch(module,board):
    stem=f'openbot-diy-{board}'
    with ZipFile(ROOT/(stem+'.fzz'))as z: payload={n:z.read(n)for n in z.namelist()}
    fn=next(n for n in payload if n.endswith('.fz'));sketch=ET.fromstring(payload[fn])
    original=deepcopy(sketch)
    removed={int(i.get('modelIndex'))for i in sketch.findall('instances/instance')if i.get('moduleIdRef')==ID or 30000<=int(i.get('modelIndex'))<30200}
    for i in list(sketch.find('instances')):
        if int(i.get('modelIndex'))in removed:sketch.find('instances').remove(i)
        else:
            for con in i.findall('views/*/connectors/connector/connects'):
                for ref in list(con):
                    if int(ref.get('modelIndex'))in removed:con.remove(ref)
    p=part()
    if board=='esp32':p.x=2300
    definition=ET.fromstring(nano.part_xml(p));definition.set('moduleId',ID)
    definition.find('description').text='6 x 2 header on perfboard: solder each row separately; one bus 5V, one bus GND. Never join the rows.'
    payload['part.power_dist.fzp']=xml(definition)
    for layer in ['breadboard','schematic','icon']:payload[f'svg.{layer}.power_dist.svg']=schematic(layer)
    instances=sketch.find('instances');inst=sub(instances,'instance',moduleIdRef=ID,modelIndex=p.index,path='power_dist.fzp');sub(inst,'title').text=p.title
    views=sub(inst,'views')
    allinst={int(i.get('modelIndex')):i for i in instances}
    for view,layer in [('breadboardView','breadboard'),('schematicView','schematic')]:
        v=sub(views,view,layer=layer);sub(v,'geometry',x=p.x,y=p.y,z=2.5);sub(v,'connectors')
        for offset,(net,src,pin,dst)in enumerate([('5V','l298n'if board=='nano'else'buck_logic','5V'if board=='nano'else'OUT+','5V1'),('GND','l298n'if board=='nano'else'buck_logic','GND','GND1')]):
            source=module.by_key[src];sv=allinst[source.index].find('views/'+view);geom=sv.find('geometry')
            sp=next(c for c in source.pins if c.name==pin);x=float(geom.get('x'))+sp.x;y=float(geom.get('y'))+sp.y
            tx,ty=p.point(dst)
            pts=[(x,y),(x,180+40*offset),(p.x-40 if net=='5V'else p.x+p.width+60,180+40*offset),(p.x-40 if net=='5V'else p.x+p.width+60,ty),(tx,ty)]
            refs=[(source.index,sp.id)]
            ids=[]
            for k,(a,b)in enumerate(zip(pts,pts[1:])):
                idx=30000+(0 if view=='schematicView'else 100)+offset*10+k;ids.append(idx)
                wi=sub(instances,'instance',moduleIdRef='WireModuleID',modelIndex=idx,path='wire.fzp');sub(wi,'title').text=f'{net} → колодка'
                vw=sub(sub(wi,'views'),view,layer='schematicTrace'if view=='schematicView'else'breadboardWire')
                sub(vw,'geometry',x=a[0],y=a[1],x1=0,y1=0,x2=b[0]-a[0],y2=b[1]-a[1],z=3.5,wireFlags=128 if view=='schematicView'else 64)
                sub(vw,'wireExtras',mils=24,color=COLORS[net],opacity=1,banded=0);sub(vw,'connectors');allinst[idx]=wi
            pairs=[((source.index,sp.id),(ids[0],'connector0'))]
            pairs.extend(((aa,'connector1'),(bb,'connector0'))for aa,bb in zip(ids,ids[1:]))
            pairs.append(((ids[-1],'connector1'),(p.index,p.connector(dst))))
            for a,b in pairs:
                for (idx,cid),(other,ocid)in [(a,b),(b,a)]:
                    target=allinst[idx].find('views/'+view);con=target.find('connectors');iswire=allinst[idx].get('moduleIdRef')=='WireModuleID'
                    lay=('schematicTrace'if view=='schematicView'else'breadboardWire')if iswire else layer
                    c=con.find(f"connector[@connectorId='{cid}']")
                    if c is None:c=sub(con,'connector',connectorId=cid,layer=lay);sub(c,'geometry',x=0,y=0);sub(c,'connects')
                    otherwire=allinst[other].get('moduleIdRef')=='WireModuleID';olay=('schematicTrace'if view=='schematicView'else'breadboardWire')if otherwire else layer
                    sub(c.find('connects'),'connect',modelIndex=other,connectorId=ocid,layer=olay)
    definitions={}
    for n,c in payload.items():
        if n.endswith('.fzp'):d=ET.fromstring(c);definitions[d.get('moduleId')]=d
    expected=graph_nets(sketch,definitions,'schematicView')
    assert graph_nets(sketch,definitions,'breadboardView')==expected
    oldnets=json.loads((ROOT/('source'if board=='nano'else'source-esp32')/'nets.json').read_text())
    assert sorted(sorted(n for n in group if not n.startswith('power_dist.'))for group in expected)==sorted(sorted(n for n in group if not n.startswith('power_dist.'))for group in oldnets)
    for old in original.findall('instances/instance'):
        if int(old.get('modelIndex'))in removed:continue
        new=allinst[int(old.get('modelIndex'))]
        for view in ['breadboardView','schematicView']:
            before=old.find('views/'+view+'/geometry');after=new.find('views/'+view+'/geometry')
            assert ET.tostring(before)==ET.tostring(after)
    payload[fn]=xml(sketch)
    source=ROOT/('source'if board=='nano'else'source-esp32')
    for n,c in payload.items():
        if n.endswith('.fz'):path=source/n
        elif n.startswith('part.'):path=source/'parts'/n.removeprefix('part.')
        else:_,layer,name=n.split('.',2);path=source/'parts/svg'/layer/name
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(c)
    (source/'nets.json').write_text(json.dumps(expected,ensure_ascii=False,indent=2)+'\n')
    with ZipFile(ROOT/(stem+'.fzz'),'w',ZIP_DEFLATED)as z:
        for n,c in payload.items():info=ZipInfo(n,(2026,10,11,12,0,0));info.compress_type=ZIP_DEFLATED;z.writestr(info,c)
    print(stem,'added 6 x 2 distributor;',len(expected),'nets; existing positions preserved')

if __name__=='__main__':patch(nano,'nano');patch(esp,'esp32')
