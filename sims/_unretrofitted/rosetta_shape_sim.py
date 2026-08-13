# Grounding sim: polyhedral shape as equation-complex container.
# Octahedron (6 vertices, 12 edges) as a spring network: each edge carries an
# equation residual r_e (imbalance of the assigned equation/constraint).
# Balanced state: all residuals zero -> vertices at reference positions.
# Imbalance: residuals act as edge-length demands -> shape relaxes to distorted config.
# Detection: Procrustes-style distance to reference. Drill-down: decompose distortion
# onto graph-Laplacian eigenmodes (symmetry-adapted failure modes) + per-edge residuals.
import math, random
random.seed(23)

# Octahedron reference vertices
V0 = [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]
edges = [(i,j) for i in range(6) for j in range(i+1,6)
         if abs(sum(a*b for a,b in zip(V0[i],V0[j])))<0.5]  # non-antipodal pairs
assert len(edges)==12, len(edges)

def relax(V, demands, iters=300, lr=0.05):
    # gradient descent on spring energy sum_e (|vi-vj| - d_e)^2
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

def procrustes_dist(V, Vref):
    # center both, RMSD (scale kept fixed -- shape includes size here)
    n=len(V)
    cV=[sum(v[a] for v in V)/n for a in range(3)]
    cR=[sum(v[a] for v in Vref)/n for a in range(3)]
    return math.sqrt(sum((V[i][a]-cV[a]-Vref[i][a]+cR[a])**2 for i in range(n) for a in range(3))/n)

def graph_laplacian_eigendecomp():
    # 6x6 Laplacian of octahedral graph; eigenvectors = symmetry-adapted modes
    L=[[0.0]*6 for _ in range(6)]
    for i,j in edges:
        L[i][i]+=1; L[j][j]+=1; L[i][j]-=1; L[j][i]-=1
    # Jacobi
    A=[row[:] for row in L]; V=[[1.0 if i==j else 0.0 for j in range(6)] for i in range(6)]
    for _ in range(200):
        off=0
        for p in range(6):
            for q in range(p+1,6):
                if abs(A[p][q])<1e-12: continue
                off+=abs(A[p][q])
                th=0.5*math.atan2(2*A[p][q],A[q][q]-A[p][p])
                c,s=math.cos(th),math.sin(th)
                for k in range(6):
                    apk,aqk=A[p][k],A[q][k]
                    A[p][k]=c*apk-s*aqk; A[q][k]=s*apk+c*aqk
                for k in range(6):
                    akp,akq=A[k][p],A[k][q]
                    A[k][p]=c*akp-s*akq; A[k][q]=s*akp+c*akq
                for k in range(6):
                    vkp,vkq=V[k][p],V[k][q]
                    V[k][p]=c*vkp-s*vkq; V[k][q]=s*vkp+c*vkq
    eig=sorted(((A[i][i],[V[j][i] for j in range(6)]) for i in range(6)), key=lambda x:x[0])
    return eig

d0 = math.sqrt(2.0)  # all reference edge lengths
print("reference edge length:", round(d0,4))

# Scenario: one "equation" (edge 0..1 pair) driven out of balance by residual delta
results=[]
for delta in [0.0,0.05,0.1,0.2,0.4]:
    demands=[d0]*12
    demands[0]=d0*(1+delta)  # edge (0,1) equation imbalanced
    V=relax(V0,demands)
    pd=procrustes_dist(V,V0)
    results.append((delta,pd))
    print(f"residual delta={delta:4.2f} -> Procrustes distortion={pd:.5f}")

# Drill-down: displacement field decomposed onto Laplacian eigenmodes
delta=0.2
demands=[d0]*12; demands[0]=d0*(1+delta)
V=relax(V0,demands)
cV=[sum(v[a] for v in V)/6 for a in range(3)]
cR=[sum(v[a] for v in V0)/6 for a in range(3)]
disp=[tuple((V[i][a]-cV[a])-(V0[i][a]-cR[a]) for a in range(3)) for i in range(6)]
mags=[math.sqrt(sum(x*x for x in d)) for d in disp]
print("\ndrill-down (delta=0.2): per-vertex displacement mags (vertices 0,1 carry the faulted edge):")
print("  ", [round(m,4) for m in mags])
eig=graph_laplacian_eigendecomp()
print("  Laplacian eigenvalues (0=rigid translation; higher=shape modes):")
print("  ", [round(l,3) for l,v in eig])
# project displacement (as 6-dim vector of mags) onto eigenmodes
print("  mode decomposition of displacement magnitude:")
for li,(l,vec) in enumerate(eig):
    amp=sum(mags[j]*vec[j] for j in range(6))
    print(f"    mode {li} (lambda={l:.3f}): amplitude {amp:+.4f}")
