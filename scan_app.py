"""Local desktop launcher. Requires Python with Tk support."""
import importlib.util
from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

base=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('photo_scan',base/'skills/scan-photos/scripts/scan.py')
scanner=importlib.util.module_from_spec(spec);spec.loader.exec_module(scanner)

class App:
    def __init__(self,root):
        self.root=root;root.title('Photo Scan');root.geometry('720x520')
        self.paths=[];self.events=queue.Queue();self.busy=False
        frame=ttk.Frame(root,padding=20);frame.pack(fill='both',expand=True)
        ttk.Label(frame,text='Photo Scan',font=('',22,'bold')).pack(anchor='w')
        ttk.Label(frame,text='Choose document photos, arrange pages, and save a PDF.').pack(anchor='w',pady=(5,15))
        self.pages=tk.Listbox(frame,selectmode='extended',height=12);self.pages.pack(fill='both',expand=True)
        controls=ttk.Frame(frame);controls.pack(fill='x',pady=12)
        for text,command in [('Add photos',self.add),('Remove',self.remove),('Move up',lambda:self.move(-1)),('Move down',lambda:self.move(1))]:
            ttk.Button(controls,text=text,command=command).pack(side='left',padx=3)
        options=ttk.Frame(frame);options.pack(fill='x')
        self.mode=tk.StringVar(value='color');self.size=tk.StringVar(value='a4');self.crop=tk.BooleanVar(value=True)
        ttk.Label(options,text='Mode').pack(side='left');ttk.Combobox(options,textvariable=self.mode,values=['color','gray','bw'],state='readonly',width=8).pack(side='left',padx=8)
        ttk.Label(options,text='Paper').pack(side='left');ttk.Combobox(options,textvariable=self.size,values=['a4','letter','original'],state='readonly',width=8).pack(side='left',padx=8)
        ttk.Checkbutton(options,text='Automatic crop',variable=self.crop).pack(side='left')
        self.button=ttk.Button(frame,text='Save scanned PDF',command=self.save);self.button.pack(anchor='e',pady=12)
        self.status=tk.StringVar(value='Photos are processed locally. Originals stay unchanged.')
        ttk.Label(frame,textvariable=self.status,wraplength=650).pack(anchor='w')
        root.after(100,self.poll)
    def refresh(self):
        self.pages.delete(0,'end')
        for i,p in enumerate(self.paths):self.pages.insert('end',f'{i+1}. {Path(p).name}')
    def add(self):
        if self.busy:return
        files=filedialog.askopenfilenames(filetypes=[('Photos','*.jpg *.jpeg *.png *.webp *.tif *.tiff'),('All files','*')])
        if len(self.paths)+len(files)>50:messagebox.showerror('Too many photos','Choose at most 50 photos.');return
        self.paths.extend(files);self.refresh()
    def remove(self):
        if self.busy:return
        for i in reversed(self.pages.curselection()):del self.paths[i]
        self.refresh()
    def move(self,direction):
        if self.busy:return
        indices=self.pages.curselection()
        if len(indices)!=1:return
        i=indices[0];j=i+direction
        if 0<=j<len(self.paths):self.paths[i],self.paths[j]=self.paths[j],self.paths[i];self.refresh();self.pages.selection_set(j)
    def save(self):
        if self.busy:return
        if not self.paths:messagebox.showinfo('Add photos','Choose at least one document photo.');return
        output=filedialog.asksaveasfilename(defaultextension='.pdf',filetypes=[('PDF','*.pdf')])
        if not output:return
        if Path(output).exists():messagebox.showerror('Choose a new file','Existing files are preserved. Choose a new filename.');return
        inputs=list(self.paths);mode=self.mode.get();size=self.size.get();crop=self.crop.get()
        self.busy=True;self.button.state(['disabled']);self.status.set('Scanning photos…')
        def job():
            try:self.events.put(('done',scanner.scan(inputs,output,mode=mode,page_size=size,crop=crop)))
            except Exception as exc:self.events.put(('error',str(exc)))
        threading.Thread(target=job,daemon=True).start()
    def poll(self):
        try:
            kind,result=self.events.get_nowait();self.busy=False;self.button.state(['!disabled'])
            if kind=='error':self.status.set('Scan failed.');messagebox.showerror('Scan failed',result)
            else:
                self.status.set(f"Saved {len(result['pages'])} pages: {result['pdf']}")
                messagebox.showinfo('PDF saved','Open the saved PDF to review page boundaries and readability. If an automatic crop cuts off content, rerun with Automatic crop switched off.')
        except queue.Empty:pass
        self.root.after(100,self.poll)
if __name__=='__main__':
    root=tk.Tk();App(root);root.mainloop()
