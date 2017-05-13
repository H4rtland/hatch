import uuid
import sys
from collections import namedtuple

import time

from compiler.expressions import *

expression_checkers = {}

class checker_for:
    def __init__(self, expression):
        self.expression = expression
    
    def __call__(self, f):
        expression_checkers[self.expression] = f
        return f
    
NamespaceFunction = namedtuple("NamespaceFunction", ["return_type", "args"])
NamespaceVariable = namedtuple("NamespaceVariable", ["type", "is_array"])

internal_functions = {
    "__internal_print":NamespaceFunction(Types.VOID, [NamespaceVariable(Types.INT, False)]),
    "__internal_print_char":NamespaceFunction(Types.VOID, [NamespaceVariable(Types.CHAR, False)]),
}
    

class TypeChecker:
    def __init__(self, source, ast):
        self.source = source.split("\n")
        self.ast = ast
        self.checking_expression = None
        
        # Use this identifier to find current function in return checker.
        # Use a uuid to prevent overlap with any user defined function name
        # like "current_function" which could otherwise be used in the namespace.
        self.current_function_identifier = uuid.uuid4().hex
        
    def print_error(self, error):
        time.sleep(0.01)
        print(f"File: {self.checking_expression.source_file}", file=sys.stderr)
        print(f"Line {self.checking_expression.source_line_num}: {self.checking_expression.source_line}", file=sys.stderr)
        print(error, file=sys.stderr)
        sys.exit(0)
        #raise Exception(error)
        
    def check(self):
        namespace = dict(internal_functions)
        for function in self.ast:
            args = [NamespaceVariable(TypeManager.get_type(arg[0].lexeme), arg[3]) for arg in function.args]
            namespace[function.name.lexeme] = NamespaceFunction(TypeManager.get_type(function.rtype.lexeme), args)
        print(namespace)
        try:
            for function in self.ast:
                self.check_branch(function, namespace)
        except ExpressionValidationException as e:
            self.print_error(str(e))
            
    def check_branch(self, branch, namespace):
        if branch.__class__ in expression_checkers:
            # copy namespace so modifications only get passed down, not back up
            self.checking_expression = branch
            expression_checkers[branch.__class__](self, branch, dict(namespace))
        else:
            print(f"TypeChecker: Unchecked branch: {branch.__class__.__name__}")
            
    @checker_for(Function)
    def check_function(self, function, namespace):
        namespace[self.current_function_identifier] = namespace[function.name.lexeme]
        for arg in function.args:
            # namespace[arg[1].lexeme] = Let(arg[0], arg[1].lexeme, 0, False, 0)
            # print(arg)
            namespace[arg[1].lexeme] = NamespaceVariable(TypeManager.get_type(arg[0].lexeme), arg[3])
        self.check_branch(function.body, namespace)
        
    @checker_for(Block)
    def check_block(self, block, namespace):
        for statement in block.statements:
            self.check_branch(statement, namespace)
            if isinstance(statement, Let):
                # namespace[statement.name.lexeme] = statement
                namespace[statement.name.lexeme] = NamespaceVariable(TypeManager.get_type(statement.vtype.lexeme), statement.array)
            
    @checker_for(If)
    def check_if(self, if_statement: If, namespace):
        if not if_statement.condition.resolve_type(namespace) == Types.BOOL:
            self.print_error("If statement did not receive boolean expression")
        self.check_branch(if_statement.then, namespace)
        self.check_branch(if_statement.otherwise, namespace)


    @checker_for(Return)
    def check_return(self, return_statement: Return, namespace):
        current_function = namespace[self.current_function_identifier]
        if not return_statement.resolve_type(namespace) == current_function.return_type:
            self.print_error(f"Return type mismatch: {return_statement.resolve_type(namespace)} != {current_function.return_type}")
            
    @checker_for(Let)
    def check_let(self, let_statement: Let, namespace):
        if TypeManager.get_type(let_statement.vtype.lexeme) == Types.VOID:
            self.print_error("Cannot create a void variable")
        if not TypeManager.get_type(let_statement.vtype.lexeme) == let_statement.initial.resolve_type(namespace):
            self.print_error(f"Let statement type mismatch: "
                             f"{TypeManager.get_type(let_statement.vtype.lexeme)} != {let_statement.initial.resolve_type(namespace)}")
            
    @checker_for(Call)
    def check_call(self, call_statement: Call, namespace):
        call_statement.resolve_type(namespace)
        
    @checker_for(Assign)
    def check_assign(self, assign_statement: Assign, namespace):
        assigning_to_type = namespace[assign_statement.name].type
        assigned_type = assign_statement.value.resolve_type(namespace)
        if not assigning_to_type == assigned_type:
            self.print_error(f"Assignment type mismatch: {assigning_to_type} != {assigned_type}")
            
    @checker_for(For)
    def check_for(self, for_loop: For, namespace):
        self.check_branch(for_loop.declare, namespace)
        if isinstance(for_loop.declare, Let):
            namespace[for_loop.declare.name.lexeme] = NamespaceVariable(TypeManager.get_type(for_loop.declare.vtype.lexeme), for_loop.declare.array)
        self.check_branch(for_loop.condition, namespace)
        if not for_loop.condition.resolve_type(namespace) == Types.BOOL:
            self.print_error("Expected boolean expression for while loop condition")
        self.check_branch(for_loop.action, namespace)
        self.check_branch(for_loop.block, namespace)
        
    @checker_for(While)
    def check_while(self, while_loop: While, namespace):
        self.check_branch(while_loop.condition, namespace)
        if not while_loop.condition.resolve_type(namespace) == Types.BOOL:
            self.print_error("Expected boolean expression for while loop condition")
        self.check_branch(while_loop.block, namespace)
        
    @checker_for(Binary)
    def check_binary(self, binary: Binary, namespace):
        binary.resolve_type(namespace)