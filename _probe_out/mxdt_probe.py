import struct, sys
def load(path):
    d=open(path,'rb').read()
    fileSize,dataSize,relocCount,rootCount,extRootCount=struct.unpack('>IIIII',d[:0x20-12]) if False else struct.unpack('>IIIII',d[:20])
    data=d[0x20:0x20+dataSize]
    reloc_off=0x20+dataSize
    relocs=set()
    for i in range(relocCount):
        (p,)=struct.unpack('>I',d[reloc_off+i*4:reloc_off+i*4+4]); relocs.add(p)
    root_off=reloc_off+relocCount*4
    roots=[]
    strtab=root_off+(rootCount+extRootCount)*8
    for i in range(rootCount+extRootCount):
        o,so=struct.unpack('>iI',d[root_off+i*8:root_off+i*8+8])
        s=strtab+so; e=d.index(b'\x00',s); roots.append((o,d[s:e].decode('ascii','replace')))
    return data,relocs,roots
def u32(data,off): return struct.unpack('>I',data[off:off+4])[0]
def i32(data,off): return struct.unpack('>i',data[off:off+4])[0]
def deref(data,off): return u32(data,off)  # offset within data
def cstr(data,off):
    e=data.index(b'\x00',off); return data[off:e].decode('ascii','replace')

path=sys.argv[1]
bf_internal=int(sys.argv[2]) if len(sys.argv)>2 else 46
data,relocs,roots=load(path)
mex=roots[0][0]
meta=deref(data,mex+0x00)
fd=deref(data,mex+0x08)
efftab=deref(data,mex+0x18)
internalIDs=i32(data,meta+0x04)
numEffects=i32(data,meta+0x24)
effIDs=deref(data,fd+0x24)
effFiles=deref(data,efftab+0x00)
print(f"root {roots[0][1]}  internalIDs={internalIDs} numEffects={numEffects}")
print("=== EffectFiles table ===")
files=[]
for e in range(numEffects):
    ent=effFiles+e*0x0C
    fnp=deref(data,ent+0x00); syp=deref(data,ent+0x04)
    fn=cstr(data,fnp) if fnp else ''
    sy=cstr(data,syp) if syp else ''
    files.append((fn,sy))
    print(f"  [{e:3}] file={fn!r:30} sym={sy!r}")
print("=== EffectIDs for fighters around BF ===")
for fi in range(internalIDs):
    eid=data[effIDs+fi]
    mark=''
    if fi==bf_internal: mark='  <== B. Falcon'
    if eid<numEffects:
        fn,sy=files[eid]
    else:
        fn,sy=('<OOB id %d>'%eid,'')
    if mark or eid>=numEffects:
        print(f"  fighter {fi:3} effId={eid:3} -> {fn} / {sy}{mark}")
print("=== BF resolved ===")
eid=data[effIDs+bf_internal]
print("BF internal",bf_internal,"effId",eid, "->", files[eid] if eid<numEffects else "OOB")
