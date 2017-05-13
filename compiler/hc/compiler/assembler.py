import sys
import time
from enum import Enum

from compiler.expressions import *
from compiler.tokenizer import TokenType
from compiler.memory import MemoryModel, Namespace, FunctionAddress, DataAddress
from compiler.instructions import Instruction, Register, mov

import uuid

SAVED_REGISTERS = 2

        
            
class Assembler:
    def __init__(self, ast):
        self.ast = ast
        
        self.had_error = False
        
        self.instructions = []
        self.memory = MemoryModel()

        self.globals = Namespace(None, self.memory)
        self.globals.globals = {"__internal_print":0, "__internal_print_char":0}
        self.function_addresses = {"main":0}
        self.function_return_addresses = {}
        self.function_names = []
        self.main = None
        self.non_main_functions = []
        for branch in self.ast:
            if isinstance(branch, Function):
                if branch.name.lexeme == "main":
                    self.main = branch
                else:
                    self.globals.globals[branch.name.lexeme] = FunctionAddress(Variable(branch.name.lexeme))
                    self.non_main_functions.append(branch)
                    self.function_names.append(branch.name.lexeme)
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
        assert 0 <= inst <= 255
        assert inst != 33
        if isinstance(data, int):
            assert 0 <= data <= 255
        self.instructions += [inst, data]
        return len(self.instructions) - 2
    
    
    def variable_exists(self, namespace, variable):
        if variable.name in namespace.get_namespace():
            return True
        print("Use of uninitialised variable", variable.name)
        self.had_error = True
        return False
        
        
    def assemble(self):
        self.parse(Namespace(self.globals, self.memory), self.main.body)
        self.add_instruction(Instruction.HLT, 0) # HLT
        
        while True:
            if all(isinstance(inst, int) for inst in self.instructions):
                # no more functions left to compile
                break
            
            # time.sleep(0.1)
            names = []
            functions_remaining = []
            for instruction in self.instructions:
                if isinstance(instruction, FunctionAddress):
                    if instruction.func_name.name not in names:
                        functions_remaining.append(instruction)
                        names.append(instruction.func_name.name)
            for func_address in functions_remaining:
                for function in self.non_main_functions:
                    if function.name.lexeme in self.function_return_addresses:
                        continue
                    if func_address.func_name.name == function.name.lexeme:
                        self.function_addresses[function.name.lexeme] = len(self.instructions)
                        namespace = Namespace(self.globals, self.memory)
                        parameter_identifiers = []
                        for arg in function.args:
                            parameter_identifiers.append(namespace.let(arg[1].lexeme, 1, arg[0].lexeme, arg[3]))
                        self.parse(namespace, function.body, is_function=True, parameter_identifiers=parameter_identifiers)
                        self.function_return_addresses[function.name.lexeme] = len(self.instructions)-1
                #print(self.function_addresses)
                for i, inst in enumerate(self.instructions):
                    if isinstance(inst, FunctionAddress):
                        if inst.func_name.name == func_address.func_name.name and inst.func_name.name in self.function_addresses:
                            self.instructions[i] = self.function_addresses[inst.func_name.name]
        
        data_start = len(self.instructions)
        for index, inst in enumerate(self.instructions):
            if isinstance(inst, DataAddress):
                if inst.addr + data_start > 255:
                    raise Exception(f"{inst.addr+data_start}")
                self.instructions[index] = inst.addr + data_start
            if isinstance(inst, FunctionAddress):
                #if self.function_addresses[inst.func_name.name] > 255:
                #    raise Exception(f"{inst.func_name.name} = {self.function_addresses[inst.func_name.name]}")
                self.instructions[index] = self.function_addresses[inst.func_name.name]
        
        if len(self.instructions) > 255-16:
            raise Exception(f"Instructions exceeded max memory size: {len(self.instructions)}")
        if not all([(0 <= x <= 255) for x in self.instructions]):
            raise Exception("Overflowed value in output instructions")
        return self.instructions, self.function_addresses
    
    
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
        elif isinstance(binary.left, Index):
            self.parse_index(namespace, binary.left.variable, binary.left.index, register=Register.AX)
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
        elif isinstance(binary.right, Index):
            self.parse_index(namespace, binary.right.variable, binary.right.index, register=Register.BX)
        else:
            raise Exception("Unhandled binary right input")
            
        
        if binary.operator.token_type == TokenType.PLUS:
            self.add_instruction(Instruction.ADD, 0) # ADD
        elif binary.operator.token_type == TokenType.MINUS:
            self.add_instruction(Instruction.NEG, 0) # NEG
        elif binary.operator.token_type == TokenType.STAR:
            self.add_instruction(Instruction.MUL, 0)
        elif binary.operator.token_type == TokenType.SLASH:
            self.add_instruction(Instruction.DIV, 0)
        else:
            raise Exception("Unhandled binary operator")
            
    def parse_call(self, namespace, func, args):
        # Save register state to restore after function return
        self.add_instruction(Instruction.SAVE, 0)
        extra_stack_vars = SAVED_REGISTERS
        self.memory.temp_extra_stack_vars += SAVED_REGISTERS
        # Add parameters to stack
        for arg in args:
            if isinstance(arg, Literal):
                self.add_instruction(Instruction.PUSH, 1)
                self.add_instruction(Instruction.LDA, arg.value) # LDA value
                self.add_instruction(Instruction.STA, 1, stack_flag=True)
            elif isinstance(arg, Variable):
                if namespace.is_array(arg.name):
                    self.add_instruction(Instruction.DUP, self.memory.id_on_stack(namespace.get_namespace()[arg.name]))
                else:
                    self.add_instruction(Instruction.LDA, self.memory.id_on_stack(namespace.get_namespace()[arg.name]), stack_flag=True)
                    self.add_instruction(Instruction.PUSH, 1)
                    self.add_instruction(Instruction.STA, 1, stack_flag=True)
            elif isinstance(arg, Binary):
                self.parse_binary(namespace, arg)
                self.add_instruction(Instruction.PUSH, 1)
                self.add_instruction(Instruction.STA, 1, stack_flag=True)
            elif isinstance(arg, Call):
                self.parse_call(namespace, arg.callee, arg.args)
                self.add_instruction(Instruction.MOV, mov(Register.AX, Register.FX)) # MOV AX <- FX
                self.add_instruction(Instruction.PUSH, 1)
                self.add_instruction(Instruction.STA, 1, stack_flag=True)
            elif isinstance(arg, Index):
                self.parse_index(namespace, arg.variable, arg.index)
                self.add_instruction(Instruction.PUSH, 1)
                self.add_instruction(Instruction.STA, 1, stack_flag=True)
            elif isinstance(arg, Array):
                self.load_array(namespace, arg)
                
            else:
                raise Exception("Unhandled function argument")
            extra_stack_vars += 1
            self.memory.temp_extra_stack_vars += 1
        
        if isinstance(func, int):
            stack_value = func + self.memory.temp_extra_stack_vars - 1
            self.add_instruction(Instruction.CALL, stack_value, stack_flag=True)
        elif isinstance(func, FunctionAddress):
            #print("CALL", func)
            self.add_instruction(Instruction.CALL, func)
        elif isinstance(func, Variable):
            #print("CALL2", func)
            if namespace.exists(func.name) and self.memory.exists(namespace.get_namespace()[func.name]):
                self.add_instruction(Instruction.CALL, self.memory.id_on_stack(namespace.get_namespace()[func.name]), stack_flag=True) # CALL function_start
            else:
                self.add_instruction(Instruction.CALL, FunctionAddress(func)) # CALL function_start
        else:
            raise Exception("Unhandled call")
        
        self.memory.temp_extra_stack_vars -= extra_stack_vars
        
    def load_array(self, namespace, array, force_length=None):
        length = force_length or len(array.elements)
        self.add_instruction(Instruction.PUSH, length+1)
        self.add_instruction(Instruction.LDA, length)
        self.add_instruction(Instruction.STA, 1, stack_flag=True)
        
        for i, element in enumerate(array.elements):
            if isinstance(element, Literal):
                self.add_instruction(Instruction.OFF, i+1)
                self.add_instruction(Instruction.LDA, element.value)
                self.add_instruction(Instruction.STA, 1, stack_flag=True)
            elif isinstance(element, Variable):
                self.add_instruction(Instruction.OFF, 0)
                self.add_instruction(Instruction.LDA, self.memory.id_on_stack(namespace.get_namespace()[element.name]), stack_flag=True)
                self.add_instruction(Instruction.OFF, i+1)
                self.add_instruction(Instruction.STA, 1, stack_flag=True)
            else:
                raise Exception("Unhandled array element")
        
        self.add_instruction(Instruction.OFF, 0)
        
    def parse_index(self, namespace, variable, index, register=Register.AX):
        if isinstance(index, Literal):
            #self.add_instruction(Instruction.LDB, index.value+1)
            #self.add_instruction(Instruction.MOV, mov(Register.OX, Register.BX))
            self.add_instruction(Instruction.OFF, index.value+1)
        elif isinstance(index, Variable):
            load_inst = {
                Register.AX: Instruction.LDA,
                Register.BX: Instruction.LDB,
            }[register]
            self.add_instruction(load_inst, self.memory.id_on_stack(namespace.get_namespace()[index.name]), stack_flag=True)
            self.add_instruction(Instruction.INC, 255-register.value)
            self.add_instruction(Instruction.MOV, mov(Register.OX, register))
        elif isinstance(index, Binary):
            self.parse_binary(namespace, index)
            self.add_instruction(Instruction.INC, 255-Register.AX.value)
            self.add_instruction(Instruction.MOV, mov(Register.OX, Register.AX))
            
        else:
            raise Exception("Unhandled index get")
        load_inst = {
            Register.AX: Instruction.LDA,
            Register.BX: Instruction.LDB,
        }[register]
        self.add_instruction(load_inst, self.memory.id_on_stack(namespace.get_namespace()[variable.name]), stack_flag=True)
        #self.add_instruction(Instruction.LDB, 0)
        #self.add_instruction(Instruction.MOV, mov(Register.OX, Register.BX))
        self.add_instruction(Instruction.OFF, 0)
        
    
    def parse_comparison(self, namespace, condition):
        if isinstance(condition.left, Literal):
            self.add_instruction(Instruction.LDA, condition.left.value)
        elif isinstance(condition.left, Variable):
            #if self.variable_exists(namespace, condition.left):
            self.add_instruction(Instruction.LDA, self.memory.id_on_stack(namespace.get_namespace()[condition.left.name]), stack_flag=True)
        elif isinstance(condition.left, Call):
            self.parse_call(namespace, condition.left.callee, condition.left.args)
            self.add_instruction(Instruction.MOV, mov(Register.AX, Register.FX))
        elif isinstance(condition.left, Index):
            self.parse_index(namespace, condition.left.variable, condition.left.index, register=Register.AX)
        else:
            raise Exception("Unhandled if statement condition")
        
        if isinstance(condition.right, Literal):
            self.add_instruction(Instruction.LDB, condition.right.value)
        elif isinstance(condition.right, Variable):
            self.add_instruction(Instruction.LDB, self.memory.id_on_stack(namespace.get_namespace()[condition.right.name]), stack_flag=True)
        elif isinstance(condition.right, Call):
            self.parse_call(namespace, condition.right.callee, condition.right.args)
            self.add_instruction(Instruction.MOV, mov(Register.BX, Register.FX))
        elif isinstance(condition.right, Index):
            self.parse_index(namespace, condition.left.variable, condition.left.index, register=Register.BX)
        else:
            raise Exception("Unhandled if statement condition")
    
    def parse_if(self, namespace, statement):
        then_index = None
        else_index = None
        if isinstance(statement.condition, Literal):
            if statement.condition.value == True:
                self.parse(Namespace(namespace, self.memory), statement.then)
            elif not (statement.otherwise is None):
                self.parse(Namespace(namespace, self.memory), statement.otherwise)
        elif isinstance(statement.condition, Binary):
            true_inst = None
            false_inst = None
            if statement.condition.operator.token_type == TokenType.EQUAL_EQUAL:
                true_inst = Instruction.JE
                false_inst = Instruction.JNE
            elif statement.condition.operator.token_type == TokenType.LESS:
                true_inst = Instruction.JL
                false_inst = Instruction.JGE
            elif statement.condition.operator.token_type == TokenType.GREATER:
                true_inst = Instruction.JG
                false_inst = Instruction.JLE
            else:
                raise Exception("Unhandled if condition operator")
                
            self.parse_comparison(namespace, statement.condition)
                
            self.add_instruction(Instruction.CMP, 0)
            self.add_instruction(true_inst, 0)
            then_index = len(self.instructions)-1
            self.add_instruction(false_inst, 0)
            else_index = len(self.instructions)-1
            self.instructions[then_index] = len(self.instructions)
            self.parse(Namespace(namespace, self.memory), statement.then)
            self.add_instruction(Instruction.JMP, 0)
            then_end_index = len(self.instructions)-1
            self.instructions[else_index] = len(self.instructions)
            if not statement.otherwise is None:
                self.parse(Namespace(namespace, self.memory), statement.otherwise)
            self.instructions[then_end_index] = len(self.instructions)
        elif isinstance(statement.condition, Variable):
            self.add_instruction(Instruction.LDA, self.memory.id_on_stack(namespace.get_namespace()[statement.condition.name]), stack_flag=True)
            self.add_instruction(Instruction.LDB, 1)
            self.add_instruction(Instruction.CMP, 0)
            self.add_instruction(Instruction.JE, 0)
            then_index = len(self.instructions)-1
            self.add_instruction(Instruction.JNE, 0)
            else_index = len(self.instructions)-1
            self.instructions[then_index] = len(self.instructions)
            self.parse(Namespace(namespace, self.memory), statement.then)
            self.add_instruction(Instruction.JMP, 0)
            then_end_index = len(self.instructions)-1
            self.instructions[else_index] = len(self.instructions)
            if not statement.otherwise is None:
                self.parse(Namespace(namespace, self.memory), statement.otherwise)
            self.instructions[then_end_index] = len(self.instructions)
        
        else:
            raise Exception("Unhandled if condition")
        
    def parse_let(self, namespace, statement):
        if isinstance(statement.initial, Literal):
            identifier = namespace.let(statement.name.lexeme, 1, statement.vtype.lexeme, False)
            value = statement.initial.value
            self.add_instruction(Instruction.PUSH, 1)
            self.add_instruction(Instruction.LDA, int(value)) # LDA value
            self.add_instruction(Instruction.STA, self.memory.id_on_stack(identifier), stack_flag=True) # STA var_name
        elif isinstance(statement.initial, Call):
            self.parse_call(namespace, statement.initial.callee, statement.initial.args)
            self.add_instruction(Instruction.MOV, mov(Register.AX, Register.FX)) # MOV AX <- FX
            identifier = namespace.let(statement.name.lexeme, 1, statement.vtype.lexeme, False)
            self.add_instruction(Instruction.PUSH, 1)
            self.add_instruction(Instruction.STA, self.memory.id_on_stack(identifier), stack_flag=True) # STA func_return
        elif isinstance(statement.initial, Binary):
            self.parse_binary(namespace, statement.initial)
            identifier = namespace.let(statement.name.lexeme, 1, statement.vtype.lexeme, False)
            self.add_instruction(Instruction.PUSH, 1)
            self.add_instruction(Instruction.STA, self.memory.id_on_stack(identifier), stack_flag=True) # STA sum
        elif isinstance(statement.initial, Variable):
            if statement.initial.name in self.function_names:
                self.add_instruction(Instruction.LDA, FunctionAddress(statement.initial))
                self.add_instruction(Instruction.PUSH, 1)
                identifier = namespace.let(statement.name.lexeme, 1, statement.vtype.lexeme, False)
                self.add_instruction(Instruction.STA, self.memory.id_on_stack(identifier), stack_flag=True)
            else:
                self.add_instruction(Instruction.LDA, self.memory.id_on_stack(namespace.get_namespace()[statement.initial.name]), stack_flag=True)
                self.add_instruction(Instruction.PUSH, 1)
                identifier = namespace.let(statement.name.lexeme, 1, statement.vtype.lexeme, False)
                self.add_instruction(Instruction.STA, self.memory.id_on_stack(identifier), stack_flag=True)
        elif isinstance(statement.initial, Array):
            identifier = namespace.let(statement.name.lexeme, statement.length.value+1, statement.vtype.lexeme, True)
            self.load_array(namespace, statement.initial, force_length=statement.length.value)
            
        elif isinstance(statement.initial, Index):
            self.parse_index(namespace, statement.initial.variable, statement.initial.index, register=Register.AX)
            self.add_instruction(Instruction.PUSH, 1)
            identifier = namespace.let(statement.name.lexeme, 1, statement.vtype.lexeme, False)
            self.add_instruction(Instruction.STA, self.memory.id_on_stack(identifier), stack_flag=True)
        else:
            raise Exception("Unhandled let statement")
        
    def parse_assign(self, namespace, statement):
        if not statement.name in namespace.get_namespace():
            raise Exception(f"Assignment to uninitialised variable {statement.name}. Use 'let type name = value;' to initialise.")
        if isinstance(statement.value, Literal):
            value = statement.value.value
            self.add_instruction(Instruction.LDA, value) # LDA value
            self.add_instruction(Instruction.STA, self.memory.id_on_stack(namespace.get_namespace()[statement.name]), stack_flag=True, mem_flag=True) # STA [var_name]
        elif isinstance(statement.value, Binary):
            # increment in place if variable and +1
            if isinstance(statement.value.left, Variable):
                if statement.value.left.name == statement.name:
                    if isinstance(statement.value.right, Literal):
                        if statement.value.right.value == 1:
                            if statement.value.operator.token_type == TokenType.PLUS:
                                self.add_instruction(Instruction.OFF, 0)
                                self.add_instruction(Instruction.INC, self.memory.id_on_stack(namespace.get_namespace()[statement.value.left.name]), stack_flag=True)
                                return
            self.parse_binary(namespace, statement.value)
            self.add_instruction(Instruction.STA, self.memory.id_on_stack(namespace.get_namespace()[statement.name]), stack_flag=True, mem_flag=True) # STA [var_name]
        elif isinstance(statement.value, Variable):
            self.add_instruction(Instruction.LDA, self.memory.id_on_stack(namespace.get_namespace()[statement.value.name]), stack_flag=True)
            self.add_instruction(Instruction.PUSH, 1)
            self.add_instruction(Instruction.STA, 1, stack_flag=True)
        elif isinstance(statement.value, Call):
            if isinstance(statement.value.callee, Call):
                self.parse_call(namespace, statement.value.callee.callee, statement.value.callee.args)
                self.add_instruction(Instruction.MOV, mov(Register.AX, Register.FX)) # MOV AX <- FX
                self.memory.temp_extra_stack_vars += 1
                self.add_instruction(Instruction.PUSH, 1)
                self.add_instruction(Instruction.STA, 1, stack_flag=True)
                self.parse_call(namespace, 1, statement.value.args)
                self.add_instruction(Instruction.FREE, 1)
                self.memory.temp_extra_stack_vars -= 1
                self.add_instruction(Instruction.MOV, mov(Register.AX, Register.FX)) # MOV AX <- FX
                self.add_instruction(Instruction.STA, self.memory.id_on_stack(namespace.get_namespace()[statement.name]), stack_flag=True, mem_flag=True)
            else:
                self.parse_call(namespace, statement.value.callee, statement.value.args)
                self.add_instruction(Instruction.MOV, mov(Register.AX, Register.FX)) # MOV AX <- FX
                self.add_instruction(Instruction.STA, self.memory.id_on_stack(namespace.get_namespace()[statement.name]), stack_flag=True, mem_flag=True) # STA func_return
        elif isinstance(statement.value, Index):
            self.parse_index(namespace, statement.value.variable, statement.value.index, register=Register.AX)
            self.add_instruction(Instruction.STA, self.memory.id_on_stack(namespace.get_namespace()[statement.name]), stack_flag=True, mem_flag=True)
        else:
            raise Exception("Unhandled assign statement")
        
    def parse_assign_index(self, namespace, statement):
        if isinstance(statement.right, Literal):
            self.add_instruction(Instruction.LDA, statement.right.value)
        elif isinstance(statement.right, Variable):
            self.add_instruction(Instruction.LDA, self.memory.id_on_stack(namespace.get_namespace()[statement.right.name]), stack_flag=True)
        elif isinstance(statement.right, Index):
            self.parse_index(namespace, statement.right.variable, statement.right.index, register=Register.AX)
        else:
            raise Exception("Unhandled index assign value")
        
        if isinstance(statement.left.index, Literal):
            index = statement.left.index.value
            self.add_instruction(Instruction.OFF, index+1)
        elif isinstance(statement.left.index, Variable):
            self.add_instruction(Instruction.LDB, self.memory.id_on_stack(namespace.get_namespace()[statement.left.index.name]), stack_flag=True)
            self.add_instruction(Instruction.INC, 255-Register.BX.value)
            self.add_instruction(Instruction.MOV, mov(Register.OX, Register.BX))
        elif isinstance(statement.left.index, Binary):
            self.parse_binary(namespace, statement.left.index)
            self.add_instruction(Instruction.INC, 255-Register.BX.value)
            self.add_instruction(Instruction.MOV, mov(Register.OX, Register.BX))
        else:
            raise Exception("Unhandled index assign index")
        
        self.add_instruction(Instruction.STA, self.memory.id_on_stack(namespace.get_namespace()[statement.left.variable.name]), stack_flag=True)
        self.add_instruction(Instruction.OFF, 0)
        
        
    def parse_for(self, namespace, statement):
        # comparison used to jump to end of loop
        compare_inst = {
            TokenType.EQUAL_EQUAL: Instruction.JNE,
            TokenType.LESS: Instruction.JGE,
            TokenType.GREATER: Instruction.JLE,
            TokenType.LESS_EQUAL: Instruction.JG,
            TokenType.GREATER_EQUAL: Instruction.JL,
        }[statement.condition.operator.token_type]
        self.parse_let(namespace, statement.declare)
        comparison_start = len(self.instructions)
        self.parse_comparison(namespace, statement.condition)
        self.add_instruction(Instruction.CMP, 0)
        self.add_instruction(compare_inst, 0)
        compare_data_byte = len(self.instructions)-1
        block_namespace = Namespace(namespace, self.memory)
        self.parse(block_namespace, statement.block, dont_free=True)
        action_start = len(self.instructions)
        self.parse_assign(namespace, statement.action)
        self.free_local_stack(block_namespace)
        self.add_instruction(Instruction.JMP, comparison_start)
        end_addr = len(self.instructions)
        self.instructions[compare_data_byte] = end_addr
        
        self.memory.unstack(len(namespace.locals))
        self.add_instruction(Instruction.POP, len(namespace.locals))
        
    def parse_while(self, namespace, statement):
        compare_inst = {
            TokenType.EQUAL_EQUAL: Instruction.JNE,
            TokenType.LESS: Instruction.JGE,
            TokenType.GREATER: Instruction.JLE,
            TokenType.LESS_EQUAL: Instruction.JG,
            TokenType.GREATER_EQUAL: Instruction.JL,
        }[statement.condition.operator.token_type]
        comparison_start = len(self.instructions)
        self.parse_comparison(namespace, statement.condition)
        self.add_instruction(Instruction.CMP, 0)
        self.add_instruction(compare_inst, 0)
        compare_data_byte = len(self.instructions)-1
        block_namespace = Namespace(namespace, self.memory)
        self.parse(block_namespace, statement.block, dont_free=True)
        self.free_local_stack(block_namespace)
        self.add_instruction(Instruction.JMP, comparison_start)
        end_addr = len(self.instructions)
        self.instructions[compare_data_byte] = end_addr
        
        
                
        
    def parse(self, namespace, block, is_function=False, dont_free=False, parameter_identifiers=None):
        # print("Parsing a block with namespace", namespace.locals, namespace.get_namespace())
        if parameter_identifiers is None:
            parameter_identifiers = []
        already_popped = dont_free
        
        for statement in block.statements:
            if isinstance(statement, Block):
                self.parse(Namespace(namespace, self.memory), statement)
            
            elif isinstance(statement, Let):
                self.parse_let(namespace, statement)
            
            elif isinstance(statement, If):
                self.parse_if(namespace, statement)
            
            elif isinstance(statement, Assign):
                self.parse_assign(namespace, statement)
                
            elif isinstance(statement, AssignIndex):
                self.parse_assign_index(namespace, statement)
                        
            
            elif isinstance(statement, Call):
                if not statement.callee.name in namespace.get_namespace():
                    raise Exception(f"Call to undefined function {statement.callee.name}")
                if statement.callee.name == "__internal_print":
                    for arg in statement.args:
                        if isinstance(arg, Variable):
                            if not arg.name in namespace.get_namespace():
                                raise Exception(f"Call with uninitialised variable {arg.name}")
                            self.add_instruction(Instruction.PRX, self.memory.id_on_stack(namespace.get_namespace()[arg.name]), stack_flag=True) # PRX var
                elif statement.callee.name == "__internal_print_char":
                    for arg in statement.args:
                        if isinstance(arg, Literal):
                            self.add_instruction(Instruction.PRC, arg.value)
                        else:
                            if not arg.name in namespace.get_namespace():
                                raise Exception(f"Call with uninitialised variable {arg.name}")
                            self.add_instruction(Instruction.PRC, self.memory.id_on_stack(namespace.get_namespace()[arg.name]), stack_flag=True) # PRX var
                else:
                    self.parse_call(namespace, statement.callee, statement.args)
                    
                        
            elif isinstance(statement, Return):
                already_popped = True
                if isinstance(statement.value, Literal):
                    if len(namespace.get_namespace(no_globals=True)) > 0:
                        self.free_local_stack(namespace, parameter_identifiers=parameter_identifiers, is_return=True)
                    self.add_instruction(Instruction.RET, statement.value.value) # RET value
                elif isinstance(statement.value, Variable):
                    if statement.value.name in self.function_names:
                        self.add_instruction(Instruction.LDA, FunctionAddress(statement.value))
                        self.add_instruction(Instruction.MOV, mov(Register.FX, Register.AX)) # MOV FX <- AX
                        if len(namespace.get_namespace(no_globals=True)) > 0:
                            self.free_local_stack(namespace, parameter_identifiers=parameter_identifiers, is_return=True)
                        self.add_instruction(Instruction.RET, 0, stack_flag=True)
                    else:
                        self.add_instruction(Instruction.LDA, self.memory.id_on_stack(namespace.get_namespace()[statement.value.name]), stack_flag=True)
                        self.add_instruction(Instruction.MOV, mov(Register.FX, Register.AX)) # MOV FX <- AX
                        if len(namespace.get_namespace(no_globals=True)) > 0:
                            self.free_local_stack(namespace, parameter_identifiers=parameter_identifiers, is_return=True)
                        self.add_instruction(Instruction.RET, 0, stack_flag=True)
                elif isinstance(statement.value, Binary):
                    self.parse_binary(namespace, statement.value)
                    self.add_instruction(Instruction.MOV, mov(Register.FX, Register.AX)) # MOV FX <- AX
                    if len(namespace.get_namespace(no_globals=True)) > 0:
                        self.free_local_stack(namespace, parameter_identifiers=parameter_identifiers, is_return=True)
                    self.add_instruction(Instruction.RET, 0, stack_flag=True)
                else:
                    raise Exception("Unhandled return value", statement.value)
                break # don't compile anything after a return
                
            elif isinstance(statement, For):
                self.parse_for(Namespace(namespace, self.memory), statement)
                
            elif isinstance(statement, While):
                self.parse_while(Namespace(namespace, self.memory), statement)
                
            else:
                raise Exception("Unhandled statement type")
                    
        
        # local variables are freed at the end of a block
        if not already_popped:
            if is_function:
                #if len(namespace.get_namespace(no_globals=True)) > 0:
                #    self.add_instruction(Instruction.FREE, len(namespace.get_namespace(True)))
                self.free_local_stack(namespace, parameter_identifiers=parameter_identifiers, is_return=True)
                self.add_instruction(Instruction.RET, 0)
            else:
                self.free_local_stack(namespace, parameter_identifiers=parameter_identifiers)
                
        #for name in namespace.locals:
        #    self.memory.free(namespace.locals[name])
    
    def free_local_stack(self, namespace, parameter_identifiers=None, is_return=False):
        if parameter_identifiers is None:
            parameter_identifiers = []
        # nuke everything in the function if returning, otherwise just the local block
        local = namespace.get_namespace(no_globals=True) if is_return else namespace.locals
        if len(local) > 0:
            reverse_locals = dict(zip(local.values(), local.keys()))
            streak = 0
            for identifier in self.memory.stack[::-1]:
                if not identifier in reverse_locals:
                    break
                if not namespace.is_array(reverse_locals[identifier]):
                    streak += 1
                else:
                    # free single byte variables from memory
                    if streak > 0:
                        self.add_instruction(Instruction.FREE, streak)
                    streak = 0
                    # free the multi byte variable from memory
                    if identifier in parameter_identifiers:
                        self.add_instruction(Instruction.POP, 1)
                    else:
                        self.add_instruction(Instruction.FREE, 0, mem_flag=True)
            if streak > 0:
                self.add_instruction(Instruction.FREE, streak)
            if not is_return:
                self.memory.unstack(len(local))