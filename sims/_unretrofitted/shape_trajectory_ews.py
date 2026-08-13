# Shape-space EWS: does the shape's trajectory in shape space show early-warning
# signals BEFORE visible distortion? Octahedron spring network; imbalance on edge (0,2)
# grows with noise; we track Procrustes distortion D(t) and per-mode amplitudes,
# windowed variance + AR(1) + Kendall-tau, and compare alarm timing vs threshold crossing.
# Face-level: faces carry interconnection (XOR-type) residuals that edge analysis misses.
import math, random

V0 = [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]
edges = [(i,j) for i in range(6) for j in range(i+1,6)
         if abs(sum(a*b for a,b in zip(V0[i],V0[j])))<0.5]
FACES = [(0,2,4),(0,4,3),(0,3,5),(0,5,2),(1,2,4),(1,4,3),(1,3,5),(1,5,2)]  # octahedron faces
D0 = math.sqrt(2.0)

def relax(V, demands, iters=250, lr=0.05):
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
    n=len(V)
    cV=[sum(v[a] for v in V)/n for a in range(3)]
    cR=[sum(v[a] for v in V0)/n for a in range(3)]
    return math.sqrt(sum((V[i][a]-cV[a]-V0[i][a]+cR[a])**2 for i in range(n) for a in range(3))/n)

def vertex_disp(V):
    cV=[sum(v[a] for v in V)/6 for a in range(3)]
    cR=[sum(v[a] for v in V0)/6 for a in range(3)]
    return [math.sqrt(sum(((V[i][a]-cV[a])-(V0[i][a]-cR[a]))**2 for a in range(3))) for i in range(6)]

edge_index = {e:k for k,e in enumerate(edges)}
FAULT_EDGE = edge_index[(0,2)]

def step(delta, noise, rng):
    demands=[D0]*12
    demands[FAULT_EDGE]=D0*(1+delta)
    # noisy measurements of all edges (finite sensor precision)
    demands=[d*(1+rng.gauss(0,noise)) for d in demands]
    demands[FAULT_EDGE]=D0*(1+delta+rng.gauss(0,noise))
    return relax(V0,demands)

def run_trial(seed, growth=0.0012, noise=0.004, T=220):
    rng=random.Random(seed)
    Ds=[]
    for t in range(T):
        delta=growth*t  # slow ramp toward failure
        V=step(delta,noise,rng)
        Ds.append(procrustes(V))
    return Ds

def win_stats(x, win=40, stride=10):
    out=[]
    for i in range(0,len(x)-win,stride):
        w=x[i:i+win]; m=sum(w)/len(w)
        var=sum((v-m)**2 for v in w)/(len(w)-1)
        ac1=sum((w[j]-m)*(w[j-1]-m) for j in range(1,len(w)))/max(sum((v-m)**2 for v in w),1e-15)
        out.append((i+win//2,var,ac1))
    return out

def tau(xs):
    n=len(xs); c=d=0
    for i in range(n):
        for j in range(i+1,n):
            s=xs[j]-xs[i]
            if s>0: c+=1
            elif s<0: d+=1
    return (c-d)/(c+d) if c+d else 0.0

THRESH=0.05  # "visible" distortion threshold
print("Shape-trajectory EWS (distortion threshold %.2f):"%THRESH)
lead_times=[]
for seed in range(12):
    Ds=run_trial(seed)
    # threshold crossing time
    tvis=next((t for t,d in enumerate(Ds) if d>THRESH), len(Ds))
    # EWS: variance tau over windows up to time t (causal)
    stats=win_stats(Ds)
    # alarm: variance kendall-tau (computed on first 60% of windows) > 0.4
    cut=[s for s in stats if s[0]<tvis]
    if len(cut)<5: continue
    tvar=tau([v for _,v,_ in cut]); tac1=tau([a for _,_,a in cut])
    # earliest window where rolling variance exceeds 2x its median-of-first-3
    base=sorted(v for _,v,_ in cut[:3])[1] if len(cut)>=3 else cut[0][1]
    talarm=next((c for c,v,_ in cut if v>2*base), None)
    lead = (tvis-talarm) if talarm else 0
    lead_times.append(lead)
    if seed<6:
        print(f"  seed={seed}: t_visible={tvis}, var_tau={tvar:+.2f}, ac1_tau={tac1:+.2f}, alarm_lead={lead} steps")
print(f"  mean alarm lead over {len(lead_times)} trials: {sum(lead_times)/max(len(lead_times),1):.1f} steps")

# Null: no drift, pure noise -> should NOT show rising variance tau
nul=[]
for seed in range(12,24):
    rng=random.Random(seed); Ds=[procrustes(step(0.3,noise=0.004,rng=rng)) for _ in range(220)]
    st=win_stats(Ds); nul.append(tau([v for _,v,_ in st]))
print(f"  null (fixed delta=0.3, no growth): var_tau mean={sum(nul)/len(nul):+.2f}, frac>0.4: {sum(1 for t in nul if t>0.4)/len(nul):.2f}")

# ---- Face-level: XOR-type interconnection residual invisible to edge analysis ----
# Two edges each slightly off in OPPOSITE directions: edge residuals cancel in sum,
# edge-magnitude analysis sees small individual faults; face-level aggregate sees tension.
rng=random.Random(99)
eA=edge_index[(0,2)]; eB=edge_index[(0,4)]
demands=[D0]*12
demands[eA]=D0*1.15; demands[eB]=D0*0.85   # opposing pulls on one face
V=relax(V0,demands)
mags=vertex_disp(V)
# edge-only detector: displacement magnitude z-scores
m=sum(mags)/6; sd=math.sqrt(sum((x-m)**2 for x in mags)/6)
print("\nXOR-type face fault (edge A +15%, edge B -15%, same face):")
print("  per-vertex displacement:", [round(x,4) for x in mags])
print("  total Procrustes:", round(procrustes(V),4))
# face aggregate: sum of |disp| over face vertices vs non-face
face=FACES[0]  # (0,2,4) contains both faulted edges
inface=sum(mags[i] for i in face); offface=sum(mags[i] for i in range(6) if i not in face)
print(f"  face(0,2,4) displacement mass={inface:.4f} vs off-face={offface:.4f} (ratio {inface/max(offface,1e-9):.2f}x)")
