#!/usr/bin/env python3
"""Prepare the checked-in Resolve textures. Requires Pillow, NumPy, SciPy.

python scripts/prepare-assets.py --desktop SOURCE.png --mobile SOURCE.jpg
Optional --contact-sheet /tmp/resolve-assets.jpg produces an offline art review.
Input files are never changed. Coordinates below refer to upright source pixels,
normalized to [0,1]. They describe visible ridges, not measured topography.
"""
import argparse
import io
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageCms, ImageDraw, ImageOps
from scipy.ndimage import gaussian_filter, sobel, map_coordinates
from scipy.interpolate import PchipInterpolator

IVORY = np.array([243, 240, 231], dtype=float)
INK = np.array([53, 67, 72], dtype=float)
LANCZOS = getattr(Image, 'Resampling', Image).LANCZOS

# Skyline and successive visible mountain/foreground boundaries, authored on the
# approved photograph. Dense vertices preserve the left descending desktop ridge.
GEOMETRY = {
 'desktop': {
  'size': (1672, 941), 'focal': [.5,.64],
  'subject': [.455,.677,.537,.853], 'peak': [.472,.365],
  'skyline': [(0,.675),(.028,.655),(.057,.623),(.087,.59),(.111,.543),(.124,.505),(.139,.475),(.148,.482),(.153,.466),(.167,.479),(.18,.44),(.193,.426),(.203,.448),(.211,.415),(.22,.428),(.23,.402),(.24,.411),(.247,.391),(.258,.397),(.269,.414),(.28,.388),(.289,.383),(.301,.402),(.32,.413),(.335,.416),(.35,.426),(.369,.429),(.386,.424),(.405,.409),(.423,.398),(.439,.387),(.459,.38),(.472,.365),(.49,.383),(.515,.401),(.54,.421),(.565,.431),(.59,.451),(.63,.496),(.675,.546),(.72,.596),(.77,.637),(.82,.676),(1,.6)],
  'ridges': [
   [(0,.7),(.08,.659),(.145,.573),(.2,.511),(.237,.453),(.27,.502),(.31,.504),(.35,.53),(.39,.542),(.43,.544),(.48,.54),(.53,.553),(.575,.587),(.62,.622),(.68,.664),(.74,.686),(.82,.676),(1,.6)],
   [(0,.735),(.055,.726),(.12,.712),(.19,.693),(.24,.652),(.28,.654),(.32,.699),(.37,.695),(.41,.72),(.46,.703),(.5,.699),(.57,.686),(.63,.678),(.74,.675),(.85,.651),(1,.6)],
   [(0,.827),(.1,.804),(.2,.781),(.3,.766),(.4,.781),(.5,.766),(.6,.769),(.7,.733),(.8,.718),(.9,.688),(1,.67)],
   [(0,1.05),(.12,1.01),(.25,1.04),(.4,.98),(.5,1.03),(.65,.98),(.75,1.01),(.85,.97),(1,.94)]],
  'spurs': [
   [(.472,.365),(.477,.42),(.505,.484),(.54,.536),(.577,.568)],
   [(.472,.365),(.452,.414),(.465,.474),(.482,.533)],
   [(.472,.365),(.51,.431),(.552,.492),(.608,.547),(.678,.611)],
   [(.237,.453),(.249,.513),(.266,.559),(.277,.629),(.308,.679)],
   [(.237,.453),(.221,.514),(.226,.577),(.243,.627)],
   [(.289,.383),(.318,.449),(.36,.482),(.394,.537)],
   [(.48,.54),(.505,.588),(.549,.639),(.601,.685)],
   [(.39,.542),(.42,.594),(.459,.64),(.48,.69)]],
  'person': [(.49,.688),(.5,.687),(.507,.705),(.516,.713),(.53,.753),(.522,.761),(.507,.734),(.512,.77),(.509,.804),(.506,.839),(.498,.845),(.496,.806),(.491,.776),(.485,.74),(.464,.764),(.458,.756),(.476,.718),(.486,.706)]
 },
 'mobile': {
  'size': (1200,1600), 'focal': [.5,.58],
  'subject': [.402,.631,.578,.795], 'peak': [.439,.332],
  'skyline': [(0,.348),(.012,.342),(.022,.347),(.033,.345),(.057,.358),(.079,.367),(.092,.378),(.109,.367),(.124,.365),(.145,.373),(.168,.376),(.194,.385),(.22,.392),(.247,.388),(.273,.38),(.297,.374),(.32,.364),(.339,.36),(.358,.35),(.376,.347),(.395,.343),(.415,.339),(.439,.332),(.463,.341),(.491,.349),(.524,.364),(.565,.373),(.606,.386),(.646,.405),(.687,.425),(.734,.447),(.781,.466),(.825,.474),(.871,.495),(.922,.511),(1,.535)],
  'ridges': [
   [(0,.394),(.075,.416),(.151,.43),(.224,.434),(.282,.443),(.345,.452),(.405,.455),(.477,.473),(.53,.482),(.586,.491),(.651,.493),(.706,.498),(.759,.526),(.815,.553),(.868,.581),(.931,.608),(1,.624)],
   [(0,.462),(.053,.473),(.092,.505),(.146,.528),(.188,.523),(.233,.546),(.285,.537),(.341,.527),(.4,.542),(.465,.555),(.514,.572),(.589,.601),(.675,.627),(.74,.642),(.85,.635),(1,.629)],
   [(0,.646),(.074,.637),(.14,.657),(.23,.654),(.32,.661),(.414,.665),(.5,.661),(.61,.648),(.73,.642),(.86,.636),(1,.629)],
   [(0,.789),(.15,.76),(.27,.749),(.4,.766),(.55,.751),(.7,.721),(.84,.717),(1,.7)],
   [(0,1.05),(.16,1.02),(.3,1.05),(.48,.98),(.62,1.02),(.76,.98),(.9,1.04),(1,1.01)]],
  'spurs': [
   [(.439,.332),(.437,.365),(.479,.421),(.522,.46),(.583,.484)],
   [(.439,.332),(.4,.368),(.427,.427),(.459,.467)],
   [(.439,.332),(.516,.401),(.597,.457),(.696,.493)],
   [(.439,.332),(.549,.388),(.68,.451),(.819,.51)],
   [(.051,.472),(.073,.526),(.104,.573),(.13,.615)],
   [(.341,.527),(.385,.567),(.451,.607),(.503,.65)],
   [(.477,.473),(.526,.515),(.585,.561),(.68,.611)],
   [(.151,.43),(.173,.476),(.22,.515)]],
  'person': [(.481,.637),(.5,.637),(.508,.653),(.529,.668),(.565,.691),(.567,.711),(.552,.706),(.519,.684),(.526,.719),(.52,.747),(.509,.778),(.5,.787),(.489,.776),(.489,.748),(.481,.723),(.469,.69),(.423,.708),(.412,.7),(.437,.672),(.468,.659)]
 }
}


def normalize(path, limit):
    with Image.open(path) as source:
        oriented = ImageOps.exif_transpose(source)
        icc = source.info.get('icc_profile')
        if icc:
            oriented = ImageCms.profileToProfile(
                oriented, ImageCms.ImageCmsProfile(io.BytesIO(icc)),
                ImageCms.createProfile('sRGB'), outputMode='RGB')
        else:
            oriented = oriented.convert('RGB')
        oriented.thumbnail(limit, LANCZOS)
        # New pixels carry no EXIF, GPS, ICC, or source metadata.
        return Image.fromarray(np.array(oriented), 'RGB')


def curve(points, xs):
    points = np.asarray(points)
    return PchipInterpolator(points[:,0], points[:,1])(xs)


def make_assets(photo, spec):
    w,h = photo.size
    rgb = np.asarray(photo, dtype=float) / 255
    luminance = rgb @ np.array([.2126,.7152,.0722])
    tone = gaussian_filter(luminance, 5)
    broad = gaussian_filter(luminance, 18)
    xs = np.linspace(0,1,w)
    skyline = curve(spec['skyline'],xs)
    ys = np.arange(h)[:,None]/h
    terrain = np.clip((ys-skyline[None,:])*h/2+.5,0,1)
    # Beyond the primary ridge, distant land still receives delayed shading.
    horizon = .403 if w>h else .355
    terrain = np.maximum(terrain, np.clip((ys-horizon)*h/4,0,1)*.36)
    person_image = Image.new('L',(w,h))
    ImageDraw.Draw(person_image).polygon([(x*w,y*h) for x,y in spec['person']],fill=255)
    person = gaussian_filter(np.asarray(person_image,dtype=float)/255, max(w,h)*.009)
    person = np.clip(person*1.4,0,1)
    # A supersampled monochrome plate keeps thin ink antialiased on WebGL1.
    plate = Image.new('L',(2*w,2*h))
    draw = ImageDraw.Draw(plate)
    def stroke(points, strength=125, width=.65):
        draw.line([(round(x*w*2),round(y*h*2)) for x,y in points],
                  fill=int(strength),width=max(1,round(width*2)),joint='curve')
    boundaries = [skyline]+[curve(r,xs) for r in spec['ridges']]
    rng=np.random.default_rng(8746)
    # Intervening strokes follow the actual neighboring ridges. Their slight
    # offsets derive only from smoothed image tone, with zero boundary offset.
    for band,(upper,lower) in enumerate(zip(boundaries,boundaries[1:])):
        spacing = 15 if band<2 else 28
        n=max(3,int(np.median(np.maximum(0,lower-upper))*h/spacing))
        for line in range(1,n+1):
            t=line/(n+1)
            y=upper*(1-t)+lower*t
            iy=np.clip((y*h).astype(int),0,h-1)
            local=tone[iy,np.arange(w)]
            y += (local-broad[iy,np.arange(w)])*.016*np.sin(np.pi*t)
            valid=(lower-upper>8/h)&(y>skyline+.002)
            # Broken, irregular-length engraving marks avoid a mechanical mesh.
            position=0
            while position<w:
                length=int(rng.uniform(.035,.12)*w)
                end=min(w,position+length)
                idx=np.arange(position,end,2)
                idx=idx[valid[idx]]
                if len(idx)>3:
                    shade=1-float(np.mean(local[idx]))
                    alpha=(120+shade*115)*(1-.2*band/len(boundaries))
                    stroke(zip(xs[idx],y[idx]),alpha,.55)
                position=end+int(rng.uniform(.005,.019)*w)
    # Major skyline has more weight; interior boundaries are quiet and broken
    # by source-aligned texture rather than a repeated waveform.
    for i,boundary in enumerate(boundaries[:-1]):
        stroke(zip(xs[::2],boundary[::2]),200 if i==0 else 140,1.0 if i==0 else .8)
    for points in spec['spurs']:
        points=np.asarray(points)
        # Parametric interpolation handles spurs that double back horizontally.
        u=np.r_[0,np.cumsum(np.linalg.norm(np.diff(points,axis=0),axis=1))]
        q=np.linspace(0,u[-1],150)
        stroke(zip(PchipInterpolator(u,points[:,0])(q),PchipInterpolator(u,points[:,1])(q)),155,.8)
    ink=np.asarray(plate.resize((w,h),LANCZOS),dtype=float)/255
    ink*=1-.35*person
    # Sparse photographic edge etching carries rock facets and a subtle human
    # outline; it never fills sky or replaces the authored mountain structure.
    smooth=gaussian_filter(luminance,1.1)
    gx,gy=sobel(smooth,axis=1)/8,sobel(smooth,axis=0)/8
    magnitude=np.hypot(gx,gy)
    yy,xx=np.mgrid[:h,:w]
    dx,dy=gx/(magnitude+1e-8),gy/(magnitude+1e-8)
    before=map_coordinates(magnitude,[yy-dy,xx-dx],order=1,mode='nearest')
    after=map_coordinates(magnitude,[yy+dy,xx+dx],order=1,mode='nearest')
    ridge=(magnitude>=before)&(magnitude>=after)
    edge=np.clip((magnitude-.014)*7,0,.27)*ridge
    edge=gaussian_filter(edge,.32)*np.clip((ys-skyline)*h/5,0,1)
    edge*=.9+.1*person
    ink=np.maximum(ink,edge)
    # Quiet diagonal jacket/leg hatching keeps the dark-clothed climber from
    # becoming a blank cutout amid the rock facets. Feathering is shared with
    # the control region; existing photographic edges preserve the silhouette.
    hatch_plate=Image.new('L',(2*w,2*h))
    hatch_draw=ImageDraw.Draw(hatch_plate)
    x0,y0,x1,y1=spec['subject']
    for offset in range(int((y0-x1)*2*h),int((y1-x0)*2*h)+20,12):
        hatch_draw.line([(x0*2*w,offset+x0*2*h),(x1*2*w,offset+x1*2*h)],fill=255,width=1)
    hatch=np.asarray(hatch_plate.resize((w,h),LANCZOS),dtype=float)/255
    ink=np.maximum(ink,hatch*person*.38)
    # Slight tooth in dark rock facets, with an opaque, absolutely clean sky.
    drawing=np.clip(IVORY[None,None,:]-(IVORY-INK)[None,None,:]*ink[:,:,None],0,255).astype('uint8')
    control=np.dstack((terrain,person,tone))
    control=Image.fromarray((np.clip(control,0,1)*255).astype('uint8')).resize((w//2,h//2),LANCZOS)
    return Image.fromarray(drawing),control


def smoothstep(a,b,x):
    t=np.clip((x-a)/(b-a),0,1)
    return t*t*(3-2*t)


def contact_sheet(sets, destination):
    # Offline approximation only: live shader is verified separately in browser.
    tiles=[]
    for name,photo,drawing,control in sets:
        size=(440,248) if name=='desktop' else (264,352)
        p=np.asarray(photo.resize(size,LANCZOS),dtype=float)/255
        d=np.asarray(drawing.resize(size,LANCZOS),dtype=float)/255
        c=np.asarray(control.resize(size,LANCZOS),dtype=float)/255
        lum=(p@np.array([.2126,.7152,.0722]))[:,:,None]
        for value in [0,.25,.5,.75,1]:
            color=smoothstep(.48,.95,value)
            toned=lum*(1-color)+p*color
            blend=smoothstep(.32,.94,value)*(1-.16*c[:,:,1,None]*(1-smoothstep(.6,.87,value)))
            frame=d*(1-blend)+toned*blend
            if value==1:frame=p
            tile=Image.new('RGB',(440,384),'#f3f0e7')
            tile.paste(Image.fromarray(np.clip(frame*255,0,255).astype('uint8')),((440-size[0])//2,24))
            ImageDraw.Draw(tile).text((12,5),f'{name} / {value:.2f}',fill='#354348')
            tiles.append(tile)
    sheet=Image.new('RGB',(2200,768),'#f3f0e7')
    for i,tile in enumerate(tiles):sheet.paste(tile,((i%5)*440,(i//5)*384))
    sheet.save(destination,quality=92)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--desktop',required=True,type=Path)
    parser.add_argument('--mobile',required=True,type=Path)
    parser.add_argument('--output',type=Path,default=Path(__file__).resolve().parent.parent/'assets')
    parser.add_argument('--contact-sheet',type=Path)
    args=parser.parse_args()
    manifest={};sets=[]
    for name in ['desktop','mobile']:
        spec=GEOMETRY[name]
        photo=normalize(getattr(args,name),spec['size'])
        drawing,control=make_assets(photo,spec)
        dest=args.output/name;dest.mkdir(parents=True,exist_ok=True)
        photo.save(dest/'photo.webp',quality=88,method=6)
        drawing.save(dest/'drawing.webp',lossless=True,method=6)
        control.save(dest/'control.png',optimize=True)
        manifest[name]={'width':photo.width,'height':photo.height,
          'focal':spec['focal'],'subject':spec['subject'],'peak':spec['peak'],
          'peakBounds': [spec['peak'][0]-.055,spec['peak'][1]-.015,spec['peak'][0]+.11,spec['peak'][1]+.17],
          'controlWidth':control.width,'controlHeight':control.height,
          'skyline':spec['skyline'],'ridges':spec['ridges']}
        sets.append((name,photo,drawing,control))
        print(name,photo.size,[(p.name,p.stat().st_size) for p in sorted(dest.iterdir())])
    (args.output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    if args.contact_sheet:contact_sheet(sets,args.contact_sheet)

if __name__=='__main__':main()
