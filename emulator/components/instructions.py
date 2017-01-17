INSTRUCTION_DEBUG = False

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
    
def PRX(emulator, mem_addr):
    if INSTRUCTION_DEBUG:
        print(f"Instruction PRX, [{mem_addr}] <- ({emulator.memory[mem_addr]})")
    print(emulator.memory[mem_addr])
    
def JMP(emulator, mem_addr):
    if INSTRUCTION_DEBUG:
        print(f"Instruction JMP, {mem_addr}")
    emulator.instruction_register.load(mem_addr)
    
def STA(emulator, mem_addr):
    if INSTRUCTION_DEBUG:
        print(f"Instruction STA, [{mem_addr}] <- ({emulator.memory[mem_addr]})")
    emulator.memory[mem_addr] = emulator.reg_a
    
def STB(emulator, mem_addr):
    if INSTRUCTION_DEBUG:
        print(f"Instruction STB, [{mem_addr}] <- ({emulator.memory[mem_addr]})")
    emulator.memory[mem_addr] = emulator.reg_b
    
def CMP(emulator, mem_addr):
    if INSTRUCTION_DEBUG:
        print(f"Instruction CMP, [{mem_addr}] <- ({emulator.memory[mem_addr]})")
    reg_a = emulator.reg_a.value
    reg_b = emulator.reg_b.value
    emulator.comparisons["JE"] = (reg_a == reg_b)
    emulator.comparisons["JG"] = (reg_a > reg_b)
    emulator.comparisons["JL"] = (reg_a < reg_b)

def JE(emulator, mem_addr):
    if INSTRUCTION_DEBUG:
        print(f"Instruction JE")
    if emulator.comparisons["JE"]:
        emulator.instruction_register.load(mem_addr)
        
instructions = {
    0b0000: NOP,
    0b0001: LDA,
    0b0010: LDB,
    0b0011: PRA,
    0b0100: PRB,
    0b0101: ADD,
    0b0110: HLT,
    0b0111: PRX,
    0b1000: JMP,
    0b1001: STA,
    0b1010: STB,
    0b1011: CMP,
    0b1100: JE,
}

class InstructionException(Exception):
    pass