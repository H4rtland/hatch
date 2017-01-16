INSTRUCTION_DEBUG = True

def NOP(emulator, mem_addr):
    if INSTRUCTION_DEBUG:
        print("Instruction NOP")
    pass

def LDA(emulator, mem_addr):
    if INSTRUCTION_DEBUG:
        print(f"Instruction LDA, [{mem_addr}] <- ({emulator.memory[mem_addr]})")
    emulator.reg_a.load(emulator.memory[mem_addr])
    
def LDB(emulator, mem_addr):
    if INSTRUCTION_DEBUG:
        print(f"Instruction LDB, [{mem_addr}] <- ({emulator.memory[mem_addr]})")
    emulator.reg_b.load(emulator.memory[mem_addr])
    
def PRA(emulator, mem_addr):
    if INSTRUCTION_DEBUG:
        print(f"Instruction PRA")
    print(emulator.reg_a)
    
def PRB(emulator, mem_addr):
    if INSTRUCTION_DEBUG:
        print(f"Instruction PRA")
    print(emulator.reg_b)
    
def ADD(emulator, mem_addr):
    if INSTRUCTION_DEBUG:
        print(f"Instruction ADD")
    emulator.reg_a += emulator.reg_b
    
def HLT(emulator, mem_addr):
    if INSTRUCTION_DEBUG:
        print(f"Instruction HLT")
    emulator.halt()
        
instructions = {
    0b0000: NOP,
    0b0001: LDA,
    0b0010: LDB,
    0b0011: PRA,
    0b0100: PRB,
    0b0101: ADD,
    0b0110: HLT,
}

class InstructionException(Exception):
    pass