INSTRUCTION_DEBUG = False

def debug(function):
    def wrapper(*args, **kwargs):
        if INSTRUCTION_DEBUG:
            print(f"Instruction {function.__name__}")
        function(*args, **kwargs)
    return wrapper

def debug_addr(function):
    def wrapper(*args, **kwargs):
        if INSTRUCTION_DEBUG:
            print(f"Instruction {function.__name__}, [{args[1]}]")
        function(*args, **kwargs)
    return wrapper

def debug_addr_data(function):
    def wrapper(*args, **kwargs):
        if INSTRUCTION_DEBUG:
            print(f"Instruction {function.__name__}, [{args[1]}] -> ({args[0].memory[args[1]]})")
        function(*args, **kwargs)
    return wrapper

def debug_addr_data_store(function):
    def wrapper(*args, **kwargs):
        if INSTRUCTION_DEBUG:
            print(f"Instruction {function.__name__}, [{args[1]}] <- ({args[0].memory[args[1]]})")
        function(*args, **kwargs)
    return wrapper
        

@debug
def NOP(emulator, mem_addr):
    pass

@debug_addr_data
def LDA(emulator, mem_addr):
    emulator.reg_a.load(emulator.memory[mem_addr])

@debug_addr_data
def LDB(emulator, mem_addr):
    emulator.reg_b.load(emulator.memory[mem_addr])

@debug
def PRA(emulator, mem_addr):
    print(emulator.reg_a)

@debug
def PRB(emulator, mem_addr):
    print(emulator.reg_b)

@debug
def ADD(emulator, mem_addr):
    emulator.reg_a += emulator.reg_b

@debug
def HLT(emulator, mem_addr):
    emulator.halt()

@debug_addr_data
def PRX(emulator, mem_addr):
    print(emulator.memory[mem_addr])

@debug_addr
def JMP(emulator, mem_addr):
    emulator.instruction_register.load(mem_addr)

@debug_addr_data_store
def STA(emulator, mem_addr):
    emulator.memory[mem_addr] = emulator.reg_a

@debug_addr_data_store
def STB(emulator, mem_addr):
    emulator.memory[mem_addr] = emulator.reg_b

@debug_addr
def INC(emulator, mem_addr):
    emulator.memory[mem_addr] += 1
    
@debug_addr
def MOV(emulator, mem_addr):
    reg_1 = emulator.memory[255-((mem_addr & 0b11110000) >> 4)]
    reg_2 = emulator.memory[255-(mem_addr & 0b1111)]
    reg_1.load(reg_2.value)

@debug_addr_data
def CMP(emulator, mem_addr):
    reg_a = emulator.reg_a.value
    reg_b = emulator.reg_b.value
    emulator.comparisons["JE"] = (reg_a == reg_b)
    emulator.comparisons["JG"] = (reg_a > reg_b)
    emulator.comparisons["JL"] = (reg_a < reg_b)

@debug_addr
def JE(emulator, mem_addr):
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
    0b1011: INC,
    0b1100: MOV,
    0b1101: CMP,
    0b1110: JE,
}

class InstructionException(Exception):
    pass