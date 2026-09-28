from pathlib import Path
import base64,subprocess,xml.etree.ElementTree as E
out=Path(__file__).resolve().parent
ns='http://www.w3.org/2000/svg';E.register_namespace('',ns)
logo=E.parse(out.parent/'master/peyvand-logo-master.svg').getroot()
def asset(p):return 'data:image/png;base64,'+base64.b64encode(p.read_bytes()).decode()
def make(n):
 root=E.Element('svg',xmlns=ns,width='1920',height='1080',viewBox='0 0 1920 1080')
 def node(tag,**a):return E.SubElement(root,tag,{k.replace('_','-'):str(v) for k,v in a.items()})
 def text(s,x,y,size=32,fill='#15181B',anchor='end'):
  z=node('text',x=x,y=y,font_family='SF Arabic, Geeza Pro, sans-serif',font_size=size,fill=fill,text_anchor=anchor);z.text=s
 node('rect',width=1920,height=1080,fill='#E9ECEF')
 # Native SVG artwork in the heading; no regenerated logo or lettering.
 l=node('svg',x=1778,y=20,width=73,height=98,viewBox='0 0 1086 1448',fill='#15181B')
 for g in logo:
  if g.tag.endswith('g'):
   import copy;l.append(copy.deepcopy(g))
 text('گفت‌وگو دربارهٔ کتاب',1738,49,25,fill='#656D75')
 text('آیا چراغ‌هات روشنه؟',1738,95,38)
 node('line',x1=40,y1=126,x2=1880,y2=126,stroke='#C7CDD2',stroke_width=1)
 text('پیوند',48,84,32,anchor='start')
 gap=12;w=(1840-gap*(n-1))/n
 names=['میلاد','هومان','مهمان سوم'];paths=['milad.png','hooman.png',None]
 for i in range(n):
  x=40+i*(w+gap)
  node('rect',x=x,y=146,width=w,height=756,fill='#DCE1E5' if i%2==0 else '#D3DADF')
  if paths[i]:
   node('image',x=x,y=146,width=w,height=756,href=asset(out/paths[i]),preserveAspectRatio='xMidYMin slice')
  else:
   node('line',x1=x+w*.35,y1=455,x2=x+w*.65,y2=455,stroke='#9DA7AF',stroke_width=2)
   node('line',x1=x+w*.5,y1=455-w*.15,x2=x+w*.5,y2=455+w*.15,stroke='#9DA7AF',stroke_width=2)
   text('جایگاه مهمان',x+w/2,635,35,fill='#656D75',anchor='middle')
   text('نمونهٔ چیدمان',x+w/2,683,25,fill='#656D75',anchor='middle')
  node('rect',x=x+w-164,y=840,width=148,height=46,fill='#E9ECEF')
  text(names[i],x+w-36,873,29)
 node('line',x1=40,y1=932,x2=1880,y2=932,stroke='#C7CDD2',stroke_width=1)
 text('«آیا چراغ‌هات روشنه؟»',960,1014,49,anchor='middle')
 # Avoid duplicate namespace declaration when embedding namespaced paths.
 root.attrib.pop('xmlns',None);root.tag=f'{{{ns}}}svg'
 p=out/f'conversation-{n}.svg';E.ElementTree(root).write(p,encoding='utf-8',xml_declaration=True)
 subprocess.run(['/opt/homebrew/bin/rsvg-convert',str(p),'-o',str(p.with_suffix('.png'))],check=True)
for n in (2,3):make(n)
