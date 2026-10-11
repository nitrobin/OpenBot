"""Use bundled, attributed Fritzing SVG artwork with the sketch's connector IDs.

Flatten nested SVG groups for Qt SVG's depth limit. Transform the original
connector coordinates together with the artwork; never guess pin positions.
"""
from copy import deepcopy
import math
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent / 'library-parts'
IDENTITY = (1, 0, 0, 1, 0, 0)


def multiply(a, b):
    aa, ab, ac, ad, ae, af = a
    ba, bb, bc, bd, be, bf = b
    return (aa*ba+ac*bb, ab*ba+ad*bb, aa*bc+ac*bd, ab*bc+ad*bd,
            aa*be+ac*bf+ae, ab*be+ad*bf+af)


def point(matrix, x, y):
    a, b, c, d, e, f = matrix
    return a*x+c*y+e, b*x+d*y+f


def transform(value):
    matrix = IDENTITY
    for name, args in re.findall(r'(\w+)\s*\(([^)]+)\)', value or ''):
        p = [float(n) for n in re.findall(r'[-+]?(?:\d*\.\d+|\d+\.?\d*)(?:[eE][-+]?\d+)?', args)]
        if name == 'matrix': m = tuple(p)
        elif name == 'translate': m = (1, 0, 0, 1, p[0], p[1] if len(p)>1 else 0)
        elif name == 'scale': m = (p[0], 0, 0, p[1] if len(p)>1 else p[0], 0, 0)
        elif name == 'rotate':
            r = math.radians(p[0]); m = (math.cos(r), math.sin(r), -math.sin(r), math.cos(r), 0, 0)
            if len(p)>1: m = multiply(multiply((1,0,0,1,p[1],p[2]),m),(1,0,0,1,-p[1],-p[2]))
        elif name == 'skewX': m = (1,0,math.tan(math.radians(p[0])),1,0,0)
        elif name == 'skewY': m = (1,math.tan(math.radians(p[0])),0,1,0,0)
        else: raise ValueError(name)
        matrix = multiply(matrix,m)
    return matrix


def matrix_text(m): return 'matrix('+','.join(f'{v:.10g}' for v in m)+')'


def center(element, end=False):
    a = element.attrib; tag = element.tag.rsplit('}',1)[-1]
    if tag=='g':
        circles=[n for n in element.iter()if n.tag.rsplit('}',1)[-1]=='circle']
        if circles:return center(circles[-1])
    if tag in ('circle','ellipse'): return float(a['cx']), float(a['cy'])
    if tag == 'rect': return float(a.get('x',0))+float(a['width'])/2, float(a.get('y',0))+float(a['height'])/2
    if tag == 'line': return (float(a['x2']),float(a['y2'])) if end else ((float(a['x1'])+float(a['x2']))/2,(float(a['y1'])+float(a['y2']))/2)
    raise ValueError((tag,a))


class Artwork:
    def __init__(self, name):
        self.name = name
        self.root = ET.parse(ROOT/(name+'.svg')).getroot()
        self.definition = ET.parse(ROOT/(name+'.fzp')).getroot()
        self.box = tuple(map(float,self.root.get('viewBox').split()))
        if name=='led':self.box=(0,0,21.467,74.754)
        self.coords = {}
        self.flat = []
        inherited_names = {'fill','stroke','stroke-width','stroke-linecap','stroke-linejoin','fill-rule','font-family','font-size','font-weight','font-style','text-anchor','visibility','display','opacity','fill-opacity','stroke-opacity','clip-path'}
        def visit(n, parent=IDENTITY, attrs=None, style=''):
            m = multiply(parent,transform(n.get('transform')))
            inherited = dict(attrs or {})
            inherited.update({k:v for k,v in n.attrib.items() if k in inherited_names})
            style += ';'+n.get('style','')
            tag = n.tag.rsplit('}',1)[-1]
            if n.get('id'): self.coords[n.get('id')] = (deepcopy(n),m)
            if tag in ('g','svg'):
                for child in n: visit(child,m,inherited,style)
            elif tag in ('metadata','namedview','title','desc'): pass
            else:
                item=deepcopy(n)
                item.tail=None
                for e in item.iter():
                    e.tag=e.tag.rsplit('}',1)[-1]
                    for k in list(e.attrib):
                        if k.startswith('{') and not k.endswith('}href'): del e.attrib[k]
                    if e.get('id'): e.set('id','lib_'+e.get('id'))
                for k,v in inherited.items(): item.attrib.setdefault(k,v)
                if style.strip(';'): item.set('style',style.strip(';'))
                item.set('transform',matrix_text(m))
                for e in item.iter():
                    for k,v in list(e.attrib.items()):
                        e.set(k,re.sub(r'url\(#([^)]+)\)',r'url(#lib_\1)',v).replace('Droid Sans','Arial').replace('Sans Serif','Arial'))
                self.flat.append(item)
        visit(self.root)

    def pin(self, cid):
        c=self.definition.find(f"connectors/connector[@id='{cid}']/views/breadboardView/p")
        ids=[c.get('terminalId'),c.get('svgId')]
        if self.name=='led':
            element,m=self.coords[c.get('legId')];return point(m,*center(element,end=True))
        for id_ in ids:
            if id_ in self.coords:
                element,m=self.coords[id_]
                try:return point(m,*center(element))
                except ValueError: pass
        # Battery packs use a path for a pin and a straight native leg.
        id_=c.get('legId')
        if id_ in self.coords:
            element,m=self.coords[id_];return point(m,*center(element,end=True))
        raise ValueError((self.name,cid,ids))

    def fit(self, x, y, w, h, rotation=0):
        bx,by,bw,bh=self.box
        if rotation==180: orient=(-1,0,0,-1,bw,bh);ow,oh=bw,bh
        elif rotation==90: orient=(0,1,-1,0,bh,0);ow,oh=bh,bw
        elif rotation==-90: orient=(0,-1,1,0,0,bw);ow,oh=bh,bw
        else: orient=IDENTITY;ow,oh=bw,bh
        scale=min(w/ow,h/oh)
        mat=multiply((scale,0,0,scale,x+(w-ow*scale)/2,y+(h-oh*scale)/2),multiply(orient,(1,0,0,1,-bx,-by)))
        graphic='<g transform="'+matrix_text(mat)+'">'+''.join(ET.tostring(n,encoding='unicode') for n in self.flat)+'</g>'
        return mat,graphic

    def resistance(self, value):
        # Keep the stock resistor shape, changing only its four color bands.
        colors={'20 кОм':['#C40808','#000000','#FF9900'],'30 кОм':['#FF9900','#000000','#FF9900'],
                '10 кОм':['#8A3D06','#000000','#FF9900'],'150 Ом':['#8A3D06','#008000','#8A3D06'],
                '1 кОм':['#8A3D06','#000000','#C40808'],'2 кОм':['#C40808','#000000','#C40808']}
        changes=dict(zip(['lib_band_1_st','lib_band_2_nd','lib_band_rd_multiplier'],colors[value]))
        changes['lib_gold_band']='#8A3D06'  # 1 % tolerance
        for n in self.flat:
            for e in n.iter():
                if e.get('id') in changes:
                    e.set('fill',changes[e.get('id')]);e.set('style',re.sub(r'fill\s*:[^;]+','',e.get('style','')))
