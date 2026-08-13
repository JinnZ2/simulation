# The shape IS the dynamical system: octahedron with one bistable strut (buckling element).
# Strut energy E(l) = a*(l-l1)^2*(l-l2)^2 -> two stable lengths l1 (short) and l2 (long).
# External compression ramps up; at a critical compression the short-well state snaps.
# Mechanical critical slowing down: probe = small impulse every K steps, measure recovery
# time of the strut length; CSD predicts recovery time & fluctuation variance rise BEFORE snap.
import math, random

V0 = [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]
edges = [(i,j) for i in range(6) for j in range(i+1,6)
         if abs(sum(a*b for a,b in zip(V0[i],V0[j])))<0.5]
edge_index = {e:k for k,e in enumerate(edges)}
BI = edge_index[(0,2)]           # bistable strut
D0 = math.sqrt(2.0)

# bistable strut: stable at l1=1.2, l2=1.8; quartic energy, force = -dE/dl
L1, L2, AA = 1.2, 1.8, 1.2
def strut_force(l):
    # dE/dl = 2a(l-l1)(l-l2)(2l-l1-l2); stable equilibria at l1,l2
    return -2*AA*(l-L1)*(l-L2)*(2*l-L1-L2)   # force along strut (positive = extend)

def relax(V, comp, iters, rng=None, kick=None):
    # comp: external compression scale on all OTHER edges (shorter rest lengths)
    V=[list(v) for v in V]
    if kick is not None:
        V[kick[0]][kick[1]] += kick[2]
    for _ in range(iters):
        G=[[0.0]*3 for _ in range(6)]
        for k,(i,j) in enumerate(edges):
            d=[V[i][a]-V[j][a] for a in range(3)]
            l=math.sqrt(sum(x*x for x in d))+1e-12
            if k==BI:
                f=strut_force(l)/l
            else:
                f=(l-D0*(1-comp))/l   # normal spring toward compressed rest length
            for a in range(3):
                G[i][a]+=f*d[a]; G[j][a]-=f*d[a]
        for i in range(6):
            for a in range(3): V[i][a]-=0.05*G[i][a]
    return V

def strut_len(V):
    i,j=edges[BI]
    return math.sqrt(sum((V[i][a]-V[j][a])**2 for a in range(3)))

# 1) map the snap: ramp compression, strut starts LONG (1.8), snaps to short
rng=random.Random(1)
Vstart=[list(v) for v in V0]
i,j=edges[BI]
d=[Vstart[i][a]-Vstart[j][a] for a in range(3)]
lcur=math.sqrt(sum(x*x for x in d))
scale=1.8/lcur
Vstart[j]=[Vstart[i][a]-d[a]*scale for a in range(3)]
V=relax(Vstart,0.0,300)
snaps=[]
for ci in range(0,180):
    comp=ci*0.005
    V=relax(V,comp,150)
    l=strut_len(V)
    if l<1.45:
        snaps.append((comp,l)); break
print(f"snap compression ~ {snaps[0][0]:.3f} (strut {L2}->{snaps[0][1]:.2f})")
SNAP=snaps[0][0]

# 2) CSD probes: at compressions below snap, measure recovery time after impulse
def recovery_time(comp, kick_mag=0.05, max_t=600):
    V=relax(Vstart,comp,400)
    l0=strut_len(V)
    Vk=relax(V,comp,1,kick=(0,0,kick_mag))
    lk=strut_len(Vk)
    dev0=abs(lk-l0)
    for t in range(max_t//10):
        Vk=relax(Vk,comp,10)
        if abs(strut_len(Vk)-l0) < 0.05*dev0:
            return t*10, l0
    return max_t, l0

print("\ncompression | rest length | recovery time (CSD signature)")
comps=[c*SNAP/8 for c in range(8)]
recs=[]
for comp in comps:
    rt,l0=recovery_time(comp)
    recs.append((comp,l0,rt))
    print(f"  {comp:.3f} ({comp/SNAP:.0%} of snap) | {l0:.3f} | {rt}")

# 3) fluctuation variance of strut length under thermal-ish noise, vs compression
print("\ncompression | strut-length fluctuation variance (noisy relaxation)")
for comp in comps:
    rng=random.Random(7)
    V=relax(Vstart,comp,400)
    ls=[]
    for s in range(40):
        Vk=relax(V,comp,15,kick=(rng.randrange(6),rng.randrange(3),rng.gauss(0,0.02)))
        ls.append(strut_len(Vk))
    m=sum(ls)/len(ls); var=sum((x-m)**2 for x in ls)/len(ls)
    print(f"  {comp:.3f} ({comp/SNAP:.0%}) | var={var:.6f}")
