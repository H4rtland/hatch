import sys
from collections import namedtuple

from compiler.expressions import *

expression_checkers = {}


class checker_for:
    def __init__(self, expression):
        self.expression = expression
    
    def __call__(self, f):
        expression_checkers[self.expression] = f
        return f
    

class TypeChecker:
    def __init__(self, source, ast):
        self.source = source.split("\n")
        self.ast = ast
        
    def print_error(self, error):
        #print(error, file=sys.stderr)
        raise Exception(error)
        
    def check(self):
        namespace = {f.name.lexeme:f for f in self.ast}
        print(namespace)
        for function in self.ast:
            self.check_branch(function, namespace)
            
    def check_branch(self, branch, namespace):
        if branch.__class__ in expression_checkers:
            # copy namespace so modifications only get passed down, not back up
            expression_checkers[branch.__class__](self, branch, dict(namespace))
        else:
            print(f"Unchecked branch: {branch.__class__.__name__}")
            
    @checker_for(Function)
    def check_function(self, function, namespace):
        self.check_branch(function.body, namespace)
        
    @checker_for(Block)
    def check_block(self, block, namespace):
        for statement in block.statements:
            self.check_branch(statement, namespace)
            if isinstance(statement, Let):
                namespace[statement.name.lexeme] = statement
            
    @checker_for(If)
    def check_if(self, if_statement: If, namespace):
        print(if_statement.condition.resolve_type(namespace))
        if not if_statement.condition.resolve_type(namespace) == Types.BOOL:
            self.print_error("If statement did not receive boolean expression")
        if isinstance(if_statement.condition, Binary):
            if not (if_statement.condition.left.resolve_type(namespace) == if_statement.condition.right.resolve_type(namespace)):
                self.print_error(f"Comparison type mismatch: {if_statement.condition.left.resolve_type(namespace)} != {if_statement.condition.right.resolve_type(namespace)}")