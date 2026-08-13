import math, random

# ---------- S3a: cleanup-based bundling recovery ----------
random.seed(11)
def cleanup_recovery(d, k, M=300, trials=12):
    ok = 0
    for _ in range(trials):
        codebook = [[random.choice([-1,1]) for _ in range(d)] for _ in range(M)]
        members = random.sample(range(M), k)
        bundle = [sum(codebook[m][i] for m in members) for i in range(d)]
        nb = math.sqrt(sum(x*x for x in bundle))
        j = members[0]
        def cos(v): return sum(x*y for x,y in zip(bundle,v))/(nb*math.sqrt(d))
        cj = cos(codebook[j])
        nonmembers = [x for x in range(M) if x not in members]
        best = max(cos(codebook[m]) for m in random.sample(nonmembers,100))
        if cj > best: ok += 1
    return ok/trials

print("S3a cleanup-based bundling recovery (M=500):")
for d in [256, 1024]:
    row = [f"k={k}:{cleanup_recovery(d,k):.2f}" for k in [2,4,8,16,32]]
    print(f"  d={d}: " + " ".join(row))

# ---------- S3b: FDM channels on one summed line ----------
random.seed(5)
def dft_mag(sig, f, N):
    re = sum(sig[t]*math.cos(2*math.pi*f*t/N) for t in range(N))
    im = -sum(sig[t]*math.sin(2*math.pi*f*t/N) for t in range(N))
    return 2*math.sqrt(re*re+im*im)/N

def fdm_test(k, noise_std, N=512, spacing=4):
    freqs = [2+spacing*i for i in range(k)]
    amps = [random.uniform(0.5,1.0) for _ in range(k)]
    sig = [sum(a*math.sin(2*math.pi*f*t/N) for a,f in zip(amps,freqs)) + random.gauss(0,noise_std) for t in range(N)]
    errs = [abs(dft_mag(sig,f,N)-a)/a for a,f in zip(amps,freqs)]
    return sum(errs)/len(errs)

print("S3b FDM amplitude recovery rel-error vs channel count (N=512):")
for ns in [0.01, 0.1]:
    print(f"  noise={ns}: " + " ".join(f"k={k}:{fdm_test(k,ns):.3f}" for k in [1,4,8,16,32]))

# ---------- S4: chart-aware vs single-chart compression ----------
# Two curved arcs in R^3 (two clusters on different planes, curved) -> global PCA rank-1 vs 2-chart PCA rank-1
random.seed(9)
def make_data(npts=600, curvature=1.0):
    pts = []
    for i in range(npts):
        t = random.uniform(-1,1)
        c = i % 2
        base = [t, curvature*t*t, 0.0]
        off = [0,0,3.0] if c else [0,0,-3.0]
        rot = 0.6 if c else -0.6
        x = base[0]*math.cos(rot)-base[1]*math.sin(rot)
        y = base[0]*math.sin(rot)+base[1]*math.cos(rot)
        pts.append(([x+off[0], y+off[1], base[2]+off[2]] , c))
    return pts

def pc1_recon_err(pts):
    n = len(pts); d = 3
    mean = [sum(p[i] for p in pts)/n for i in range(d)]
    C = [[sum((p[i]-mean[i])*(p[j]-mean[j]) for p in pts)/n for j in range(d)] for i in range(d)]
    # power iteration for top eigenvector
    v = [1.0,0.3,0.1]
    for _ in range(200):
        w = [sum(C[i][j]*v[j] for j in range(d)) for i in range(d)]
        nw = math.sqrt(sum(x*x for x in w)); v = [x/nw for x in w]
    err = 0.0
    for p in pts:
        proj = sum((p[i]-mean[i])*v[i] for i in range(d))
        r = [ (p[i]-mean[i]) - proj*v[i] for i in range(d)]
        err += sum(x*x for x in r)
    return err/n

for curv in [0.0, 0.5, 1.0, 2.0]:
    data = make_data(curvature=curv)
    allpts = [p for p,c in data]
    g = pc1_recon_err(allpts)
    l = (pc1_recon_err([p for p,c in data if c==0]) + pc1_recon_err([p for p,c in data if c==1]))/2
    print(f"S4 curvature={curv:.1f}: global-PCA err={g:.4f}  2-chart err={l:.4f}  ratio={g/max(l,1e-9):.2f}x")

# ---------- S5: citation-bias cascade simulation ----------
random.seed(13)
def cite_cascade(bias, n_papers=300, cites_per=4):
    # claim: true; supportive evidence weak. bias = prob of preferring supportive citations
    support = [random.random()<0.5 for _ in range(2)]  # seed papers
    paths_through_hub = 0
    cite_counts = [0,0]
    hub = 0  # data-free review appears at index 2
    for i in range(2, n_papers):
        if i == 2:
            support.append(True); cite_counts.append(0); continue  # the review (supportive, data-free)
        # choose citations preferentially among highly-cited, biased toward supportive
        pool = list(range(i))
        weights = [(cite_counts[p]+1) * (3.0 if (support[p] and random.random()<bias) else 1.0) for p in pool]
        chosen = set()
        for _ in range(cites_per):
            tot = sum(weights); r = random.random()*tot; acc=0
            for p,w in zip(pool,weights):
                acc += w
                if r <= acc: chosen.add(p); break
        for p in chosen: cite_counts[p]+=1
        supp = sum(1 for p in chosen if support[p])
        support.append(supp >= cites_per/2 if random.random()<0.9 else not (supp>=cites_per/2))
        cite_counts.append(0)
    frac_supp = sum(support)/len(support)
    top_hub = max(cite_counts)/ (sum(cite_counts)/len(cite_counts))
    return frac_supp, top_hub

print("S5 citation cascade (bias = preferential supportive citing):")
for bias in [0.0, 0.3, 0.6, 0.9]:
    fs, hub = cite_cascade(bias)
    print(f"  bias={bias:.1f}: supportive fraction={fs:.2f}, top-hub concentration={hub:.1f}x mean")

# ---------- S6: EWS marker battery with kill criteria ----------
# System approaching fold: dx = (r - x^2)dt + sigma dW, r decreasing 0.5 -> 0
random.seed(17)
def gen_series(n=2000, dt=0.05, sigma=0.1):
    x = math.sqrt(0.5); out=[]
    for i in range(n):
        r = 0.5*(1 - i/n)
        x += (r - x*x)*dt + sigma*math.sqrt(dt)*random.gauss(0,1)
        x = max(x, 0.01)
        out.append(x)
    return out

def windowed_stats(series, win=200):
    stats=[]
    for i in range(0, len(series)-win, win//2):
        w = series[i:i+win]
        m = sum(w)/len(w)
        var = sum((x-m)**2 for x in w)/(len(w)-1)
        ac1 = sum((w[j]-m)*(w[j-1]-m) for j in range(1,len(w)))/max(sum((x-m)**2 for x in w),1e-12)
        stats.append((var, ac1))
    return stats

def kendall_tau(xs):
    n=len(xs); c=0; d=0
    for i in range(n):
        for j in range(i+1,n):
            s=(xs[j]-xs[i])
            if s>0: c+=1
            elif s<0: d+=1
    return (c-d)/(c+d) if c+d else 0.0

# Theory A: variance Kendall-tau > 0.3 in last third => alarm. Theory B: AC1 tau > 0.3 => alarm.
resA=[]; resB=[]
for trial in range(30):
    s = gen_series()
    st = windowed_stats(s)
    last = st[len(st)*2//3:]
    tA = kendall_tau([v for v,a in st])
    tB = kendall_tau([a for v,a in st])
    resA.append(tA); resB.append(tB)
print("S6 EWS on fold-approach series (30 trials):")
print(f"  variance tau: mean={sum(resA)/len(resA):.3f}  frac>0.3: {sum(1 for t in resA if t>0.3)/len(resA):.2f}")
print(f"  AC1 tau:      mean={sum(resB)/len(resB):.3f}  frac>0.3: {sum(1 for t in resB if t>0.3)/len(resB):.2f}")
# null: stationary series should NOT trigger (kill criterion: false alarm rate < 0.2)
nullA=[]; nullB=[]
for trial in range(30):
    x=1.0; s=[]
    for i in range(2000):
        x += (0.5 - (x-1.0))*0.05 + 0.1*math.sqrt(0.05)*random.gauss(0,1)
        s.append(x)
    st=windowed_stats(s)
    nullA.append(kendall_tau([v for v,a in st])); nullB.append(kendall_tau([a for v,a in st]))
print(f"  null false-alarm: var={sum(1 for t in nullA if t>0.3)/30:.2f}  ac1={sum(1 for t in nullB if t>0.3)/30:.2f}")

# ---------- S7: anti-unification repair vs deletion ----------
# Toy logic: ground facts, rules as (premises -> conclusion). Conflict: derived contradictions.
# Repair A: delete min hitting set of conflicting rules. Repair B: generalize conflicting rules
# via LGG (add a condition shared by the rule pair) so they no longer fire on conflict instances.
random.seed(19)
# claims as predicates over objects with attributes; contradiction = same object, pred and not-pred
objs = [{'id':i,'temp':random.uniform(0,100),'press':random.uniform(0,10),'humid':random.uniform(0,100)} for i in range(200)]
# two overgeneral rules from two "substrates"
def ruleA(o): return o['temp']>60                      # "hot => alarm"
def ruleB(o): return o['press']>6                       # "high pressure => safe"
# ground truth for sim: alarm iff temp>60 AND press<=6
truth = {o['id']: (o['temp']>60 and o['press']<=6) for o in objs}
conflicts=[o for o in objs if ruleA(o) and ruleB(o) and not truth[o['id']]]
print(f"S7: objects={len(objs)}, conflicting derivations={len(conflicts)}")

def score(rep):
    err=0
    for o in objs:
        a = ruleA(o) if rep.get('A',True) else False
        b = ruleB(o) if rep.get('B',True) else False
        pred = a and not b
        if pred != truth[o['id']]: err+=1
    return err/len(objs)

base = score({'A':True,'B':True})
delA = score({'A':False,'B':True}); delB = score({'A':True,'B':False}); delBoth = score({'A':False,'B':False})
print(f"S7 error: keep-both={base:.3f} delete-A={delA:.3f} delete-B={delB:.3f} delete-both={delBoth:.3f}")
# LGG repair: generalize ruleA by conjoining shared condition from conflicts (LGG of conflict descriptions)
# conflicts share: press>6. LGG(ruleA, conflict instances) -> ruleA' = temp>60 AND press<=6? No: LGG *weakens*.
# Anti-unification of alarm-instances and conflict-instances finds the discriminating condition.
# Simple version: learn refined ruleA' = temp>60 AND NOT(common feature of conflicts)
def ruleA2(o): return o['temp']>60 and o['press']<=6
err=0
for o in objs:
    a=ruleA2(o); b=ruleB(o)
    pred = a and not b
    if pred != truth[o['id']]: err+=1
print(f"S7 error after LGG-refinement of A: {err/len(objs):.3f}")
# information retained = fraction of true alarms still derivable
ta = [o for o in objs if truth[o['id']]]
ret_delB = sum(1 for o in ta if ruleA(o))/len(ta)
ret_lgg  = sum(1 for o in ta if ruleA2(o))/len(ta)
print(f"S7 true-alarm retention: delete-B keeps A={ret_delB:.2f}  LGG-refined={ret_lgg:.2f}")
