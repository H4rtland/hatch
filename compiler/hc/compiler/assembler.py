from enum import Enum

from compiler.expressions import *
from compiler.tokenizer import TokenType
from compiler.memory import MemoryModel, Namespace, FunctionAddress, DataAddress
from compiler.instructions import Instruction, Register, mov

        
            
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
        if isinstance(inst, Enum):
            inst = inst.value
        if mem_flag:
            # set memory reference bit
            inst = 0b1000_0000 | inst
        self.instructions += [inst, data]
        return len(self.instructions) - 2
        
        
    def assemble(self):
        self.parse(self.main.body, Namespace(self.globals, self.memory))
        self.add_instruction(Instruction.HLT, 0) # HLT
        for function in self.non_main_functions:
            self.function_addresses[function.name.lexeme] = len(self.instructions)
            self.parse(function.body, Namespace(self.globals, self.memory))
            self.function_return_addresses[function.name.lexeme] = len(self.instructions)-1
        
        data_start = len(self.instructions)
        for index, inst in enumerate(self.instructions):
            if isinstance(inst, DataAddress):
                self.instructions[index] = inst.addr + data_start
            if isinstance(inst, FunctionAddress):
                self.instructions[index] = self.function_addresses[inst.func_name.name]
        
        return self.instructions
    
    
    def parse_binary(self, namespace, binary):
        if isinstance(binary.left, Literal):
            self.add_instruction(Instruction.LDA, binary.left.value) # LDA value
        elif isinstance(binary.left, Variable):
            self.add_instruction(Instruction.LDA, DataAddress(namespace.get_namespace()[binary.left.name]), True) # LDA [left_name]
        elif isinstance(binary.left, Call):
            self.parse_call(namespace, binary.left.callee, binary.left.args)
            # move function return value into AX
            self.add_instruction(Instruction.MOV, mov(Register.AX, Register.FX)) # MOV AX <- FX
        elif isinstance(binary.left, Binary):
            self.parse_binary(namespace, binary.left)
        
        if isinstance(binary.right, Literal):
            self.add_instruction(Instruction.LDB, binary.right.value) # LDB value
        elif isinstance(binary.right, Variable):
            self.add_instruction(Instruction.LDB, DataAddress(namespace.get_namespace()[binary.right.name]), True) # LDB [right_name]
        elif isinstance(binary.right, Call):
            self.parse_call(namespace, binary.right.callee, binary.right.args)
            # move function return value into BX
            self.add_instruction(Instruction.MOV, mov(Register.BX, Register.FX)) # MOV BX <- FX
            
        
        if binary.operator.token_type ==  TokenType.PLUS:
            self.add_instruction(Instruction.ADD, 0) # ADD
        
        if binary.operator.token_type == TokenType.MINUS:
            self.add_instruction(Instruction.NEG, 0) # NEG
            
    def parse_call(self, namespace, func, args):
        self.add_instruction(Instruction.CALL, FunctionAddress(func)) # CALL function_start
        
                
        
    def parse(self, block, namespace):
        for statement in block.statements:
            if isinstance(statement, Block):
                self.parse(statement, Namespace(namespace, self.memory))
            
            if isinstance(statement, Let):
                addr = namespace.let(statement.name.lexeme, 1, statement.vtype.lexeme)
                if isinstance(statement.initial, Literal):
                    value = statement.initial.value
                    self.add_instruction(Instruction.LDA, value) # LDA value
                    self.add_instruction(Instruction.STA, DataAddress(addr)) # STA [var_name]
            
            if isinstance(statement, If):
                self.parse(statement.then, Namespace(namespace, self.memory))
                self.parse(statement.otherwise, Namespace(namespace, self.memory))
            
            if isinstance(statement, Assign):
                if not statement.name in namespace.get_namespace():
                    raise Exception(f"Assignment to uninitialised variable {statement.name}. Use 'let type name = value;' to initialise.")
                if isinstance(statement.value, Literal):
                    value = statement.value.value
                    self.add_instruction(Instruction.LDA, value) # LDA value
                    self.add_instruction(Instruction.STA, DataAddress(namespace.get_namespace()[statement.name])) # STA [var_name]
                if isinstance(statement.value, Binary):
                    self.parse_binary(namespace, statement.value)
                    self.add_instruction(Instruction.STA, DataAddress(namespace.get_namespace()[statement.name])) # STA [var_name]
                        
            
            if isinstance(statement, Call):
                if not statement.callee.name in namespace.get_namespace():
                    raise Exception(f"Call to undefined function {statement.callee.name}")
                if statement.callee.name == "print":
                    for arg in statement.args:
                        if not arg.name in namespace.get_namespace():
                            raise Exception(f"Call with uninitialised variable {arg.name}")
                        self.add_instruction(Instruction.PRX, DataAddress(namespace.get_namespace()[arg.name]), True) # PRX var
                        
            if isinstance(statement, Return):
                if isinstance(statement.value, Literal):
                    self.add_instruction(Instruction.RET, statement.value.value) # RET value
                    
                    
         
        # print(namespace.get_namespace(), self.memory.memory)
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