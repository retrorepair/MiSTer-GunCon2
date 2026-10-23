// GunCon 2 calibration and monitor core: a 15 kHz picture for the gun to look at.
//
// Words from the HPS (a Main_MiSTer with guncal support):
//   gun  (joystick_5)  [11:0] raw X  [23:12] raw Y  [24] trigger        the gun's raw report
//   cmd  (joystick_4)  [1:0] page (0 monitor, 1 calibration, 2 check)  [5:2] target number  [7:6] flash sequence
//                      [9:8] message  [10] pointer valid  [20:11] pointer x  [28:21] pointer y   (core pixels)
//   tgt  (joystick_3)  [9:0] target x  [17:10] target y  [21:18] number of targets            (core pixels)
// The core draws and displays; the sequencing and the maths live in the HPS (guncal.cpp).
//
// Picture: 529 x 240 active, shown as 480i (see the video timing), pixel clock 10 MHz, 15.7 kHz / 59.9 Hz fields (NTSC) or PAL timing. A CRT hides part of this
// (overscan, bezel), so nothing here assumes the whole picture is visible.

module guncal
(
	input         clk,        // 20 MHz
	input         reset,

	input         pal,
	input         scandouble,

	input  [31:0] gun,
	input  [31:0] cmd,
	input  [31:0] tgt,
	input         clear,      // clear min/max and the pull counter

	output reg    ce_pix,
	output        hvcnt_atzero,

	output reg    HBlank,
	output reg    HSync,
	output reg    VBlank,
	output reg    VSync,
	output        field_out,    // which field this is (the framework's VGA_F1)

	output [23:0] rgb
);

// ---------------------------------------------------------------- video timing (the MiSTer template's, made 480i)
//
// On the 15 kHz output the picture is interlaced: two fields of 240 lines (263 and 262 lines, 525 a frame, NTSC; 313 and 312, PAL). Both
// fields show the same picture, so every line is drawn twice, a row apart: a filled 480-line picture with the resolution of what is drawn
// (529 x 240). What interlaces the fields is VSync starting half a line (319 pixels) early in field 1. The gun counts lines per field, so
// its Y is as in a 240 line picture, give or take half a line between the fields.

reg [9:0] hc = 0;
reg [9:0] vc = 0;
reg       field = 0;                 // 0: the longer field, VSync on the line's HSync; 1: the shorter one, VSync half a line early
wire      il = !scandouble;          // the scandoubler output (31 kHz) stays progressive

wire [9:0] vmax = scandouble ? (pal ? 10'd623 : 10'd523) :
                  pal        ? (field ? 10'd311 : 10'd312) : (field ? 10'd261 : 10'd262);

assign hvcnt_atzero = ce_pix && !hc && !vc && !field;

always @(posedge clk) begin
	if(scandouble) ce_pix <= 1;
		else ce_pix <= ~ce_pix;

	if(ce_pix) begin
		if(hc == 637) begin
			hc <= 0;
			if(vc >= vmax) begin
				vc <= 0;
				if (il) field <= ~field;
			end else vc <= vc + 1'd1;
		end else begin
			hc <= hc + 1'd1;
		end
	end
end

wire vs_at = (il && field) ? (hc == 225) : (hc == 544);

always @(posedge clk) begin
	if (hc == 529) HBlank <= 1;
		else if (hc == 0) HBlank <= 0;

	if (hc == 544) begin
		HSync <= 1;

		if(pal) begin
			if(vc == (scandouble ? 601 : 300)) VBlank <= 1;
				else if (vc == 0) VBlank <= 0;
		end
		else begin
			if(vc == (scandouble ? 480 : 240)) VBlank <= 1;
				else if (vc == 0) VBlank <= 0;
		end
	end

	if (vs_at) begin
		if(pal) begin
			if(vc == (scandouble ? 609 : 304)) VSync <= 1;
				else if (vc == (scandouble ? 617 : 308)) VSync <= 0;
		end
		else begin
			if(vc == (scandouble ? 490 : 245)) VSync <= 1;
				else if (vc == (scandouble ? 496 : 248)) VSync <= 0;
		end
	end

	if (hc == 590) HSync <= 0;
end

// ---------------------------------------------------------------- commands from the HPS

wire [1:0]  page   = cmd[1:0];
wire [3:0]  target = cmd[5:2];
wire [1:0]  fseq   = cmd[7:6];
wire [1:0]  msgc   = cmd[9:8];
wire        pvalid = cmd[10];
wire        intro  = cmd[29];                    // the title and the prompt, until the first shot
wire [9:0]  ptr_x  = cmd[20:11];
wire [7:0]  ptr_y  = cmd[28:21];
wire [9:0]  tx     = tgt[9:0];
wire [7:0]  ty     = tgt[17:10];
wire [3:0]  npts   = tgt[21:18];

// ---------------------------------------------------------------- gun data

reg [31:0] gun_d;
wire       changed = (gun != gun_d);
wire [11:0] gx = gun[11:0];
wire [11:0] gy = gun[23:12];
wire       gtrig = gun[24];
wire       valid = (gx >= 12'd16);          // X of 0 or 1 means the gun sees no light

reg        vs_d;
wire       frame_tick = VSync & ~vs_d;
reg  [5:0] frames;
wire       sec_tick = frame_tick && (frames == 6'd59);

reg [11:0] ev_cnt, ev_rate;                  // gun reports per second
reg [11:0] pulls;
reg        trig_d;
reg [11:0] pvx, pvy;                         // previous valid sample, for the steadiness test
reg        has_prev;
reg  [7:0] steady;                           // consecutive valid samples within 8 units of the one before
reg  [5:0] age;                              // frames since the gun last reported anything new
reg [11:0] lx, ly;                           // last valid sample
reg        seen;
reg [11:0] minx, maxx, miny, maxy;
reg        clear_d;
reg  [1:0] fseq_d;
reg  [3:0] flash;                            // frames of white flash left

wire [11:0] dx = (gx > pvx) ? gx - pvx : pvx - gx;
wire [11:0] dy = (gy > pvy) ? gy - pvy : pvy - gy;

always @(posedge clk) begin
	gun_d   <= gun;
	vs_d    <= VSync;
	trig_d  <= gtrig;
	clear_d <= clear;
	fseq_d  <= fseq;

	if (frame_tick) begin
		frames <= sec_tick ? 6'd0 : frames + 1'd1;
		if (age != 6'd63) age <= age + 1'd1;
		if (flash != 4'd0) flash <= flash - 1'd1;
	end

	if (fseq != fseq_d) flash <= 4'd6;       // the HPS saw a trigger pull: flash the screen white

	if (sec_tick) begin
		ev_rate <= ev_cnt;
		ev_cnt  <= 0;
	end

	if (changed) begin
		ev_cnt <= ev_cnt + 1'd1;
		age    <= 0;
		if (valid) begin
			lx   <= gx;
			ly   <= gy;
			seen <= 1;
			pvx  <= gx;
			pvy  <= gy;
			has_prev <= 1;
			if (has_prev && dx <= 12'd8 && dy <= 12'd8) steady <= (steady == 8'd255) ? 8'd255 : steady + 1'd1;
				else steady <= 0;
			if (!seen || gx < minx) minx <= gx;
			if (!seen || gx > maxx) maxx <= gx;
			if (!seen || gy < miny) miny <= gy;
			if (!seen || gy > maxy) maxy <= gy;
		end else begin
			steady   <= 0;
			has_prev <= 0;
		end
	end

	if (gtrig && !trig_d) pulls <= pulls + 1'd1;

	if (reset || (clear && !clear_d)) begin
		pulls <= 0; seen <= 0; minx <= 0; maxx <= 0; miny <= 0; maxy <= 0; steady <= 0; has_prev <= 0;
	end
end

// 0 = no light, 1 = steady, 2 = jumpy
wire [1:0] lockst = !valid ? 2'd0 : (steady >= 8'd6 || age >= 6'd12) ? 2'd1 : 2'd2;

// ---------------------------------------------------------------- numbers for the display (latched once a frame)

function [15:0] bin2bcd12(input [11:0] bin);
	reg [27:0] s;
	integer i;
	begin
		s = {16'd0, bin};
		for (i = 0; i < 12; i = i + 1) begin
			if (s[27:24] > 4) s[27:24] = s[27:24] + 4'd3;
			if (s[23:20] > 4) s[23:20] = s[23:20] + 4'd3;
			if (s[19:16] > 4) s[19:16] = s[19:16] + 4'd3;
			if (s[15:12] > 4) s[15:12] = s[15:12] + 4'd3;
			s = s << 1;
		end
		bin2bcd12 = s[27:12];
	end
endfunction

function [31:0] ascii4(input [15:0] bcd);
	ascii4 = {4'h3, bcd[15:12], 4'h3, bcd[11:8], 4'h3, bcd[7:4], 4'h3, bcd[3:0]};
endfunction

reg [11:0] d_nowx, d_nowy, d_lx, d_ly, d_evs, d_pulls, d_minx, d_maxx, d_miny, d_maxy, d_px, d_py;
reg  [1:0] d_lock, d_msg, d_page;
reg  [3:0] d_target, d_npts;
reg        d_valid, d_trig, d_pvalid, d_intro;
reg [10:0] mx, my;
reg  [9:0] ttx;
reg  [7:0] tty;

always @(posedge clk) if (frame_tick) begin
	d_nowx <= gx; d_nowy <= gy; d_lx <= lx; d_ly <= ly;
	d_evs <= ev_rate; d_pulls <= pulls;
	d_minx <= minx; d_maxx <= maxx; d_miny <= miny; d_maxy <= maxy;
	d_lock <= lockst; d_valid <= valid; d_trig <= gtrig;
	d_px <= {2'b0, ptr_x}; d_py <= {4'b0, ptr_y};
	d_intro <= intro; d_msg <= msgc; d_page <= page; d_target <= target; d_npts <= npts; d_pvalid <= pvalid;
	mx <= {1'b0, ptr_x};
	my <= {3'b0, ptr_y};
	ttx <= tx; tty <= ty;
end

wire [31:0] f_nowx  = ascii4(bin2bcd12(d_nowx));
wire [31:0] f_nowy  = ascii4(bin2bcd12(d_nowy));
wire [31:0] f_lastx = ascii4(bin2bcd12(d_lx));
wire [31:0] f_lasty = ascii4(bin2bcd12(d_ly));
wire [31:0] f_px    = d_pvalid ? ascii4(bin2bcd12(d_px)) : "----";
wire [31:0] f_py    = d_pvalid ? ascii4(bin2bcd12(d_py)) : "----";
wire [31:0] f_evs   = ascii4(bin2bcd12(d_evs));
wire [31:0] f_pulls = ascii4(bin2bcd12(d_pulls));
wire [31:0] f_minx  = ascii4(bin2bcd12(d_minx));
wire [31:0] f_maxx  = ascii4(bin2bcd12(d_maxx));
wire [31:0] f_miny  = ascii4(bin2bcd12(d_miny));
wire [31:0] f_maxy  = ascii4(bin2bcd12(d_maxy));
wire [23:0] f_light = d_valid ? "YES" : "NO ";
wire [31:0] f_trig  = d_trig ? "DOWN" : "UP  ";
wire [63:0] f_lock  = (d_lock == 2'd1) ? "STEADY  " : (d_lock == 2'd2) ? "JUMPY   " : "NO LIGHT";
// ---------------------------------------------------------------- picture
//
// The picture is 480i: ry is the row of the 480-row picture (field 0 draws the even rows, field 1 the odd ones), and what is drawn in rows is
// really 480 rows fine. A pixel is 100 ns wide, which on a 4:3 tube is 1.21 rows, so a horizontal distance is multiplied by 310/256 where
// something must be round. Text and boxes are drawn on a grid of 2 rows, so that each field shows the same thing (no flicker).

wire [8:0] y   = scandouble ? vc[9:1] : vc[8:0];                // the line of the field (the grid of the text and the boxes)
wire [8:0] ry  = il ? {y[7:0], field} : vc[8:0];                // the row of the 480-row picture
wire [4:0] row = y[7:3];

// text: 5 x 7 glyphs, each dot 2 pixels wide and 2 rows tall (about square on the tube), in cells of 6 dots = 12 pixels x 16 rows:
// 44 columns and 30 rows
reg        sub = 0;
reg  [2:0] dot = 0;
reg  [5:0] col = 0;
always @(posedge clk) if (ce_pix) begin
	if (hc == 637) begin
		sub <= 0; dot <= 0; col <= 0;
	end else if (sub) begin
		sub <= 0;
		if (dot == 3'd5) begin dot <= 0; col <= col + 1'd1; end
			else dot <= dot + 1'd1;
	end else begin
		sub <= 1;
	end
end

wire [7:0] tch;
guncal_text txt
(
	.page(d_page), .row(row), .col(col),
	.nowx(f_nowx), .nowy(f_nowy), .lastx(f_lastx), .lasty(f_lasty), .px(f_px), .py(f_py),
	.light(f_light), .lock(f_lock), .evs(f_evs), .trig(f_trig), .pulls(f_pulls),
	.minx(f_minx), .maxx(f_maxx), .miny(f_miny), .maxy(f_maxy),
	.ch(tch)
);

reg  [7:0] a_ch;
reg  [2:0] a_gx, a_gy;
wire [5:0] fidx;
wire [4:0] fbits;
font_idx fi(.a(a_ch), .i(fidx));
font5x7  ft(.ch(fidx), .row(a_gy), .bits(fbits));

reg txt_px;
always @(posedge clk) if (ce_pix) begin
	a_ch  <= tch;
	a_gx  <= dot;
	a_gy  <= y[2:0];
	txt_px <= (a_gx < 3'd5) && (a_gy < 3'd7) && fbits[3'd4 - a_gx];
end

// the crosshair that follows the calibrated pointer (monitor and check pages); its middle is left empty so the gun keeps seeing light there
wire signed [11:0] ddx = $signed({1'b0, hc}) - $signed({1'b0, mx});
wire signed [11:0] ddy = $signed({3'b0, ry}) - $signed({3'b0, my[7:0], 1'b0});
wire [11:0] adx = ddx[11] ? -ddx : ddx;
wire [11:0] ady = ddy[11] ? -ddy : ddy;
wire [20:0] adx_r = adx * 9'd310;
wire [12:0] adxr  = adx_r[20:8];                                // the horizontal distance in rows
wire marker = d_pvalid && (((ady <= 12'd1) && (adxr >= 13'd12) && (adxr <= 13'd36)) ||
                           ((adx <= 12'd1) && (ady >= 12'd12)  && (ady <= 12'd36)));

// the target crosshair (calibration and check pages): a thin round ring with a plus and four ticks, centred where the HPS says; the ring's
// radius is 42..45 rows, a fifth of the picture's height across, the strokes are 2 rows thick (each field shows them)
wire signed [11:0] tdx = $signed({1'b0, hc}) - $signed({2'b0, ttx});
wire signed [11:0] tdy = $signed({3'b0, ry}) - $signed({3'b0, tty, 1'b0});
wire [11:0] atx = tdx[11] ? -tdx : tdx;
wire [11:0] aty = tdy[11] ? -tdy : tdy;
wire [20:0] atx_r = atx * 9'd310;
wire [12:0] atxr  = atx_r[20:8];                                // the horizontal distance in rows
wire [25:0] r2  = atxr * atxr + aty * aty;
wire bar_h = (tdy >= 0) && (tdy <= 1);                          // the two rows of the horizontal strokes
wire bar_v = (tdx >= 0) && (tdx <= 1);                          // the two pixels of the vertical strokes
wire target_px = ((r2 >= 26'd1764) && (r2 < 26'd2116)) ||                                   // ring
                 (bar_h && (atxr <= 13'd10)) || (bar_v && (aty <= 12'd10)) ||             // plus
                 (bar_v && (aty >= 12'd34) && (aty <= 12'd54)) ||                          // ticks across the ring
                 (bar_h && (atxr >= 13'd34) && (atxr <= 13'd54));

// What is drawn besides the target crosshair. At the start (page 1, nothing shot yet: intro) the title and the prompt, as a console game's own
// GunCon calibration shows them; they are gone at the first pull. While the points are asked for nothing but the target is drawn. The check
// page (2) has two buttons under the crosshair; shoot one (the app tests the shot against the same rectangles: GUNCAL_BTN_* in guncal.h, keep
// them in step).
wire cal_on   = (d_page != 2'd0);
wire flash_on = (flash != 4'd0);

wire show_intro   = (d_page == 2'd1) && d_intro;
wire in_title     = show_intro && (hc >= 156) && (hc <= 360) && (y >= 12) && (y <= 27);
wire in_prompt    = show_intro && (hc >= 24)  && (hc <= 372) && (y >= 204) && (y <= 227);
wire edge_prompt  = in_prompt && ((hc <= 25) || (hc >= 371) || (y == 204) || (y == 227));

wire in_btn_y     = (d_page == 2'd2) && (y >= 168) && (y <= 191);
wire in_btn_retry = in_btn_y && (hc >= 108) && (hc <= 240);
wire in_btn_exit  = in_btn_y && (hc >= 288) && (hc <= 420);
wire btn_edge     = (in_btn_retry && ((hc <= 109) || (hc >= 239) || (y <= 169) || (y >= 190))) ||
                    (in_btn_exit  && ((hc <= 289) || (hc >= 419) || (y <= 169) || (y >= 190)));
wire hot_y        = d_pvalid && (my >= 11'd168) && (my <= 11'd191);
wire hot_retry    = hot_y && (mx >= 11'd108) && (mx <= 11'd240);
wire hot_exit     = hot_y && (mx >= 11'd288) && (mx <= 11'd420);

reg [23:0] px_rgb;
always @* begin
	if (!cal_on) begin
		// monitor: white page, black text, black crosshair
		px_rgb = (txt_px || marker) ? 24'h000000 : 24'hFFFFFF;
	end else if (flash_on) begin
		px_rgb = 24'hFFFFFF;                                    // the flash the gun measures
	end else if (txt_px && (in_title || in_prompt)) begin
		px_rgb = 24'hFFFFFF;
	end else if (edge_prompt) begin
		px_rgb = 24'h00FFFF;
	end else if (in_title) begin
		px_rgb = 24'h2040D0;
	end else if (in_prompt) begin
		px_rgb = 24'h484020;
	end else if (btn_edge || (txt_px && (in_btn_retry || in_btn_exit))) begin
		px_rgb = 24'h00006E;
	end else if (marker && (d_page == 2'd2)) begin
		px_rgb = 24'h000000;
	end else if (in_btn_retry) begin
		px_rgb = hot_retry ? 24'h40FF40 : 24'hFFFFFF;           // light where the gun is aimed, so the aim can be seen to land
	end else if (in_btn_exit) begin
		px_rgb = hot_exit ? 24'h40FF40 : 24'hFFFFFF;
	end else if (target_px) begin
		px_rgb = 24'h0040FF;
	end else begin
		px_rgb = 24'hFFFFC0;                                    // a very light yellow: the gun sees plenty of light wherever it points
	end
end

assign rgb = px_rgb;
assign field_out = il & field;

endmodule
