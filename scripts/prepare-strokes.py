#!/usr/bin/env python3
"""Author deterministic colored brushstroke atlases and lengthwise reveal maps.

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
        self.schedule=None
        self.preserve_earliest=False
    def path(self,points,width,color,start,span,opacity=1,taper=False):
        p=np.asarray(points,dtype=float)
        if len(p)<2:return
        d=np.linalg.norm(np.diff(p,axis=0),axis=1);cum=np.r_[0,np.cumsum(d)]
        if cum[-1]<.01:return
        if self.schedule is not None:start,span=self.schedule(p,width)
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
            progress=np.clip((cum[i]+t*length)/cum[-1],0,1) if taper else 0
            radius=r*(.18+.82*np.sin(np.pi*progress)**.45) if taper else r
            cov=np.clip(radius+.6-dist,0,1)*opacity
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
            time[take]=np.minimum(time[take],threshold[take]) if self.preserve_earliest else threshold[take]
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
    w,h=size
    photo=Image.open(ROOT/f'assets/{name}/photo.webp').convert('RGB').resize(size,Image.Resampling.LANCZOS)
    source=np.asarray(photo,dtype=float)
    source=gaussian_filter(source,(2.2,2.2,0))
    lum=source@np.array([.2126,.7152,.0722])
    # A slightly richer limited-value brush palette makes light and shade read
    # as colored marks while avoiding the dense black of an unmodified photo.
    source=np.clip(lum[:,:,None]+(source-lum[:,:,None])*1.2,0,255)
    source=np.clip(source*.96+PAPER*.04,0,255)
    plates=[Plate(w,h) for _ in range(3)]
    plates[0].preserve_earliest=True
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
                  [(.472,.365),(.50,.47),(.57,.56)]],
      'mobile': [[(.19,.39),(.439,.332),(.67,.42)],[(.439,.332),(.46,.42),(.58,.48)]]
    }
    for line in rough[name]:
        plates[0].path(subdivide(points(line)),.83,INK,-.09,.045,.40)
    # First establish only the skyline and principal mountain ridge. The
    # nearer slope/foreground boundaries join the human in the second phase.
    for i,line in enumerate(bounds[:-1]):
        sections=5 if i==0 else 4
        for section,idx in enumerate(np.array_split(np.arange(0,w,3),sections)):
            p=np.column_stack((idx,line[idx]))
            start=(.035+section*.021) if i==0 else (.08+section*.021 if i==1 else .25+(i-2)*.025+section*.013)
            plates[0].path(p,1.05 if i==0 else .72,INK,start,.055,.76 if i==0 else .48)
    for i,spur in enumerate(g['spurs']):
        p=subdivide(points(spur))
        major=[0,2,3]
        start=.075+major.index(i)*.023 if i in major else .435+i*.014
        plates[0].path(p,.85,INK,start,.075,.58)
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
        plates[0].path(subdivide(points(line)),.68,INK,.625+i*.028,.07,.38)
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
        # Fine contours follow the complete mountain/human/foreground skeleton.
        # Background sketching waits until the later distant-land/cloud work.
        if region=='cloud':start=.68+rank*.10;span=.055;opacity=.38
        elif region=='mountain':start=.435+rank*.18;span=.055;opacity=.50
        else:start=.445+rank*.23;span=.055;opacity=.54
        # Reduce pixel-scale stair stepping without erasing a rock's corners.
        p=gaussian_filter(p,(.65,0))[::2]
        plates[0].path(p,.72 if region=='cloud' else .82,INK,start,span,opacity)
    # A few long source rock edges define foreground scale during phase two;
    # leave the dense small-rock contour map for the detail phase above.
    foreground_edges=[]
    for lo,hi in [(0,.28),(.28,.53),(.53,.78),(.78,1.01)]:
        candidates=[entry for entry in paths if entry[1]=='rock'
                    and lo<=entry[2][:,0].mean()/w<hi
                    and entry[2][:,1].mean()/h>.84]
        if not candidates:continue
        _,_,p,_=max(candidates,key=lambda entry:entry[0])
        ids=np.linspace(0,len(p)-1,min(12,len(p))).astype(int)
        foreground_edges.append(p[ids])
    for i,p in enumerate(foreground_edges):
        plates[0].path(subdivide(p),.95,INK,.265+i*.02,.065,.62)
    # Phase two establishes the rough full human silhouette and both poles;
    # facial, clothing and inner-leg detail waits for the detail phase.
    p=subdivide(points(g['person']+[g['person'][0]]))
    plates[0].path(p,1.05,INK,.235,.095,.78)
    person_details={
      'desktop': [[(.49,.705),(.5,.705),(.503,.715),(.493,.722),(.49,.705)],
                   [(.485,.718),(.499,.726),(.509,.724)],[(.49,.737),(.505,.741),(.508,.767),(.494,.771)],
                   [(.499,.774),(.501,.806),(.498,.836)],[(.459,.765),(.466,.845)],[(.527,.76),(.527,.852)]],
      'mobile': [[(.479,.649),(.498,.649),(.502,.66),(.488,.671),(.479,.649)],
                  [(.47,.671),(.49,.688),(.516,.679)],[(.479,.692),(.514,.697),(.516,.719),(.485,.72)],
                  [(.5,.723),(.505,.75),(.499,.777)],[(.415,.705),(.438,.794)],[(.563,.707),(.56,.787)]]
    }
    for i,line in enumerate(person_details[name]):
        start=.27+(i-4)*.025 if i>=4 else .435+i*.018
        plates[0].path(subdivide(points(line)),.8,INK,start,.065 if i>=4 else .05,.66)
    print(name,'structural paths',counts,flush=True)
    # Keep the approved distant-land orientation field independent of the
    # closer, finer photo structure used for the new terrain brushes.
    tone=gaussian_filter(lum,2.7)
    gx=sobel(tone,axis=1);gy=sobel(tone,axis=0)
    a=gaussian_filter(gx*gx,4);b=gaussian_filter(gx*gy,4);c=gaussian_filter(gy*gy,4)
    theta=.5*np.arctan2(2*b,a-c)+np.pi/2
    # The source, rather than interpolated authored ridges, determines every
    # colored landform. Preserve small crags, snow edges and the human figure.
    terrain_source=gaussian_filter(np.asarray(photo,dtype=float),(.65,.65,0))
    terrain_lum=terrain_source@np.array([.2126,.7152,.0722])
    terrain_source=np.clip(terrain_lum[:,:,None]+(terrain_source-terrain_lum[:,:,None])*1.2,0,255)
    terrain_source=np.clip(terrain_source*.96+PAPER*.04,0,255)
    land_tone=gaussian_filter(terrain_lum,1.05)
    tx=sobel(land_tone,axis=1)/8;ty=sobel(land_tone,axis=0)/8
    ta=gaussian_filter(tx*tx,1.8);tb=gaussian_filter(tx*ty,1.8);tc=gaussian_filter(ty*ty,1.8)
    land_theta=.5*np.arctan2(2*tb,ta-tc)+np.pi/2
    directions=np.dstack((np.cos(land_theta),np.sin(land_theta)))
    land_rng=np.random.default_rng(32691)
    def terrain_sample(p):
        q=np.asarray(p);ix=np.clip(q[:,0].astype(int),0,w-1);iy=np.clip(q[:,1].astype(int),0,h-1)
        return terrain_source[iy,ix]
    def land_path(x,y,length):
        ix=int(x);iy=int(y);origin=terrain_source[iy,ix]
        # Integrate in both directions, choosing the same sign of the tensor
        # tangent at every step. Curvature follows the actual fissure/facet.
        branches=[];step=.9 if np.hypot(tx[iy,ix],ty[iy,ix])>8 else 2.1
        for sign in [-1,1]:
            p=np.array([x,y]);direction=directions[iy,ix]*sign;branch=[]
            for _ in range(max(2,int(length/2/step))):
                px=int(p[0]);py=int(p[1]);candidate=directions[py,px].copy()
                if candidate@direction<0:candidate=-candidate
                if candidate@direction<.72:break
                direction=direction*.35+candidate*.65;direction/=np.linalg.norm(direction)
                q=p+direction*step;qx=int(q[0]);qy=int(q[1])
                if qx<0 or qx>=w or qy<0 or qy>=h or qy<skyline[qx]-1:break
                # Stop before crossing a snow, cliff, silhouette or light/shade
                # boundary, even when the local orientation remains similar.
                color=terrain_source[qy,qx]
                if np.linalg.norm(color-origin)>30 or np.linalg.norm(color-terrain_source[py,px])>18:break
                branch.append(q.copy());p=q
            branches.append(branch)
        result=branches[0][::-1]+[np.array([x,y])]+branches[1]
        if len(result)<2:
            # A tiny tapered dab preserves source color where a sharp facial,
            # snow or cliff edge cannot support a longer curved gesture.
            delta=directions[iy,ix]*.65
            return np.array([[x,y]-delta,[x,y]+delta])
        return np.asarray(result)
    # Color follows the same construction hierarchy as pencil. Distances are
    # measured to narrow line masks, never filled subject/terrain regions.
    # This schedules existing painted gestures without changing their pixels.
    def line_distance(lines):
        mask=Image.new('L',size);draw=ImageDraw.Draw(mask)
        for line in lines:draw.line([tuple(q) for q in line],fill=255,width=1)
        return distance_transform_edt(np.asarray(mask)==0)
    ridge_lines=[points(g['skyline']),points(g['ridges'][0])]
    ridge_lines.extend(points(g['spurs'][i]) for i in [0,2,3])
    ridge_distance=line_distance(ridge_lines)
    figure_lines=[points(g['person']+[g['person'][0]])]
    figure_lines.extend(points(line) for line in person_details[name][-2:])
    figure_distance=line_distance(figure_lines)
    figure_interior_mask=Image.new('L',size)
    ImageDraw.Draw(figure_interior_mask).polygon([tuple(q) for q in points(g['person'])],fill=255)
    figure_interior=np.asarray(figure_interior_mask)>0
    foreground_lines=[np.column_stack((np.arange(w)[::3],line[::3])) for line in bounds[2:-1]]
    foreground_distance=line_distance(foreground_lines+foreground_edges)
    def stroke_jitter(p):
        x,y=np.mean(p,axis=0)
        return (np.sin(x*12.9898+y*78.233)*43758.5453)%1
    def terrain_schedule(p,width,detail=False,fill=False):
        x,y=np.mean(p,axis=0)/[w,h]
        ix=np.clip(p[:,0].astype(int),0,w-1);iy=np.clip(p[:,1].astype(int),0,h-1)
        # Include the brush radius and almost the entire path: a wide body
        # merely touching a contour must not expose the adjacent surface early.
        def near(distance,band):
            return np.percentile(distance[iy,ix],90)+width*.5<=band
        jitter=stroke_jitter(p)
        length=np.linalg.norm(np.diff(p,axis=0),axis=1).sum()
        span=np.clip(length/(w*.9),.014,.028)
        follow=(.004 if detail else 0)+(.008 if fill else 0)
        # Terrain boundaries pass behind the person. They must not reveal a
        # horizontal strip through an otherwise unpainted human interior.
        crosses_figure=np.any(figure_interior[iy,ix]&(figure_distance[iy,ix]>4))
        if not crosses_figure and near(ridge_distance,7):
            onset=.470+.055*x+(jitter-.5)*.012+follow
        elif not crosses_figure and near(figure_distance,4):
            onset=.570+.040*np.clip((y-by0)/(by1-by0),0,1)+(jitter-.5)*.010+follow
        elif not crosses_figure and near(foreground_distance,5):
            onset=.575+.045*x+(jitter-.5)*.012+follow
        else:
            # Only after both outline passes do the mountain, human and rock
            # surfaces accumulate body strokes, then detail and compact fill.
            rank=np.clip(.45*x+.55*(y-.35)/.65,0,1)
            onset=.675+.075*rank+(jitter-.5)*.045
            onset+=(.018 if detail else 0)+(.025 if fill else 0)
            onset=max(.675,onset)
        return np.clip(onset,.468,.810),span
    plates[1].schedule=lambda p,width:terrain_schedule(p,width)
    plates[2].schedule=lambda p,width:terrain_schedule(p,width,True)
    # Overlapping body strokes share the tapered sky brush language. Seed
    # positions are staggered and jittered, so no rows or crosshatch survive.
    for pass_index in range(2):
        spacing=2.7
        for row,y0 in enumerate(np.arange(np.min(skyline)-2,h+3,spacing)):
            for x0 in np.arange(-3+(row%2)*spacing*.5,w+3,spacing):
                x=x0+land_rng.uniform(-spacing*.45,spacing*.45)
                y=y0+land_rng.uniform(-spacing*.45,spacing*.45)
                ix=int(x);iy=int(y)
                if ix<0 or ix>=w or iy<0 or iy>=h or y<skyline[ix]-1:continue
                foreground=y>h*(.72 if name=='desktop' else .66)
                figure=(bx0*w<x<bx1*w and by0*h<y<by1*h and terrain_lum[iy,ix]<70)
                target_spacing=(4 if foreground else 6.2) if pass_index else (2.7 if foreground else 6.7)
                if land_rng.random()>(spacing/target_spacing)**2:continue
                if figure:
                    length=land_rng.uniform(8,18);width=land_rng.uniform(3,4.5)
                elif foreground:
                    length=land_rng.uniform(9,24);width=land_rng.uniform(3.8,6.5)
                else:
                    length=land_rng.uniform(19,49);width=land_rng.uniform(4.5,7.5)
                if pass_index:
                    length*=.65;width*=.48
                # A strong gradient is transverse to these contour-following
                # paths. Narrow the body there to protect snow and silhouettes.
                strength=np.hypot(tx[iy,ix],ty[iy,ix])
                width*=np.clip(7/(strength+1),.48,1)
                p=land_path(x,y,length)
                if len(p)<2:continue
                col=terrain_sample(p);col=col*.60+col.mean(axis=0)*.40
                col=np.clip(col+land_rng.uniform(-5,5),0,255)
                start=land_rng.uniform(.19,.38) if pass_index==0 else land_rng.uniform(.45,.80)
                span=land_rng.uniform(.10,.16)
                plates[pass_index+1].path(p,width,col,start,span,.98,taper=True)
    plates[1].schedule=lambda p,width:terrain_schedule(p,width,fill=True)
    # Compact body gestures close excessive gaps where strong local contrasts
    # shorten the paths, without filling them with a smooth photographic layer.
    for y0 in np.arange(np.min(skyline),h,2.8):
        for x0 in np.arange(0,w,2.8):
            x=x0+land_rng.uniform(-1,1);y=y0+land_rng.uniform(-1,1)
            ix=int(x);iy=int(y)
            if ix<0 or ix>=w or iy<0 or iy>=h or y<skyline[ix]-1:continue
            if plates[1].alpha[iy,ix]>.40 or land_rng.random()>.82:continue
            p=land_path(x,y,land_rng.uniform(5,10))
            if len(p)<2:continue
            col=terrain_sample(p)
            width=land_rng.uniform(2.6,4.2)*np.clip(9/(np.hypot(tx[iy,ix],ty[iy,ix])+1),.65,1)
            plates[1].path(p,width,col,
                           land_rng.uniform(.21,.39),.12,.98,taper=True)
    # Source-derived edge gestures recover the lit sawtooth wall, cliff teeth,
    # snow margins and figure silhouette. No synthetic colored ridge outline.
    for _,region,p,_ in sorted(paths,key=lambda q:-q[0]):
        if region=='cloud':continue
        p=p[::2]
        if len(p)<3:continue
        for start in range(0,len(p)-2,15):
            stroke=p[start:start+17]
            col=terrain_sample(stroke)
            plates[2].path(stroke,land_rng.uniform(1.2,2.2),col,
                           land_rng.uniform(.57,.79),.12,.91,taper=True)
    # Preserve the approved background brush family in its own random stream.
    background=[Plate(w,h),Plate(w,h)]
    brush_rng=np.random.default_rng(19042)
    far_horizon={
        'desktop': [(0,.472),(.22,.438),(.47,.401),(.60,.391),(.72,.400),(.86,.398),(1,.395)],
        'mobile': [(0,.395),(.44,.355),(.60,.355),(.78,.360),(1,.361)]
    }
    horizon=geo.curve(far_horizon[name],xs)*h
    def background_region(x,y):
        ix=int(np.clip(x,0,w-1));iy=int(np.clip(y,0,h-1))
        if y>=skyline[ix]-2:return None
        if y>horizon[ix]:return 'distant'
        color=source[iy,ix]
        return 'cloud' if color[2]-color[0]<55 and lum[iy,ix]>140 else 'sky'
    def background_schedule(p,width,detail=False):
        x,y=np.mean(p,axis=0);region=background_region(x,y)
        jitter=stroke_jitter(p)
        if region=='distant':
            # The distant range grows outwards from behind the principal peak.
            rank=np.clip(abs(x/w-.53)*1.4+(y/h-.39)*1.4,0,1)
            onset=.70+.105*rank
        elif region=='cloud':
            rank=np.clip((x/w-.45)*1.25+( .35-y/h)*.7,0,1)
            onset=.735+.095*rank
        else:
            # Blue sky starts along the horizon and works upward, with an
            # irregular diagonal sweep instead of a uniform full-sky fade.
            rank=.75*(1-np.clip(y/(h*.38),0,1))+.25*x/w
            onset=.85+.10*rank
        onset+=(.017 if detail else 0)+(jitter-.5)*.008
        length=np.linalg.norm(np.diff(p,axis=0),axis=1).sum()
        span=np.clip(length/(w*3),.012,.022)
        return min(onset,.950),min(span,.968-min(onset,.950))
    background[0].schedule=lambda p,width:background_schedule(p,width)
    background[1].schedule=lambda p,width:background_schedule(p,width,True)
    # Staggered, jittered brush starts avoid ruled rows. The long axis curves
    # independently for each gesture and tapers at both ends, leaving paper
    # between marks rather than adding photographic grain to a solid fill.
    for pass_index,spacing in enumerate([3.9,4.5]):
        for y0 in np.arange(-8,np.max(skyline)+8,spacing):
            x=-brush_rng.uniform(0,80)
            while x<w+25:
                y=y0+brush_rng.uniform(-spacing*.65,spacing*.65)
                region=background_region(x,y)
                distant=region=='distant'
                if pass_index==0:
                    length=brush_rng.uniform(24,65) if distant else brush_rng.uniform(48,125)
                    width=brush_rng.uniform(8,11) if distant else brush_rng.uniform(7,10)
                else:
                    length=brush_rng.uniform(14,38) if distant else brush_rng.uniform(20,57)
                    width=brush_rng.uniform(1.8,3.2) if distant else brush_rng.uniform(2,3.5)
                if region is not None:
                    ix=int(np.clip(x,0,w-1));iy=int(np.clip(y,0,h-1))
                    if distant:
                        # Local ridge/valley direction gives distant land its
                        # own short facets, distinct from the open sky sweeps.
                        angle=theta[iy,ix]
                        angle=((angle+np.pi/2)%np.pi-np.pi/2)*.48
                    else:
                        angle=-.06+brush_rng.uniform(-.10,.10)
                    bend=brush_rng.uniform(-3.2,3.2) if distant else brush_rng.uniform(-4.5,4.5)
                    u=np.linspace(0,1,max(5,int(length/5)))
                    p=np.column_stack((x+np.cos(angle)*length*u,
                                       y+np.sin(angle)*length*u+bend*np.sin(np.pi*u)))
                    # Restrict the whole mark to one family of forms; no brush
                    # can carry blue sky through a cloud or into a distant ridge.
                    keep=np.array([background_region(px,py)==region for px,py in p])
                    for ids in np.split(np.arange(len(p)),np.flatnonzero(np.diff(keep))+1):
                        if len(ids)<2 or not keep[ids[0]]:continue
                        stroke=p[ids];col=sample(stroke)
                        col=col*.22+np.mean(col,axis=0)*.78
                        variation=brush_rng.uniform(-4,4) if region=='sky' else brush_rng.uniform(-7,7)
                        col=np.clip(col+variation,0,255)
                        start=(.14+max(y,0)/h*.20+brush_rng.uniform(0,.13)) if pass_index==0 else brush_rng.uniform(.45,.80)
                        span=brush_rng.uniform(.10,.17) if pass_index==0 else brush_rng.uniform(.09,.16)
                        background[pass_index].path(stroke,width,col,start,span,.98,taper=True)
                x+=length*brush_rng.uniform(.80,1.07)+brush_rng.uniform(2,8)
    # The two colored plates share one boundary and the same tapered brush
    # family, while retaining the three-plate/six-sampler runtime layout.
    background_mask=np.arange(h)[:,None]<skyline[None,:]-3
    for plate,replacement in zip(plates[1:],background):
        plate.rgb[background_mask]=replacement.rgb[background_mask]
        plate.alpha[background_mask]=replacement.alpha[background_mask]
        plate.time[background_mask]=replacement.time[background_mask]
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
        opacity=[1-smoothstep(.965,1,value),1,1]
        for i,(rgb,coverage,time) in enumerate(decoded):
            feather=.012 if i==0 else .003
            reveal=np.ones_like(time) if value==1 else smoothstep(time-feather,time+feather,value)
            age=value-time
            maturity=1 if i==0 or value==1 else .55+.45*smoothstep(-.006,.018,age)
            alpha=coverage*reveal*opacity[i]*maturity
            sat=0 if i==0 else (1 if value==1 else smoothstep(-.006,.026,age))
            gray=rgb@np.array([.2126,.7152,.0722])
            color=gray[:,:,None]*(1-np.asarray(sat)[...,None])+rgb*np.asarray(sat)[...,None]
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
