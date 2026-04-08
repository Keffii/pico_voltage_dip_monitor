/*
  Base + Lid enclosure.
  - Banana plug holes: round, 10.2mm diameter.
  - Ear fine positions updated from Customizer.
  - OLED seating pocket sized and rotated correctly for 90 deg display rotation.
  - Enclosure widened to fit display legs.
  - OLED mount style selectable: pegs, ear clamps, rear capture, rails, shelf clips.
  - Pico 2 STL reference model import (moveable in X/Y/Z).
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
// "base", "base_front_fit_test", "base_left_fit_test", "lid", "lid_text", "assembly",
// "assembly_text", "print_layout", "print_layout_main"
part = is_undef(part_override) ? "print_layout_main" : part_override;
assembly_lid_gap = 0.0;  // visual Z-gap between base and lid in assembly view
base_front_fit_test_depth = 22.0;
base_left_fit_test_width = 16.0;
base_left_fit_test_depth = 26.0;

// -------------------- Tolerances --------------------
cut_tol = 0.50;
lip_clear = 0.30;

// -------------------- Hidden snap-fit --------------------
snap_enabled = true;
snap_tab_mode = "4_side_center";
snap_tab_width = 7.0;
snap_hook_h = 4.5;       // taller pegs/tabs for stronger snap engagement
snap_window_depth = 1.5; // deeper mating grooves in lid wall
snap_window_clear = 0.30;
snap_outer_wall_min = 0.9; // minimum outer wall left at snap grooves (increase to thicken wall there)
snap_release_slot_enabled = false;
snap_release_slot_xy = [1.2, 6.0];

// -------------------- Pico-ish board defaults --------------------
pico_len = 51.0;
pico_w   = 21.0;

pico_hole_dx = 48.26;
pico_hole_dy = 17.78;

standoff_h = 6.0;
standoff_od = 4;
standoff_hole_d = 2.2;

// Make standoffs actually fuse into the base floor (mm)
standoff_floor_overlap = 0.6;   // 0.3 to 1.0 typical

pico_clear_x = 4.0;
pico_clear_y = 8.0;

// ==================== PICO PLACEMENT KNOBS ====================
pico_usb_wall_gap = 3.25;  // target gap from Pico board edge to the USB-side inner wall
pico_place_xy = [pico_usb_wall_gap - pico_clear_x, 0];   // [x, y] in mm. +x right, +y back

// Fine tune each standoff individually (added on top of pico_place_xy)
st0_xy = [-2.4, 11.5];  // standoff 0 = pico_holes()[0]
st1_xy = [-3.7, 11.5];  // standoff 1 = pico_holes()[1]
st2_xy = [-3.7,  5.5];  // standoff 2 = pico_holes()[2]
st3_xy = [-2.4,  5.5];  // standoff 3 = pico_holes()[3]

// Visual-only alignment for the imported Pico STL
pico_model_trim_xy = [0, 0];   // [x, y] in mm

// -------------------- Enclosure size adjustment --------------------
enclosure_extra_len = 0;
enclosure_extra_w   = 17;
enclosure_extra_h_base = 0;

// -------------------- Enclosure --------------------
wall = 4.0;
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
lid_display_cut_w = 30;
lid_display_cut_h = 23;
lid_display_cut_offset_x = -0.6;
lid_display_cut_offset_y = 1.7;
lid_display_cut_corner_r = 1.5;
lid_display_cut_rotate = 0; // extra rotation on top of oled_rot[2]

// -------------------- OLED display mount --------------------
// Select one of:
// "mega_boss_pegs", "ear_clamps", "rear_capture", "side_rails", "shelf_clips"
lid_oled_mount_style = is_undef(lid_oled_mount_style_override) ? "mega_boss_pegs" : lid_oled_mount_style_override;

// Mega-style boss pegs:
// full narrow peg shaft plus a separate wider support collar.
// If you're opening this main file directly, these are the easiest values to tweak.
mega_boss_peg_shaft_d = 1.7;
mega_boss_peg_shaft_h = 5;
mega_boss_peg_boss_d  = 4.6;
mega_boss_peg_boss_h  = 2;
mega_boss_peg_boss_drop = 0.0; // move only the bulky collar lower on the shaft

lid_oled_mount_body_xy = [34.0, 24.0];
lid_oled_mount_body_th = 4.0;
lid_oled_mount_offset_xy = [0, 0];
lid_oled_mount_side_clear = 0.45;
lid_oled_mount_bottom_clear = 0.30;
lid_oled_mount_top_clear = 0.30;
lid_oled_bottom_hook_w = 5.5;
lid_oled_bottom_hook_depth = 2.0;
lid_oled_bottom_hook_inset = 5.0;
lid_oled_side_locator_w = 1.4;
lid_oled_side_locator_span = 4.0;
lid_oled_side_locator_offset_y = -2.0;
lid_oled_top_latch_w = 8.0;
lid_oled_top_latch_len = 9.0;
lid_oled_top_latch_th = 1.4;
lid_oled_top_latch_gap = 0.8;
lid_oled_top_latch_anchor_len = 2.0;
lid_oled_top_latch_hook_depth = 1.2;
lid_oled_top_latch_hook_drop = 1.0;
lid_oled_top_latch_hook_overlap = 0.7;

lid_oled_rear_mount_enabled = (lid_oled_mount_style == "rear_capture");
lid_display_mount_enabled  = (lid_oled_mount_style == "mega_boss_pegs" ||
                              lid_oled_mount_style == "locator_pegs" ||
                              lid_oled_mount_style == "locator_pegs_heavy" ||
                              lid_oled_mount_style == "pin_bosses");
lid_display_mount_d        = is_undef(lid_display_mount_d_override)
                             ? (lid_oled_mount_style == "mega_boss_pegs" ? mega_boss_peg_shaft_d : 1.6)
                             : lid_display_mount_d_override;    // peg shaft diameter
lid_display_mount_d_scale  = is_undef(lid_display_mount_d_scale_override) ? 1.0 : lid_display_mount_d_scale_override;
lid_display_mount_peg_h    = is_undef(lid_display_mount_peg_h_override)
                             ? (lid_oled_mount_style == "mega_boss_pegs" ? mega_boss_peg_shaft_h : 5.0)
                             : lid_display_mount_peg_h_override;    // total peg height
lid_display_mount_offset_z = is_undef(lid_display_mount_offset_z_override) ? 0.0 : lid_display_mount_offset_z_override;    // shared Z trim for OLED supports
lid_display_mount_tip_h    = is_undef(lid_display_mount_tip_h_override)
                             ? (lid_oled_mount_style == "mega_boss_pegs" ? mega_boss_peg_shaft_h : lid_display_mount_peg_h)
                             : lid_display_mount_tip_h_override;
lid_display_mount_tip_d_scale = is_undef(lid_display_mount_tip_d_scale_override) ? 1.0 : lid_display_mount_tip_d_scale_override;
lid_display_mount_tip_taper = is_undef(lid_display_mount_tip_taper_override) ? 0.0 : lid_display_mount_tip_taper_override;
lid_display_mount_boss_enabled = is_undef(lid_display_mount_boss_enabled_override)
                                 ? (lid_oled_mount_style == "mega_boss_pegs" ||
                                    lid_oled_mount_style == "locator_pegs" ||
                                    lid_oled_mount_style == "locator_pegs_heavy" ||
                                    lid_oled_mount_style == "pin_bosses")
                                 : lid_display_mount_boss_enabled_override;
lid_display_mount_boss_h   = is_undef(lid_display_mount_boss_h_override)
                             ? (lid_oled_mount_style == "mega_boss_pegs" ? mega_boss_peg_boss_h : 1.8)
                             : lid_display_mount_boss_h_override;
lid_display_mount_boss_d   = is_undef(lid_display_mount_boss_d_override)
                             ? (lid_oled_mount_style == "mega_boss_pegs" ? mega_boss_peg_boss_d : 4.8)
                             : lid_display_mount_boss_d_override;
lid_display_mount_boss_taper = is_undef(lid_display_mount_boss_taper_override)
                               ? (lid_oled_mount_style == "mega_boss_pegs" ? 0.0 : 0.6)
                               : lid_display_mount_boss_taper_override;
lid_display_mount_pilot_enabled = is_undef(lid_display_mount_pilot_enabled_override)
                                  ? (lid_oled_mount_style == "pin_bosses")
                                  : lid_display_mount_pilot_enabled_override;
lid_display_mount_pilot_d  = is_undef(lid_display_mount_pilot_d_override) ? 1.2 : lid_display_mount_pilot_d_override;
lid_display_mount_pilot_h  = is_undef(lid_display_mount_pilot_h_override) ? max(1.6, lid_display_mount_boss_h + 1.2) : lid_display_mount_pilot_h_override;

// -------------------- OLED side-rail mount --------------------
lid_oled_side_rails_enabled      = (lid_oled_mount_style == "side_rails");
lid_oled_side_rail_th            = 1.8;
lid_oled_side_rail_span_extra    = 0.8;
lid_oled_side_rail_stop_w        = 5.0;
lid_oled_side_rail_stop_depth    = 1.8;
lid_oled_side_rail_latch_w       = 8.0;
lid_oled_side_rail_latch_len     = 5.5;
lid_oled_side_rail_latch_th      = 1.4;
lid_oled_side_rail_latch_gap     = 0.9;
lid_oled_side_rail_latch_anchor_len = 2.0;
lid_oled_side_rail_latch_hook_depth = 1.1;
lid_oled_side_rail_latch_hook_drop  = 0.9;
lid_oled_side_rail_latch_overlap    = 0.8;

// -------------------- OLED shelf-clip mount --------------------
lid_oled_shelf_clips_enabled     = (lid_oled_mount_style == "shelf_clips");
lid_oled_shelf_depth             = 2.2;
lid_oled_shelf_w                 = 18.0;
lid_oled_shelf_corner_w          = 5.2;
lid_oled_shelf_clip_w            = 6.0;
lid_oled_shelf_clip_len          = 4.8;
lid_oled_shelf_clip_th           = 1.5;
lid_oled_shelf_clip_gap          = 0.9;
lid_oled_shelf_clip_anchor_len   = 2.0;
lid_oled_shelf_clip_hook_depth   = 1.1;
lid_oled_shelf_clip_hook_drop    = 0.9;
lid_oled_shelf_clip_overlap      = 0.8;
lid_oled_shelf_clip_inset        = 4.6;
lid_oled_shelf_side_locator_w    = 1.4;
lid_oled_shelf_side_locator_span = 5.0;
lid_oled_shelf_side_locator_y    = -1.0;

// -------------------- OLED shelf + retainer bar mount (robust) --------------------
// PCB rests on a full-width shelf at one edge; a thick printed retainer bar sits
// flush over the opposite PCB edge and is held by two M2 self-tapping screws.
// This is the recommended robust mount: no cantilevers, no thin features.
lid_oled_shelf_bar_enabled       = (lid_oled_mount_style == "shelf_bar");
// Bottom shelf that the PCB lower edge rests on.
lid_oled_sbar_shelf_depth        = 3.0;   // how far the shelf ledge protrudes (PCB rests on this)
lid_oled_sbar_shelf_h            = 2.0;   // shelf ledge thickness (Z, printed flat = strong)
lid_oled_sbar_shelf_w            = 28.0;  // shelf ledge total width (wider than PCB for support)
// Side walls that constrain the PCB in X.
lid_oled_sbar_side_wall_th       = 2.5;   // side wall printed thickness
lid_oled_sbar_side_wall_h        = 3.5;   // side wall height from lid inner ceiling
lid_oled_sbar_pcb_side_clear     = 0.40;  // XY clearance each side around PCB
lid_oled_sbar_screw_d            = 1.9;   // screw pilot hole diameter (M2 self-tap)
lid_oled_sbar_screw_boss_d       = 5.0;   // boss OD around each screw hole
lid_oled_sbar_screw_boss_h       = 4.0;   // boss protrusion height from lid inner ceiling
// Retainer bar geometry (the separate printed crossbar part).
lid_oled_sbar_bar_w              = 22.0;  // retainer bar total width
lid_oled_sbar_bar_th             = 3.5;   // retainer bar body thickness (printed flat, robust)
lid_oled_sbar_bar_len            = 8.0;   // retainer bar body length (spans over top PCB edge)
lid_oled_sbar_bar_screw_d        = 2.3;   // clearance hole in bar for M2 screw body

// -------------------- OLED bezel + foam compression backer --------------------
// PCB sits against a broad front bezel ledge. A separate rear backer plate and
// thin foam pad compress the PCB gently into the bezel.
lid_oled_foam_backer_enabled      = (lid_oled_mount_style == "foam_backer");
lid_oled_fback_pcb_xy             = [34.0, 24.0];
lid_oled_fback_side_clear         = 0.40;
lid_oled_fback_bottom_clear       = 0.35;
lid_oled_fback_top_clear          = 0.35;
lid_oled_fback_side_wall_th       = 2.6;
lid_oled_fback_side_wall_h        = 3.2;
lid_oled_fback_bottom_shelf_depth = 2.4;
lid_oled_fback_bottom_shelf_h     = 2.0;
lid_oled_fback_top_stop_depth     = 2.0;
lid_oled_fback_top_stop_h         = 1.8;
lid_oled_fback_boss_pitch_y       = 18.0;
lid_oled_fback_boss_d             = 5.2;
lid_oled_fback_boss_h             = 4.2;
lid_oled_fback_screw_d            = 1.9;
lid_oled_fback_plate_xy           = [30.0, 20.0];
lid_oled_fback_plate_th           = 3.0;
lid_oled_fback_plate_screw_d      = 2.3;
lid_oled_fback_plate_window_xy    = [22.0, 14.0];

// -------------------- OLED channel frame mount (robust) --------------------
// PCB slides laterally into a 3-walled pocket channel printed into the lid interior.
// A separate removable end cap (4th wall) is retained by two M2 self-tapping screws.
// All four PCB edges are supported by wide flat walls. Zero stress concentrations.
lid_oled_channel_enabled         = (lid_oled_mount_style == "channel_frame");
lid_oled_chan_pcb_xy             = [34.0, 24.0]; // PCB footprint (W x H)
lid_oled_chan_pcb_th             = 1.6;           // PCB thickness
lid_oled_chan_pcb_clear_xy       = 0.40;          // clearance each side in X and Y
lid_oled_chan_pcb_clear_z        = 0.30;          // clearance above PCB face (toward lid top)
lid_oled_chan_wall_th            = 3.0;           // channel wall printed thickness
lid_oled_chan_endcap_screw_pitch = 14.0;          // M2 screw pitch for end cap
lid_oled_chan_endcap_screw_d     = 1.9;           // pilot hole M2
lid_oled_chan_endcap_boss_d      = 5.0;
lid_oled_chan_endcap_boss_h      = 4.0;
// End cap (separate printed piece) dimensions
lid_oled_chan_cap_w              = lid_oled_chan_pcb_xy[0] + 2*lid_oled_chan_wall_th;
lid_oled_chan_cap_th             = lid_oled_chan_wall_th;
lid_oled_chan_cap_h              = lid_oled_chan_pcb_th + lid_oled_chan_pcb_clear_z + 1.5;
lid_oled_chan_cap_screw_d        = 2.3;   // clearance through-hole in cap

// -------------------- OLED solid rails + keyhole crossbar (robust) --------------------
// Thick side rails (no cantilevers) constrain X entirely.
// PCB drops into the rails from above. A full-width printed crossbar with a keyhole
// slot locks the top edge — slid in sideways, captured flat against lid wall.
// No screws needed; easily serviceable by sliding the crossbar out.
lid_oled_solid_rails_enabled     = (lid_oled_mount_style == "solid_rails");
lid_oled_srail_th                = 2.5;   // rail wall thickness (printed upright, solid)
lid_oled_srail_pcb_clear         = 0.35;  // clearance between PCB edge and rail inner face
lid_oled_srail_h                 = 4.0;   // rail height (how deep the slot is)
lid_oled_srail_floor_depth       = 2.0;   // bottom floor/stop ledge depth
lid_oled_srail_floor_h           = 2.0;   // floor ledge thickness
lid_oled_srail_floor_w           = 10.0;  // width of each bottom stop ledge
// Crossbar geometry
lid_oled_srail_bar_slot_w        = 3.5;   // slot opening width in each rail (crossbar slides through)
lid_oled_srail_bar_slot_h        = 2.2;   // slot opening height (crossbar thickness + 0.3)
lid_oled_srail_bar_th            = 1.9;   // crossbar body thickness (fits in slot)
lid_oled_srail_bar_total_w       = lid_oled_mount_body_xy[0] + 2*lid_oled_srail_th + 6.0; // extends past both rails
lid_oled_srail_bar_body_w        = lid_oled_mount_body_xy[0] - 2.0; // active span over PCB
lid_oled_srail_bar_lug_w         = 4.0;   // keyhole head lug width (wider than slot opening)
lid_oled_srail_bar_lug_h         = 4.0;   // keyhole head lug height (locks crossbar from sliding back out)

// -------------------- Per-peg XYZ fine-tune (single source of truth) --------------------
peg_group_xy = [0, 1]; // shared [x,y] move for all 4 OLED pegs/standoffs
peg0_x = -13.2;    peg0_y = -17.1; peg0_z = 0;
peg1_x =  -13.4; peg1_y = -17.1;    peg1_z = 0;
peg2_x = -13.4; peg2_y = -17.1;  peg2_z = 0;
peg3_x = -13.2;  peg3_y = -17.1; peg3_z = 0;

// -------------------- USB cutout --------------------
usb_wall = "left";
usb_cut_xy  = [8.6, 4.2];
usb_cut_pos = [outer_w*0.50, 10.0];
usb_shell_groove_xy = [13.0, 8.5];
usb_shell_groove_depth = 3.2;
usb_shell_groove_offset_xy = [0.0, 0];  // [along wall, upward] bias shell relief above the plug opening

// -------------------- Front ports (banana sockets) --------------------
ports_z = 11.0;
ports_center_x = outer_len * 0.50;
port_center_pitch = 14.0;

// Front/base banana socket stepped opening.
// Outer/front opening stays at the current size; the inner pocket is smaller
// so the second nut is captured firmly instead of floating in a through-hole.
base_banana_outer_hole_af_nominal = 9.1;
base_banana_inner_nut_af_nominal = 6.4;
base_banana_inner_nut_clearance = 0.10;
base_banana_inner_nut_depth_nominal = wall * 0.5;
// -------------------- Lid top: 2 banana plug holes --------------------
lid_top_ports_enabled = true;
lid_top_banana_hole_d = 12.0; // lid only (independent of base banana_panel_hole_d)
// Spacing between neighboring holes (center-to-center) in local row coordinates.
// This is independent from row position.
lid_top_banana_pitch = 28.0;
// Row anchor position on lid (independent from spacing).
lid_top_banana_center_xy = [lid_outer_len/2, 16.5];
// Extra XY trim after center anchor. Keeps previous default placement (~X center -13).
lid_top_banana_offset_xy = [-13, 12];
// 0 = spacing spreads left/right (X). 90 = spacing spreads along Y.
lid_top_banana_row_rotate = 90;
// Hidden button mount for that same 2-hole row:
// top stays clean, hardware sits in underside pockets.
lid_top_hidden_mount_enabled = true;
lid_top_hidden_mount_shaft_d = 7.0;     // visible top hole for the threaded button body
lid_top_hidden_mount_bridge_d = 15.0;    // underside reinforcement around each hole
lid_top_hidden_mount_bridge_h = 3.2;     // extra clamping thickness under the lid skin
lid_top_hidden_mount_nut_af = 10.0;      // nut size across flats (measured 10 mm)
lid_top_hidden_mount_nut_depth = 2.0;
lid_top_hidden_mount_washer_d = 13.0;    // round washer / ring OD
lid_top_hidden_mount_washer_depth = 0.9;
lid_top_hidden_mount_clear = 0.05;
lid_top_hidden_mount_group_offset_xy = [0, 2]; // move bridge pad, through-holes, washer pockets, and hex pockets together
lid_top_hidden_mount_bridge_offset_xy = [0, 0]; // move bridge pad only; does not move holes/nut cuts
// Fine-tune the visible/captured hole cuts without moving the outer bridge pad.
// [left, right] in world XY after row placement/rotation.
lid_top_hidden_mount_cut0_offset_xy = [0, 0];
lid_top_hidden_mount_cut1_offset_xy = [0, 0];
// Per-hole HEX pocket fine tune only (does not move top through-hole or washer circle).
lid_top_hidden_mount_nut0_offset_xy = [0, 0];
lid_top_hidden_mount_nut1_offset_xy = [0, 0];

// -------------------- Lid top text (separate printable body) --------------------
lid_top_text_enabled = true;
lid_top_text_labels = ["Channel", "Toggle"];
lid_top_text_font = "Arial:style=Bold";
lid_top_text_size = 4.8;
lid_top_text_height = 0.8;
lid_top_text_pitch = 28.0;
lid_top_text_offset_xy = [-10, 0.0];
lid_top_text_offset_z = 0.0;
lid_top_text_rotate = -90;
lid_top_text_spacing = 1.0;
lid_top_text_hal = "center";
lid_top_text_val = "center";

// -------------------- OLED placement --------------------
lcd_center_xy = [outer_len/2, outer_w/2];

oled_model = true; // legacy simple toggle: true/false
show_oled_model = is_undef(show_oled_model_override) ? oled_model : show_oled_model_override;   // enabled for visualization
oled_stl_path = "1_27inch_rgb_oled_module_asm.stl";
oled_model_scale = 1.0;

oled_feature_move = [10, -1, 0]; // real geometry anchor: cutout/pegs/pockets follow this
oled_move = [-13, -16, -4];           // visual-only OLED STL move (does NOT move cutout/pegs)
oled_rot  = [0, 0, -90];
oled_model_move = [0, 0, 0];     // extra visual-only OLED STL offset

// -------------------- Pico 2 STL reference model --------------------
pico_model_enabled = false;
show_pico_model = is_undef(show_pico_model_override) ? pico_model_enabled : show_pico_model_override;  // enabled for visualization
pico_model_background = true;  // draw Pico STL as ghost reference so it doesn't visually "cut" standoffs
pico_stl_path = "pico2.stl";
pico_model_scale = 1.0;
pico_model_rot = [90, 0, 90];
pico_model_move_xy = [-4.5, -109];  // [x, y] mm offset for imported Pico model
pico_model_move_z  = -124;       // z mm offset for imported Pico model
pico_model_follow_standoffs_z = true; // keep reference model clear of posts when standoff_h changes

// -------------------- Print layout display position adjustment --------------------
print_layout_display_offset = [0, 0, 0];
print_layout_text_offset = [0, lid_outer_w + 10, 0];
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

// -------------------- OLED ear clamps --------------------
lid_oled_ear_clamps_enabled     = (lid_oled_mount_style == "ear_clamps");
lid_oled_ear_hole_d             = 2.7;
lid_oled_ear_clamp_intrusion    = 0.55;
lid_oled_ear_clamp_thickness    = 1.8;
lid_oled_ear_clamp_height       = 2.4;
lid_oled_ear_clamp_gap          = 1.2;
lid_oled_ear_clamp_lead_in      = 0.55;
lid_oled_ear_support_pad_d      = 7.2;
lid_oled_ear_support_pad_h      = 1.2;
lid_oled_ear_support_z          = 0.0;
lid_oled_ear_clamp_clearance    = 0.15;
ear0_clamp_rot = 0;
ear1_clamp_rot = 0;
ear2_clamp_rot = 0;
ear3_clamp_rot = 0;

// -------------------- Optional lid cuts --------------------
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
  // Default wall cut depth should only pass through the wall,
  // so interior features (like standoffs) are not unintentionally clipped.
  d_auto = wall + 2;
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


module usb_shell_groove_cut() {
  groove_w = usb_shell_groove_xy[0] + cut_tol;
  groove_h = usb_shell_groove_xy[1];
  groove_d = min(usb_shell_groove_depth, wall + EPS);
  groove_pos = [
    usb_cut_pos[0] + usb_shell_groove_offset_xy[0],
    usb_cut_pos[1] + usb_shell_groove_offset_xy[1]
  ];

  if (usb_wall == "left")
    translate([-EPS, groove_pos[0] - groove_w/2, groove_pos[1] - groove_h/2])
      cube([groove_d + EPS, groove_w, groove_h + EPS], center=false);
  if (usb_wall == "right")
    translate([outer_len - groove_d, groove_pos[0] - groove_w/2, groove_pos[1] - groove_h/2])
      cube([groove_d + EPS, groove_w, groove_h + EPS], center=false);
  if (usb_wall == "front")
    translate([groove_pos[0] - groove_w/2, -EPS, groove_pos[1] - groove_h/2])
      cube([groove_w, groove_d + EPS, groove_h + EPS], center=false);
  if (usb_wall == "back")
    translate([groove_pos[0] - groove_w/2, outer_w - groove_d, groove_pos[1] - groove_h/2])
      cube([groove_w, groove_d + EPS, groove_h + EPS], center=false);
}

module banana_hole(x, z) {
  outer_depth = base_banana_outer_cut_depth();
  inner_depth = base_banana_inner_pocket_depth();

  // Front-facing opening for the existing outer hardware.
  translate([x, -EPS, z])
    rotate([-90, 0, 0])
      rotate([0, 0, 30])
        cylinder(h = outer_depth + 2*EPS,
                 d = hex_circ_d(base_banana_outer_hole_af()),
                 $fn = 6);

  // Inner nut capture pocket sized tighter so the inner nut cannot float loose.
  translate([x, wall - inner_depth - EPS, z])
    rotate([-90, 0, 0])
      rotate([0, 0, 30])
        cylinder(h = inner_depth + 2*EPS,
                 d = hex_circ_d(base_banana_inner_pocket_af()),
                 $fn = 6);
}

function rot2d(p, a) = [p[0]*cos(a) - p[1]*sin(a), p[0]*sin(a) + p[1]*cos(a)];
function hex_circ_d(af) = af / cos(30);
function base_banana_outer_hole_af() = base_banana_outer_hole_af_nominal;
function base_banana_inner_pocket_af() = base_banana_inner_nut_af_nominal + base_banana_inner_nut_clearance;
function base_banana_inner_pocket_depth() = min(base_banana_inner_nut_depth_nominal, wall * 0.5);
function base_banana_outer_cut_depth() = wall - base_banana_inner_pocket_depth();

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
  [ lcd_center_xy[0] + oled_feature_move[0] + pr[0] + ef[0],
    lcd_center_xy[1] + oled_feature_move[1] + pr[1] + ef[1] ];

function oled_center_world_xy() =
  [ lcd_center_xy[0] + oled_feature_move[0],
    lcd_center_xy[1] + oled_feature_move[1] ];

function oled_mount_rot_z() = oled_rot[2] + lid_display_cut_rotate;

function oled_mount_center_world_xy() =
  let(
    c = oled_center_world_xy(),
    cut_off = rot2d([lid_display_cut_offset_x, lid_display_cut_offset_y], oled_rot[2]),
    mount_off = rot2d(lid_oled_mount_offset_xy, oled_mount_rot_z())
  )
  [c[0] + cut_off[0] + mount_off[0],
   c[1] + cut_off[1] + mount_off[1]];

function oled_mount_capture_z() =
  max(1.2, lid_oled_mount_body_th + lid_oled_mount_top_clear);

function ear_clamp_rot(i) =
  (i==0) ? ear0_clamp_rot :
  (i==1) ? ear1_clamp_rot :
  (i==2) ? ear2_clamp_rot :
           ear3_clamp_rot;

function oled_mount_world_xy(i, hole_ox, hole_oy) =
  let(xy = oled_ear_world_xy(i))
  [xy[0] + hole_ox[i], xy[1] + hole_oy[i]];

function oled_ear_clamp_axis_rot(i, hole_ox, hole_oy) =
  let(
    c = oled_center_world_xy(),
    xy = oled_mount_world_xy(i, hole_ox, hole_oy),
    v = [xy[0] - c[0], xy[1] - c[1]]
  )
  atan2(v[1], v[0]) + ear_clamp_rot(i);

module oled_ear_support_and_clamp(xy, z_top, rot_z=0) {
  hole_r = (lid_oled_ear_hole_d + lid_oled_ear_clamp_clearance) / 2;
  lobe_r = lid_oled_ear_clamp_thickness / 2;
  lobe_center = max(hole_r + lobe_r - lid_oled_ear_clamp_intrusion,
                    lobe_r + lid_oled_ear_clamp_gap/2);
  lobe_d1 = max(lid_oled_ear_clamp_thickness - 2*lid_oled_ear_clamp_lead_in,
                lid_oled_ear_clamp_thickness * 0.45);

  translate([xy[0], xy[1], z_top - lid_oled_ear_support_pad_h + lid_oled_ear_support_z])
    difference() {
      cylinder(h = lid_oled_ear_support_pad_h, d = lid_oled_ear_support_pad_d, $fn = 80);
      translate([0, 0, -EPS])
        cylinder(h = lid_oled_ear_support_pad_h + 2*EPS,
                 d = lid_oled_ear_hole_d + 2*lid_oled_ear_clamp_clearance,
                 $fn = 80);
    }

  translate([xy[0], xy[1], z_top + lid_oled_ear_support_z - lid_oled_ear_clamp_height])
    rotate([0, 0, rot_z])
      for (side = [-1, 1])
        translate([0, side * lobe_center, 0])
          cylinder(h = lid_oled_ear_clamp_height,
                   d1 = lobe_d1,
                   d2 = lid_oled_ear_clamp_thickness,
                   $fn = 60);
}

module oled_display_mount_clamps(hole_ox, hole_oy, hole_oz) {
  if (lid_oled_ear_clamps_enabled) {
    for (i = [0:3]) {
      xy = oled_mount_world_xy(i, hole_ox, hole_oy);
      z_top = lid_h - lid_top_th + lid_display_mount_offset_z + hole_oz[i];
      oled_ear_support_and_clamp(xy, z_top, oled_ear_clamp_axis_rot(i, hole_ox, hole_oy));
    }
  }
}

module oled_display_mount_peg_feature(xy, z_top) {
  peg_d = lid_display_mount_d * lid_display_mount_d_scale;
  tip_d = peg_d * lid_display_mount_tip_d_scale;
  tip_h = max(0, min(lid_display_mount_tip_h, lid_display_mount_peg_h));
  boss_h = max(0, lid_display_mount_boss_h);
  boss_d = max(peg_d, lid_display_mount_boss_d);
  is_mega_boss = (lid_oled_mount_style == "mega_boss_pegs");
  boss_drop = is_mega_boss ? mega_boss_peg_boss_drop : 0;
  // Mega-style pegs are a full narrow shaft with a wider boss/collar around it.
  // Lowering boss_drop moves only the collar lower on the shaft, exposing more peg above it.
  shaft_h = lid_display_mount_peg_h;
  tip_z0  = z_top - shaft_h;
  boss_z0 = is_mega_boss ? (z_top - boss_h - boss_drop) : (z_top - boss_h);

  difference() {
    union() {
      if (lid_display_mount_boss_enabled && boss_h > 0) {
        translate([xy[0], xy[1], boss_z0])
          cylinder(
            h = boss_h,
            d1 = max(peg_d, boss_d - 2*lid_display_mount_boss_taper),
            d2 = boss_d,
            $fn = 60
          );
      }

      if (tip_h > 0) {
        translate([xy[0], xy[1], tip_z0])
          cylinder(
            h = tip_h,
            d1 = max(0.8, tip_d - 2*lid_display_mount_tip_taper),
            d2 = tip_d,
            $fn = 48
          );
      }
    }

    if (lid_display_mount_pilot_enabled) {
      translate([xy[0], xy[1], z_top - lid_display_mount_pilot_h - EPS])
        cylinder(h = lid_display_mount_pilot_h + 2*EPS,
                 d = lid_display_mount_pilot_d,
                 $fn = 40);
    }
  }
}

module oled_mount_box_local(c, rot_z, local_xy, size_xy, z0, h) {
  translate([c[0], c[1], z0 + h/2])
    rotate([0, 0, rot_z])
      translate([local_xy[0], local_xy[1], 0])
        cube([size_xy[0], size_xy[1], h], center=true);
}

module oled_display_mount_rear_capture() {
  if (lid_oled_rear_mount_enabled) {
    c = oled_mount_center_world_xy();
    rot_z = oled_mount_rot_z();
    capture_z = oled_mount_capture_z();
    z0 = lid_h - lid_top_th - capture_z + lid_display_mount_offset_z;
    beam_z0 = lid_h - lid_top_th - lid_oled_top_latch_gap - lid_oled_top_latch_th + lid_display_mount_offset_z;

    body_w = lid_oled_mount_body_xy[0];
    body_h = lid_oled_mount_body_xy[1];

    bottom_hook_x = body_w/2 - lid_oled_bottom_hook_inset;
    bottom_y = -(body_h/2 + lid_oled_mount_bottom_clear + lid_oled_bottom_hook_depth/2);

    locator_x = body_w/2 + lid_oled_mount_side_clear + lid_oled_side_locator_w/2;
    locator_y = lid_oled_side_locator_offset_y;

    latch_inner_y = body_h/2 + lid_oled_mount_top_clear - lid_oled_top_latch_hook_overlap;
    latch_center_y = latch_inner_y + lid_oled_top_latch_len/2;
    latch_anchor_y = latch_center_y + lid_oled_top_latch_len/2 - lid_oled_top_latch_anchor_len/2;
    latch_hook_y = latch_inner_y + lid_oled_top_latch_hook_depth/2;

    for (sx = [-1, 1])
      oled_mount_box_local(
        c, rot_z,
        [sx * bottom_hook_x, bottom_y],
        [lid_oled_bottom_hook_w, lid_oled_bottom_hook_depth],
        z0, capture_z
      );

    for (sx = [-1, 1])
      oled_mount_box_local(
        c, rot_z,
        [sx * locator_x, locator_y],
        [lid_oled_side_locator_w, lid_oled_side_locator_span],
        z0, capture_z
      );

    oled_mount_box_local(
      c, rot_z,
      [0, latch_center_y],
      [lid_oled_top_latch_w, lid_oled_top_latch_len],
      beam_z0, lid_oled_top_latch_th
    );

    oled_mount_box_local(
      c, rot_z,
      [0, latch_anchor_y],
      [lid_oled_top_latch_w, lid_oled_top_latch_anchor_len],
      beam_z0, lid_oled_top_latch_th + lid_oled_top_latch_gap
    );

    oled_mount_box_local(
      c, rot_z,
      [0, latch_hook_y],
      [lid_oled_top_latch_w, lid_oled_top_latch_hook_depth],
      beam_z0 - lid_oled_top_latch_hook_drop,
      lid_oled_top_latch_th + lid_oled_top_latch_hook_drop
    );
  }
}

module oled_display_mount_side_rails() {
  if (lid_oled_side_rails_enabled) {
    c = oled_mount_center_world_xy();
    rot_z = oled_mount_rot_z();
    capture_z = oled_mount_capture_z();
    z0 = lid_h - lid_top_th - capture_z + lid_display_mount_offset_z;
    beam_z0 = lid_h - lid_top_th - lid_oled_side_rail_latch_gap - lid_oled_side_rail_latch_th + lid_display_mount_offset_z;

    body_w = lid_oled_mount_body_xy[0];
    body_h = lid_oled_mount_body_xy[1];

    rail_x = body_w/2 + lid_oled_mount_side_clear + lid_oled_side_rail_th/2;
    rail_span = body_h + lid_oled_mount_bottom_clear + lid_oled_mount_top_clear + lid_oled_side_rail_span_extra;
    rail_center_y = (lid_oled_mount_top_clear - lid_oled_mount_bottom_clear) / 2;

    stop_x = body_w/2 - lid_oled_side_rail_stop_w/2;
    stop_y = -(body_h/2 + lid_oled_mount_bottom_clear + lid_oled_side_rail_stop_depth/2);

    latch_inner_y = body_h/2 + lid_oled_mount_top_clear - lid_oled_side_rail_latch_overlap;
    latch_center_y = latch_inner_y + lid_oled_side_rail_latch_len/2;
    latch_anchor_y = latch_center_y + lid_oled_side_rail_latch_len/2 - lid_oled_side_rail_latch_anchor_len/2;
    latch_hook_y = latch_inner_y + lid_oled_side_rail_latch_hook_depth/2;

    for (sx = [-1, 1])
      oled_mount_box_local(
        c, rot_z,
        [sx * rail_x, rail_center_y],
        [lid_oled_side_rail_th, rail_span],
        z0, capture_z
      );

    for (sx = [-1, 1])
      oled_mount_box_local(
        c, rot_z,
        [sx * stop_x, stop_y],
        [lid_oled_side_rail_stop_w, lid_oled_side_rail_stop_depth],
        z0, capture_z
      );

    oled_mount_box_local(
      c, rot_z,
      [0, latch_center_y],
      [lid_oled_side_rail_latch_w, lid_oled_side_rail_latch_len],
      beam_z0, lid_oled_side_rail_latch_th
    );

    oled_mount_box_local(
      c, rot_z,
      [0, latch_anchor_y],
      [lid_oled_side_rail_latch_w, lid_oled_side_rail_latch_anchor_len],
      beam_z0, lid_oled_side_rail_latch_th + lid_oled_side_rail_latch_gap
    );

    oled_mount_box_local(
      c, rot_z,
      [0, latch_hook_y],
      [lid_oled_side_rail_latch_w, lid_oled_side_rail_latch_hook_depth],
      beam_z0 - lid_oled_side_rail_latch_hook_drop,
      lid_oled_side_rail_latch_th + lid_oled_side_rail_latch_hook_drop
    );
  }
}

module oled_display_mount_shelf_clips() {
  if (lid_oled_shelf_clips_enabled) {
    c = oled_mount_center_world_xy();
    rot_z = oled_mount_rot_z();
    capture_z = oled_mount_capture_z();
    z0 = lid_h - lid_top_th - capture_z + lid_display_mount_offset_z;
    beam_z0 = lid_h - lid_top_th - lid_oled_shelf_clip_gap - lid_oled_shelf_clip_th + lid_display_mount_offset_z;

    body_w = lid_oled_mount_body_xy[0];
    body_h = lid_oled_mount_body_xy[1];

    shelf_y = -(body_h/2 + lid_oled_mount_bottom_clear + lid_oled_shelf_depth/2);
    locator_x = body_w/2 + lid_oled_mount_side_clear + lid_oled_shelf_side_locator_w/2;
    clip_x = body_w/2 - lid_oled_shelf_clip_inset;

    clip_inner_y = body_h/2 + lid_oled_mount_top_clear - lid_oled_shelf_clip_overlap;
    clip_center_y = clip_inner_y + lid_oled_shelf_clip_len/2;
    clip_anchor_y = clip_center_y + lid_oled_shelf_clip_len/2 - lid_oled_shelf_clip_anchor_len/2;
    clip_hook_y = clip_inner_y + lid_oled_shelf_clip_hook_depth/2;

    oled_mount_box_local(
      c, rot_z,
      [0, shelf_y],
      [lid_oled_shelf_w, lid_oled_shelf_depth],
      z0, capture_z
    );

    for (sx = [-1, 1])
      oled_mount_box_local(
        c, rot_z,
        [sx * (body_w/2 - lid_oled_shelf_corner_w/2), shelf_y],
        [lid_oled_shelf_corner_w, lid_oled_shelf_depth],
        z0, capture_z
      );

    for (sx = [-1, 1])
      oled_mount_box_local(
        c, rot_z,
        [sx * locator_x, lid_oled_shelf_side_locator_y],
        [lid_oled_shelf_side_locator_w, lid_oled_shelf_side_locator_span],
        z0, capture_z
      );

    for (sx = [-1, 1]) {
      oled_mount_box_local(
        c, rot_z,
        [sx * clip_x, clip_center_y],
        [lid_oled_shelf_clip_w, lid_oled_shelf_clip_len],
        beam_z0, lid_oled_shelf_clip_th
      );

      oled_mount_box_local(
        c, rot_z,
        [sx * clip_x, clip_anchor_y],
        [lid_oled_shelf_clip_w, lid_oled_shelf_clip_anchor_len],
        beam_z0, lid_oled_shelf_clip_th + lid_oled_shelf_clip_gap
      );

      oled_mount_box_local(
        c, rot_z,
        [sx * clip_x, clip_hook_y],
        [lid_oled_shelf_clip_w, lid_oled_shelf_clip_hook_depth],
        beam_z0 - lid_oled_shelf_clip_hook_drop,
        lid_oled_shelf_clip_th + lid_oled_shelf_clip_hook_drop
      );
    }
  }
}

// ==================== SHELF + RETAINER BAR (robust) ====================
// Concept: PCB lower edge rests on a wide shelf ledge (printed flat).
// Two thick side walls constrain X. A separate printed retainer bar pinches
// the top PCB edge down with two M2 self-tapping screws through bosses.
// Retention force: screw clamping. Load path: shelf (bottom), bar (top), walls (sides).
// No cantilevers, no thin features. Serviceable.
module oled_display_mount_shelf_bar() {
  if (lid_oled_shelf_bar_enabled) {
    c = oled_mount_center_world_xy();
    rot_z = oled_mount_rot_z();
    z0    = lid_h - lid_top_th;           // inner ceiling of lid (Z=0 here is lid inner face)
    pcb_w = lid_oled_mount_body_xy[0];    // PCB span in local X
    pcb_h = lid_oled_mount_body_xy[1];    // PCB span in local Y
    sw    = lid_oled_sbar_side_wall_th;
    sh    = lid_oled_sbar_side_wall_h;
    sc    = lid_oled_sbar_pcb_side_clear;

    translate([c[0], c[1], 0])
    rotate([0, 0, rot_z]) {

      // Shelf ledge the PCB bottom edge rests on (printed flat = strong)
      translate([0,
                 -(pcb_h/2 + lid_oled_mount_bottom_clear + lid_oled_sbar_shelf_depth/2),
                 z0 - lid_oled_sbar_shelf_h])
        cube([lid_oled_sbar_shelf_w, lid_oled_sbar_shelf_depth, lid_oled_sbar_shelf_h], center=true);

      // Side walls constraining PCB in X (symmetric pair)
      for (sx = [-1, 1])
        translate([sx * (pcb_w/2 + sc + sw/2),
                   -(pcb_h/2 + lid_oled_mount_bottom_clear + lid_oled_sbar_shelf_depth*0.5),
                   z0 - sh])
          cube([sw, pcb_h + lid_oled_mount_bottom_clear + lid_oled_sbar_shelf_depth*0.5, sh], center=false);

      // Screw bosses for M2 retainer bar (near top PCB edge)
      for (sx = [-1, 1])
        translate([sx * lid_oled_sbar_screw_pitch/2,
                   pcb_h/2 + lid_oled_mount_top_clear + lid_oled_sbar_screw_boss_d/2 + 0.5,
                   z0 - lid_oled_sbar_screw_boss_h])
          difference() {
            cylinder(h = lid_oled_sbar_screw_boss_h, d = lid_oled_sbar_screw_boss_d, $fn=40);
            translate([0, 0, -EPS])
              cylinder(h = lid_oled_sbar_screw_boss_h + 2*EPS, d = lid_oled_sbar_screw_d, $fn=30);
          }
    }
  }
}

// Retainer bar: separate printed part (printed flat = very stiff).
// Print separately, place over top PCB edge, drive two M2 screws.
module oled_shelf_bar_retainer_bar() {
  bw = lid_oled_sbar_bar_w;
  bth = lid_oled_sbar_bar_th;
  bl = lid_oled_sbar_bar_len;
  difference() {
    translate([-bw/2, -bl/2, 0])
      cube([bw, bl, bth]);
    // M2 clearance through-holes
    for (sx = [-1, 1])
      translate([sx * lid_oled_sbar_screw_pitch/2, 0, -EPS])
        cylinder(h = bth + 2*EPS, d = lid_oled_sbar_bar_screw_d, $fn=30);
  }
}

// ==================== BEZEL + FOAM COMPRESSION BACKER ====================
// Concept: PCB perimeter rests against the front opening/bezel side.
// Lower shelf and side walls position the board. A separate backer plate,
// with a thin foam pad between plate and PCB rear, compresses the board
// evenly into the bezel using two M2 screws.
module oled_display_mount_foam_backer() {
  if (lid_oled_foam_backer_enabled) {
    c = oled_mount_center_world_xy();
    rot_z = oled_mount_rot_z();
    z0    = lid_h - lid_top_th;

    pcb_w = lid_oled_fback_pcb_xy[0];
    pcb_h = lid_oled_fback_pcb_xy[1];
    sw    = lid_oled_fback_side_wall_th;
    sh    = lid_oled_fback_side_wall_h;
    sc    = lid_oled_fback_side_clear;
    shelf_d = lid_oled_fback_bottom_shelf_depth;
    shelf_h = lid_oled_fback_bottom_shelf_h;
    top_d   = lid_oled_fback_top_stop_depth;
    top_h   = lid_oled_fback_top_stop_h;

    translate([c[0], c[1], 0])
    rotate([0, 0, rot_z]) {
      // Bottom shelf
      translate([0,
                 -(pcb_h/2 + lid_oled_fback_bottom_clear + shelf_d/2),
                 z0 - shelf_h])
        cube([pcb_w + 2*sc + 2.0, shelf_d, shelf_h], center=true);

      // Side walls
      for (sx = [-1, 1])
        translate([sx * (pcb_w/2 + sc + sw/2),
                   0,
                   z0 - sh])
          cube([sw, pcb_h + lid_oled_fback_bottom_clear + lid_oled_fback_top_clear + shelf_d, sh], center=true);

      // Top stop
      translate([0,
                 pcb_h/2 + lid_oled_fback_top_clear + top_d/2,
                 z0 - top_h])
        cube([pcb_w + 2*sc + 2.0, top_d, top_h], center=true);

      // Two backer plate bosses
      for (sy = [-1, 1])
        translate([0, sy * lid_oled_fback_boss_pitch_y/2, z0 - lid_oled_fback_boss_h])
          difference() {
            cylinder(h = lid_oled_fback_boss_h, d = lid_oled_fback_boss_d, $fn=40);
            translate([0, 0, -EPS])
              cylinder(h = lid_oled_fback_boss_h + 2*EPS, d = lid_oled_fback_screw_d, $fn=30);
          }
    }
  }
}

module oled_foam_backer_plate() {
  px = lid_oled_fback_plate_xy[0];
  py = lid_oled_fback_plate_xy[1];
  pth = lid_oled_fback_plate_th;
  wx = min(lid_oled_fback_plate_window_xy[0], px - 6);
  wy = min(lid_oled_fback_plate_window_xy[1], py - 6);

  difference() {
    translate([-px/2, -py/2, 0])
      cube([px, py, pth]);

    translate([0, 0, -EPS])
      cube([wx, wy, pth + 2*EPS], center=true);

    for (sy = [-1, 1])
      translate([0, sy * lid_oled_fback_boss_pitch_y/2, -EPS])
        cylinder(h = pth + 2*EPS, d = lid_oled_fback_plate_screw_d, $fn=30);
  }
}

// ==================== CHANNEL FRAME (robust) ====================
// Concept: Three solid walls form a pocket channel in the lid interior.
// PCB slides in from the open (bottom) end, supported on all three sides.
// A separate thick end cap encloses the fourth edge; two M2 screws hold the cap.
// Load is distributed across the full PCB perimeter edge — maximum support area.
module oled_display_mount_channel_frame() {
  if (lid_oled_channel_enabled) {
    c = oled_mount_center_world_xy();
    rot_z = oled_mount_rot_z();
    z0    = lid_h - lid_top_th;

    pcb_w = lid_oled_chan_pcb_xy[0];
    pcb_h = lid_oled_chan_pcb_xy[1];
    cl    = lid_oled_chan_pcb_clear_xy;
    cz    = lid_oled_chan_pcb_clear_z;
    th    = lid_oled_chan_wall_th;
    pth   = lid_oled_chan_pcb_th;

    // Channel interior = pcb + clearance
    chan_inner_w = pcb_w + 2*cl;
    chan_inner_h = pcb_h + 2*cl;
    chan_depth   = pth + cz;   // Z depth of channel slot from lid inner ceiling

    translate([c[0], c[1], 0])
    rotate([0, 0, rot_z]) {

      // Top wall (at local Y = +chan_inner_h/2)
      translate([0, chan_inner_h/2 + th/2, z0 - chan_depth])
        cube([chan_inner_w + 2*th, th, chan_depth], center=true);

      // Left wall
      translate([-(chan_inner_w/2 + th/2), 0, z0 - chan_depth])
        cube([th, chan_inner_h + 2*th, chan_depth], center=true);

      // Right wall
      translate([(chan_inner_w/2 + th/2), 0, z0 - chan_depth])
        cube([th, chan_inner_h + 2*th, chan_depth], center=true);

      // Screw bosses for end cap (at bottom side, local Y = -chan_inner_h/2 - th)
      for (sx = [-1, 1])
        translate([sx * lid_oled_chan_endcap_screw_pitch/2,
                   -(chan_inner_h/2 + th + lid_oled_chan_endcap_boss_d/2),
                   z0 - lid_oled_chan_endcap_boss_h])
          difference() {
            cylinder(h = lid_oled_chan_endcap_boss_h, d = lid_oled_chan_endcap_boss_d, $fn=40);
            translate([0, 0, -EPS])
              cylinder(h = lid_oled_chan_endcap_boss_h + 2*EPS,
                       d = lid_oled_chan_endcap_screw_d, $fn=30);
          }
    }
  }
}

// End cap: separate printed part for the open end of the channel.
// Print separately, slide onto the channel opening, drive two M2 screws.
module oled_channel_frame_endcap() {
  cw = lid_oled_chan_cap_w;
  ct = lid_oled_chan_cap_th;
  ch = lid_oled_chan_cap_h;
  difference() {
    translate([-cw/2, 0, 0])
      cube([cw, ct, ch]);
    for (sx = [-1, 1])
      translate([sx * lid_oled_chan_endcap_screw_pitch/2, -EPS, ch/2])
        rotate([-90, 0, 0])
          cylinder(h = ct + 2*EPS, d = lid_oled_chan_cap_screw_d, $fn=30);
  }
}

// ==================== SOLID RAILS + KEYHOLE CROSSBAR (robust) ====================
// Concept: Two thick solid side rails constrain the PCB in X. The board drops in
// from the open top with a Y sliding-then-drop motion (no force on glass edge).
// A full-width printed crossbar slides laterally through a slot in both rails and
// captures a keyhole lug that prevents withdrawal. No screws or cantilevers.
// To remove: slide bar sideways until lug clears the slot width opening, lift out.
module oled_display_mount_solid_rails() {
  if (lid_oled_solid_rails_enabled) {
    c = oled_mount_center_world_xy();
    rot_z = oled_mount_rot_z();
    z0    = lid_h - lid_top_th;

    pcb_w = lid_oled_mount_body_xy[0];
    pcb_h = lid_oled_mount_body_xy[1];
    sc    = lid_oled_srail_pcb_clear;
    rt    = lid_oled_srail_th;
    rh    = lid_oled_srail_h;
    fd    = lid_oled_srail_floor_depth;
    fh    = lid_oled_srail_floor_h;
    fw    = lid_oled_srail_floor_w;
    sw    = lid_oled_srail_bar_slot_w;
    slot_h = lid_oled_srail_bar_slot_h;
    slot_z = z0 - rh + fh;  // slot sits just above the floor stop

    translate([c[0], c[1], 0])
    rotate([0, 0, rot_z]) {

      // Side rails (symmetric pair), each with a keyhole slot cut out
      for (sx = [-1, 1]) {
        rail_x = sx * (pcb_w/2 + sc + rt/2);
        difference() {
          // Rail body
          translate([rail_x - rt/2,
                     -(pcb_h/2 + lid_oled_mount_bottom_clear),
                     z0 - rh])
            cube([rt,
                  pcb_h + lid_oled_mount_bottom_clear + lid_oled_mount_top_clear,
                  rh]);
          // Slot opening for crossbar
          translate([rail_x - rt/2 - EPS,
                     pcb_h/2 + lid_oled_mount_top_clear - sw/2,
                     slot_z])
            cube([rt + 2*EPS, sw, slot_h]);
        }
      }

      // Bottom stop ledges (one near each lower corner, printed flat = strong)
      for (sx = [-1, 1])
        translate([sx * (pcb_w/4),
                   -(pcb_h/2 + lid_oled_mount_bottom_clear + fd/2),
                   z0 - fh])
          cube([fw, fd, fh], center=true);
    }
  }
}

// Crossbar: separate printed part that slides through the rail slots.
// Printed flat (XY face down) — stiff in bending.
// The lug head is wider than the slot opening so it cannot withdraw after insertion.
module oled_solid_rails_crossbar() {
  bt   = lid_oled_srail_bar_th;
  bw_body = lid_oled_srail_bar_body_w;
  bw_total = lid_oled_srail_bar_total_w;
  lw   = lid_oled_srail_bar_lug_w;
  lh   = lid_oled_srail_bar_lug_h;
  sw   = lid_oled_srail_bar_slot_w;

  difference() {
    union() {
      // Main bar body (spans full width including past both rails)
      translate([-bw_total/2, -bt/2, 0])
        cube([bw_total, bt, bt]);

      // Keyhole lug head on each end (wider than slot, prevents extraction)
      for (sx = [-1, 1])
        translate([sx * bw_total/2 + (sx > 0 ? -lw : 0), -lh/2, 0])
          cube([lw, lh, bt]);
    }
    // Nothing to subtract — the bar is a solid flat piece
  }
}

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
// Keep enough exterior skin so snap grooves don't thin the outer wall too much.
function snap_lug_t() =
  max(0.60, min(wall - snap_fit_clear() - snap_outer_wall_min, max(0.90, snap_window_depth)));
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
    model_z_base = bottom + (pico_model_follow_standoffs_z ? standoff_h : 0);
    if (pico_model_background)
      %translate([
        wall + pico_clear_x + pico_place_xy[0] + pico_model_trim_xy[0] + pico_model_move_xy[0],
        wall + pico_clear_y + pico_place_xy[1] + pico_model_trim_xy[1] + pico_model_move_xy[1],
        model_z_base + pico_model_move_z
      ])
        rotate(pico_model_rot)
          scale(pico_model_scale)
            import(pico_stl_path, convexity=10);
    else
      translate([
        wall + pico_clear_x + pico_place_xy[0] + pico_model_trim_xy[0] + pico_model_move_xy[0],
        wall + pico_clear_y + pico_place_xy[1] + pico_model_trim_xy[1] + pico_model_move_xy[1],
        model_z_base + pico_model_move_z
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
  union() {
    difference() {
      union() {
        hollow_rounded_box_bottom([outer_len, outer_w, base_h], wall, corner_r, bottom);
        base_feet();
        base_snap_lugs();
      }

      wall_cutout(usb_wall, usb_cut_pos, usb_cut_xy);
      usb_shell_groove_cut();
      front_four_banana_holes_cut();
    }

    pico_standoffs_in_base();
  }
}

module base_front_fit_test() {
  z_shift = feet_enabled ? feet_h : 0;
  z_span = z_shift + base_h + (snap_enabled ? snap_hook_h : 0) + 2*EPS;
  front_foot_y = outer_w/2 - feet_spacing_y/2;
  front_foot_xs = [
    outer_len/2 - feet_spacing_x/2,
    outer_len/2 + feet_spacing_x/2
  ];
  lug_t = snap_lug_t();

  difference() {
    intersection() {
      translate([0, 0, z_shift]) base();
      translate([-EPS, -EPS, -EPS])
        cube([outer_len + 2*EPS, base_front_fit_test_depth + EPS, z_span], center=false);
    }

    translate([0, 0, z_shift]) {
      if (feet_enabled)
        for (x = front_foot_xs)
          translate([x, front_foot_y, -feet_h])
            cylinder(h = feet_h, d = feet_od + 2*EPS, $fn = $fn);

      if (snap_enabled)
        for (p = base_snap_window_positions())
          if (p[0] == "front")
            snap_side_frame(p[0], p[1], p[2])
              translate([-snap_tab_width/2 - EPS, -lug_t/2 - EPS, base_h - EPS])
                cube([snap_tab_width + 2*EPS, lug_t + 2*EPS, snap_hook_h + EPS], center=false);
    }
  }
}

module base_left_fit_test() {
  z_shift = feet_enabled ? feet_h : 0;
  z_span = z_shift + base_h + (snap_enabled ? snap_hook_h : 0) + 2*EPS;
  left_foot_x = outer_len/2 - feet_spacing_x/2;
  band_y0 = usb_cut_pos[0] - base_left_fit_test_depth/2;

  difference() {
    intersection() {
      translate([0, 0, z_shift]) base();
      translate([-EPS, band_y0 - EPS, -EPS])
        cube([base_left_fit_test_width + EPS, base_left_fit_test_depth + 2*EPS, z_span], center=false);
    }

    translate([0, 0, z_shift]) {
      if (feet_enabled)
        for (y = [
          outer_w/2 - feet_spacing_y/2,
          outer_w/2 + feet_spacing_y/2
        ])
          translate([left_foot_x, y, -feet_h])
            cylinder(h = feet_h, d = feet_od + 2*EPS, $fn = $fn);
    }
  }
}

// ==================== LID TOP BANANA HOLES ====================

function lid_top_row_local_pts() =
[
  [-lid_top_banana_pitch/2, 0],
  [ lid_top_banana_pitch/2, 0]
];

module lid_top_row_positions(z0=0) {
  cx = lid_top_banana_center_xy[0] + lid_top_banana_offset_xy[0];
  cy = lid_top_banana_center_xy[1] + lid_top_banana_offset_xy[1];

  translate([cx, cy, z0])
    rotate([0, 0, lid_top_banana_row_rotate])
      for (p = lid_top_row_local_pts())
        translate([p[0], p[1], 0])
          children();
}

function lid_top_row_anchor_xy() =
  [lid_top_banana_center_xy[0] + lid_top_banana_offset_xy[0],
   lid_top_banana_center_xy[1] + lid_top_banana_offset_xy[1]];

function lid_top_hidden_mount_anchor_xy() =
  [lid_top_row_anchor_xy()[0] + lid_top_hidden_mount_group_offset_xy[0],
   lid_top_row_anchor_xy()[1] + lid_top_hidden_mount_group_offset_xy[1]];

function lid_top_hidden_mount_cut_fine(i) =
  (i == 0) ? lid_top_hidden_mount_cut0_offset_xy
           : lid_top_hidden_mount_cut1_offset_xy;

function lid_top_hidden_mount_nut_fine(i) =
  (i == 0) ? lid_top_hidden_mount_nut0_offset_xy
           : lid_top_hidden_mount_nut1_offset_xy;

function lid_top_text_local_pts() =
[
  [-lid_top_text_pitch/2, 0],
  [ lid_top_text_pitch/2, 0]
];

function lid_top_text_world_xy(i) =
  let(
    p = lid_top_text_local_pts()[i],
    qr = rot2d(p, lid_top_banana_row_rotate),
    a = lid_top_row_anchor_xy()
  )
  [a[0] + qr[0] + lid_top_text_offset_xy[0],
   a[1] + qr[1] + lid_top_text_offset_xy[1]];

module lid_text() {
  if (lid_top_ports_enabled && lid_top_text_enabled) {
    for (i = [0:len(lid_top_text_labels)-1]) {
      xy = lid_top_text_world_xy(i);
      translate([xy[0], xy[1], lid_h - lid_top_th + lid_top_text_offset_z])
        rotate([0, 0, lid_top_text_rotate])
          linear_extrude(height = lid_top_text_height)
            text(lid_top_text_labels[i],
                 size = lid_top_text_size,
                 font = lid_top_text_font,
                 halign = lid_top_text_hal,
                 valign = lid_top_text_val,
                 spacing = lid_top_text_spacing);
    }
  }
}

module lid_top_hidden_mount_bridge() {
  if (lid_top_ports_enabled && lid_top_hidden_mount_enabled) {
    z0 = lid_h - lid_top_th - lid_top_hidden_mount_bridge_h;

    translate([lid_top_hidden_mount_bridge_offset_xy[0], lid_top_hidden_mount_bridge_offset_xy[1], 0])
      translate([lid_top_hidden_mount_group_offset_xy[0], lid_top_hidden_mount_group_offset_xy[1], 0])
        hull()
          lid_top_row_positions(z0)
            cylinder(h=lid_top_hidden_mount_bridge_h, d=lid_top_hidden_mount_bridge_d, $fn=80);
  }
}

module lid_top_banana_holes_cut() {
  if (lid_top_ports_enabled) {
    shaft_d = lid_top_hidden_mount_enabled ? lid_top_hidden_mount_shaft_d
                                           : lid_top_banana_hole_d;
    z0 = lid_h - lid_top_th - (lid_top_hidden_mount_enabled ? lid_top_hidden_mount_bridge_h : 0);
    through_h = lid_top_th + (lid_top_hidden_mount_enabled ? lid_top_hidden_mount_bridge_h : 0) + 4*EPS;

    for (i = [0:1]) {
      p = lid_top_row_local_pts()[i];
      fine = lid_top_hidden_mount_cut_fine(i);
      translate([lid_top_hidden_mount_anchor_xy()[0], lid_top_hidden_mount_anchor_xy()[1], z0 - EPS])
        rotate([0, 0, lid_top_banana_row_rotate])
          translate([p[0], p[1], 0])
            translate([fine[0], fine[1], 0])
              cylinder(h=through_h, d=shaft_d, $fn=80);
    }

    if (lid_top_hidden_mount_enabled) {
      nut_d = hex_circ_d(lid_top_hidden_mount_nut_af + lid_top_hidden_mount_clear);

      for (i = [0:1]) {
        p = lid_top_row_local_pts()[i];
        fine = lid_top_hidden_mount_cut_fine(i);
        nut_fine = lid_top_hidden_mount_nut_fine(i);

        translate([lid_top_hidden_mount_anchor_xy()[0], lid_top_hidden_mount_anchor_xy()[1], z0 - EPS])
          rotate([0, 0, lid_top_banana_row_rotate])
            translate([p[0], p[1], 0])
              translate([fine[0] + nut_fine[0], fine[1] + nut_fine[1], 0])
                rotate([0, 0, 30])
                  cylinder(h=lid_top_hidden_mount_nut_depth + 2*EPS, d=nut_d, $fn=6);

        translate([lid_top_hidden_mount_anchor_xy()[0], lid_top_hidden_mount_anchor_xy()[1], z0 + lid_top_hidden_mount_nut_depth - EPS])
          rotate([0, 0, lid_top_banana_row_rotate])
            translate([p[0], p[1], 0])
              translate([fine[0], fine[1], 0])
                cylinder(h=lid_top_hidden_mount_washer_depth + 2*EPS,
                         d=lid_top_hidden_mount_washer_d + lid_top_hidden_mount_clear,
                         $fn=80);
      }
    }
  }
}

// ==================== LID ====================

module oled_model_on_lid() {
  if (show_oled_model) {
    translate([lcd_center_xy[0], lcd_center_xy[1], base_h + assembly_lid_gap + lid_h + oled_on_lid_z_offset])
      translate([oled_feature_move[0] + oled_move[0] + oled_model_move[0],
                 oled_feature_move[1] + oled_move[1] + oled_model_move[1],
                 oled_feature_move[2] + oled_move[2] + oled_model_move[2]])
        rotate(oled_rot)
          oled_module(pos=[0,0,0], rot=[0,0,0], scale=oled_model_scale, stl_path=oled_stl_path);
  }
}

module lid() {
  hole_ox = [peg0_x + peg_group_xy[0], peg1_x + peg_group_xy[0], peg2_x + peg_group_xy[0], peg3_x + peg_group_xy[0]];
  hole_oy = [peg0_y + peg_group_xy[1], peg1_y + peg_group_xy[1], peg2_y + peg_group_xy[1], peg3_y + peg_group_xy[1]];
  hole_oz = [peg0_z, peg1_z, peg2_z, peg3_z];

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

      lid_top_hidden_mount_bridge();

      if (lid_oled_rear_mount_enabled) {
        oled_display_mount_rear_capture();
      } else if (lid_oled_side_rails_enabled) {
        oled_display_mount_side_rails();
      } else if (lid_oled_shelf_clips_enabled) {
        oled_display_mount_shelf_clips();
      } else if (lid_oled_ear_clamps_enabled) {
        oled_display_mount_clamps(hole_ox, hole_oy, hole_oz);
      } else if (lid_oled_shelf_bar_enabled) {
        oled_display_mount_shelf_bar();
      } else if (lid_oled_foam_backer_enabled) {
        oled_display_mount_foam_backer();
      } else if (lid_oled_channel_enabled) {
        oled_display_mount_channel_frame();
      } else if (lid_oled_solid_rails_enabled) {
        oled_display_mount_solid_rails();
      } else if (lid_display_mount_enabled) {
        for (i=[0:3]) {
          xy = oled_ear_world_xy(i);
          z_top = lid_h - lid_top_th + lid_display_mount_offset_z + hole_oz[i];
          oled_display_mount_peg_feature(
            [xy[0] + hole_ox[i], xy[1] + hole_oy[i]],
            z_top
          );
        }
      }

    }

    // Lid top banana holes and hidden hardware pockets
    lid_top_banana_holes_cut();

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
      // Keep display cutout aligned with OLED orientation/offset convention.
      dco = rot2d([lid_display_cut_offset_x, lid_display_cut_offset_y], oled_rot[2]);
      translate([c[0] + dco[0],
                 c[1] + dco[1],
                 lid_h - lid_top_th/2])
        rotate([0, 0, oled_rot[2] + lid_display_cut_rotate])
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
    translate(print_layout_text_offset)
      lid_text();
  }
}

module print_layout_main() {
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

module assembly_text() {
  base();
  pico_model_in_base();
  translate([0, 0, base_h + assembly_lid_gap]) {
    lid();
    lid_text();
  }
  oled_model_on_lid();
}

// -------------------- Render --------------------
if (part == "base")         base();
if (part == "base_front_fit_test") base_front_fit_test();
if (part == "base_left_fit_test") base_left_fit_test();
if (part == "lid")          lid();
if (part == "lid_text")     lid_text();
if (part == "assembly")     assembly();
if (part == "assembly_text") assembly_text();
if (part == "print_layout") print_layout();
if (part == "print_layout_main") print_layout_main();