from compiler.expressions import *
from compiler.tokenizer import TokenType

AX = 0
BX = 1
CX = 2
INST = 3
FX = 4

def mov(into, from_):
    return ((into) << 4) + (from_)

class DataAddress:
    def __init__(self, addr):
        self.addr = addr
        
    def __repr__(self):
        return f"<DataAddress: {self.addr}>"
    
class FunctionAddress:
    def __init__(self, func_name):
        self.func_name = func_name
    
    def __repr__(self):
        return f"<FuncAddress: {self.func_name}>"


class MemoryBlock:
    def __init__(self, length, var_type):
        self.length = length
        self.var_type = var_type
    
    def __repr__(self):
        return f"<MemoryBlock: length {self.length}>"

class MemoryModel:
    def __init__(self):
        self.memory = {}
        self.memory_size = 256
        
    def space_is_free(self, at, length):
        for addr, block in self.memory.items():
            a = set(range(at, at+length))
            b = set(range(addr, addr+block.length))
            if len(a & b) > 0:
                return False
        return True
        
    def find_space(self, length):
        for at in range(0, self.memory_size):
            if self.space_is_free(at, length):
                return at
        
    def allocate(self, bytes_, var_type):
        address = self.find_space(bytes_)
        block = MemoryBlock(bytes_, var_type)
        self.memory[address] = block
        return address
    
    def free(self, address):
        if address in self.memory:
            del self.memory[address]
    
class Namespace:
    def __init__(self, parent, memory):
        self.parent = parent
        self.memory = memory
        self.locals = {}
        
    def let(self, name, length, var_type):
        #print(f"Allocating variable {name} in namespace")
        addr = self.memory.allocate(length, var_type)
        self.locals[name] = addr
        return addr
    
    def get_namespace(self):
        if self.parent is None:
            return self.locals
        namespace = self.parent.get_namespace()
        namespace.update(self.locals)
        return namespace
        
            
class Assembler:
    def __init__(self, ast):
        self.ast = ast
        self.instructions = []
        self.memory = MemoryModel()

        self.globals = Namespace(None, self.memory)
        self.globals.locals = {"print":0}
        self.function_addresses = {"main":0}
        self.function_return_addresses = {}
        self.main = None
        self.non_main_functions = []
        for branch in self.ast:
            if isinstance(branch, Function):
                if branch.name.lexeme == "main":
                    self.main = branch
                else:
                    self.globals.locals[branch.name.lexeme] = 0
                    self.non_main_functions.append(branch)
        if self.main is None:
            raise Exception("No main function found")
        
        
    def add_instruction(self, inst, data, mem_flag=False):
        if mem_flag:
            inst = 0b1000_0000 | inst
        self.instructions += [inst, data]
        return len(self.instructions) - 2
        
        
    def assemble(self):
        self.parse(self.main.body, Namespace(self.globals, self.memory))
        self.add_instruction(0b00110, 0) # HLT
        for function in self.non_main_functions:
            self.function_addresses[function.name.lexeme] = len(self.instructions)
            self.parse(function.body, Namespace(self.globals, self.memory))
            self.function_return_addresses[function.name.lexeme] = len(self.instructions)-1
        print(self.instructions)
        data_start = len(self.instructions)
        for index, inst in enumerate(self.instructions):
            if isinstance(inst, DataAddress):
                self.instructions[index] = inst.addr + data_start
            if isinstance(inst, FunctionAddress):
                self.instructions[index] = self.function_addresses[inst.func_name.name]
        print(self.instructions)
        return self.instructions
    
    
    def parse_binary(self, namespace, binary):
        if isinstance(binary.left, Literal):
            self.add_instruction(0b00001, binary.left.value) # LDA value
        elif isinstance(binary.left, Variable):
            self.add_instruction(0b00001, DataAddress(namespace.get_namespace()[binary.left.name]), True) # LDA [left_name]
        elif isinstance(binary.left, Call):
            self.parse_call(namespace, binary.left.callee, binary.left.args)
            # move function return value into AX
            self.add_instruction(0b01101, mov(AX, FX)) # MOV AX <- FX
        elif isinstance(binary.left, Binary):
            self.parse_binary(namespace, binary.left)
        
        if isinstance(binary.right, Literal):
            self.add_instruction(0b00010, binary.right.value) # LDB value
        elif isinstance(binary.right, Variable):
            self.add_instruction(0b00010, DataAddress(namespace.get_namespace()[binary.right.name]), True) # LDB [right_name]
        elif isinstance(binary.right, Call):
            self.parse_call(namespace, binary.right.callee, binary.right.args)
            # move function return value into BX
            self.add_instruction(0b01101, mov(BX, FX)) # MOV BX <- FX
            
        
        if binary.operator.token_type ==  TokenType.PLUS:
            self.add_instruction(0b00101, 0) # ADD
        
        if binary.operator.token_type == TokenType.MINUS:
            self.add_instruction(0b10000, 0) # NEG
            
    def parse_call(self, namespace, func, args):
        # move current instruction address into STORE register
        # store that address at the return point for function
        # jump to start of function
        #self.add_instruction(0b01101, mov(ST, INST)) # MOV ST <- INST
        #self.add_instruction(0b10001, FunctionReturnAddress(func)) # ST current_instuction_place
        #self.add_instruction(0b01000, FunctionAddress(func)) # JMP function_start
        self.add_instruction(0b10001, FunctionAddress(func)) # CALL function_start
        
                
        
    def parse(self, block, namespace):
        print("Parsing a block", block.statements)
        for statement in block.statements:
            if isinstance(statement, Block):
                self.parse(statement, Namespace(namespace, self.memory))
            
            if isinstance(statement, Let):
                addr = namespace.let(statement.name.lexeme, 1, statement.vtype.lexeme)
                if isinstance(statement.initial, Literal):
                    value = statement.initial.value
                    self.add_instruction(0b00001, value) # LDA value
                    self.add_instruction(0b01001, DataAddress(addr)) # STA [var_name]
            
            if isinstance(statement, If):
                self.parse(statement.then, Namespace(namespace, self.memory))
                self.parse(statement.otherwise, Namespace(namespace, self.memory))
            
            if isinstance(statement, Assign):
                if not statement.name in namespace.get_namespace():
                    raise Exception(f"Assignment to uninitialised variable {statement.name}. Use 'let type name = value;' to initialise.")
                if isinstance(statement.value, Literal):
                    value = statement.value.value
                    self.add_instruction(0b00001, value) # LDA value
                    self.add_instruction(0b01001, DataAddress(namespace.get_namespace()[statement.name])) # STA [var_name]
                if isinstance(statement.value, Binary):
                    self.parse_binary(namespace, statement.value)
                    self.add_instruction(0b01001, DataAddress(namespace.get_namespace()[statement.name])) # STA [var_name]
                        
            
            if isinstance(statement, Call):
                print(statement)
                if not statement.callee.name in namespace.get_namespace():
                    raise Exception(f"Call to undefined function {statement.callee.name}")
                if statement.callee.name == "print":
                    for arg in statement.args:
                        if not arg.name in namespace.get_namespace():
                            raise Exception(f"Call with uninitialised variable {arg.name}")
                        self.add_instruction(0b00111, DataAddress(namespace.get_namespace()[arg.name]), True) # PRX var
                        
            if isinstance(statement, Return):
                if isinstance(statement.value, Literal):
                    self.add_instruction(0b10010, statement.value.value) # RET value
                    
                    
         
        print(namespace.get_namespace(), self.memory.memory)
        # local variables are freed at the end of a block
        for name in namespace.locals:
            self.memory.free(namespace.locals[name])
        
        
        
if __name__ == "__main__":
    memory = MemoryModel()
    x = memory.allocate(1, int)
    y = memory.allocate(2, int)
    z = memory.allocate(5, int)
    print(x, y, z)
    memory.free(y)
    
    a = memory.allocate(6, int)
    b = memory.allocate(1, int)
    print(a, b)
    
    print(memory.memory)