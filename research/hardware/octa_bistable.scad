// Octahedral Shape Instrument v1 — bistable strut demonstrator
// CC0 — JinnZ2 ecosystem, GBCB-emitter-compatible OpenSCAD
// Print: 6 vertex nodes, 10 rigid struts (edges), 1 bistable strut (2 beams + apex cap),
// 1 compression screw collar. Assembly = octahedron; edge (0,2) = snap-through element.
//
// Geometry: octahedron vertices at (±s,0,0),(0,±s,0),(0,0,±s); 12 edges, length s*sqrt(2).
// The bistable strut is a von Mises truss: two inclined beams meeting at an apex;
// apex height h0 sets the two stable states (up/down snap-through).

s         = 40;    // octahedron half-size (mm)
node_r    = 6;     // vertex node radius
socket_d  = 3.2;   // strut socket diameter (3mm rod + clearance)
rod_d     = 3.0;   // rigid strut rod diameter
beam_w    = 6;     // snap-beam width (print direction = flat)
beam_t    = 0.8;   // snap-beam thickness — sets snap force; tune 0.6–1.2
beam_apex = 6;     // snap-beam apex height — sets bistability well separation
screw_d   = 5.2;   // M5 compression screw clearance

// ---------- derived ----------
edge_len = s*sqrt(2);
beam_len = edge_len/2 - node_r;   // each snap beam spans node->midpoint
beam_angle = atan(beam_apex / beam_len);

// ---------- vertex node: sphere with 4 orthogonal axial sockets ----------
module vertex_node() {
    difference() {
        sphere(r=node_r, $fn=32);
        // 4 sockets in the plane perpendicular to the node's own axis (octahedral
        // incidence = 4 edges, all at 90 deg to each other in that plane).
        // Mount node with its axis along the load direction, then rotate 45 deg
        // at assembly so sockets aim at the 4 neighboring vertices.
        for (a=[0:90:270])
            rotate([a,0,0]) translate([0,0,-node_r-1])
                cylinder(d=socket_d, h=node_r*2+2, $fn=24);
    }
}

// ---------- rigid strut ----------
module rigid_strut(len) {
    cylinder(d=rod_d, h=len, center=true, $fn=24);
}

// ---------- bistable strut: von Mises truss, printed flat, folds at apex ----------
module snap_beam() {
    // single inclined beam with root tab and apex tab
    L = beam_len/cos(beam_angle);
    difference() {
        union() {
            cube([beam_w, L, beam_t]);                        // beam body
            translate([0,-4,0]) cube([beam_w,4+2,beam_t]);    // root tab (into node socket)
            translate([0,L-2,0]) cube([beam_w,4,beam_t]);     // apex tab
        }
        // root pin hole
        translate([beam_w/2,-2,-1]) cylinder(d=2.2,h=beam_t+2,$fn=16);
    }
}
module apex_cap() {
    // joins the two beam apexes; central pad takes probe impulse (flick point / accelerometer mount)
    difference() {
        cube([beam_w+4, 10, 3], center=true);
        for (sg=[-1,1]) translate([sg*(beam_w/2),0,0])
            rotate([0,sg*beam_angle,0]) cube([2.4,10,5], center=true);
    }
}

// ---------- compression collar: opposite vertex (0,1 pair) gets screw drive ----------
module compression_collar() {
    difference() {
        cylinder(r=node_r+3, h=8, center=true, $fn=32);
        cylinder(d=screw_d, h=10, center=true, $fn=24);   // M5 nut trap or thread-forming
    }
}

// ---------- layout for printing ----------
translate([0,0,node_r])   vertex_node();                       // x6 (reuse plate)
translate([20,0,rod_d])   rigid_strut(edge_len-2*node_r);      // x10 (rotate to print vertically)
translate([40,0,beam_t])  snap_beam();                         // x2
translate([60,10,1.5])    apex_cap();                          // x1
translate([80,0,4])       compression_collar();                // x2 (both antipodal nodes of load axis)
