

module top(input clk);


    reg reset_ = 1'b0;

    always @(posedge clk) begin
        reset_ <= 1'b1;
    end

    jtag_uart u_jtag_uart (
		.clk_clk(clk),
		.reset_reset_n(reset),
		.avbus_chipselect(1'b0)   //  avbus_w8_r64.chipselect
//		input  wire        avbus_w8_r64_address,      //              .address
//		input  wire        avbus_w8_r64_read_n,       //              .read_n
//		output wire [31:0] avbus_w8_r64_readdata,     //              .readdata
//		input  wire        avbus_w8_r64_write_n,      //              .write_n
//		input  wire [31:0] avbus_w8_r64_writedata,    //              .writedata
//		output wire        avbus_w8_r64_waitrequest,  //              .waitrequest

	);

endmodule

