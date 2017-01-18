INSTRUCTION_DEBUG = True

def debug(function):
    def wrapper(*args, **kwargs):
        if INSTRUCTION_DEBUG:
            print(f"Instruction {function.__name__}")
        function(*args, **kwargs)
    return wrapper

def debug_addr(function):
    def wrapper(*args, **kwargs):
        if INSTRUCTION_DEBUG:
            print(f"Instruction m={args[1]}, {function.__name__}, [{args[2]}]")
        function(*args, **kwargs)
    return wrapper

def debug_addr_data(function):
    def wrapper(*args, **kwargs):
        if INSTRUCTION_DEBUG:
            print(f"Instruction m={args[1]}, {function.__name__}, [{args[2]}] -> ({args[0].memory[args[2]]})")
        function(*args, **kwargs)
    return wrapper

def debug_addr_data_store(function):
    def wrapper(*args, **kwargs):
        function(*args, **kwargs)
        if INSTRUCTION_DEBUG:
            print(f"Instruction m={args[1]}, {function.__name__}, [{args[2]}] <- ({args[0].memory[args[2]]})")
    return wrapper
        

@debug
def NOP(emulator, mem_flag, data):
    pass

@debug_addr_data
def LDA(emulator, mem_flag, data):
    if mem_flag:
        emulator.reg_a.load(emulator.memory[data])
    else:
        emulator.reg_a.load(data)

@debug_addr_data
def LDB(emulator, mem_flag, data):
    if mem_flag:
        emulator.reg_b.load(emulator.memory[data])
    else:
        emulator.reg_b.load(data)

@debug
def PRA(emulator, mem_flag, data):
    print(emulator.reg_a)

@debug
def PRB(emulator, mem_flag, data):
    print(emulator.reg_b)

@debug
def ADD(emulator, mem_flag, data):
    emulator.reg_a += emulator.reg_b

@debug
def HLT(emulator, mem_flag, data):
    emulator.halt()

@debug_addr_data
def PRX(emulator, mem_flag, data):
    if mem_flag:
        print(emulator.memory[data])
    else:
        print(data)

@debug_addr
def JMP(emulator, mem_flag, data):
    if mem_flag:
        emulator.instruction_register.load(emulator.memory[data])
    else:
        emulator.instruction_register.load(data)

@debug_addr_data_store
def STA(emulator, mem_flag, data):
    emulator.memory[data] = emulator.reg_a

@debug_addr_data_store
def STB(emulator, mem_flag, data):
    emulator.memory[data] = emulator.reg_b

@debug_addr
def INC(emulator, mem_flag, data):
    emulator.memory[data] += 1
    
@debug_addr
def DEC(emulator, mem_flag, data):
    emulator.memory[data] -= 1
    
@debug_addr
def MOV(emulator, mem_flag, data):
    reg_1 = emulator.memory[255-((data & 0b11110000) >> 4)]
    reg_2 = emulator.memory[255-(data & 0b1111)]
    reg_1.load(reg_2.value)

@debug
def CMP(emulator, mem_flag, data):
    reg_a = emulator.reg_a.value
    reg_b = emulator.reg_b.value
    emulator.comparisons["JE"] = (reg_a == reg_b)
    emulator.comparisons["JG"] = (reg_a > reg_b)
    emulator.comparisons["JL"] = (reg_a < reg_b)

@debug_addr
def JE(emulator, mem_flag, data):
    if emulator.comparisons["JE"]:
        emulator.instruction_register.load(data)
        
instructions = {
    0b00000: NOP,
    0b00001: LDA,
    0b00010: LDB,
    0b00011: PRA,
    0b00100: PRB,
    0b00101: ADD,
    0b00110: HLT,
    0b00111: PRX,
    0b01000: JMP,
    0b01001: STA,
    0b01010: STB,
    0b01011: INC,
    0b01100: DEC,
    0b01101: MOV,
    0b01110: CMP,
    0b01111: JE,
}

class InstructionException(Exception):
    pass