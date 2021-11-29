; References:
;   $HOME/ti/ccs1020/ccs/tools/compiler/ti-cgt-msp430_20.2.3.LTS/lib/src/div16u.asm
;   https://www.ti.com/lit/ug/slau131r/slau131r.pdf (for .xxx directives)
;   https://www.ti.com/lit/an/slaa664/slaa664.pdf (for calling convention)
;   https://www.ti.com/lit/ug/slau132x/slau132x.pdf (for RET vs. RETA)

    .if $DEFINED(__LARGE_CODE_MODEL__)
       .asg RETA, RET
       .asg 4,    RETADDRSZ
    .else
       .asg 2,    RETADDRSZ
    .endif

    .if __TI_EABI__
        .asg R12, ARG1
    .else
        .asg R15, ARG1
    .endif

    .global our_delay_cycles_internal

our_delay_cycles_internal: .asmfunc stack_usage(RETADDRSZ)
.Lour_delay_cycles_loop:
    ; based on assembly code generated by __delay_cycles()
    DEC ARG1
    NOP
    JNE .Lour_delay_cycles_loop
    RET
    .endasmfunc
