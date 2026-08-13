# Null-calibrated shape EWS: use Kendall-tau criterion on windowed variance/AC1 of D(t)
# (same statistic as notes/12 S6), comparing drift-to-fold vs stationary null.
import math, random
exec(open('/mnt/agents/output/sims/shape_fold_ews.py').read().split('print("Shape EWS')[0])  # reuse defs

def tau(xs):
    n=len(xs); c=d=0
    for i in range(n):
        for j in range(i+1,n):
            s=xs[j]-xs[i]
            if s>0: c+=1
            elif s<0: d+=1
    return (c-d)/(c+d) if c+d else 0.0

print("Null-calibrated (Kendall-tau>0.5) shape EWS under fold:")
det_v=det_a=0; fa_v=fa_a=0; lead_v=[]; lead_a=[]
for seed in range(15):
    Ds,xs=run_fold(seed)
    drops=[(xs[t-1]-xs[t],t) for t in range(1,len(xs))]
    t_snap=max(drops)[1]
    st=[s for s in win_stats(Ds) if s[0]<t_snap]
    if len(st)<6: continue
    tv=tau([v for _,v,_ in st]); ta=tau([a for _,_,a in st])
    if tv>0.5:
        det_v+=1
        base=sorted(v for _,v,_ in st[:4]); thr=4*base[2]
        tal=next((c for c,v,_ in st if v>thr),None)
        if tal: lead_v.append(t_snap-tal)
    if ta>0.5:
        det_a+=1
        tal=next((c for c,_,a in st if a>0.4),None)
        if tal: lead_a.append(t_snap-tal)
for seed in range(30,45):
    rng=random.Random(seed); x=math.sqrt(0.5); Ds=[]
    for t in range(600):
        x += (0.5-x*x)*0.02 + 0.12*math.sqrt(0.02)*rng.gauss(0,1)
        demands=[D0]*12; demands[FE]=D0*(1+0.35*max(x,0)+rng.gauss(0,0.003))
        Ds.append(procrustes(relax(V0,demands)))
    st=win_stats(Ds)
    if tau([v for _,v,_ in st])>0.5: fa_v+=1
    if tau([a for _,_,a in st])>0.5: fa_a+=1
print(f"  fold: variance detection {det_v}/15 (mean lead {sum(lead_v)/max(len(lead_v),1):.0f}), "
      f"AC1 detection {det_a}/15 (mean lead {sum(lead_a)/max(len(lead_a),1):.0f})")
print(f"  null false positives: variance {fa_v}/15, AC1 {fa_a}/15")
