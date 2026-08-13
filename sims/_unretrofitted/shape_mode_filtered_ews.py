# Mode-filtered shape EWS: project distortion onto fault-bearing symmetry modes BEFORE
# window statistics. Hypothesis: modal projection raises SNR -> better sensitivity at
# matched false-positive rate vs scalar Procrustes-distance monitoring.
import math, random
src=open('/mnt/agents/output/sims/shape_fold_ews.py').read().split('print("Shape EWS')[0]
src=src.replace("iters=200","iters=120")
exec(src)

# Octahedral graph Laplacian eigenbasis (6 eigenvectors; lambda 0,4x3,6x2)
def lap_eigvecs():
    L=[[0.0]*6 for _ in range(6)]
    for i,j in edges:
        L[i][i]+=1; L[j][j]+=1; L[i][j]-=1; L[j][i]-=1
    A=[r[:] for r in L]; V=[[float(i==j) for j in range(6)] for i in range(6)]
    for _ in range(300):
        off=0
        for p in range(6):
            for q in range(p+1,6):
                if abs(A[p][q])<1e-12: continue
                off+=abs(A[p][q])
                th=0.5*math.atan2(2*A[p][q],A[q][q]-A[p][p])
                c,s=math.cos(th),math.sin(th)
                for k in range(6):
                    a,b=A[p][k],A[q][k]; A[p][k]=c*a-s*b; A[q][k]=s*a+c*b
                for k in range(6):
                    a,b=A[k][p],A[k][q]; A[k][p]=c*a-s*b; A[k][q]=s*a+c*b
                for k in range(6):
                    a,b=V[k][p],V[k][q]; V[k][p]=c*a-s*b; V[k][q]=s*a+c*b
    order=sorted(range(6), key=lambda i:A[i][i])
    return [ [V[j][i] for j in range(6)] for i in order ], [A[i][i] for i in order]

EVEC,EVAL=lap_eigvecs()
# fault-bearing subspace: modes with support on the fault edge's vertices (0,2), excluding rigid mode
FAULT_MODES=[1,2,3]  # lambda=4 triplet (from earlier sim: carries the signal)

def vertex_disp_vec(V):
    cV=[sum(v[a] for v in V)/6 for a in range(3)]
    return [math.sqrt(sum(((V[i][a]-cV[a])-V0[i][a])**2 for a in range(3))) for i in range(6)]

def mode_energy(V, modes):
    mags=vertex_disp_vec(V)
    return sum(sum(mags[j]*EVEC[m][j] for j in range(6))**2 for m in modes)

def run_fold_mode(seed,T=600,dt=0.02,sigma=0.12,meas_noise=0.003):
    rng=random.Random(seed)
    x=math.sqrt(0.5); Ms=[]; Ds=[]; xs=[]
    for t in range(T):
        r=0.5*(1-1.4*t/T)
        x += (r-x*x)*dt + sigma*math.sqrt(dt)*rng.gauss(0,1)
        if r<=0 and x<=0.05: x=-1.0
        xs.append(x)
        delta=0.35*max(x,0.0)
        demands=[D0]*12; demands[FE]=D0*(1+delta+rng.gauss(0,meas_noise))
        V=relax(V0,demands)
        Ds.append(procrustes(V)); Ms.append(mode_energy(V,FAULT_MODES))
    return Ds,Ms,xs

def tau(xs):
    n=len(xs); c=d=0
    for i in range(n):
        for j in range(i+1,n):
            s=xs[j]-xs[i]
            if s>0: c+=1
            elif s<0: d+=1
    return (c-d)/(c+d) if c+d else 0.0

def win_var(x,win=60,stride=15):
    out=[]
    for i in range(0,len(x)-win,stride):
        w=x[i:i+win]; m=sum(w)/len(w)
        out.append((i+win//2, sum((v-m)**2 for v in w)/(len(w)-1)))
    return out

fold_s=[]; fold_m=[]; null_s=[]; null_m=[]
for seed in range(12):
    Ds,Ms,xs=run_fold_mode(seed)
    drops=[(xs[t-1]-xs[t],t) for t in range(1,len(xs))]
    t_snap=max(drops)[1]
    sv=[v for c,v in win_var(Ds) if c<t_snap]; mv=[v for c,v in win_var(Ms) if c<t_snap]
    if len(sv)>=6:
        fold_s.append(tau(sv)); fold_m.append(tau(mv))
for seed in range(30,42):
    rng=random.Random(seed); x=math.sqrt(0.5); Ds=[]; Ms=[]
    for t in range(600):
        x += (0.5-x*x)*0.02 + 0.12*math.sqrt(0.02)*rng.gauss(0,1)
        demands=[D0]*12; demands[FE]=D0*(1+0.35*max(x,0)+rng.gauss(0,0.003))
        V=relax(V0,demands)
        Ds.append(procrustes(V)); Ms.append(mode_energy(V,FAULT_MODES))
    sv=[v for _,v in win_var(Ds)]; mv=[v for _,v in win_var(Ms)]
    null_s.append(tau(sv)); null_m.append(tau(mv))

print("threshold | scalar: det FP | mode-filtered: det FP")
for thr in [0.2,0.3,0.4,0.5]:
    ds=sum(1 for t in fold_s if t>thr)/len(fold_s); fs=sum(1 for t in null_s if t>thr)/len(null_s)
    dm=sum(1 for t in fold_m if t>thr)/len(fold_m); fm=sum(1 for t in null_m if t>thr)/len(null_m)
    print(f"  tau>{thr:.1f}   | scalar: {ds:.2f} {fs:.2f} | modal: {dm:.2f} {fm:.2f}")
print(f"\n  fold mean tau: scalar={sum(fold_s)/len(fold_s):+.3f} modal={sum(fold_m)/len(fold_m):+.3f}")
print(f"  null mean tau: scalar={sum(null_s)/len(null_s):+.3f} modal={sum(null_m)/len(null_m):+.3f}")
