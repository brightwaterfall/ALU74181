/*
 * Copyright (c) 2026 brightwaterfall / gddwms
 * SPDX-License-Identifier: Apache-2.0
 *
 * Tiny Tapeout top: 74181 4-bit ALU
 *
 * Pin map
 *   ui_in[3:0]  = A[3:0]
 *   ui_in[7:4]  = B[3:0]
 *   uio_in[3:0] = S[3:0]
 *   uio_in[4]   = M
 *   uio_in[5]   = Cn_n (active-low carry in)
 *   uio_in[7:6] = unused (must be driven 0 on PCB / tie down)
 *   uo_out[3:0] = F[3:0]
 *   uo_out[4]   = AeqB
 *   uo_out[5]   = P_n
 *   uo_out[6]   = G_n
 *   uo_out[7]   = Cn4_n
 */

`default_nettype none

module tt_um_brightwaterfall_alu74181 (
    input  wire [7:0] ui_in,
    output wire [7:0] uo_out,
    input  wire [7:0] uio_in,
    output wire [7:0] uio_out,
    output wire [7:0] uio_oe,
    input  wire       ena,
    input  wire       clk,
    input  wire       rst_n
);

  wire [3:0] A    = ui_in[3:0];
  wire [3:0] B    = ui_in[7:4];
  wire [3:0] S    = uio_in[3:0];
  wire       M    = uio_in[4];
  wire       Cn_n = uio_in[5];

  wire [3:0] F;
  wire       AeqB;
  wire       P_n;
  wire       G_n;
  wire       Cn4_n;

  // When tile not selected (ena=0), still safe combinational decode;
  // force outputs low to avoid fighting other tiles on shared bus demos.
  wire [3:0] F_i;
  wire       AeqB_i, P_n_i, G_n_i, Cn4_n_i;

  alu74181 u_alu (
      .A    (A),
      .B    (B),
      .S    (S),
      .M    (M),
      .Cn_n (Cn_n),
      .F    (F_i),
      .AeqB (AeqB_i),
      .P_n  (P_n_i),
      .G_n  (G_n_i),
      .Cn4_n(Cn4_n_i)
  );

  assign F     = ena ? F_i     : 4'h0;
  assign AeqB  = ena ? AeqB_i  : 1'b0;
  assign P_n   = ena ? P_n_i   : 1'b0;
  assign G_n   = ena ? G_n_i   : 1'b0;
  assign Cn4_n = ena ? Cn4_n_i : 1'b0;

  assign uo_out  = {Cn4_n, G_n, P_n, AeqB, F};
  assign uio_out = 8'h00;
  assign uio_oe  = 8'h00; // uio used as inputs only

  wire _unused = &{clk, rst_n, uio_in[7:6], 1'b0};

endmodule
