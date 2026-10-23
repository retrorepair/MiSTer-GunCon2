// Renders one frame of the GunCal core to a text file (hc, line, rgb per picture pixel), for tools/render_frames.py.
//   iverilog -g2012 -o tb rtl/guncal.v rtl/guncal_text.v rtl/font5x7.v tools/tb_frame.v && vvp tb +page=1 +tx=63 +ty=28 +out=frame.txt
`timescale 1ns/1ps
module tb;
	reg clk = 0;
	always #25 clk = ~clk;                       // 20 MHz

	reg  reset = 1;
	reg  [31:0] gun = 0, cmd = 0, tgt = 0;
	wire ce_pix, hvz, HBlank, HSync, VBlank, VSync;
	wire [23:0] rgb;

	guncal dut(.clk(clk), .reset(reset), .pal(1'b0), .scandouble(1'b0), .gun(gun), .cmd(cmd), .tgt(tgt), .clear(1'b0),
	           .ce_pix(ce_pix), .hvcnt_atzero(hvz), .HBlank(HBlank), .HSync(HSync), .VBlank(VBlank), .VSync(VSync), .field_out(), .rgb(rgb));

	integer page, target, msg, pvalid, px, py, tx, ty, np, gx, gy, intro, fd, ticks;
	reg [1023:0] outname;
	reg vs_d = 0;
	initial dut.ce_pix = 1'b0;                  // a register with no reset: undefined in a simulator, zero when an FPGA starts

	initial begin
		if (!$value$plusargs("page=%d", page))     page = 1;
		if (!$value$plusargs("target=%d", target)) target = 0;
		if (!$value$plusargs("msg=%d", msg))       msg = 0;
		if (!$value$plusargs("pvalid=%d", pvalid)) pvalid = 0;
		if (!$value$plusargs("px=%d", px))         px = 264;
		if (!$value$plusargs("py=%d", py))         py = 120;
		if (!$value$plusargs("tx=%d", tx))         tx = 264;
		if (!$value$plusargs("ty=%d", ty))         ty = 120;
		if (!$value$plusargs("np=%d", np))         np = 5;
		if (!$value$plusargs("intro=%d", intro))   intro = 0;
		if (!$value$plusargs("gx=%d", gx))         gx = 424;
		if (!$value$plusargs("gy=%d", gy))         gy = 136;
		if (!$value$plusargs("out=%s", outname))   outname = "frame.txt";
		cmd = page | (target << 2) | (msg << 8) | (pvalid << 10) | (px << 11) | (py << 21) | (intro << 29);
		tgt = tx | (ty << 10) | (np << 18);
		gun = gx | (gy << 12);
		fd = $fopen(outname, "w");
		ticks = 0;
		#200 reset = 0;
	end

	always @(posedge clk) begin
		vs_d <= VSync;
		if (VSync && !vs_d) begin
			ticks = ticks + 1;
			if (ticks == 4) begin $fclose(fd); $finish; end
		end
		if ((ticks == 2 || ticks == 3) && ce_pix && !HBlank && !VBlank)     // both fields: the 480 rows of one frame
			$fwrite(fd, "%0d %0d %06h\n", dut.hc, dut.ry, rgb);
	end
endmodule
