from enum import Enum

from compiler.expressions import *
from compiler.tokenizer import TokenType
from compiler.memory import MemoryModel, Namespace, FunctionAddress, DataAddress
from compiler.instructions import Instruction, Register, mov

import uuid

        
            
class Assembler:
    def __init__(self, ast):
        self.ast = ast
        self.instructions = []
        self.memory = MemoryModel()

        self.globals = Namespace(None, self.memory)
        self.globals.globals = {"__internal_print":0}
        self.function_addresses = {"main":0}
        self.function_return_addresses = {}
        self.main = None
        self.non_main_functions = []
        for branch in self.ast:
            if isinstance(branch, Function):
                if branch.name.lexeme == "main":
                    self.main = branch
                else:
                    self.globals.globals[branch.name.lexeme] = 0
                    self.non_main_functions.append(branch)
        if self.main is None:
            raise Exception("No main function found")
        
        
    def add_instruction(self, inst, data, mem_flag=False, stack_flag=False):
        if isinstance(inst, Enum):
            inst = inst.value
        if mem_flag:
            # set memory reference bit
            inst = 0b1000_0000 | inst
        if stack_flag:
            # set stack lookup bit
            inst = 0b0100_0000 | inst
        self.instructions += [inst, data]
        return len(self.instructions) - 2
        
        
    def assemble(self):
        self.parse(self.main.body, Namespace(self.globals, self.memory))
        self.add_instruction(Instruction.HLT, 0) # HLT
        for function in self.non_main_functions:
            self.function_addresses[function.name.lexeme] = len(self.instructions)
            namespace = Namespace(self.globals, self.memory)
            for arg in function.args:
                namespace.let(arg[1].lexeme, 1, arg[0].lexeme)
            self.parse(function.body, namespace, is_function=True)
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
            # self.add_instruction(Instruction.LDA, DataAddress(namespace.get_namespace()[binary.left.name]), True) # LDA [left_name]
            self.add_instruction(Instruction.LDA, self.memory.id_on_stack(namespace.get_namespace()[binary.left.name]), stack_flag=True) # LDA [left_name]
        elif isinstance(binary.left, Call):
            self.parse_call(namespace, binary.left.callee, binary.left.args)
            # move function return value into AX
            self.add_instruction(Instruction.MOV, mov(Register.AX, Register.FX)) # MOV AX <- FX
        elif isinstance(binary.left, Binary):
            self.parse_binary(namespace, binary.left)
        else:
            raise Exception("Unhandled binary left input")
        
        if isinstance(binary.right, Literal):
            self.add_instruction(Instruction.LDB, binary.right.value) # LDB value
        elif isinstance(binary.right, Variable):
            # self.add_instruction(Instruction.LDB, DataAddress(namespace.get_namespace()[binary.right.name]), True) # LDB [right_name]
            self.add_instruction(Instruction.LDB, self.memory.id_on_stack(namespace.get_namespace()[binary.right.name]), stack_flag=True) # LDB [right_name]
        elif isinstance(binary.right, Call):
            self.parse_call(namespace, binary.right.callee, binary.right.args)
            # move function return value into BX
            self.add_instruction(Instruction.MOV, mov(Register.BX, Register.FX)) # MOV BX <- FX
        else:
            raise Exception("Unhandled binary right input")
            
        
        if binary.operator.token_type ==  TokenType.PLUS:
            self.add_instruction(Instruction.ADD, 0) # ADD
        elif binary.operator.token_type == TokenType.MINUS:
            self.add_instruction(Instruction.NEG, 0) # NEG
        else:
            raise Exception("Unhandled binary operator")
            
    def parse_call(self, namespace, func, args):
        # Save register state to restore after function return
        self.add_instruction(Instruction.SAVE, 0)
        extra_stack_vars = 2
        self.memory.temp_extra_stack_vars += 2
        # Add parameters to stack
        for arg in args:
            if isinstance(arg, Literal):
                self.add_instruction(Instruction.PUSH, 0)
                self.add_instruction(Instruction.LDA, arg.value) # LDA value
                self.add_instruction(Instruction.STA, 1, stack_flag=True)
            elif isinstance(arg, Variable):
                self.add_instruction(Instruction.LDA, self.memory.id_on_stack(namespace.get_namespace()[arg.name]), stack_flag=True)
                self.add_instruction(Instruction.PUSH, 0)
                self.add_instruction(Instruction.STA, 1, stack_flag=True)
            elif isinstance(arg, Binary):
                self.parse_binary(namespace, arg)
                self.add_instruction(Instruction.PUSH, 0)
                self.add_instruction(Instruction.STA, 1, stack_flag=True)
            elif isinstance(arg, Call):
                self.parse_call(namespace, arg.callee, arg.args)
                self.add_instruction(Instruction.MOV, mov(Register.AX, Register.FX)) # MOV AX <- FX
                self.add_instruction(Instruction.PUSH, 0)
                self.add_instruction(Instruction.STA, 1, stack_flag=True)
            else:
                raise Exception("Unhandled function argument")
            extra_stack_vars += 1
            self.memory.temp_extra_stack_vars += 1
        self.memory.temp_extra_stack_vars -= extra_stack_vars
        self.add_instruction(Instruction.CALL, FunctionAddress(func)) # CALL function_start
        
    def parse_if(self, namespace, statement):
        then_index = None
        else_index = None
        if isinstance(statement.condition, Binary):
            true_inst = None
            false_inst = None
            if statement.condition.operator.token_type == TokenType.EQUAL_EQUAL:
                true_inst = Instruction.JE
                false_inst = Instruction.JNE
            else:
                raise Exception("Unhandled if condition operator")
                
            if isinstance(statement.condition.left, Literal):
                self.add_instruction(Instruction.LDA, statement.condition.left.value)
            elif isinstance(statement.condition.left, Variable):
                self.add_instruction(Instruction.LDA, self.memory.id_on_stack(namespace.get_namespace()[statement.condition.left.name]), stack_flag=True)
            elif isinstance(statement.condition.left, Call):
                self.parse_call(namespace, statement.condition.left.callee, statement.condition.left.args)
                self.add_instruction(Instruction.MOV, mov(Register.AX, Register.FX))
            else:
                raise Exception("Unhandled if statement condition")
            
            if isinstance(statement.condition.right, Literal):
                self.add_instruction(Instruction.LDB, statement.condition.right.value)
            elif isinstance(statement.condition.right, Variable):
                self.add_instruction(Instruction.LDB, self.memory.id_on_stack(namespace.get_namespace()[statement.condition.right.name]), stack_flag=True)
            elif isinstance(statement.condition.right, Call):
                self.parse_call(namespace, statement.condition.right.callee, statement.condition.right.args)
                self.add_instruction(Instruction.MOV, mov(Register.BX, Register.FX))
            else:
                raise Exception("Unhandled if statement condition")
                
            self.add_instruction(Instruction.CMP, 0)
            self.add_instruction(true_inst, 0)
            then_index = len(self.instructions)-1
            self.add_instruction(false_inst, 0)
            else_index = len(self.instructions)-1
            self.instructions[then_index] = len(self.instructions)
            self.parse(statement.then, Namespace(namespace, self.memory))
            self.add_instruction(Instruction.JMP, 0)
            then_end_index = len(self.instructions)-1
            self.instructions[else_index] = len(self.instructions)
            if not statement.otherwise is None:
                self.parse(statement.otherwise, Namespace(namespace, self.memory))
            self.instructions[then_end_index] = len(self.instructions)
                
        
    def parse(self, block, namespace, is_function=False):
        
        already_popped = False
        
        for statement in block.statements:
            if isinstance(statement, Block):
                self.parse(statement, Namespace(namespace, self.memory))
            
            elif isinstance(statement, Let):
                
                if isinstance(statement.initial, Literal):
                    identifier = namespace.let(statement.name.lexeme, 1, statement.vtype.lexeme)
                    value = statement.initial.value
                    self.add_instruction(Instruction.PUSH, 0)
                    self.add_instruction(Instruction.LDA, value) # LDA value
                    self.add_instruction(Instruction.STA, self.memory.id_on_stack(identifier), stack_flag=True) # STA var_name
                elif isinstance(statement.initial, Call):
                    self.parse_call(namespace, statement.initial.callee, statement.initial.args)
                    self.add_instruction(Instruction.MOV, mov(Register.AX, Register.FX)) # MOV AX <- FX
                    identifier = namespace.let(statement.name.lexeme, 1, statement.vtype.lexeme)
                    self.add_instruction(Instruction.PUSH, 0)
                    self.add_instruction(Instruction.STA, self.memory.id_on_stack(identifier), stack_flag=True) # STA func_return
                elif isinstance(statement.initial, Binary):
                    self.parse_binary(namespace, statement.initial)
                    identifier = namespace.let(statement.name.lexeme, 1, statement.vtype.lexeme)
                    self.add_instruction(Instruction.PUSH, 0)
                    self.add_instruction(Instruction.STA, self.memory.id_on_stack(identifier), stack_flag=True) # STA sum
                else:
                    raise Exception("Unhandled let statement")
            
            elif isinstance(statement, If):
                self.parse_if(namespace, statement)
            
            elif isinstance(statement, Assign):
                if not statement.name in namespace.get_namespace():
                    raise Exception(f"Assignment to uninitialised variable {statement.name}. Use 'let type name = value;' to initialise.")
                if isinstance(statement.value, Literal):
                    value = statement.value.value
                    self.add_instruction(Instruction.LDA, value) # LDA value
                    self.add_instruction(Instruction.STA, self.memory.id_on_stack(namespace.get_namespace()[statement.name]), stack_flag=True) # STA [var_name]
                elif isinstance(statement.value, Binary):
                    self.parse_binary(namespace, statement.value)
                    self.add_instruction(Instruction.STA, self.memory.id_on_stack(namespace.get_namespace()[statement.name]), stack_flag=True) # STA [var_name]
                elif isinstance(statement.value, Call):
                    self.parse_call(namespace, statement.value.callee, statement.value.args)
                    self.add_instruction(Instruction.MOV, mov(Register.AX, Register.FX)) # MOV AX <- FX
                    self.add_instruction(Instruction.STA, self.memory.id_on_stack(namespace.get_namespace()[statement.name]), stack_flag=True) # STA func_return
                else:
                    raise Exception("Unhandled let statement")
                        
            
            elif isinstance(statement, Call):
                if not statement.callee.name in namespace.get_namespace():
                    raise Exception(f"Call to undefined function {statement.callee.name}")
                if statement.callee.name == "__internal_print":
                    for arg in statement.args:
                        if not arg.name in namespace.get_namespace():
                            raise Exception(f"Call with uninitialised variable {arg.name}")
                        self.add_instruction(Instruction.PRX, self.memory.id_on_stack(namespace.get_namespace()[arg.name]), stack_flag=True) # PRX var
                else:
                    self.parse_call(namespace, statement.callee, statement.args)
                    
                        
            elif isinstance(statement, Return):
                already_popped = True
                if isinstance(statement.value, Literal):
                    if len(namespace.get_namespace(True)) > 0:
                        self.add_instruction(Instruction.POP, len(namespace.get_namespace(True)))
                    self.add_instruction(Instruction.RET, statement.value.value) # RET value
                elif isinstance(statement.value, Variable):
                    self.add_instruction(Instruction.LDA, self.memory.id_on_stack(namespace.get_namespace()[statement.value.name]), stack_flag=True)
                    self.add_instruction(Instruction.MOV, mov(Register.FX, Register.AX)) # MOV FX <- AX
                    if len(namespace.get_namespace(True)) > 0:
                        self.add_instruction(Instruction.POP, len(namespace.get_namespace(True)))
                    self.add_instruction(Instruction.RET, 0, stack_flag=True) # RET none
                elif isinstance(statement.value, Binary):
                    self.parse_binary(namespace, statement.value)
                    self.add_instruction(Instruction.MOV, mov(Register.FX, Register.AX)) # MOV FX <- AX
                    if len(namespace.get_namespace(True)) > 0:
                        self.add_instruction(Instruction.POP, len(namespace.get_namespace(True)))
                    self.add_instruction(Instruction.RET, 0, stack_flag=True) # RET none
                else:
                    raise Exception("Unhandled return value")
                
            else:
                raise Exception("Unhandled statement type")
                    
                    
                    
         
        # print(namespace.get_namespace(), self.memory.memory)
        # local variables are freed at the end of a block
        if not already_popped:
            self.add_instruction(Instruction.POP, len(namespace.get_namespace(True)))
            if is_function:
                self.add_instruction(Instruction.RET, 0)
        #for name in namespace.locals:
        #    self.memory.free(namespace.locals[name])
