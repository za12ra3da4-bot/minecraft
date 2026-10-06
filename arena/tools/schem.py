"""WorldEdit Sponge 스키매틱 (.schem, v3) 읽기 — 사용자가 서버에서 직접 고친 맵을 가져올 때
   load(path) → NBT dict · read(path) → (블록 배열 [x, y, z], 팔레트 목록, 원점 메타)"""
import gzip, struct, sys, io
import numpy as np
def rd(f, t):
    if t==1: return struct.unpack('>b', f.read(1))[0]
    if t==2: return struct.unpack('>h', f.read(2))[0]
    if t==3: return struct.unpack('>i', f.read(4))[0]
    if t==4: return struct.unpack('>q', f.read(8))[0]
    if t==5: return struct.unpack('>f', f.read(4))[0]
    if t==6: return struct.unpack('>d', f.read(8))[0]
    if t==7:
        n=struct.unpack('>i', f.read(4))[0]; return np.frombuffer(f.read(n), np.int8)
    if t==8:
        n=struct.unpack('>H', f.read(2))[0]; return f.read(n).decode('utf-8')
    if t==9:
        et=f.read(1)[0]; n=struct.unpack('>i', f.read(4))[0]; return [rd(f,et) for _ in range(n)]
    if t==10:
        d={}
        while True:
            tt=f.read(1)[0]
            if tt==0: return d
            k=rd(f,8); d[k]=rd(f,tt)
    if t==11:
        n=struct.unpack('>i', f.read(4))[0]; return np.frombuffer(f.read(4*n), '>i4')
    if t==12:
        n=struct.unpack('>i', f.read(4))[0]; return np.frombuffer(f.read(8*n), '>i8')
    raise ValueError(t)
def load(path):
    f=io.BytesIO(gzip.open(path).read())
    t=f.read(1)[0]; name=rd(f,8); return rd(f,t)
def varints(b):
    out=[]; v=0; s=0
    for x in b.astype(np.uint8):
        v|=(int(x)&0x7f)<<s
        if x&0x80: s+=7
        else: out.append(v); v=0; s=0
    return np.array(out, np.int32)
def read(path):
    root = load(path)["Schematic"]
    W, H, L = root["Width"], root["Height"], root["Length"]
    pal = root["Blocks"]["Palette"]
    inv = {v: k for k, v in pal.items()}
    idx = varints(root["Blocks"]["Data"]).reshape(H, L, W)       # y, z, x
    names = [inv[i].replace("minecraft:", "") for i in range(len(inv))]
    return np.transpose(idx, (2, 0, 1)), names, root


if __name__=='__main__':
    root=load(sys.argv[1])
    def show(d,ind=0):
        for k,v in d.items():
            if isinstance(v,dict): print(' '*ind+k+':'); show(v,ind+2) if len(v)<40 else print(' '*ind+'  (%d keys)'%len(v))
            elif isinstance(v,np.ndarray): print(' '*ind+k, 'array', v.shape)
            elif isinstance(v,list): print(' '*ind+k,'list',len(v))
            else: print(' '*ind+k, v)
    show(root)
