// (C) 2001-2013 Altera Corporation. All rights reserved.
// Your use of Altera Corporation's design tools, logic functions and other 
// software and tools, and its AMPP partner logic functions, and any output 
// files any of the foregoing (including device programming or simulation 
// files), and any associated documentation or information are expressly subject 
// to the terms and conditions of the Altera Program License Subscription 
// Agreement, Altera MegaCore Function License Agreement, or other applicable 
// license agreement, including, without limitation, that your use is for the 
// sole purpose of programming logic devices manufactured by Altera and sold by 
// Altera or its authorized distributors.  Please refer to the applicable 
// agreement for further details.


// $Id: //acds/rel/13.0sp1/ip/merlin/altera_reset_controller/altera_reset_controller.v#2 $
// $Revision: #2 $
// $Date: 2013/06/03 $
// $Author: wkleong $

// --------------------------------------
// Reset controller
//
// Combines all the input resets and synchronizes
// the result to the clk.
// ACDS13.1 - Added reset request as part of reset sequencing
// --------------------------------------

`timescale 1 ns / 1 ns

module altera_reset_controller
#(
    parameter NUM_RESET_INPUTS        = 6,
    parameter OUTPUT_RESET_SYNC_EDGES = "deassert",
    parameter SYNC_DEPTH              = 2,
    parameter RESET_REQUEST_PRESENT   = 0
)
(
    // --------------------------------------
    // We support up to 16 reset inputs, for now
    // --------------------------------------
    input reset_in0,
    input reset_in1,
    input reset_in2,
    input reset_in3,
    input reset_in4,
    input reset_in5,
    input reset_in6,
    input reset_in7,
    input reset_in8,
    input reset_in9,
    input reset_in10,
    input reset_in11,
    input reset_in12,
    input reset_in13,
    input reset_in14,
    input reset_in15,

    input  clk,
    output reg reset_out,
    output reg reset_req
);

   localparam ASYNC_RESET = (OUTPUT_RESET_SYNC_EDGES == "deassert");

   localparam DEPTH = 2;
   localparam CLKEN_LAGS_RESET = 0;
   localparam EARLY_RST_TAP = (CLKEN_LAGS_RESET != 0) ? 0 : 1;

   wire merged_reset;
   wire reset_out_pre;

   // Registers and Interconnect
   (*preserve*) reg  [SYNC_DEPTH: 0]   altera_reset_synchronizer_int_chain;
   reg   [(SYNC_DEPTH-1): 0]           r_sync_rst_chain;
   reg                                 r_sync_rst_dly;
   reg                                 r_sync_rst;
   reg                                 r_early_rst;
   
    // --------------------------------------
    // "Or" all the input resets together
    // --------------------------------------
    assign merged_reset = (  
                              reset_in0 | 
                              reset_in1 | 
                              reset_in2 | 
                              reset_in3 | 
                              reset_in4 | 
                              reset_in5 | 
                              reset_in6 | 
                              reset_in7 | 
                              reset_in8 | 
                              reset_in9 | 
                              reset_in10 | 
                              reset_in11 | 
                              reset_in12 | 
                              reset_in13 | 
                              reset_in14 | 
                              reset_in15
                          );

    // --------------------------------------
    // And if required, synchronize it to the required clock domain,
    // with the correct synchronization type
    // --------------------------------------
    generate if (OUTPUT_RESET_SYNC_EDGES == "none") begin

        assign reset_out_pre = merged_reset;

    end else begin

        altera_reset_synchronizer
        #(
            .DEPTH      (SYNC_DEPTH),
            .ASYNC_RESET(ASYNC_RESET)
        )
        alt_rst_sync_uq1
        (
            .clk        (clk),
            .reset_in   (merged_reset),
            .reset_out  (reset_out_pre)
        );

    end
    endgenerate

    generate if (RESET_REQUEST_PRESENT == 0) begin
        always @* begin
            reset_out = reset_out_pre;
            reset_req = 1'b0;
        end
    end
    else begin

    // 3-FF Metastability Synchronizer
    initial
    begin
        altera_reset_synchronizer_int_chain <= 3'b111;
    end

    always @(posedge clk)
    begin
        altera_reset_synchronizer_int_chain[2:0] <= {altera_reset_synchronizer_int_chain[1:0], reset_out_pre}; 
    end


    // Synchronous reset pipe
    initial
    begin
        r_sync_rst_chain <= {DEPTH{1'b1}};
    end

    always @(posedge clk)
    begin
        if (altera_reset_synchronizer_int_chain[2] == 1'b1)
        begin
            r_sync_rst_chain <= {DEPTH{1'b1}};
    end
    else
    begin
        r_sync_rst_chain <= {1'b0, r_sync_rst_chain[DEPTH-1:1]};
    end
    end

    // Standard synchronous reset output.  From 0-1, the transition lags the early output.  For 1->0, the transition
    // matches the early input.
    initial
    begin
        r_sync_rst_dly <= 1'b1;
        r_sync_rst     <= 1'b1;
        r_early_rst    <= 1'b1;
    end

    always @(posedge clk)
    begin
        // Delayed reset pipeline register
        r_sync_rst_dly <= r_sync_rst_chain[DEPTH-1];

        case ({r_sync_rst_dly, r_sync_rst_chain[1], r_sync_rst})
            3'b000:   r_sync_rst <= 1'b0; // Not reset
            3'b001:   r_sync_rst <= 1'b0;
            3'b010:   r_sync_rst <= 1'b0;
            3'b011:   r_sync_rst <= 1'b1;
            3'b100:   r_sync_rst <= 1'b1; 
            3'b101:   r_sync_rst <= 1'b1;
            3'b110:   r_sync_rst <= 1'b1;
            3'b111:   r_sync_rst <= 1'b1; // In Reset
            default:  r_sync_rst <= 1'b1;
        endcase

        case ({r_sync_rst_chain[DEPTH-1], r_sync_rst_chain[EARLY_RST_TAP]})
            2'b00:   r_early_rst <= 1'b0; // Not reset
            2'b01:   r_early_rst <= 1'b1; // Coming out of reset
            2'b10:   r_early_rst <= 1'b0; // Spurious reset - should not be possible via synchronous design.
            2'b11:   r_early_rst <= 1'b1; // Held in reset
            default: r_early_rst <= 1'b1;
        endcase
    end

    always @* begin
        reset_out = r_sync_rst;
        reset_req = r_early_rst;
    end

    end
    endgenerate

endmodule
