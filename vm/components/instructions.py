from settings import debug as INSTRUCTION_DEBUG

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
def NOP(emulator, mem_flag, stack_flag, data):
    pass

@debug_addr_data
def LDA(emulator, mem_flag, stack_flag, data):
    if mem_flag:
        emulator.reg_a.load(emulator.memory[data])
    elif stack_flag:
        emulator.reg_a.load(emulator.memory[emulator.stack[-data]])
    else:
        emulator.reg_a.load(data)

@debug_addr_data
def LDB(emulator, mem_flag, stack_flag, data):
    if mem_flag:
        emulator.reg_b.load(emulator.memory[data])
    elif stack_flag:
        emulator.reg_b.load(emulator.memory[emulator.stack[-data]])
    else:
        emulator.reg_b.load(data)

@debug
def PRA(emulator, mem_flag, stack_flag, data):
    print(emulator.reg_a)

@debug
def PRB(emulator, mem_flag, stack_flag, data):
    print(emulator.reg_b)

@debug
def ADD(emulator, mem_flag, stack_flag, data):
    emulator.reg_a += emulator.reg_b

@debug
def HLT(emulator, mem_flag, stack_flag, data):
    emulator.halt()

@debug_addr_data
def PRX(emulator, mem_flag, stack_flag, data):
    if mem_flag:
        print(emulator.memory[data])
    elif stack_flag:
        print(emulator.memory[emulator.stack[-data]])
    else:
        print(data)

@debug_addr
def JMP(emulator, mem_flag, stack_flag, data):
    if mem_flag:
        emulator.instruction_register.load(emulator.memory[data])
    else:
        emulator.instruction_register.load(data)

@debug_addr_data_store
def STA(emulator, mem_flag, stack_flag, data):
    if stack_flag:
        emulator.memory[emulator.stack[-data]] = emulator.reg_a.value
    else:
        emulator.memory[data] = emulator.reg_a.value

@debug_addr_data_store
def STB(emulator, mem_flag, stack_flag, data):
    if stack_flag:
        emulator.memory[emulator.stack[-data]] = emulator.reg_b.value
    else:
        emulator.memory[data] = emulator.reg_b.value

@debug_addr
def INC(emulator, mem_flag, stack_flag, data):
    if stack_flag:
        emulator.memory[emulator.stack[-data]] += 1
    emulator.memory[data] += 1
    
@debug_addr
def DEC(emulator, mem_flag, stack_flag, data):
    if stack_flag:
        emulator.memory[emulator.stack[-data]] -= 1
    emulator.memory[data] -= 1
    
@debug_addr
def MOV(emulator, mem_flag, stack_flag, data):
    reg_1 = emulator.memory[255-((data & 0b11110000) >> 4)]
    reg_2 = emulator.memory[255-(data & 0b1111)]
    reg_1.load(reg_2.value)

@debug
def CMP(emulator, mem_flag, stack_flag, data):
    reg_a = emulator.reg_a.value
    reg_b = emulator.reg_b.value
    emulator.comparisons["JE"] = (reg_a == reg_b)
    emulator.comparisons["JG"] = (reg_a > reg_b)
    emulator.comparisons["JL"] = (reg_a < reg_b)
    emulator.comparisons["JNE"] = (reg_a != reg_b)

@debug_addr
def JE(emulator, mem_flag, stack_flag, data):
    if emulator.comparisons["JE"]:
        emulator.instruction_register.load(data)

@debug
def NEG(emulator, mem_flag, stack_flag, data):
    emulator.reg_a -= emulator.reg_b

@debug_addr
def CALL(emulator, mem_flag, stack_flag, data):
    emulator.call_stack.append(emulator.instruction_register.value)
    emulator.instruction_register.load(data)

@debug_addr
def RET(emulator, mem_flag, stack_flag, data):
    emulator.instruction_register.load(emulator.call_stack.pop())
    if not stack_flag:
        emulator.reg_func.load(data)
    emulator.reg_b.load(emulator.stack[-1])
    emulator.reg_a.load(emulator.stack[-2])
    emulator.stack = emulator.stack[:-2]

@debug_addr
def PUSH(emulator, mem_flag, stack_flag, data):
    into_addr = 0
    for addr, occupied in emulator.memory_map.items():
        if not occupied:
            into_addr = addr
            break
    else:
        raise Exception("Out of memory")
    emulator.memory_map[into_addr] = True
    emulator.stack.append(into_addr)
    # print("Using memory address", into_addr)

@debug_addr_data
def POP(emulator, mem_flag, stack_flag, data):
    emulator.stack = emulator.stack[:-data]

@debug
def SAVE(emulator, mem_flag, stack_flag, data):
    emulator.stack.append(emulator.reg_a.value)
    emulator.stack.append(emulator.reg_b.value)
    
@debug_addr
def JNE(emulator, mem_flag, stack_flag, data):
    if emulator.comparisons["JNE"]:
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
    0b10000: NEG,
    0b10001: CALL,
    0b10010: RET,
    0b10011: PUSH,
    0b10100: POP,
    0b10101: SAVE,
    0b10110: JNE,
}

class InstructionException(Exception):
    pass