from compiler.types import Types
from compiler.instructions import Instruction
from compiler.expressions import *

MEM_FLAG = 0b1000_0000
STACK_FLAG = 0b0100_0000

class InternalFunctions:
    functions = {}


def register(func):
    func.return_type = func.__annotations__["return"]
    func.arg_types = list(func.__annotations__.values())[:-1]
    InternalFunctions.functions[func.__name__] = func
    return func

class InternalFunctionDefinitions:
    @staticmethod
    @register
    def __internal_print(i: Types.INT) -> Types.VOID:
        if isinstance(i, Variable):
            yield Instruction.PRX, i.position_on_stack, STACK_FLAG
        elif isinstance(i, Literal):
            yield Instruction.PRX, i.value


    @staticmethod
    @register
    def __internal_print_char(c: Types.CHAR) -> Types.VOID:
        if isinstance(c, Variable):
            yield Instruction.PRC, c.position_on_stack, STACK_FLAG
        elif isinstance(c, Literal):
            yield Instruction.PRC, c.value