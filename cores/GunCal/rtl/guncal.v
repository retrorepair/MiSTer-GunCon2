// GunCon 2 calibration and monitor core: a 15 kHz picture for the gun to look at.
//
// Words from the HPS (a Main_MiSTer with guncal support):
//   gun  (joystick_5)  [11:0] raw X  [23:12] raw Y  [24] trigger        the gun's raw report
//   cmd  (joystick_4)  [1:0] page (0 monitor, 1 calibration, 2 check)  [5:2] target number  [7:6] flash sequence
//                      [9:8] message  [10] pointer valid  [20:11] pointer x  [28:21] pointer y   (core pixels)
//   tgt  (joystick_3)  [9:0] target x  [17:10] target y  [21:18] number of targets            (core pixels)
// The core draws and displays; the sequencing and the maths live in the HPS (guncal.cpp).
//
// Picture: 529 x 240 active, pixel clock 10 MHz, 15.7 kHz / 59.8 Hz (NTSC) or PAL timing. A CRT hides part of this
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

	output [23:0] rgb
);

// ---------------------------------------------------------------- video timing (same as the MiSTer template)

reg [9:0] hc = 0;
reg [9:0] vc = 0;

assign hvcnt_atzero = ce_pix && !hc && !vc;

always @(posedge clk) begin
	if(scandouble) ce_pix <= 1;
		else ce_pix <= ~ce_pix;

	if(ce_pix) begin
		if(hc == 637) begin
			hc <= 0;
			if(vc >= (pal ? (scandouble ? 623 : 311) : (scandouble ? 523 : 261))) vc <= 0;
				else vc <= vc + 1'd1;
		end else begin
			hc <= hc + 1'd1;
		end
	end
end

always @(posedge clk) begin
	if (hc == 529) HBlank <= 1;
		else if (hc == 0) HBlank <= 0;

	if (hc == 544) begin
		HSync <= 1;

		if(pal) begin
			if(vc == (scandouble ? 609 : 304)) VSync <= 1;
				else if (vc == (scandouble ? 617 : 308)) VSync <= 0;

			if(vc == (scandouble ? 601 : 300)) VBlank <= 1;
				else if (vc == 0) VBlank <= 0;
		end
		else begin
			if(vc == (scandouble ? 490 : 245)) VSync <= 1;
				else if (vc == (scandouble ? 496 : 248)) VSync <= 0;

			if(vc == (scandouble ? 480 : 240)) VBlank <= 1;
				else if (vc == 0) VBlank <= 0;
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
reg        d_valid, d_trig, d_pvalid;
reg [10:0] mx, my;
reg  [9:0] ttx;
reg  [7:0] tty;

always @(posedge clk) if (frame_tick) begin
	d_nowx <= gx; d_nowy <= gy; d_lx <= lx; d_ly <= ly;
	d_evs <= ev_rate; d_pulls <= pulls;
	d_minx <= minx; d_maxx <= maxx; d_miny <= miny; d_maxy <= maxy;
	d_lock <= lockst; d_valid <= valid; d_trig <= gtrig;
	d_px <= {2'b0, ptr_x}; d_py <= {4'b0, ptr_y};
	d_msg <= msgc; d_page <= page; d_target <= target; d_npts <= npts; d_pvalid <= pvalid;
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
wire  [7:0] f_pt    = 8'h31 + {4'd0, d_target};                 // '1'..'9'
wire  [7:0] f_np    = 8'h30 + {4'd0, d_npts};
wire [175:0] f_msg  = (d_msg == 2'd1) ? "MISSED - TRY AGAIN    " :
                      (d_msg == 2'd2) ? "SAVED                 " :
                      (d_msg == 2'd3) ? "BAD SHOTS - START OVER" : "                      ";

// ---------------------------------------------------------------- picture

wire [8:0] y   = scandouble ? vc[9:1] : vc[8:0];
wire [5:0] col = hc[9:4];
wire [3:0] row = y[7:4];

wire [7:0] tch;
guncal_text txt
(
	.page(d_page), .row(row), .col(col),
	.nowx(f_nowx), .nowy(f_nowy), .lastx(f_lastx), .lasty(f_lasty), .px(f_px), .py(f_py),
	.light(f_light), .lock(f_lock), .evs(f_evs), .trig(f_trig), .pulls(f_pulls),
	.minx(f_minx), .maxx(f_maxx), .miny(f_miny), .maxy(f_maxy),
	.pt(f_pt), .np(f_np), .msg(f_msg),
	.ch(tch)
);

// each glyph is 5 x 7 pixels drawn at 2 x 2 in a 16 x 16 cell
reg  [7:0] a_ch;
reg  [2:0] a_gx, a_gy;
wire [5:0] fidx;
wire [4:0] fbits;
font_idx fi(.a(a_ch), .i(fidx));
font5x7  ft(.ch(fidx), .row(a_gy), .bits(fbits));

reg txt_px;
always @(posedge clk) if (ce_pix) begin
	a_ch  <= tch;
	a_gx  <= hc[3:1];
	a_gy  <= y[3:1];
	txt_px <= (a_gx < 3'd5) && (a_gy < 3'd7) && fbits[3'd4 - a_gx];
end

// crosshair at the calibrated pointer (monitor and check pages); its middle is left empty so the gun keeps seeing light there
wire signed [11:0] ddx = $signed({1'b0, hc}) - $signed({1'b0, mx});
wire signed [11:0] ddy = $signed({3'b0, y})  - $signed({1'b0, my});
wire [11:0] adx = ddx[11] ? -ddx : ddx;
wire [11:0] ady = ddy[11] ? -ddy : ddy;
wire marker = d_pvalid && (((ady <= 12'd1) && (adx >= 12'd10) && (adx <= 12'd30)) ||
                           ((adx <= 12'd1) && (ady >= 12'd8)  && (ady <= 12'd20)));

// calibration and check pages: a ring with a plus and four ticks, centred where the HPS says
wire signed [11:0] tdx = $signed({1'b0, hc}) - $signed({2'b0, ttx});
wire signed [11:0] tdy = $signed({3'b0, y})  - $signed({4'b0, tty});
wire [11:0] atx = tdx[11] ? -tdx : tdx;
wire [11:0] aty = tdy[11] ? -tdy : tdy;
wire [23:0] r2  = atx * atx + aty * aty;
wire target_px = ((r2 >= 24'd324) && (r2 <= 24'd529)) ||                                   // ring, radius 18..23
                 ((aty <= 12'd1) && (atx <= 12'd12)) || ((atx <= 12'd1) && (aty <= 12'd12)) ||   // plus
                 ((atx <= 12'd1) && (aty >= 12'd23) && (aty <= 12'd29)) ||                 // ticks
                 ((aty <= 12'd1) && (atx >= 12'd23) && (atx <= 12'd29));

// boxes like the PS1 GunCon calibration screen: a navy title, olive prompts with a cyan border
wire in_title  = (hc >= 60)  && (hc <= 468) && (y >= 10)  && (y <= 36);
wire in_prompt = (hc >= 24)  && (hc <= 504) && (y >= 56)  && (y <= 104);
wire in_bottom = (hc >= 24)  && (hc <= 504) && (y >= 168) && (y <= 228);
wire edge_prompt = in_prompt && ((hc <= 26) || (hc >= 502) || (y <= 58)  || (y >= 102));
wire edge_bottom = in_bottom && ((hc <= 26) || (hc >= 502) || (y <= 170) || (y >= 226));

wire cal_on   = (d_page != 2'd0);
wire flash_on = (flash != 4'd0);

reg [23:0] px_rgb;
always @* begin
	if (!cal_on) begin
		// monitor: white page, black text, black crosshair
		px_rgb = (txt_px || marker) ? 24'h000000 : 24'hFFFFFF;
	end else if (flash_on && (d_page == 2'd1)) begin
		px_rgb = 24'hFFFFFF;                                    // the flash the gun measures
	end else if (txt_px && (in_title || in_prompt || in_bottom)) begin
		px_rgb = 24'hFFFFFF;
	end else if (edge_prompt || edge_bottom) begin
		px_rgb = 24'h00FFFF;
	end else if (in_title) begin
		px_rgb = 24'h00006E;
	end else if (in_prompt || in_bottom) begin
		px_rgb = 24'h484020;
	end else if (target_px) begin
		px_rgb = 24'h0040FF;
	end else if (marker && d_page == 2'd2) begin
		px_rgb = 24'h000000;
	end else begin
		px_rgb = 24'hE0F77F;                                    // bright, so the gun sees light wherever it points
	end
end

assign rgb = px_rgb;

endmodule
