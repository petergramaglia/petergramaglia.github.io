#!/usr/bin/env python3
"""Author deterministic colored engraving atlases and lengthwise reveal maps.

Every visible pixel is coverage from a drawn path, never a photograph overlay.
Photographs guide selected contour paths and the brush palette. timeN.png is an
8-bit threshold: reveal = channel / 255 * 1.1 - .1. All assets share normalized
coordinates with the approved source. Requires Pillow, NumPy, SciPy.
"""
from pathlib import Path
import importlib.util
import json
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter, sobel, distance_transform_edt, map_coordinates
from scipy.interpolate import PchipInterpolator

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('geometry',ROOT/'scripts/prepare-assets.py')
geo=importlib.util.module_from_spec(spec);spec.loader.exec_module(geo)
PAPER=np.array([243.,240.,231.]); INK=np.array([57.,69.,71.])

class Plate:
    def __init__(self,w,h):
        self.w=w;self.h=h
        self.rgb=np.zeros((h,w,3),np.float32)
        self.alpha=np.zeros((h,w),np.float32)
        self.time=np.ones((h,w),np.float32)
    def path(self,points,width,color,start,span,opacity=1):
        p=np.asarray(points,dtype=float)
        if len(p)<2:return
        d=np.linalg.norm(np.diff(p,axis=0),axis=1);cum=np.r_[0,np.cumsum(d)]
        if cum[-1]<.01:return
        colors=np.asarray(color)
        fixed=colors.ndim==1
        for i,(a,b) in enumerate(zip(p[:-1],p[1:])):
            length=d[i]
            if length<.01:continue
            r=width/2
            x0=max(0,int(min(a[0],b[0])-r-1));x1=min(self.w,int(max(a[0],b[0])+r+2))
            y0=max(0,int(min(a[1],b[1])-r-1));y1=min(self.h,int(max(a[1],b[1])+r+2))
            if x1<=x0 or y1<=y0:continue
            yy,xx=np.mgrid[y0:y1,x0:x1]
            t=np.clip(((xx-a[0])*(b[0]-a[0])+(yy-a[1])*(b[1]-a[1]))/(length*length),0,1)
            dist=np.hypot(xx-a[0]-t*(b[0]-a[0]),yy-a[1]-t*(b[1]-a[1]))
            cov=np.clip(r+.6-dist,0,1)*opacity
            c=colors if fixed else colors[i][None,None,:]*(1-t[:,:,None])+colors[i+1][None,None,:]*t[:,:,None]
            olda=self.alpha[y0:y1,x0:x1]
            oldrgb=self.rgb[y0:y1,x0:x1]
            newa=cov+olda*(1-cov)
            oldrgb[:]=(c*cov[:,:,None]+oldrgb*olda[:,:,None]*(1-cov[:,:,None]))/np.maximum(newa[:,:,None],1e-8)
            time=self.time[y0:y1,x0:x1]
            threshold=start+span*(cum[i]+t*length)/cum[-1]
            # Store threshold even at antialiased edges: empty texels must not
            # pull thin stroke edges toward the final frame when filtered.
            take=(cov>.02)&((cov>=olda*.65)|(olda<.1))
            time[take]=threshold[take]
            olda[:]=newa
    def save(self,dest,index):
        covered=self.alpha>.02
        distance,nearest=distance_transform_edt(~covered,return_indices=True)
        gutter=(~covered)&(distance<=3)
        self.rgb[gutter]=self.rgb[nearest[0][gutter],nearest[1][gutter]]
        self.time[gutter]=self.time[nearest[0][gutter],nearest[1][gutter]]
        # Overlapping very faint antialias edges can accumulate coverage before
        # any segment wins the threshold test. Give those the nearest true
        # stroke timing rather than leaving their default final-frame value.
        timed=(self.alpha>.02)&(self.time<.99)
        distance,nearest=distance_transform_edt(~timed,return_indices=True)
        missing=(self.time>=.99)&((distance<=3)|(self.alpha>0))
        self.time[missing]=self.time[nearest[0][missing],nearest[1][missing]]
        rgba=np.dstack((np.clip(self.rgb,0,255),self.alpha*255)).astype('uint8')
        Image.fromarray(rgba,'RGBA').save(dest/f'layer{index}.webp',lossless=True,method=6,exact=True)
        t=np.clip((self.time+.1)/1.1*255,0,255).astype('uint8')
        Image.fromarray(t,'L').save(dest/f'time{index}.png',optimize=True)


def make(name):
    g=geo.GEOMETRY[name]
    size=(1440,810) if name=='desktop' else (900,1200)
    w,h=size; rng=np.random.default_rng(7426)
    photo=Image.open(ROOT/f'assets/{name}/photo.webp').convert('RGB').resize(size,Image.Resampling.LANCZOS)
    source=np.asarray(photo,dtype=float)
    source=gaussian_filter(source,(2.2,2.2,0))
    lum=source@np.array([.2126,.7152,.0722])
    # A slightly richer limited-value pencil palette makes light and shade read
    # as colored marks while avoiding the dense black of an unmodified photo.
    source=np.clip(lum[:,:,None]+(source-lum[:,:,None])*1.2,0,255)
    source=np.clip(source*.96+PAPER*.04,0,255)
    plates=[Plate(w,h) for _ in range(3)]
    xs=np.arange(w)/w
    skyline=geo.curve(g['skyline'],xs)*h
    bounds=[skyline]+[geo.curve(r,xs)*h for r in g['ridges']]
    bounds[-1]=np.maximum(bounds[-1],h*1.035)
    def sample(p):
        p=np.asarray(p);x=np.clip(p[:,0].astype(int),0,w-1);y=np.clip(p[:,1].astype(int),0,h-1)
        return source[y,x]
    def points(norm):return np.asarray(norm)*np.array([w,h])
    def subdivide(p,step=4):
        p=np.asarray(p);u=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]
        q=np.linspace(0,u[-1],max(2,int(u[-1]/step)))
        return np.column_stack((np.interp(q,u,p[:,0]),np.interp(q,u,p[:,1])))
    # A few open construction gestures establish the mountain at zero. They
    # intentionally omit the full skyline, foreground, clouds and climber.
    # Subsequent paths add actual geographic structure over the first half.
    rough = {
      'desktop': [[(.08,.60),(.24,.40),(.35,.43)],[(.37,.43),(.472,.365),(.67,.55)],
                  [(.472,.365),(.50,.47),(.57,.56)],[(.14,.68),(.28,.65),(.40,.70)]],
      'mobile': [[(.19,.39),(.439,.332),(.67,.42)],[(.439,.332),(.46,.42),(.58,.48)],
                 [(.03,.48),(.23,.55),(.38,.54)]]
    }
    for line in rough[name]:
        plates[0].path(subdivide(points(line)),.83,INK,-.09,.045,.40)
    # Draw each refined ridge in sections, so the first fifteen percent is
    # visibly an unfinished outline rather than a complete landscape.
    for i,line in enumerate(bounds[:-1]):
        sections=5 if i==0 else 4
        for section,idx in enumerate(np.array_split(np.arange(0,w,3),sections)):
            p=np.column_stack((idx,line[idx]))
            start=(.065+section*.025) if i==0 else (.16+i*.035+section*.018)
            plates[0].path(p,1.05 if i==0 else .72,INK,start,.065,.76 if i==0 else .48)
    for i,spur in enumerate(g['spurs']):
        p=subdivide(points(spur))
        plates[0].path(p,.85,INK,.10+i*.016,.12,.58)
    # Cloud gestures are open contours following the prominent cloud bank.
    clouds = {
      'desktop': [[(.51,.342),(.56,.294),(.62,.255),(.72,.211),(.83,.169),(.96,.135)],
                  [(.55,.30),(.66,.284),(.75,.267),(.87,.222),(.99,.181)],
                  [(.68,.337),(.79,.326),(.9,.317),(1,.30)]],
      'mobile': [[(.485,.311),(.53,.298),(.58,.276),(.66,.249),(.75,.228),(.85,.199),(1,.166)],
                 [(.59,.267),(.69,.27),(.78,.257),(.9,.24),(1,.232)],
                 [(.50,.337),(.61,.336),(.72,.326),(.82,.327),(.96,.315)]]
    }
    for i,line in enumerate(clouds[name]):
        plates[0].path(subdivide(points(line)),.68,INK,.21+i*.035,.11,.38)
    # Trace selected long source edges as individual connected pencil paths.
    # Nonmaximum suppression selects contours; minimum arc length and a cap
    # per region discard photographic grain. These are new ridge/rock/cloud
    # shapes, not a blanket edge image or repeated texture strokes.
    contour_tone=gaussian_filter(lum,1.05)
    gx=sobel(contour_tone,axis=1)/8;gy=sobel(contour_tone,axis=0)/8
    magnitude=np.hypot(gx,gy)
    yy,xx=np.mgrid[:h,:w]
    dx=gx/(magnitude+1e-8);dy=gy/(magnitude+1e-8)
    before=map_coordinates(magnitude,[yy-dy,xx-dx],order=1,mode='nearest')
    after=map_coordinates(magnitude,[yy+dy,xx+dx],order=1,mode='nearest')
    ridge=(magnitude>=before)&(magnitude>=after)&(magnitude>1.8)
    available=set(map(tuple,np.column_stack(np.nonzero(ridge))))
    neighbors=[(dy,dx) for dy in [-1,0,1] for dx in [-1,0,1] if dx or dy]
    def walk(seed):
        result=[seed];available.discard(seed);direction=None
        while True:
            y,x=result[-1]
            candidates=[(y+dy,x+dx) for dy,dx in neighbors if (y+dy,x+dx) in available]
            if not candidates:break
            if direction is None:
                nxt=max(candidates,key=lambda q:magnitude[q])
            else:
                def score(q):
                    v=np.array(q)-np.array((y,x));v=v/np.linalg.norm(v)
                    return np.dot(v,direction)+.015*magnitude[q]
                nxt=max(candidates,key=score)
                if score(nxt)<-.15:break
            v=np.array(nxt)-np.array((y,x));direction=v/np.linalg.norm(v)
            available.remove(nxt);result.append(nxt)
        return result
    paths=[]
    seeds=sorted(available,key=lambda q:float(magnitude[q]),reverse=True)
    for seed in seeds:
        if seed not in available:continue
        forward=walk(seed)
        # The strongest point is usually in the middle of its contour.
        available.add(seed);backward=walk(seed)
        chain=backward[:0:-1]+forward
        if len(chain)<13:continue
        p=np.array(chain)[:,::-1].astype(float)
        length=np.linalg.norm(np.diff(p,axis=0),axis=1).sum()
        if length<20:continue
        cx,cy=p.mean(axis=0);cx=int(cx);cy=int(cy)
        region='cloud' if cy<skyline[cx]-5 else ('rock' if cy>h*.74 else 'mountain')
        # Keep the sky mostly empty and reject weak, featureless gradients.
        strength=float(np.mean([magnitude[q] for q in chain]))
        if region=='cloud' and strength<2.6:continue
        paths.append((length*strength,region,p,strength))
    counts=dict(cloud=0,mountain=0,rock=0)
    limits=dict(cloud=115,mountain=430,rock=250)
    bx0,by0,bx1,by1=g['subject']
    for score,region,p,strength in sorted(paths,key=lambda q:-q[0]):
        if counts[region]>=limits[region]:continue
        cx,cy=p.mean(axis=0)/[w,h]
        if bx0<cx<bx1 and by0<cy<by1:continue
        rank=counts[region]/limits[region];counts[region]+=1
        # Broad shapes arrive first; small facets follow across .3--.6.
        if region=='cloud':start=.23+rank*.11;span=.07;opacity=.38
        elif region=='mountain':start=.20+rank*.27;span=.075;opacity=.50
        else:start=.32+rank*.20;span=.075;opacity=.54
        # Reduce pixel-scale stair stepping without erasing a rock's corners.
        p=gaussian_filter(p,(.65,0))[::2]
        plates[0].path(p,.72 if region=='cloud' else .82,INK,start,span,opacity)
    # The human figure is discovered after the main landforms. Silhouette,
    # hood, pack, bent arms, legs and walking poles have independent timings.
    p=subdivide(points(g['person']+[g['person'][0]]))
    plates[0].path(p,1.05,INK,.31,.12,.78)
    person_details={
      'desktop': [[(.49,.705),(.5,.705),(.503,.715),(.493,.722),(.49,.705)],
                   [(.485,.718),(.499,.726),(.509,.724)],[(.49,.737),(.505,.741),(.508,.767),(.494,.771)],
                   [(.499,.774),(.501,.806),(.498,.836)],[(.459,.765),(.466,.845)],[(.527,.76),(.527,.852)]],
      'mobile': [[(.479,.649),(.498,.649),(.502,.66),(.488,.671),(.479,.649)],
                  [(.47,.671),(.49,.688),(.516,.679)],[(.479,.692),(.514,.697),(.516,.719),(.485,.72)],
                  [(.5,.723),(.505,.75),(.499,.777)],[(.415,.705),(.438,.794)],[(.563,.707),(.56,.787)]]
    }
    for i,line in enumerate(person_details[name]):
        plates[0].path(subdivide(points(line)),.8,INK,.38+i*.019,.07,.66)
    print(name,'structural paths',counts,flush=True)
    # Sky is a field of long horizontal colored pencil strokes, clipped to the
    # real skyline. Cloud and sunset color is sampled along each moving stroke.
    sky_rows=np.cumsum(rng.uniform(4.1,4.6,int(h*.68/4.1)+10))-18
    for y in sky_rows:
        x=-rng.uniform(0,120)
        while x<w:
            length=rng.uniform(320,900); xx=np.linspace(max(-2,x),min(w+2,x+length),max(2,int(length/5)))
            yy=y+np.sin(xx/w*2.8+y/h*1.4)*13
            valid=yy<skyline[np.clip(xx.astype(int),0,w-1)]-1
            p=np.column_stack((xx[valid],yy[valid]))
            if len(p)>1:
                start=.12+.20*(y/h)+rng.uniform(0,.13)
                plates[1].path(p,rng.uniform(3.8,4.2),sample(p),start,rng.uniform(.11,.18),.98)
            x+=length+rng.uniform(.1,.7)
    # Underlying terrain ribbons interpolate the authored ridge contours.
    # Each ribbon is broken into long independent pencil gestures.
    for band,(upper,lower) in enumerate(zip(bounds,bounds[1:])):
        height=np.median(np.maximum(lower-upper,0));n=max(4,int(height/3.6))
        for j in range(n+1):
            t=(j+.2)/(n+1);line=upper*(1-t)+lower*t
            line+=np.sin(xs*31+j*.7)*.65*np.sin(t*np.pi)
            x=-rng.uniform(0,100)
            while x<w:
                length=rng.uniform(65,165) if band<3 else rng.uniform(28,85)
                idx=np.arange(max(0,int(x)),min(w,int(x+length)),3)
                valid=(lower[idx]-upper[idx]>0)&(line[idx]<h)&(line[idx]>0)
                idx=idx[valid];p=np.column_stack((idx,line[idx]))
                if len(p)>1:
                    col=sample(p)
                    col=col*.35+np.mean(col,axis=0)*.65
                    plates[1].path(p,2.8 if band<3 else 3.1,col,.17+band*.025+rng.uniform(0,.17),rng.uniform(.10,.16),1)
                x+=length+rng.uniform(1.5,4)
    # Fine strokes trace local tonal orientation. Long mountainside marks use
    # image structure; foreground strokes shorten naturally into rock facets.
    tone=gaussian_filter(lum,2.7)
    gx=sobel(tone,axis=1);gy=sobel(tone,axis=0)
    a=gaussian_filter(gx*gx,4);b=gaussian_filter(gx*gy,4);c=gaussian_filter(gy*gy,4)
    theta=.5*np.arctan2(2*b,a-c)+np.pi/2
    for yy in np.arange(h*.33,h,5.5):
        for xx in np.arange(0,w,7):
            x=xx+rng.uniform(-2,2);y=yy+rng.uniform(-2,2)
            if y<skyline[int(np.clip(x,0,w-1))]+2:continue
            ix=int(np.clip(x,0,w-1));iy=int(np.clip(y,0,h-1))
            angle=theta[iy,ix]
            length=rng.uniform(12,33) if y<h*.72 else rng.uniform(7,19)
            p=[]
            for t in np.linspace(-.5,.5,7):
                px=x+np.cos(angle)*length*t;py=y+np.sin(angle)*length*t
                if 0<=px<w and 0<=py<h and py>skyline[int(px)]+1:p.append((px,py))
            if len(p)<2:continue
            p=np.asarray(p);col=np.mean(sample(p),axis=0)
            plates[2].path(p,rng.uniform(1.25,2.3),col,rng.uniform(.45,.80),rng.uniform(.09,.16),.92)
    # Refined colored ridges add crisp geography after the broad color arrives.
    for i,spur in enumerate([g['skyline']]+g['spurs']):
        p=subdivide(points(spur),3);col=sample(p)*.86
        plates[2].path(p,1.1,col,.63+i*.014,.12,.88)
    # The climber is drawn in short colored cross hatching within the authored
    # silhouette so the human scale remains evident even in the small crop.
    person=Image.new('L',size);ImageDraw.Draw(person).polygon([tuple(x) for x in points(g['person'])],fill=255)
    mask=np.asarray(person)>0
    bx0,by0,bx1,by1=g['subject']
    for y in np.arange(by0*h,by1*h,2):
        xx=np.arange(bx0*w,bx1*w,1);yy=y+(xx-(bx0+bx1)*w/2)*.35
        valid=mask[np.clip(yy.astype(int),0,h-1),np.clip(xx.astype(int),0,w-1)]
        p=np.column_stack((xx[valid],yy[valid]))
        if len(p)>1:plates[2].path(p,1.7,sample(p)*.87,.65+rng.uniform(0,.12),.12,1)
    # Preserve lengthwise growth while moving color into the second half.
    for plate,old_start,old_end,new_start,new_end in [
        (plates[1],.12,.60,.46,.90),(plates[2],.45,.96,.70,.985)]:
        valid=plate.time<.99
        plate.time[valid]=new_start+np.clip((plate.time[valid]-old_start)/(old_end-old_start),0,1)*(new_end-new_start)
    dest=ROOT/'assets'/name
    for i,plate in enumerate(plates):plate.save(dest,i)
    def smoothstep(a,b,x):
        t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
    decoded=[]
    for i in range(3):
        rgba=np.asarray(Image.open(dest/f'layer{i}.webp').convert('RGBA'),dtype=float)
        time=np.asarray(Image.open(dest/f'time{i}.png'),dtype=float)/255*1.1-.1
        decoded.append((rgba[:,:,:3],rgba[:,:,3]/255,time))
    frames=[];metrics={}
    for value in [0,.15,.3,.45,.6,.75,.9,1]:
        frame=np.broadcast_to(PAPER,(h,w,3)).copy()
        opacity=[1-smoothstep(.72,1,value),smoothstep(.45,1,value),smoothstep(.68,1,value)]
        for i,(rgb,coverage,time) in enumerate(decoded):
            reveal=np.ones_like(time) if value==1 else smoothstep(time-.012,time+.012,value)
            alpha=coverage*reveal*opacity[i]
            sat=smoothstep(.62,1,value)
            gray=rgb@np.array([.2126,.7152,.0722])
            color=gray[:,:,None]*(1-sat)+rgb*sat
            frame=frame*(1-alpha[:,:,None])+color*alpha[:,:,None]
        frames.append(Image.fromarray(np.clip(frame,0,255).astype('uint8')))
        sketch=decoded[0][1]*smoothstep(decoded[0][2]-.012,decoded[0][2]+.012,value)
        metrics[str(value)]={'sketchPixels':int(np.sum(sketch>.12)),
                             'skyPixels':int(np.sum((sketch>.12)&(np.arange(h)[:,None]<skyline[None,:]-6))),
                             'foregroundPixels':int(np.sum((sketch>.12)&(np.arange(h)[:,None]>h*.74)))}
    # At 1 the sketch opacity is zero. The fallback composites only delivered
    # color plates, exactly matching the fully revealed shader endpoint.
    frames[-1].save(dest/'finished.webp',lossless=True,method=6)
    print(name,size,'growth',json.dumps(metrics),flush=True)
    return frames

def main():
    frames=[make(name) for name in ['desktop','mobile']]
    manifest_path=ROOT/'assets/manifest.json'
    manifest=json.loads(manifest_path.read_text())
    for name,images in zip(['desktop','mobile'],frames):
        manifest[name]['width'],manifest[name]['height']=images[-1].size
        manifest[name].pop('controlWidth',None)
        manifest[name].pop('controlHeight',None)
    manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
    sheet=Image.new('RGB',(3200,850),tuple(PAPER.astype(int)))
    draw=ImageDraw.Draw(sheet)
    for row,images in enumerate(frames):
        for i,im in enumerate(images):
            im.thumbnail((390,390),Image.Resampling.LANCZOS)
            sheet.paste(im,(i*400+(400-im.width)//2,row*425+25))
            draw.text((i*400+12,row*425+6),f'{["desktop","mobile"][row]} / {[0,.15,.3,.45,.6,.75,.9,1][i]}',fill=(57,69,71))
    sheet.save('/tmp/resolve-stages-preview.jpg',quality=94)

if __name__=='__main__':main()
