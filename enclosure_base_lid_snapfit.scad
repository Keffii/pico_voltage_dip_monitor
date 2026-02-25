/*
  Base + Lid enclosure.
  - Banana plug holes: round, 10.2mm diameter.
  - Ear fine positions updated from Customizer.
  - OLED seating pocket sized and rotated correctly for 90 deg display rotation.
  - Enclosure widened to fit display legs.
  - Display located by pegs from lid interior.
  - Pico 2 STL reference model import (moveable in X/Y).
  - Base Pico standoffs: group offset + per-standoff XY offsets.
  - Lid top: 3 banana plug holes (same as front banana sockets).
  - Standoffs fused into the base floor (overlap) so they are one solid and always move with the base.
  - Lid top: engraved text strip near the 3 holes (same size as Blue/Yellow/Green and same depth).
  - Hidden 4-point snap-fit closure between base and lid with tool-release slots.
*/

$fn = 60;
EPS = 0.05;

use <1_27inch_rgb_oled_module_wrapper.scad>;

// -------------------- Show --------------------
// "base", "lid", "assembly", "print_layout"
part = "print_layout";
assembly_lid_gap = 0.0;  // visual Z-gap between base and lid in assembly view

// -------------------- Tolerances --------------------
cut_tol = 0.50;
lip_clear = 0.30;

// -------------------- Hidden snap-fit --------------------
snap_enabled = true;
snap_tab_mode = "4_side_center";
snap_tab_width = 7.0;
snap_tab_free_len = 6.5;
snap_tab_anchor_top = true;
snap_hook_proj = 0.8;
snap_hook_h = 1.4;
snap_hook_z_from_lid_bottom = 1.5;
snap_relief_gap = 0.35;
snap_window_depth = 1.2;
snap_window_clear = 0.30;
snap_release_slot_enabled = false;
snap_release_slot_xy = [1.2, 6.0];

// -------------------- Pico-ish board defaults --------------------
pico_len = 51.0;
pico_w   = 21.0;

pico_hole_dx = 48.26;
pico_hole_dy = 17.78;

standoff_h = 4.0;
standoff_od = 4;
standoff_hole_d = 2.2;

// Make standoffs actually fuse into the base floor (mm)
standoff_floor_overlap = 0.6;   // 0.3 to 1.0 typical

pico_clear_x = 4.0;
pico_clear_y = 8.0;

// ==================== PICO PLACEMENT KNOBS ====================
pico_place_xy = [0, 0];   // [x, y] in mm. +x right, +y back

// Fine tune each standoff individually (added on top of pico_place_xy)
st0_xy = [-2.4, 11.5];  // standoff 0 = pico_holes()[0]
st1_xy = [-3.7, 11.5];  // standoff 1 = pico_holes()[1]
st2_xy = [-3.7,  5.5];  // standoff 2 = pico_holes()[2]
st3_xy = [-2.4,  5.5];  // standoff 3 = pico_holes()[3]

// Visual-only alignment for the imported Pico STL
pico_model_trim_xy = [0, 0];   // [x, y] in mm
pico_model_move_z  = 0;        // z trim if needed (mm)

// -------------------- Enclosure size adjustment --------------------
enclosure_extra_len = 0;
enclosure_extra_w   = 17;
enclosure_extra_h_base = 0;

// -------------------- Enclosure --------------------
wall = 2.0;
bottom = 2.0;

base_inner_h = 18.0 + enclosure_extra_h_base;
corner_r = 3.0;

inner_len = (pico_len + 2*pico_clear_x) + enclosure_extra_len;
inner_w   = (pico_w   + 2*pico_clear_y) + enclosure_extra_w;

outer_len = inner_len + 2*wall;
outer_w   = inner_w   + 2*wall;

base_h = bottom + base_inner_h;

// -------------------- Lid sizing --------------------
lid_outer_extra_xy = [0, 0];
lid_extra_z = 0;

lid_top_th  = 2.0 + lid_extra_z;
lid_skirt_h = 8.0 + lid_extra_z;
lid_h = lid_top_th + lid_skirt_h;

lip_h = 4.0 + lid_extra_z;
lip_wall = 1.6;

lid_outer_len = outer_len + lid_outer_extra_xy[0];
lid_outer_w   = outer_w   + lid_outer_extra_xy[1];

// -------------------- Display cutout on lid top --------------------
lid_display_cut_enabled = true;
lid_display_cut_w = 34.0;
lid_display_cut_h = 28.0;
lid_display_cut_offset_x = 0;
lid_display_cut_offset_y = 0;
lid_display_cut_corner_r = 1.5;
lid_display_cut_rotate = 0;

// -------------------- Display mount pegs --------------------
lid_display_mount_enabled  = true;
lid_display_mount_d        = 2.7;   // peg diameter
lid_display_mount_peg_h    = 3.0;   // peg height

// -------------------- Per-peg XY fine-tune --------------------
peg0_x = 0;  peg0_y = 0;
peg1_x = 0;  peg1_y = 0;
peg2_x = 0;  peg2_y = 0;
peg3_x = 0;  peg3_y = 0;

// Legacy aliases
mount_hole0_x = peg0_x;  mount_hole0_y = peg0_y;
mount_hole1_x = peg1_x;  mount_hole1_y = peg1_y;
mount_hole2_x = peg2_x;  mount_hole2_y = peg2_y;
mount_hole3_x = peg3_x;  mount_hole3_y = peg3_y;

// -------------------- USB cutout --------------------
usb_wall = "left";
usb_cut_xy  = [9.0, 5.0];
usb_cut_pos = [outer_w*0.50, 10.0];

// -------------------- Front ports (banana sockets) --------------------
ports_wall = "front";
ports_z = 14.0;
ports_center_x = outer_len * 0.50;
port_center_pitch = 14.0;

// Your banana socket panel hole diameter (keep at 6.0 if using panel sockets)
banana_panel_hole_d = 6.0;

// -------------------- Lid top: 3 banana plug holes --------------------
lid_top_ports_enabled = true;
lid_top_banana_hole_d = banana_panel_hole_d;
lid_top_banana_pitch = port_center_pitch;
lid_top_banana_center_xy = [lid_outer_len/2 - port_center_pitch, 16];
lid_top_banana_offset_xy = [0, 21];
lid_top_banana_row_rotate = 90;

// -------------------- OLED placement --------------------
lcd_center_xy = [outer_len/2, outer_w/2];

show_oled_model = true;
oled_stl_path = "1_27inch_rgb_oled_module_asm.stl";
oled_model_scale = 1.0;

oled_move = [0, -17, 0];
oled_rot  = [0, 0, -90];

// -------------------- Pico 2 STL reference model --------------------
show_pico_model = true;
pico_stl_path = "pico2.stl";
pico_model_scale = 1.0;
pico_model_rot = [0, 0, 0];

// -------------------- Print layout display position adjustment --------------------
print_layout_display_offset = [0, 0, 0];
oled_on_lid_z_offset = 0.2;

// -------------------- OLED ear hole pattern --------------------
oled_hole_dx = 36.0;
oled_hole_dy = 23.0;
oled_hole_center_offset = [0, 0];

// Updated from Customizer
ear0_fine = [12.0,  18.0];
ear1_fine = [37.0,  54.0];
ear2_fine = [14.0,  16.0];
ear3_fine = [-11.0, -20.0];

// -------------------- Standoffs (disabled) --------------------
lid_oled_standoffs_enabled = false;
lid_oled_ear_clear_d = 2.7;
lid_oled_standoff_od = 9.0;
lid_oled_standoff_h  = 3.0;
lid_oled_standoff_pilot_d = 2.8;

// -------------------- Bridge settings --------------------
lid_oled_pair_bridges_enabled = false;
lid_oled_bridge_w = 6.0;

// -------------------- OLED seating pocket --------------------
lid_oled_pocket_enabled   = false;
lid_oled_pocket_xy        = [19.9, 26.3];
lid_oled_pocket_depth     = 1.5;
lid_oled_pocket_corner_r  = 1.0;
lid_oled_pocket_offset_xy = [0, 8];

// -------------------- Cable slot through lid --------------------
lid_cable_cut_enabled    = false;
lid_cable_cut_xy         = [12, 5];
lid_cable_cut_offset_xy  = [0, -2];
lid_cable_cut_corner_r   = 1.0;

// -------------------- Big opening (disabled) --------------------
lid_big_open_enabled = false;

// -------------------- Button hole (disabled) --------------------
lid_button_enabled = false;
lid_button_hole_d = 10.2;
lid_button_offset_xy = [-10, +18];

// -------------------- Base feet --------------------
feet_enabled = true;
feet_od = 10.0;
feet_h  = 2.5;
feet_hole_d = 3.4;
feet_spacing_x = 40.0;
feet_spacing_y = 30.0;

// ==================== HELPERS ====================

module rounded_box(size_xyz, r) {
  x=size_xyz[0]; y=size_xyz[1]; z=size_xyz[2];
  rr = min(r, min(x,y)/2);
  hull() {
    for (cx=[rr, x-rr])
      for (cy=[rr, y-rr])
        translate([cx, cy, 0]) cylinder(h=z, r=rr);
  }
}

module hollow_rounded_box_bottom(outer_xyz, wall_th, r, bottom_th=0) {
  difference() {
    rounded_box(outer_xyz, r);
    translate([wall_th, wall_th, bottom_th - EPS])
      rounded_box(
        [outer_xyz[0]-2*wall_th, outer_xyz[1]-2*wall_th, outer_xyz[2]-bottom_th + 2*EPS],
        max(r-wall_th, 0.8)
      );
  }
}

module hollow_rounded_box_top(outer_xyz, wall_th, r, top_th=2) {
  difference() {
    rounded_box(outer_xyz, r);
    translate([wall_th, wall_th, -EPS])
      rounded_box(
        [outer_xyz[0]-2*wall_th, outer_xyz[1]-2*wall_th, outer_xyz[2]-top_th + EPS],
        max(r-wall_th, 0.8)
      );
  }
}

function pico_hole_off_x() = (pico_len - pico_hole_dx)/2;
function pico_hole_off_y() = (pico_w   - pico_hole_dy)/2;

function pico_holes() =
[
  [pico_hole_off_x(),              pico_hole_off_y()              ],
  [pico_hole_off_x()+pico_hole_dx, pico_hole_off_y()              ],
  [pico_hole_off_x()+pico_hole_dx, pico_hole_off_y()+pico_hole_dy ],
  [pico_hole_off_x(),              pico_hole_off_y()+pico_hole_dy ]
];

module wall_cutout(which, pos, size, depth = 0) {
  w = size[0] + cut_tol;
  h = size[1] + cut_tol;
  d_auto =
    (which == "front" || which == "back") ? (outer_w + 4) :
    (which == "left"  || which == "right") ? (outer_len + 4) :
    (wall + 2);
  d = ((depth <= 0) ? d_auto : depth) + 2*EPS;

  if (which == "front")
    translate([pos[0], wall/2, pos[1]]) cube([w, d, h], center=true);
  if (which == "back")
    translate([pos[0], outer_w - wall/2, pos[1]]) cube([w, d, h], center=true);
  if (which == "left")
    translate([wall/2, pos[0], pos[1]]) cube([d, w, h], center=true);
  if (which == "right")
    translate([outer_len - wall/2, pos[0], pos[1]]) cube([d, w, h], center=true);
}

module banana_hole(x, z) {
  translate([x, -EPS, z])
    rotate([-90, 0, 0])
      cylinder(h = wall + 2*EPS, d = banana_panel_hole_d, $fn = 60);
}

function rot2d(p, a) = [p[0]*cos(a) - p[1]*sin(a), p[0]*sin(a) + p[1]*cos(a)];

function oled_hole_points(dx, dy) =
[
  [-dx/2, -dy/2],
  [ dx/2, -dy/2],
  [ dx/2,  dy/2],
  [-dx/2,  dy/2]
];

function ear_fine(i) =
  (i==0) ? ear0_fine :
  (i==1) ? ear1_fine :
  (i==2) ? ear2_fine :
           ear3_fine;

function oled_ear_world_xy(i) =
  let(
    p0 = oled_hole_points(oled_hole_dx, oled_hole_dy)[i],
    p1 = [p0[0] + oled_hole_center_offset[0], p0[1] + oled_hole_center_offset[1]],
    pr = rot2d(p1, oled_rot[2]),
    ef = ear_fine(i)
  )
  [ lcd_center_xy[0] + oled_move[0] + pr[0] + ef[0],
    lcd_center_xy[1] + oled_move[1] + pr[1] + ef[1] ];

function oled_center_world_xy() =
  [ lcd_center_xy[0] + oled_move[0],
    lcd_center_xy[1] + oled_move[1] ];

module rounded_rect_cut_xy(size_xy, r, h) {
  sx = size_xy[0];
  sy = size_xy[1];
  rr = max(0.01, min(r, min(sx,sy)/2));
  hull() {
    for (ix=[-1,1])
      for (iy=[-1,1])
        translate([ix*(sx/2-rr), iy*(sy/2-rr), 0])
          cylinder(h=h, r=rr, center=true);
  }
}

// ==================== SNAP-FIT HELPERS ====================
function snap_side_positions(len_val, wid_val, inset) =
[
  ["front", len_val/2, inset],
  ["back",  len_val/2, wid_val - inset],
  ["left",  inset, wid_val/2],
  ["right", len_val - inset, wid_val/2]
];

function snap_fit_clear() = min(0.12, max(0.05, snap_window_clear*0.4));
function snap_lug_t() = min(wall - 0.30, max(0.90, snap_window_depth));
function snap_rim_inset() = wall - snap_lug_t()/2;

function snap_tab_positions() =
  (snap_tab_mode == "4_side_center")
    ? snap_side_positions(lid_outer_len, lid_outer_w, snap_rim_inset())
    : [];

function base_snap_window_positions() =
  (snap_tab_mode == "4_side_center")
    ? snap_side_positions(outer_len, outer_w, snap_rim_inset())
    : [];

module snap_side_frame(side, px, py) {
  if (side == "front") translate([px, py, 0]) children();
  if (side == "back")  translate([px, py, 0]) rotate([0, 0, 180]) children();
  if (side == "left")  translate([px, py, 0]) rotate([0, 0, -90]) children();
  if (side == "right") translate([px, py, 0]) rotate([0, 0, 90]) children();
}

// Keep lid union hook path as a no-op: this interlock uses base lugs + lid sockets.
module lid_snap_tabs() {}

module base_snap_lugs() {
  if (snap_enabled) {
    lug_t = snap_lug_t();
    lug_h = snap_hook_h;

    for (p = base_snap_window_positions()) {
      side = p[0];
      px = p[1];
      py = p[2];

      snap_side_frame(side, px, py)
        translate([-snap_tab_width/2, -lug_t/2, base_h - EPS])
          cube([snap_tab_width, lug_t, lug_h + EPS]);
    }
  }
}

module lid_snap_relief_cuts() {
  if (snap_enabled) {
    fit = snap_fit_clear();
    lug_t = snap_lug_t();
    sock_w = snap_tab_width + 2*fit;
    sock_t = lug_t + 2*fit;
    sock_h = snap_hook_h + fit;

    for (p = snap_tab_positions()) {
      side = p[0];
      px = p[1];
      py = p[2];

      snap_side_frame(side, px, py)
        translate([-sock_w/2, -sock_t/2, -EPS])
          cube([sock_w, sock_t, sock_h + 2*EPS]);
    }
  }
}

module lid_snap_release_slots_cut() {
  if (snap_enabled && snap_release_slot_enabled) {
    fit = snap_fit_clear();
    lug_t = snap_lug_t();
    slot_depth = max(lug_t + fit, snap_release_slot_xy[0]) + fit;
    slot_width = snap_release_slot_xy[1];
    slot_h = snap_hook_h + 0.8;

    for (p = snap_tab_positions()) {
      side = p[0];
      px = p[1];
      py = p[2];

      snap_side_frame(side, px, py)
        translate([-slot_width/2, -wall - EPS, -EPS])
          cube([slot_width, slot_depth, slot_h + 2*EPS]);
    }
  }
}

module base_snap_windows_cut() {
  // No base-side cutouts for this interlock style.
}

// ==================== PICO STANDOFFS (BASE) ====================
module pico_standoffs_in_base() {
  translate([wall + pico_clear_x + pico_place_xy[0],
             wall + pico_clear_y + pico_place_xy[1],
             bottom - standoff_floor_overlap])
    for (i = [0:3]) {
      q = pico_holes()[i];

      off =
        (i==0) ? st0_xy :
        (i==1) ? st1_xy :
        (i==2) ? st2_xy :
                 st3_xy;

      translate([q[0] + off[0], q[1] + off[1], 0])
        difference() {
          cylinder(h = standoff_h + standoff_floor_overlap, d = standoff_od);
          translate([0,0,-EPS])
            cylinder(h = standoff_h + standoff_floor_overlap + 2*EPS, d = standoff_hole_d);
        }
    }
}

// ==================== PICO STL MODEL ====================
module pico_model_in_base() {
  if (show_pico_model) {
    translate([
      wall + pico_clear_x + pico_place_xy[0] + pico_model_trim_xy[0],
      wall + pico_clear_y + pico_place_xy[1] + pico_model_trim_xy[1],
      bottom + pico_model_move_z
    ])
      rotate(pico_model_rot)
        scale(pico_model_scale)
          import(pico_stl_path, convexity=10);
  }
}

// ==================== BASE ====================

module front_four_banana_holes_cut() {
  centers = [
    ports_center_x - 1.5*port_center_pitch,
    ports_center_x - 0.5*port_center_pitch,
    ports_center_x + 0.5*port_center_pitch,
    ports_center_x + 1.5*port_center_pitch
  ];
  for (i = [0:3]) banana_hole(centers[i], ports_z);
}

module base_feet() {
  if (feet_enabled) {
    pts = [
      [outer_len/2 - feet_spacing_x/2,  outer_w/2 - feet_spacing_y/2],
      [outer_len/2 + feet_spacing_x/2,  outer_w/2 - feet_spacing_y/2],
      [outer_len/2 + feet_spacing_x/2,  outer_w/2 + feet_spacing_y/2],
      [outer_len/2 - feet_spacing_x/2,  outer_w/2 + feet_spacing_y/2]
    ];
    for (p = pts) {
      translate([p[0], p[1], -feet_h])
        difference() {
          cylinder(h=feet_h, d=feet_od);
          translate([0,0,-EPS]) cylinder(h=feet_h + 2*EPS, d=feet_hole_d);
        }
    }
  }
}

module base() {
  difference() {
    union() {
      hollow_rounded_box_bottom([outer_len, outer_w, base_h], wall, corner_r, bottom);
      pico_standoffs_in_base();
      base_feet();
      base_snap_lugs();
    }

    wall_cutout(usb_wall, usb_cut_pos, usb_cut_xy);
    front_four_banana_holes_cut();
    base_snap_windows_cut();
  }
}

// ==================== LID TOP BANANA HOLES ====================

module lid_top_three_banana_holes_cut() {
  if (lid_top_ports_enabled) {

    local_pts = [
      [-lid_top_banana_pitch, 0],
      [0, 0],
      [ lid_top_banana_pitch, 0]
    ];

    cx = lid_top_banana_center_xy[0] + lid_top_banana_offset_xy[0];
    cy = lid_top_banana_center_xy[1] + lid_top_banana_offset_xy[1];

    zc = lid_h - lid_top_th/2;
    hcut = lid_top_th + 4*EPS;

    translate([cx, cy, zc])
      rotate([0, 0, lid_top_banana_row_rotate])
        for (p = local_pts)
          translate([p[0], p[1], 0])
            cylinder(h=hcut, d=lid_top_banana_hole_d, center=true, $fn=80);
  }
}

// ==================== LID ====================

module oled_model_on_lid() {
  if (show_oled_model) {
    translate([lcd_center_xy[0], lcd_center_xy[1], base_h + assembly_lid_gap + lid_h + oled_on_lid_z_offset])
      translate(oled_move)
        rotate(oled_rot)
          oled_module(pos=[0,0,0], rot=[0,0,0], scale=oled_model_scale, stl_path=oled_stl_path);
  }
}

module lid() {
  hole_ox = [mount_hole0_x, mount_hole1_x, mount_hole2_x, mount_hole3_x];
  hole_oy = [mount_hole0_y, mount_hole1_y, mount_hole2_y, mount_hole3_y];

  difference() {
    union() {
      hollow_rounded_box_top([lid_outer_len, lid_outer_w, lid_h], wall, corner_r, lid_top_th);

      intersection() {
        hollow_rounded_box_top([lid_outer_len, lid_outer_w, lid_h], wall, corner_r, lid_top_th);
        translate([wall + lip_clear + lid_outer_extra_xy[0]/2,
                   wall + lip_clear + lid_outer_extra_xy[1]/2, 0])
          difference() {
            rounded_box(
              [outer_len - 2*(wall + lip_clear),
               outer_w   - 2*(wall + lip_clear),
               lip_h],
              max(corner_r - (wall + lip_clear), 0.8)
            );
            translate([lip_wall, lip_wall, -EPS])
              rounded_box(
                [outer_len - 2*(wall + lip_clear) - 2*lip_wall,
                 outer_w   - 2*(wall + lip_clear) - 2*lip_wall,
                 lip_h + 2*EPS],
                max(corner_r - (wall + lip_clear) - lip_wall, 0.8)
              );
          }
      }

      if (lid_display_mount_enabled) {
        for (i=[0:3]) {
          xy = oled_ear_world_xy(i);
          translate([xy[0] + hole_ox[i],
                     xy[1] + hole_oy[i],
                     lid_h - lid_top_th - lid_display_mount_peg_h])
            cylinder(h=lid_display_mount_peg_h, d=lid_display_mount_d);
        }
      }

      lid_snap_tabs();
    }

    // Lid top banana holes (3)
    lid_top_three_banana_holes_cut();

    // Hidden snap-fit relief and release features
    lid_snap_relief_cuts();
    lid_snap_release_slots_cut();

    if (lid_oled_pocket_enabled) {
      c = oled_center_world_xy();
      offr = rot2d(lid_oled_pocket_offset_xy, oled_rot[2]);
      translate([c[0] + offr[0], c[1] + offr[1], lid_h - lid_oled_pocket_depth]) {
        rotate([0, 0, oled_rot[2]])
          rounded_rect_cut_xy(
            lid_oled_pocket_xy,
            lid_oled_pocket_corner_r,
            lid_oled_pocket_depth + 2*EPS
          );
      }
    }

    if (lid_cable_cut_enabled) {
      c = oled_center_world_xy();
      offr = rot2d(lid_cable_cut_offset_xy, oled_rot[2]);
      zc = lid_h - lid_top_th/2;
      translate([c[0] + offr[0], c[1] + offr[1], zc])
        rotate([0, 0, oled_rot[2]])
          rounded_rect_cut_xy(
            lid_cable_cut_xy,
            lid_cable_cut_corner_r,
            lid_top_th + 4*EPS
          );
    }

    if (lid_button_enabled) {
      cx = lid_outer_len/2 + lid_button_offset_xy[0];
      cy = lid_outer_w/2   + lid_button_offset_xy[1];
      translate([cx, cy, lid_h - lid_top_th/2])
        cylinder(h=lid_top_th + 4*EPS, d=lid_button_hole_d, center=true);
    }

    if (lid_display_cut_enabled) {
      c = oled_center_world_xy();
      translate([c[0] + lid_display_cut_offset_x,
                 c[1] + lid_display_cut_offset_y,
                 lid_h - lid_top_th/2])
        rotate([0, 0, lid_display_cut_rotate])
          rounded_rect_cut_xy(
            [lid_display_cut_w, lid_display_cut_h],
            lid_display_cut_corner_r,
            lid_top_th + 4*EPS
          );
    }
  }
}

// ==================== PRINT LAYOUT ====================
module print_layout() {
  gap = 8;

  translate([0, 0, feet_enabled ? feet_h : 0]) base();
  pico_model_in_base();

  translate([outer_len + gap, 0, 0]) {
    lid();
    translate([print_layout_display_offset[0],
               print_layout_display_offset[1],
               -(base_h + assembly_lid_gap) + print_layout_display_offset[2]])
      oled_model_on_lid();
  }
}

// ==================== ASSEMBLY ====================
module assembly() {
  base();
  pico_model_in_base();
  translate([0, 0, base_h + assembly_lid_gap]) lid();
  oled_model_on_lid();
}

// -------------------- Render --------------------
if (part == "base")         base();
if (part == "lid")          lid();
if (part == "assembly")     assembly();
if (part == "print_layout") print_layout();
