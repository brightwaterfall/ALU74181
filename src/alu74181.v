/*
 * Copyright (c) 2026 gddwms
 * SPDX-License-Identifier: Apache-2.0
 *
 * SN74xx181-compatible 4-bit ALU (active-high A/B/F).
 * Cn_n is active-low carry-in (TTL pin name Cn).
 */

`default_nettype none

module alu74181 (
    input  wire [3:0] A,
    input  wire [3:0] B,
    input  wire [3:0] S,
    input  wire       M,
    input  wire       Cn_n,
    output reg  [3:0] F,
    output wire       AeqB,
    output wire       P_n,
    output wire       G_n,
    output reg        Cn4_n
);

  // cin=1 when TTL Cn is asserted (low)
  wire cin = ~Cn_n;

  wire [3:0] A_and_B  = A & B;
  wire [3:0] A_and_nB = A & ~B;
  wire [3:0] A_or_B   = A | B;
  wire [3:0] A_or_nB  = A | ~B;

  reg [4:0] arith;

  always @(*) begin
    F     = 4'b0000;
    Cn4_n = 1'b1;
    arith = 5'b00000;

    if (M) begin
      // Logic mode (M=1) — TI active-high data table
      case (S)
        4'b0000: F = ~A;
        4'b0001: F = ~(A | B);
        4'b0010: F = ~A & B;
        4'b0011: F = 4'b0000;
        4'b0100: F = ~(A & B);
        4'b0101: F = ~B;
        4'b0110: F = A ^ B;
        4'b0111: F = A & ~B;
        4'b1000: F = ~A | B;
        4'b1001: F = ~(A ^ B);
        4'b1010: F = B;
        4'b1011: F = A & B;
        4'b1100: F = 4'b1111;
        4'b1101: F = A | ~B;
        4'b1110: F = A | B;
        default: F = A;
      endcase
      Cn4_n = 1'b1;
    end else begin
      // Arithmetic mode (M=0)
      // cin=0 => Cn high column; cin=1 => Cn low column
      case (S)
        4'b0000: arith = {1'b0, A} + cin;
        4'b0001: arith = {1'b0, A_or_B} + cin;
        4'b0010: arith = {1'b0, A_or_nB} + cin;
        4'b0011: arith = 5'h0f + cin;
        4'b0100: arith = {1'b0, A} + {1'b0, A_and_nB} + cin;
        4'b0101: arith = {1'b0, A_or_B} + {1'b0, A_and_nB} + cin;
        // A-B-1 / A-B  == A + ~B + cin
        4'b0110: arith = {1'b0, A} + {1'b0, ~B} + cin;
        // (A&~B)-1 / (A&~B) == (A&~B) + cin - 1
        4'b0111: arith = {1'b0, A_and_nB} + cin - 5'd1;
        4'b1000: arith = {1'b0, A} + {1'b0, A_and_B} + cin;
        4'b1001: arith = {1'b0, A} + {1'b0, B} + cin;
        4'b1010: arith = {1'b0, A_or_nB} + {1'b0, A_and_B} + cin;
        // (A&B)-1 / (A&B)
        4'b1011: arith = {1'b0, A_and_B} + cin - 5'd1;
        4'b1100: arith = {1'b0, A} + {1'b0, A} + cin;
        4'b1101: arith = {1'b0, A_or_B} + {1'b0, A} + cin;
        4'b1110: arith = {1'b0, A_or_nB} + {1'b0, A} + cin;
        // A-1 / A
        default: arith = {1'b0, A} + cin - 5'd1;
      endcase
      F     = arith[3:0];
      Cn4_n = ~arith[4];
    end
  end

  assign AeqB = &F;

  // Carry look-ahead P/G (active-low), classic style from A/B/S
  wire [3:0] p = ~(({4{S[1]}} & ~B) | ({4{S[0]}} & B) | A);
  wire [3:0] g = ~(({4{S[3]}} & B) | ({4{S[2]}} & ~B) | A);

  assign P_n = ~(&p);
  assign G_n = ~(
      g[3]
    | (p[3] & g[2])
    | (p[3] & p[2] & g[1])
    | (p[3] & p[2] & p[1] & g[0])
  );

endmodule
