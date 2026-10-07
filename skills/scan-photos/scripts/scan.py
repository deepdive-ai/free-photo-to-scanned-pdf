"""Photo scanning using Pillow and NumPy. All processing stays in the host runtime."""
import argparse, json, os, tempfile
from pathlib import Path
import numpy as np
from PIL import Image, ImageOps, ImageFilter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

Image.MAX_IMAGE_PIXELS = 50_000_000

def edge_crop(rgb):
    """Conservative top/bottom border crop when paper extends past both side edges."""
    gray = rgb.mean(2)
    h,w = gray.shape
    if h < w: return None
    delta = np.diff(gray, axis=0)
    xs = np.arange(int(w*.15), int(w*.85))
    span = max(8,int(h*.12))
    top_span=max(8,int(h*.08))
    top = delta[2:top_span, xs].argmax(axis=0)+2
    bottom = delta[h-span:h-3, xs].argmin(axis=0)+h-span
    top_strength = delta[top,xs]
    bottom_strength = -delta[bottom,xs]
    good = (top_strength>18) & (bottom_strength>18)
    if good.mean()<.6: return None
    lines=[]
    for ys in (top,bottom):
        x=xs[good];y=ys[good]
        # Robust line fit avoids letterhead graphics overpowering the outer boundary.
        keep=None
        samples=np.linspace(0,len(x)-1,12,dtype=int)
        for i in samples:
            for j in samples:
                if x[j]-x[i]<w*.2: continue
                slope=(y[j]-y[i])/(x[j]-x[i])
                candidate=np.abs(y-(slope*x+y[i]-slope*x[i]))<h*.012
                if keep is None or candidate.sum()>keep.sum(): keep=candidate
        if keep is None or keep.mean()<.6: return None
        coeff=np.polyfit(x[keep],y[keep],1)
        lines.append(np.polyval(coeff,[0,w-1]))
    t,b=lines
    # Include a small margin on the outside of detected boundaries.
    t=np.clip(t-2,0,h-1);b=np.clip(b+3,0,h-1)
    if np.any(b-t<h*.72): return None
    return np.array([[0,t[0]],[w-1,t[1]],[w-1,b[1]],[0,b[0]]])/np.array([w-1,h-1])

def detect(image):
    small = image.copy()
    small.thumbnail((500, 500))
    rgb = np.asarray(small.convert('RGB'), dtype=float)
    gray = rgb.mean(2)
    mask = (gray >= max(150, float(np.percentile(gray, 65)))) & ((rgb.max(2)-rgb.min(2)) < 65)
    # Follow the largest connected bright region; avoid selecting scattered text/highlights.
    seen = np.zeros(mask.shape, bool)
    best = []
    h,w = mask.shape
    for y,x in zip(*np.where(mask)):
        if seen[y,x]: continue
        stack=[(int(y),int(x))]; seen[y,x]=True; component=[]
        while stack:
            yy,xx=stack.pop(); component.append((xx,yy))
            for ny,nx in ((yy-1,xx),(yy+1,xx),(yy,xx-1),(yy,xx+1)):
                if 0<=ny<h and 0<=nx<w and mask[ny,nx] and not seen[ny,nx]:
                    seen[ny,nx]=True; stack.append((ny,nx))
        if len(component)>len(best): best=component
    if len(best)<w*h*.2: return edge_crop(rgb)
    p=np.array(best, dtype=float)
    sums=p.sum(1); diffs=p[:,0]-p[:,1]
    corners=p[[sums.argmin(),diffs.argmax(),sums.argmax(),diffs.argmin()]]
    if len(np.unique(corners,axis=0))<4: return None
    area=abs(np.dot(corners[:,0],np.roll(corners[:,1],1))-np.dot(corners[:,1],np.roll(corners[:,0],1)))/2
    if not .2*w*h<area<.94*w*h or len(best)/area<.7: return edge_crop(rgb)
    if np.any(corners[:,0]<3) or np.any(corners[:,0]>w-4) or np.any(corners[:,1]<3) or np.any(corners[:,1]>h-4): return edge_crop(rgb)
    return corners / np.array([w-1,h-1])

def warp(image, points):
    p=np.asarray(points,dtype=float)
    if p.shape!=(4,2) or not np.isfinite(p).all() or (p<0).any() or (p>1).any():
        raise ValueError('Corners must be four normalized [x,y] pairs in TL, TR, BR, BL order.')
    p=p*np.array([image.width-1,image.height-1])
    edges=np.roll(p,-1,axis=0)-p
    following=np.roll(edges,-1,axis=0)
    crosses=edges[:,0]*following[:,1]-edges[:,1]*following[:,0]
    if not all(float(c)>1 for c in crosses): raise ValueError('Corners must form a convex clockwise page, starting top-left.')
    width=round(max(np.linalg.norm(p[1]-p[0]),np.linalg.norm(p[2]-p[3])))
    height=round(max(np.linalg.norm(p[3]-p[0]),np.linalg.norm(p[2]-p[1])))
    if min(width,height)<32: raise ValueError('Selected page is too small.')
    dest=[(0,0),(width-1,0),(width-1,height-1),(0,height-1)]
    a=[]; b=[]
    for (x,y),(u,v) in zip(dest,p):
        a.extend([[x,y,1,0,0,0,-u*x,-u*y],[0,0,0,x,y,1,-v*x,-v*y]])
        b.extend([u,v])
    coeff=np.linalg.solve(np.array(a),np.array(b))
    return image.transform((width,height),Image.Transform.PERSPECTIVE,coeff,Image.Resampling.BICUBIC)

def clean(image, mode):
    if mode=='color': return ImageOps.autocontrast(image,cutoff=.5)
    gray=ImageOps.grayscale(image)
    # Estimate illumination at low resolution to flatten soft shadows without erasing letters.
    small=gray.copy(); small.thumbnail((160,160))
    background=small.filter(ImageFilter.MaxFilter(15)).filter(ImageFilter.GaussianBlur(5)).resize(gray.size,Image.Resampling.BILINEAR)
    normalized=np.clip(np.asarray(gray,dtype=float)/(np.asarray(background,dtype=float)+1)*245,0,255).astype('uint8')
    if mode=='bw': normalized=np.where(normalized>185,255,0).astype('uint8')
    return Image.fromarray(normalized)

def scan(inputs, output, mode='color', page_size='a4', corners=None, crop=True, rotate=0, preview_dir=None):
    if not inputs or len(inputs)>50: raise ValueError('Provide 1 to 50 photos.')
    out=Path(output)
    if out.exists(): raise ValueError('Output exists; choose a new filename.')
    if corners is not None and len(corners)!=len(inputs): raise ValueError('Provide one corners entry per input photo (null for automatic).')
    out.parent.mkdir(parents=True,exist_ok=True)
    previews=Path(preview_dir) if preview_dir else None
    if previews: previews.mkdir(parents=True,exist_ok=True)
    report=[]
    fd,tmp=tempfile.mkstemp(suffix='.pdf',dir=out.parent); os.close(fd)
    try:
        pdf=canvas.Canvas(tmp)
        pdf.setTitle('Photo Scan'); pdf.setCreator('Photo Scan plugin')
        for index,path in enumerate(inputs):
            with Image.open(path) as source:
                image=ImageOps.exif_transpose(source).convert('RGB')
            image.thumbnail((3000,3000))
            if rotate: image=image.rotate(-rotate,expand=True)
            manual=corners[index] if corners else None
            points=manual if manual is not None else (detect(image) if crop else None)
            if points is not None: image=warp(image,points)
            warning=None if manual is not None else ('Automatic crop needs visual review.' if points is not None else 'No reliable page boundary found; full photo retained.')
            image=clean(image,mode)
            if previews: image.save(previews/f'page-{index+1:03}.png')
            if page_size=='original': size=(image.width*72/200,image.height*72/200)
            else:
                size=(595.276,841.89) if page_size=='a4' else (612,792)
                if image.width>image.height: size=size[::-1]
            pdf.setPageSize(size)
            margin=0 if page_size=='original' else 12
            factor=min((size[0]-2*margin)/image.width,(size[1]-2*margin)/image.height)
            pw,ph=image.width*factor,image.height*factor
            pdf.drawImage(ImageReader(image),(size[0]-pw)/2,(size[1]-ph)/2,pw,ph)
            pdf.showPage()
            report.append({'page':index+1,'source':Path(path).name,'cropped':points is not None,'warning':warning})
        pdf.save()
        os.replace(tmp,out)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)
    return {'pdf':str(out.resolve()),'pages':report,'mode':mode,'searchable':False}

def main():
    p=argparse.ArgumentParser(description='Convert ordered phone photos into a cleaned multi-page PDF.')
    p.add_argument('photos',nargs='+'); p.add_argument('--output',required=True)
    p.add_argument('--mode',choices=['color','gray','bw'],default='color')
    p.add_argument('--page-size',choices=['a4','letter','original'],default='a4')
    p.add_argument('--corners',help='JSON file: ordered list of four normalized corners per page, or null.')
    p.add_argument('--no-crop',action='store_true'); p.add_argument('--rotate',type=int,choices=[0,90,180,270],default=0)
    p.add_argument('--preview-dir')
    args=p.parse_args()
    try:
        points=json.loads(Path(args.corners).read_text()) if args.corners else None
        print(json.dumps(scan(args.photos,args.output,args.mode,args.page_size,points,not args.no_crop,args.rotate,args.preview_dir),indent=2))
    except (ValueError,OSError,Image.DecompressionBombError,np.linalg.LinAlgError) as exc:
        p.exit(2,f'Scan failed: {exc}\n')
if __name__=='__main__': main()
