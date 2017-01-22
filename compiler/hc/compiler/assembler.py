from compiler.expressions import *
from compiler.tokenizer import TokenType

class MemoryAddress:
    def __init__(self, addr):
        self.addr = addr
        
    def __repr__(self):
        return f"<MemoryAddress: {self.addr}>"

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
            return {"print":0}
        namespace = self.parent.get_namespace()
        namespace.update(self.locals)
        return namespace
        
            
class Assembler:
    def __init__(self, ast):
        self.ast = ast
        self.instructions = []
        self.memory = MemoryModel()
        self.main = None
        for branch in self.ast:
            if isinstance(branch, Function):
                if branch.name.lexeme == "main":
                    self.main = branch
        if self.main is None:
            raise Exception("No main function found")
        
        
    def add_instruction(self, inst, data, mem_flag=False):
        if mem_flag:
            inst = 0b1000_0000 | inst
        self.instructions += [inst, data]
        return len(self.instructions) - 2
        
        
    def assemble(self):
        self.globals = Namespace(None, self.memory)
        self.parse(self.main.body, Namespace(self.globals, self.memory))
        self.add_instruction(0b00110, 0) # HLT
        print(self.instructions)
        data_start = len(self.instructions)
        for index, inst in enumerate(self.instructions):
            if isinstance(inst, MemoryAddress):
                self.instructions[index] = inst.addr + data_start
        print(self.instructions)
        return self.instructions
    
    
    def parse_binary(self, namespace, binary):
        if isinstance(binary.left, Literal):
            self.add_instruction(0b00001, binary.left.value) # LDA value
        elif isinstance(binary.left, Variable):
            self.add_instruction(0b00001, MemoryAddress(namespace.get_namespace()[binary.left.name]), True) # LDA [left_name]
        elif isinstance(binary.left, Binary):
            self.parse_binary(namespace, binary.left)
        
        if isinstance(binary.right, Literal):
            self.add_instruction(0b00010, binary.right.value) # LDB value
        elif isinstance(binary.right, Variable):
            self.add_instruction(0b00010, MemoryAddress(namespace.get_namespace()[binary.right.name]), True) # LDB [right_name]
        
        if binary.operator.token_type ==  TokenType.PLUS:
            self.add_instruction(0b00101, 0)
        
        if binary.operator.token_type == TokenType.MINUS:
            self.add_instruction(0b10000, 0)
                
        
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
                    self.add_instruction(0b01001, MemoryAddress(addr)) # STA [var_name]
            
            if isinstance(statement, If):
                self.parse(statement.then, Namespace(namespace, self.memory))
                self.parse(statement.otherwise, Namespace(namespace, self.memory))
            
            if isinstance(statement, Assign):
                if not statement.name in namespace.get_namespace():
                    raise Exception(f"Assignment to uninitialised variable {statement.name}. Use 'let type name = value;' to initialise.")
                if isinstance(statement.value, Literal):
                    value = statement.value.value
                    self.add_instruction(0b00001, value) # LDA value
                    self.add_instruction(0b01001, MemoryAddress(namespace.get_namespace()[statement.name])) # STA [var_name]
                if isinstance(statement.value, Binary):
                    self.parse_binary(namespace, statement.value)
                    self.add_instruction(0b01001, MemoryAddress(namespace.get_namespace()[statement.name])) # STA [var_name]
                        
            
            if isinstance(statement, Call):
                print(statement)
                if not statement.callee.name in namespace.get_namespace():
                    raise Exception(f"Call to undefined function {statement.callee.name}")
                if statement.callee.name == "print":
                    for arg in statement.args:
                        if not arg.name in namespace.get_namespace():
                            raise Exception(f"Call with uninitialised variable {arg.name}")
                        self.add_instruction(0b00111, MemoryAddress(namespace.get_namespace()[arg.name]), True) # PRX var
                    
                    
         
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