from enum import Enum

class Instruction(Enum):
    NOP =   0b00000
    LDA =   0b00001
    LDB =   0b00010
    FREE =  0b00011
    PRB =   0b00100
    ADD =   0b00101
    HLT =   0b00110
    PRX =   0b00111
    JMP =   0b01000
    STA =   0b01001
    STB =   0b01010
    INC =   0b01011
    DEC =   0b01100
    MOV =   0b01101
    CMP =   0b01110
    JE =    0b01111
    NEG =   0b10000
    CALL =  0b10001
    RET =   0b10010
    PUSH =  0b10011
    POP =   0b10100
    SAVE =  0b10101
    JNE =   0b10110
    JG =    0b10111
    JL =    0b11000
    JGE =   0b11001
    JLE =   0b11010
    OFF =   0b11011
    MUL =   0b11100
    DIV =   0b11101
    PRC =   0b11110
    DUP =   0b11111
    
class Register(Enum):
    AX = 0
    BX = 1
    CX = 2
    INST = 3
    FX = 4
    OX = 5
    
def mov(into, from_):
    return ((into.value) << 4) + (from_.value)