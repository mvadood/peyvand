"""Quick native SVG composition; real footage, exact approved logo, shaped Persian type."""
from pathlib import Path
import base64,copy,io,subprocess,xml.etree.ElementTree as E
from PIL import Image,ImageDraw,ImageFont
out=Path(__file__).resolve().parent
ns='http://www.w3.org/2000/svg';E.register_namespace('',ns)
root=E.Element(f'{{{ns}}}svg',width='1920',height='1080',viewBox='0 0 1920 1080')
def el(tag,parent=None,**args):return E.SubElement(root if parent is None else parent,tag,{k.replace('_','-'):str(v) for k,v in args.items()})
def data(p):return 'data:image/png;base64,'+base64.b64encode(p.read_bytes()).decode()
def type_(text,x,y,size,color='#E9ECEF',right=False):
 # Typography is rendered from the actual font using HarfBuzz/FriBidi (RAQM).
 font=ImageFont.truetype(str(out/'fonts/Vazirmatn-Bold.ttf'),size,layout_engine=ImageFont.Layout.RAQM)
 box=font.getbbox(text,direction='rtl',language='fa');w,h=box[2]-box[0]+8,box[3]-box[1]+8
 im=Image.new('RGBA',(w,h));ImageDraw.Draw(im).text((4-box[0],4-box[1]),text,font=font,fill=color,direction='rtl',language='fa')
 b=io.BytesIO();im.save(b,format='PNG')
 el('image',x=x-w if right else x,y=y,width=w,height=h,href='data:image/png;base64,'+base64.b64encode(b.getvalue()).decode())
 return h
el('rect',width=1920,height=1080,fill='#15181B')
defs=el('defs')
grad=el('radialGradient',parent=defs,id='light',cx='.6',cy='.35',r='.7')
el('stop',parent=grad,offset='0%',stop_color='#343C43');el('stop',parent=grad,offset='100%',stop_color='#15181B')
el('rect',x=710,y=0,width=1210,height=1080,fill='url(#light)')
# Oversized approved stroke carries the brand through the backdrop.
master=E.parse(out.parent/'master/peyvand-logo-master.svg').getroot()
g=el('g',transform='translate(-300 -260) scale(1.5)',fill='#22282D')
g.append(copy.deepcopy(master.find(f'{{{ns}}}g[@id="stroke-left"]')))
# One dominant speaker and a supporting reaction; no tiled meeting UI.
el('image',x=790,y=86,width=1130,height=955,href=data(out.parent/'layout-v1/hooman.png'))
el('image',x=130,y=105,width=550,height=465,href=data(out.parent/'layout-v1/milad.png'))
# Intentional hard baseline for the smaller camera crop; editorial topic below.
el('line',x1=100,y1=570,x2=700,y2=570,stroke='#737D86',stroke_width=2)
type_('میلاد',690,596,27,color='#A6B0B8',right=True)
type_('موضوع گفت‌وگو',690,659,24,color='#A6B0B8',right=True)
type_('مسئله',704,709,126,right=True)
type_('کجاست؟',704,858,126,right=True)
# Modest original logo, with the original Persian lettering.
l=el('svg',x=1782,y=36,width=76,height=102,viewBox='0 0 1086 1448',fill='#E9ECEF')
for node in master.findall(f'{{{ns}}}g'):l.append(copy.deepcopy(node))
type_('آیا چراغ‌هات روشنه؟',1720,52,31,color='#C1C9CF',right=True)
type_('هومان',1760,798,29,right=True)
# Compact subtitle over the camera instead of a permanent full-width footer.
el('rect',x=1036,y=914,width=690,height=88,fill='#15181B',fill_opacity='.94')
type_('«آیا چراغ‌هات روشنه؟»',1690,933,43,right=True)
p=out/'conversation-focus.svg';E.ElementTree(root).write(p,encoding='utf-8',xml_declaration=True)
subprocess.run(['/opt/homebrew/bin/rsvg-convert',str(p),'-o',str(p.with_suffix('.png'))],check=True)
