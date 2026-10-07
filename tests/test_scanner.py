import sys,tempfile,unittest
from pathlib import Path
from PIL import Image,ImageDraw
from pypdf import PdfReader
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'skills/scan-photos/scripts'))
from scan import scan,warp,detect

class ScannerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        im=Image.new('RGB',(800,1100),'#403a32');d=ImageDraw.Draw(im)
        d.polygon([(140,80),(700,140),(660,1020),(80,930)],fill='#f4f0e8')
        for y in range(260,800,60):d.line((200,y,540,y),fill='black',width=4)
        self.photo=self.root/'page.jpg';im.save(self.photo)
        self.note=self.root/'note.png';Image.new('RGB',(600,800),'white').save(self.note)
    def test_modes_and_order(self):
        for mode in ['color','gray','bw']:
            result=scan([self.photo,self.note],self.root/f'{mode}.pdf',mode=mode)
            self.assertEqual(len(PdfReader(result['pdf']).pages),2)
            self.assertEqual([p['source'] for p in result['pages']],['page.jpg','note.png'])
            self.assertTrue(result['pages'][0]['cropped']);self.assertFalse(result['pages'][1]['cropped'])
    def test_manual_and_original_preserved(self):
        before=self.photo.read_bytes()
        result=scan([self.photo],self.root/'manual.pdf',corners=[[[.175,.073],[.875,.127],[.825,.927],[.1,.845]]])
        self.assertTrue(result['pages'][0]['cropped']);self.assertEqual(before,self.photo.read_bytes())
        self.assertEqual(result['mode'],'color')
    def test_reject_existing_and_bad_corners(self):
        target=self.root/'existing.pdf';target.write_bytes(b'preserve me')
        with self.assertRaises(ValueError):scan([self.photo],target)
        self.assertEqual(target.read_bytes(),b'preserve me')
        with Image.open(self.photo) as im:
            with self.assertRaises(ValueError):warp(im,[[0,0],[0,0],[1,1],[0,1]])
    def test_edge_crop_and_fallback(self):
        im=Image.new('RGB',(600,1000),'#555555');d=ImageDraw.Draw(im)
        d.polygon([(0,60),(599,30),(599,920),(0,900)],fill='#eeeeee')
        points=detect(im);self.assertIsNotNone(points)
        self.assertLess(points[0][1],.08);self.assertGreater(points[2][1],.88)
        self.assertIsNone(detect(Image.new('RGB',(600,1000),'white')))
    def test_cli_no_crop_and_failed_input(self):
        result=scan([self.photo],self.root/'full.pdf',crop=False)
        self.assertFalse(result['pages'][0]['cropped'])
        with self.assertRaises(OSError):scan([self.root/'missing.jpg'],self.root/'failed.pdf')
        self.assertFalse((self.root/'failed.pdf').exists())
if __name__=='__main__':unittest.main()
