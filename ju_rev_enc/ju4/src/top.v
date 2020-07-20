

module top(input clk);


    reg reset_ = 1'b0;

    always @(posedge clk) begin
        reset_ <= 1'b1;
    end

    jtag_uart u_jtag_uart (
		.clk_clk(clk),
		.reset_reset_n(reset),
		.avbus_w8_r64_chipselect(1'b0),   //  avbus_w8_r64.chipselect
//		input  wire        avbus_w8_r64_address,      //              .address
//		input  wire        avbus_w8_r64_read_n,       //              .read_n
//		output wire [31:0] avbus_w8_r64_readdata,     //              .readdata
//		input  wire        avbus_w8_r64_write_n,      //              .write_n
//		input  wire [31:0] avbus_w8_r64_writedata,    //              .writedata
//		output wire        avbus_w8_r64_waitrequest,  //              .waitrequest
		.avbus_w16_r32_chipselect(1'b0),  // avbus_w16_r32.chipselect
//		input  wire        avbus_w16_r32_address,     //              .address
//		input  wire        avbus_w16_r32_read_n,      //              .read_n
//		output wire [31:0] avbus_w16_r32_readdata,    //              .readdata
//		input  wire        avbus_w16_r32_write_n,     //              .write_n
//		input  wire [31:0] avbus_w16_r32_writedata,   //              .writedata
//		output wire        avbus_w16_r32_waitrequest, //              .waitrequest
		.avbus_w32r16_chipselect(1'b0),   //  avbus_w32r16.chipselect
//		input  wire        avbus_w32r16_address,      //              .address
//		input  wire        avbus_w32r16_read_n,       //              .read_n
//		output wire [31:0] avbus_w32r16_readdata,     //              .readdata
//		input  wire        avbus_w32r16_write_n,      //              .write_n
//		input  wire [31:0] avbus_w32r16_writedata,    //              .writedata
//		output wire        avbus_w32r16_waitrequest   //              .waitrequest
		.avbus_w8r2048_chipselect(1'b0)   //  avbus_w32r16.chipselect
	);

endmodule

