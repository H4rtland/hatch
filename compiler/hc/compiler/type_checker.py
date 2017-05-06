import uuid

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
        
        # Use this identifier to find current function in return checker.
        # Use a uuid to prevent overlap with any user defined function name
        # like "current_function" which could otherwise be used in the namespace.
        self.current_function_identifier = uuid.uuid4().hex
        
    def print_error(self, error):
        #print(error, file=sys.stderr)
        raise Exception(error)
        
    def check(self):
        namespace = {f.name.lexeme:f for f in self.ast}
        #print(namespace)
        for function in self.ast:
            self.check_branch(function, namespace)
            
    def check_branch(self, branch, namespace):
        if branch.__class__ in expression_checkers:
            # copy namespace so modifications only get passed down, not back up
            expression_checkers[branch.__class__](self, branch, dict(namespace))
        else:
            print(f"TypeChecker: Unchecked branch: {branch.__class__.__name__}")
            
    @checker_for(Function)
    def check_function(self, function, namespace):
        namespace[self.current_function_identifier] = function
        for arg in function.args:
            namespace[arg[1].lexeme] = Let(arg[0], arg[1].lexeme, 0, False, 0)
        self.check_branch(function.body, namespace)
        
    @checker_for(Block)
    def check_block(self, block, namespace):
        for statement in block.statements:
            self.check_branch(statement, namespace)
            if isinstance(statement, Let):
                namespace[statement.name.lexeme] = statement
            
    @checker_for(If)
    def check_if(self, if_statement: If, namespace):
        #print(if_statement.condition.resolve_type(namespace))
        if not if_statement.condition.resolve_type(namespace) == Types.BOOL:
            self.print_error("If statement did not receive boolean expression")
        #if isinstance(if_statement.condition, Binary):
        #    if not (if_statement.condition.left.resolve_type(namespace) == if_statement.condition.right.resolve_type(namespace)):
        #        self.print_error(f"Comparison type mismatch: {if_statement.condition.left.resolve_type(namespace)} != {if_statement.condition.right.resolve_type(namespace)}")
    
    @checker_for(Return)
    def check_return(self, return_statement: Return, namespace):
        current_function = namespace[self.current_function_identifier]
        print(type(return_statement.resolve_type(namespace)), type(current_function.resolve_type(namespace)))
        if not return_statement.resolve_type(namespace) == current_function.resolve_type(namespace):
            self.print_error(f"Return type mismatch: {return_statement.resolve_type(namespace)} != {current_function.resolve_type(namespace)}")
            
    @checker_for(Let)
    def check_let(self, let_statement: Let, namespace):
        if not TypeManager.get_type(let_statement.vtype.lexeme) == let_statement.initial.resolve_type(namespace):
            self.print_error(f"Let statement type mismatch: "
                             f"{TypeManager.get_type(let_statement.vtype.lexeme)} != {let_statement.initial.resolve_type(namespace)}")