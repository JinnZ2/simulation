# Shape EWS under FOLD dynamics: the imbalance variable x approaches a saddle-node
# (dx = (r - x^2)dt + sigma dW, r ramping down) then JUMPS. The shape distortion D(t)
# inherits the fold: slow drift then sudden snap. Question: does variance/AR(1) on the
# shape trajectory D(t) fire BEFORE the snap? (Critical slowing down in shape space.)
import math, random

V0 = [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]
edges = [(i,j) for i in range(6) for j in range(i+1,6)
         if abs(sum(a*b for a,b in zip(V0[i],V0[j])))<0.5]
D0 = math.sqrt(2.0)
edge_index = {e:k for k,e in enumerate(edges)}
FE = edge_index[(0,2)]

def relax(V, demands, iters=200, lr=0.06):
    V=[list(v) for v in V]
    for _ in range(iters):
        G=[[0.0]*3 for _ in range(6)]
        for k,(i,j) in enumerate(edges):
            d=[V[i][a]-V[j][a] for a in range(3)]
            L=math.sqrt(sum(x*x for x in d))+1e-12
            f=(L-demands[k])/L
            for a in range(3):
                G[i][a]+=f*d[a]; G[j][a]-=f*d[a]
        for i in range(6):
            for a in range(3): V[i][a]-=lr*G[i][a]
    return V

def procrustes(V):
    cV=[sum(v[a] for v in V)/6 for a in range(3)]
    return math.sqrt(sum((V[i][a]-cV[a]-V0[i][a])**2 for i in range(6) for a in range(3))/6)

def run_fold(seed, T=600, dt=0.02, sigma=0.12, meas_noise=0.003):
    rng=random.Random(seed)
    x=math.sqrt(0.5); Ds=[]; xs=[]
    for t in range(T):
        r=0.5*(1 - 1.4*t/T)          # crosses 0 at ~71% of run -> fold
        x += (r - x*x)*dt + sigma*math.sqrt(dt)*rng.gauss(0,1)
        if r<=0 and x<=0.05: x=-1.0   # snap to collapsed branch
        xs.append(x)
        delta=0.35*max(x,0.0)         # imbalance drives shape
        demands=[D0]*12
        demands[FE]=D0*(1+delta+rng.gauss(0,meas_noise))
        Ds.append(procrustes(relax(V0,demands)))
    return Ds,xs

def win_stats(x,win=60,stride=15):
    out=[]
    for i in range(0,len(x)-win,stride):
        w=x[i:i+win]; m=sum(w)/len(w)
        var=sum((v-m)**2 for v in w)/(len(w)-1)
        ac1=sum((w[j]-m)*(w[j-1]-m) for j in range(1,len(w)))/max(sum((v-m)**2 for v in w),1e-15)
        out.append((i+win//2,var,ac1))
    return out

print("Shape EWS under fold dynamics:")
leads_var=[]; leads_ac1=[]
for seed in range(10):
    Ds,xs=run_fold(seed)
    # snap time = largest single-step drop in xs
    drops=[(xs[t-1]-xs[t],t) for t in range(1,len(xs))]
    t_snap=max(drops)[1]
    st=[s for s in win_stats(Ds) if s[0]<t_snap]
    if len(st)<6: continue
    base=sorted(v for _,v,_ in st[:4])
    thr_var=3*base[len(base)//2]
    # rolling ac1 rising above 0.3
    t_var=next((c for c,v,_ in st if v>thr_var),None)
    t_ac1=next((c for c,_,a in st if a>0.3),None)
    if t_var: leads_var.append(t_snap-t_var)
    if t_ac1: leads_ac1.append(t_snap-t_ac1)
    if seed<5:
        print(f"  seed={seed}: t_snap={t_snap}, var_alarm_lead={t_snap-t_var if t_var else None}, ac1_alarm_lead={t_snap-t_ac1 if t_ac1 else None}")
print(f"  mean lead: variance={sum(leads_var)/max(len(leads_var),1):.1f} steps ({len(leads_var)}/10 fired), "
      f"ac1={sum(leads_ac1)/max(len(leads_ac1),1):.1f} steps ({len(leads_ac1)}/10 fired)")
# null: constant r, no fold
null_leads=[]
for seed in range(20,30):
    rng=random.Random(seed); x=math.sqrt(0.5); Ds=[]
    for t in range(600):
        x += (0.5-x*x)*0.02 + 0.12*math.sqrt(0.02)*rng.gauss(0,1)
        demands=[D0]*12; demands[FE]=D0*(1+0.35*max(x,0)+rng.gauss(0,0.003))
        Ds.append(procrustes(relax(V0,demands)))
    st=win_stats(Ds)
    base=sorted(v for _,v,_ in st[:4]); thr=3*base[len(base)//2]
    fired=sum(1 for _,v,_ in st if v>thr)
    null_leads.append(fired>0)
print(f"  null (no fold): variance-alarm false-positive rate = {sum(null_leads)/len(null_leads):.2f}")
