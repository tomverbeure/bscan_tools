

module top(input clk);

    reg reset_ = 1'b0;

    always @(posedge clk) begin
        reset_ <= 1'b1;
    end

    reg read_n, write_n, address;
    reg [31:0] writedata; 
    wire [31:0] readdata;
    wire waitrequest;

    jtag_uart u_jtag_uart (
        .clk_clk(clk),
        .reset_reset_n(reset_),
        .avbus_chipselect(1'b1),                   
        .avbus_address(address),           
        .avbus_read_n(read_n),
        .avbus_readdata(readdata),
        .avbus_write_n(write_n),
        .avbus_writedata(writedata),
        .avbus_waitrequest(waitrequest)
	);

    reg [20:0] counter = 0;

    always @(posedge clk) begin
        counter <= counter + 1;
    end

    reg [2:0] cur_state, nxt_state = 0;
    reg [7:0] byte_val = 48;
    reg [7:0] byte_val_nxt;

    always @(*) begin
        nxt_state       = cur_state;
        byte_val_nxt    = byte_val;

        case(cur_state) 
            0: begin
                read_n      = 1'b1;
                write_n     = 1'b1;
                address     = 1'b0;

                if (counter == 21'h100000) begin
                    nxt_state   = 1;
                end
            end
            1: begin
                write_n     = 1'b0;
                writedata   = { 24'd0, byte_val };

                if (!waitrequest) begin
                    nxt_state       = 0;

                    if (byte_val < 100)
                        byte_val_nxt    = byte_val + 1;
                    else
                        byte_val_nxt    = 48;
                end
            end
        endcase
    end

    always @(posedge clk) begin
        cur_state <= nxt_state;
        byte_val  <= byte_val_nxt;
    end

endmodule

