# Operating curve for shape-trajectory EWS: detection rate vs false-positive rate
# as the Kendall-tau alarm threshold varies. Fold drift vs stationary null.
import math, random
src=open('/mnt/agents/output/sims/shape_fold_ews.py').read().split('print("Shape EWS')[0]
src=src.replace("iters=200","iters=120")  # speed
exec(src)

def tau(xs):
    n=len(xs); c=d=0
    for i in range(n):
        for j in range(i+1,n):
            s=xs[j]-xs[i]
            if s>0: c+=1
            elif s<0: d+=1
    return (c-d)/(c+d) if c+d else 0.0

fold_v=[]; fold_a=[]; null_v=[]; null_a=[]
for seed in range(12):
    Ds,xs=run_fold(seed)
    drops=[(xs[t-1]-xs[t],t) for t in range(1,len(xs))]
    t_snap=max(drops)[1]
    st=[s for s in win_stats(Ds) if s[0]<t_snap]
    if len(st)<6: continue
    fold_v.append(tau([v for _,v,_ in st])); fold_a.append(tau([a for _,_,a in st]))
for seed in range(30,42):
    rng=random.Random(seed); x=math.sqrt(0.5); Ds=[]
    for t in range(600):
        x += (0.5-x*x)*0.02 + 0.12*math.sqrt(0.02)*rng.gauss(0,1)
        demands=[D0]*12; demands[FE]=D0*(1+0.35*max(x,0)+rng.gauss(0,0.003))
        Ds.append(procrustes(relax(V0,demands)))
    st=win_stats(Ds)
    null_v.append(tau([v for _,v,_ in st])); null_a.append(tau([a for _,_,a in st]))

print("threshold | var: det  FP | ac1: det  FP")
for thr in [0.2,0.3,0.4,0.5]:
    dv=sum(1 for t in fold_v if t>thr)/len(fold_v); fv=sum(1 for t in null_v if t>thr)/len(null_v)
    da=sum(1 for t in fold_a if t>thr)/len(fold_a); fa=sum(1 for t in null_a if t>thr)/len(null_a)
    print(f"  tau>{thr:.1f}   | var: {dv:.2f} {fv:.2f} | ac1: {da:.2f} {fa:.2f}")
print(f"\n  fold var_tau mean={sum(fold_v)/len(fold_v):+.2f} vs null {sum(null_v)/len(null_v):+.2f}")
print(f"  fold ac1_tau mean={sum(fold_a)/len(fold_a):+.2f} vs null {sum(null_a)/len(null_a):+.2f}")
