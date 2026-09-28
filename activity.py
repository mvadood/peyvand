import numpy as np, wave, json
def rms(p, hop=0.1):
    w=wave.open(p); sr=w.getframerate(); x=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32)/32768
    n=int(sr*hop); x=x[:len(x)//n*n].reshape(-1,n)
    return 20*np.log10(np.sqrt((x**2).mean(1))+1e-9)
m,h=rms("milad.wav"),rms("hooman.wav"); L=min(len(m),len(h)); m,h=m[:L],h[:L]
thr_m=thr_h=-40
print("noise floors", np.percentile(m,30), np.percentile(h,30))
k=np.ones(5)/5  # 0.5s smoothing
ms=np.convolve((m>thr_m).astype(float),k,"same")>0.3
hs=np.convolve((h>thr_h).astype(float),k,"same")>0.3
st=np.where(ms&~hs,"M",np.where(hs&~ms,"H",np.where(ms&hs,"B","-")))
np.save("state.npy",st)
for s in "MHB-": print(s, round((st==s).mean()*100,1),"%")
