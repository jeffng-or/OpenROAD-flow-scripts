(* blackbox *)
module fakeram_256x64 (
   output reg [63:0] rd_out,
   input [7:0] addr_in,
   input we_in,
   input [31:0] wd_in,
   input clk,
   input ce_in
);
endmodule
