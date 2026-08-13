# What does the snap REPORT? Information content of a snap-through event.
# Double well E(x) = a(x-1.2)^2 (x-1.8)^2, damped oscillator.
# Q1: does post-snap ringdown reveal the LANDING state's stiffness? (self-reporting event)
# Q2: does the flip direction (up vs down load) encode traversal history? (hysteresis = memory)
# Q3: how many bits does a snap transmit about where in the load cycle it happened?
import numpy as np

a = 1.0
def E(x): return a*(x-1.2)**2*(x-1.8)**2
def F(x, h=1e-5): return -(E(x+h)-E(x-h))/(2*h)

def stiffness(c):
    return 2*a*((c-1.8)**2 + 4*(c-1.2)*(c-1.8) + (c-1.2)**2)

def simulate(x0, v0, load, dt=0.01, T=300.0, gamma=0.05):
    """well centers shift with load: effective wells at 1.2+load and 1.8+load (toy)."""
    x, v = x0, v0
    traj = []
    for _ in range(int(T/dt)):
        v += dt*(F(x - load) - gamma*v)
        x += dt*v
        traj.append(x)
    return np.array(traj)

def ringdown_freq(traj, dt=0.01, tail_frac=0.5):
    seg = traj[int(len(traj)*tail_frac):]
    seg = seg - seg.mean()
    sp = np.abs(np.fft.rfft(seg)); fr = np.fft.rfftfreq(len(seg), dt)
    return fr[np.argmax(sp[1:])+1]

# --- Q1: snaps at different loads -> ringdown frequency reads out landing stiffness ---
print("Q1: post-snap ringdown frequency vs load (landing-state self-report)")
print("load   true_k(landing)   ringdown_freq   implied_k  (k = (2*pi*f)^2, unit mass)")
for load in [0.0, 0.05, 0.10, 0.15, 0.20]:
    # start compressed (short well side), release -> snap to long well
    tr = simulate(1.2+load, 0.0, load, T=300)
    f = ringdown_freq(tr)
    k_true = stiffness(1.8)   # lands at long well (load-shifted)
    k_impl = (2*np.pi*f)**2
    print(f"{load:4.2f}   {k_true:8.3f}        {f:7.3f} Hz     {k_impl:7.3f}")

# --- Q2: hysteresis direction bit ---
# approaching snap from compression vs tension leaves different landing signatures:
print("\nQ2: direction memory — snap-from-compression vs snap-from-tension landing amplitude")
for name, x0, load in [("from-compression", 1.2, 0.0), ("from-tension", 1.8, 0.0)]:
    tr = simulate(x0+ (0.3 if x0<1.5 else -0.3), 0.0, load, T=200)
    amp = np.abs(tr[int(len(tr)*0.7):] - (1.8 if x0<1.5 else 1.2)).max()
    print(f"  {name}: post-snap max amplitude {amp:.3f} (distinct => 1 bit of history)")

# --- Q3: bits per snap about load, using ringdown frequency as decoder ---
print("\nQ3: mutual information load -> ringdown frequency (snapped trajectories)")
loads = np.linspace(0.0, 0.25, 11)
obs = []
for L in loads:
    for rep in range(8):
        tr = simulate(1.2+L, 0.05*np.random.randn(), L, T=250)
        obs.append((L, ringdown_freq(tr) + 0.002*np.random.randn()))  # sensor noise
obs = np.array(obs)
# discretize: 5 load bins x 5 freq bins, empirical MI
def mutual_info(x, y, bins=5):
    H = lambda p: -np.sum(p[p>0]*np.log2(p[p>0]))
    cx = np.digitize(x, np.quantile(x, np.linspace(0,1,bins+1)[1:-1]))
    cy = np.digitize(y, np.quantile(y, np.linspace(0,1,bins+1)[1:-1]))
    n = len(x)
    px = np.bincount(cx)/n; py = np.bincount(cy)/n
    pxy = np.zeros((bins, bins))
    for i in range(n): pxy[cx[i], cy[i]] += 1
    pxy /= n
    return H(px) + H(py) - H(pxy.flatten())
mi = mutual_info(obs[:,0], obs[:,1])
print(f"  MI(load; ringdown) = {mi:.2f} bits  (max possible with 11 loads = {np.log2(11):.2f})")
print("  => a snap event is an ADC: it digitizes accumulated analog load into discrete report")
