#!/usr/bin/env python3
"""Author deterministic colored engraving atlases and lengthwise reveal maps.

Every visible pixel is coverage from a drawn path, never a photograph overlay.
The photographs only supply a palette sampled by the brush. timeN.png is an
8-bit threshold: reveal = channel / 255 * 1.1 - .1. All assets share normalized
coordinates with the approved source. Requires Pillow, NumPy, SciPy.
"""
from pathlib import Path
import importlib.util
import json
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter, sobel, distance_transform_edt
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
    # The initial sketch: skyline, figure and long geographic contours.
    for i,line in enumerate(bounds[:-1]):
        p=np.column_stack((np.arange(0,w,3),line[::3]))
        plates[0].path(p,1.05 if i==0 else .7,INK,-.095 if i<2 else -.04,.035 if i<2 else .19,.73 if i==0 else .48)
    for i,spur in enumerate(g['spurs']):
        p=subdivide(points(spur));plates[0].path(p,.8,INK,-.08 if i<3 else .03,.08,.56)
    p=subdivide(points(g['person']+[g['person'][0]]));plates[0].path(p,.9,INK,-.07,.06,.8)
    for band,(upper,lower) in enumerate(zip(bounds,bounds[1:])):
        n=max(3,int(np.median(np.maximum(lower-upper,0))/13))
        for j in range(1,n):
            t=j/n;line=upper*(1-t)+lower*t
            for x in range(int(rng.integers(0,20)),w,150):
                end=min(w,x+int(rng.uniform(65,130))); idx=np.arange(x,end,4)
                p=np.column_stack((idx,line[idx]));plates[0].path(p,.62,INK,float(rng.uniform(-.06,.12)),.1,.38)
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
    dest=ROOT/'assets'/name
    for i,plate in enumerate(plates):plate.save(dest,i)
    frames=[]
    for value in [0,.25,.5,.75,1]:
        frame=np.broadcast_to(PAPER,(h,w,3)).copy()
        for plate in plates:
            reveal=np.clip((value-plate.time+.006)/.012,0,1);reveal=reveal*reveal*(3-2*reveal)
            alpha=plate.alpha*reveal
            # Saturation grows separately from stroke coverage, as in the UI.
            sat_t=np.clip((value-.05)/.87,0,1)
            sat=.3+.7*sat_t*sat_t*(3-2*sat_t)
            gray=plate.rgb@np.array([.2126,.7152,.0722])
            rgb=gray[:,:,None]*(1-sat)+plate.rgb*sat
            frame=frame*(1-alpha[:,:,None])+rgb*alpha[:,:,None]
        frames.append(Image.fromarray(np.clip(frame,0,255).astype('uint8')))
    # Composite the decoded delivery atlases so fallback matches their colors.
    final=np.broadcast_to(PAPER,(h,w,3)).copy()
    for i in range(3):
        rgba=np.asarray(Image.open(dest/f'layer{i}.webp').convert('RGBA'),dtype=float)
        a=rgba[:,:,3:]/255
        final=final*(1-a)+rgba[:,:,:3]*a
    frames[-1]=Image.fromarray(np.clip(final,0,255).astype('uint8'))
    frames[-1].save(dest/'finished.webp',lossless=True,method=6)
    print(name,size,flush=True)
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
    sheet=Image.new('RGB',(2000,850),tuple(PAPER.astype(int)))
    draw=ImageDraw.Draw(sheet)
    for row,images in enumerate(frames):
        for i,im in enumerate(images):
            im.thumbnail((390,390),Image.Resampling.LANCZOS)
            sheet.paste(im,(i*400+(400-im.width)//2,row*425+25))
            draw.text((i*400+12,row*425+6),f'{["desktop","mobile"][row]} / {[0,.25,.5,.75,1][i]}',fill=(57,69,71))
    sheet.save('/tmp/resolve-strokes-preview.jpg',quality=94)

if __name__=='__main__':main()
