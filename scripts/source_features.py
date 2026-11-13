"""Photo-registered structural paths, independent of the paint partition.

Anchors are in the upright source photograph's pixel coordinates. They identify
separate visible features, never interpolated full-scene contour bands. A narrow
normal corridor follows the strongest coherent source edge between anchors.
"""
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter, sobel, map_coordinates

# id, kind, anchor pixels; mountain entries tagged opening seed the zero state.
FEATURES={
'desktop': {'size':(1672,941),'paths':[
 ('west_skyline','mountain',[(0,631),(93,577),(142,554),(184,500),(232,451),(260,453),(299,427),(324,402),(341,392),(358,381),(388,385),(420,369),(451,391),(479,362),(514,393),(540,383),(600,399),(625,401),(655,393)]),
 ('peak_left','opening',[(655,393),(686,381),(706,376),(726,363),(747,360),(766,351),(790,344)]),
 ('peak_right','opening',[(790,344),(819,360),(845,373),(866,382),(896,397),(926,411),(956,433),(995,464),(1040,490),(1085,521),(1120,547),(1166,575),(1214,597),(1260,618)]),
 ('peak_shadow_rib','mountain',[(749,360),(760,389),(779,414),(798,439),(812,460)]),
 ('peak_light_rib','mountain',[(794,350),(819,380),(847,411),(879,439),(908,462),(937,482)]),
 ('west_crag_crest','mountain',[(480,396),(508,411),(541,418),(567,419),(594,412),(615,429),(642,440),(663,443),(684,440)]),
 ('middle_crag_crest','mountain',[(684,440),(711,453),(743,466),(769,470),(804,471),(827,481),(852,489),(875,492)]),
 ('east_crag_crest','mountain',[(885,495),(903,501),(914,495),(928,500),(941,509),(954,507),(970,503),(984,511),(1004,509),(1018,513),(1034,522),(1048,536),(1068,556)]),
 ('lit_cliff_west_edge','mountain',[(391,429),(381,453),(365,468),(347,477),(333,490),(338,516),(353,547),(374,570),(402,591),(430,603),(450,601)]),
 ('lit_cliff_east_edge','mountain',[(393,430),(406,447),(418,465),(430,487),(440,514),(453,544),(463,576),(473,595)]),
 ('near_crag_crest','mountain',[(472,464),(489,460),(506,474),(524,492),(544,503),(562,513),(581,518),(604,533),(626,542)]),
 ('behind_hiker_rock','foreground',[(887,660),(916,646),(944,640),(971,647),(993,655)]),
 ('left_stone','foreground',[(289,843),(309,832),(336,835),(355,855),(345,874)]),
 ('center_stone','foreground',[(717,876),(739,860),(762,865),(781,888),(769,910)]),
 ('right_boulder','foreground',[(968,788),(989,775),(1017,789),(1048,806),(1065,827),(1043,844)]),
 ('far_right_stone','foreground',[(1320,824),(1342,809),(1370,817),(1391,838),(1381,857)]),
 ('human','person',[(813,648),(823,645),(835,647),(842,660),(855,665),(868,680),(882,701),(890,708),(886,718),(878,714),(863,697),(854,689),(856,719),(852,741),(852,760),(845,780),(841,793),(832,795),(826,789),(830,776),(828,755),(823,736),(822,756),(826,775),(822,786),(814,786),(812,778),(813,757),(809,738),(806,718),(804,695),(788,708),(779,719),(769,717),(768,710),(782,694),(797,675),(811,663),(813,648)]),
 ('left_pole','person',[(766,699),(774,741),(782,793)]),
 ('right_pole','person',[(887,698),(884,751),(882,800)]),
 ('hood_brim','person_detail',[(817,660),(826,657),(835,660)]),
 ('inner_leg','person_detail',[(832,732),(836,758),(834,781)]),
]},
'mobile': {'size':(1200,1600),'paths':[
 ('west_skyline','mountain',[(0,556),(17,548),(38,563),(68,575),(100,593),(120,586),(145,583),(174,595),(205,605),(239,618),(268,626),(297,621)]),
 ('peak_left','opening',[(297,621),(337,604),(371,596),(404,581),(438,568),(469,558),(500,549),(527,531)]),
 ('peak_right','opening',[(527,531),(558,548),(589,559),(622,577),(663,590),(705,609),(744,630),(784,655),(827,679),(867,704),(915,738),(962,759),(1015,787),(1061,810)]),
 ('peak_shadow_rib','mountain',[(465,559),(477,593),(494,621),(522,657),(554,688),(572,713)]),
 ('peak_light_rib','mountain',[(532,541),(550,576),(582,613),(614,648),(648,680),(685,713),(718,737)]),
 ('west_crag_crest','mountain',[(0,618),(29,626),(52,625),(78,643),(108,648),(138,636),(164,638),(185,649),(213,638),(235,653),(259,681),(282,691)]),
 ('middle_crag_crest','mountain',[(282,691),(313,688),(339,698),(361,689),(385,716),(414,726),(442,729),(464,731),(489,727),(514,737),(544,736),(569,749),(597,755)]),
 ('east_crag_crest','mountain',[(597,755),(621,771),(649,775),(675,788),(701,781),(726,782),(751,793),(773,796),(800,789),(823,798),(847,807),(872,805),(893,824),(917,844),(942,863)]),
 ('lit_cliff_edge','mountain',[(1,696),(24,711),(43,736),(65,751),(81,774),(100,791),(113,817),(129,842),(142,872),(153,905),(161,935),(180,950)]),
 ('near_crag_crest','mountain',[(0,813),(25,826),(48,845),(73,857),(96,874),(118,885),(143,889),(167,904),(190,908),(217,930),(241,944)]),
 ('behind_hiker_rock','foreground',[(636,1025),(668,1011),(703,996),(735,991),(766,1001)]),
 ('left_stone','foreground',[(220,1353),(250,1330),(282,1336),(309,1359),(314,1381)]),
 ('center_stone','foreground',[(381,1450),(416,1412),(445,1416),(468,1456),(449,1490)]),
 ('right_boulder','foreground',[(796,1255),(827,1232),(857,1238),(890,1267),(924,1294),(945,1327),(934,1352)]),
 ('right_stone','foreground',[(1010,1378),(1040,1358),(1075,1367),(1103,1396),(1091,1422)]),
 ('human','person',[(562,1030),(565,1021),(580,1016),(596,1018),(604,1034),(616,1040),(637,1054),(654,1077),(671,1102),(681,1112),(686,1124),(678,1133),(666,1127),(656,1107),(639,1091),(626,1084),(630,1120),(628,1154),(625,1183),(618,1219),(615,1241),(627,1257),(607,1258),(596,1250),(585,1255),(572,1250),(581,1226),(580,1196),(573,1173),(568,1142),(564,1117),(556,1096),(538,1108),(520,1124),(507,1134),(497,1132),(491,1121),(498,1110),(521,1081),(547,1055),(559,1044),(562,1030)]),
 ('left_pole','person',[(494,1097),(506,1172),(525,1262)]),
 ('right_pole','person',[(677,1095),(677,1167),(672,1260)]),
 ('hood_brim','person_detail',[(570,1039),(584,1035),(598,1038)]),
 ('inner_leg','person_detail',[(597,1158),(599,1194),(594,1232)]),
]}}


def register_features(photo,name):
    """Follow source edges within a small corridor around each visual anchor."""
    w,h=photo.size;spec=FEATURES[name];scale=np.array([w,h])/spec['size']
    tone=gaussian_filter(np.asarray(photo,dtype=float)@np.array([.2126,.7152,.0722]),.65)
    gx=sobel(tone,axis=1)/8;gy=sobel(tone,axis=0)/8
    features=[]
    for label,kind,anchors in spec['paths']:
        anchors=np.asarray(anchors,dtype=float)*scale
        arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(anchors,axis=0),axis=1))]
        u=np.linspace(0,arc[-1],max(3,int(arc[-1])))
        base=np.column_stack([np.interp(u,arc,anchors[:,i]) for i in range(2)])
        tangent=gaussian_filter(np.gradient(base,axis=0),(1.1,0))
        tangent/=np.maximum(np.linalg.norm(tangent,axis=1)[:,None],1e-8)
        normal=np.column_stack([-tangent[:,1],tangent[:,0]])
        radius=3 if kind.startswith('person') else 6
        offsets=np.arange(-radius,radius+1,dtype=float)
        samples=base[:,None,:]+normal[:,None,:]*offsets[None,:,None]
        coords=[samples[:,:,1],samples[:,:,0]]
        edge=np.abs(map_coordinates(gx,coords,order=1,mode='nearest')*normal[:,0,None]+
                    map_coordinates(gy,coords,order=1,mode='nearest')*normal[:,1,None])
        cost=-1.6*np.log1p(edge)+.035*offsets[None,:]**2
        # Coherent normal offsets retain jagged rock edges without jumping to
        # unrelated nearby texture. Each feature terminates at its own anchors.
        n,m=cost.shape;back=np.zeros((n,m),dtype=np.int16);previous=cost[0].copy()
        transitions=.22*(offsets[:,None]-offsets[None,:])**2
        transitions[np.abs(offsets[:,None]-offsets[None,:])>2]=1e6
        for j in range(1,n):
            candidates=previous[:,None]+transitions
            back[j]=np.argmin(candidates,axis=0)
            previous=cost[j]+np.min(candidates,axis=0)
        choices=np.empty(n,dtype=int);choices[-1]=np.argmin(previous)
        for j in range(n-1,0,-1):choices[j-1]=back[j,choices[j]]
        path=samples[np.arange(n),choices]
        if np.linalg.norm(anchors[0]-anchors[-1])<1:path[-1]=path[0]
        features.append({'id':label,'kind':kind,'path':path,
                         'mean_gradient':float(np.mean(edge[np.arange(n),choices]))})
    return features


def save_overlays(photo,features,name,directory='/tmp/resolve-source-features'):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    overlay=photo.convert('RGB').copy();draw=ImageDraw.Draw(overlay)
    colors={'opening':(255,100,60),'mountain':(255,100,60),'foreground':(70,255,240),
            'person':(130,255,80),'person_detail':(255,240,80)}
    for i,feature in enumerate(features):
        p=feature['path'];draw.line([tuple(q) for q in p],fill=colors[feature['kind']],width=1)
        q=p[len(p)//2];draw.text(tuple(q+2),str(i),fill='white',stroke_width=1,stroke_fill='black')
    overlay.save(directory/f'{name}-features-overlay.png')
    photo.save(directory/f'{name}-source.png')
    (directory/f'{name}-features.json').write_text(json.dumps([
        {**f,'path':f['path'].round(2).tolist()} for f in features],indent=2)+'\n')

if __name__=='__main__':
    root=Path(__file__).resolve().parents[1]
    for name in FEATURES:
        photo=Image.open(root/f'assets/{name}/photo.webp').convert('RGB')
        save_overlays(photo,register_features(photo,name),name)
