from compiler.tokenizer import TokenType
from compiler.types import TypeManager, Types

class ExpressionValidationException(Exception):
    pass

class Block:
    def __init__(self, statements):
        self.statements = statements
    
    def print(self, indent=0):
        print("    "*indent + "<Block> {")
        for statement in self.statements:
            statement.print(indent+1)
        print("    "*indent + "}")

class Function:
    def __init__(self, name, rtype, args, body):
        self.name = name
        self.rtype = rtype
        self.args = args
        self.body = body
        
    def resolve_type(self, namespace):
        return TypeManager.get_type(self.rtype.lexeme)
    
    def print(self, indent=0):
        print("    "*indent + f"<Function: {self.rtype} {self.name.lexeme} ({self.args})>")
        self.body.print(indent+1)
        
    def __repr__(self):
        return f"<Function: {self.rtype} {self.name.lexeme} ({self.args})>"
        
class Expression:
    def __init__(self, expression):
        self.expression = expression
        
class Assign:
    def __init__(self, name, value):
        self.name = name
        self.value = value
    
    def print(self, indent=0):
        print("    "*indent + f"<Assign: {self.name} = {self.value}>")
    
    def __repr__(self):
        return f"<Assign: {self.name} = {self.value}>"
    
class AssignIndex:
    def __init__(self, left, right):
        self.left = left
        self.right = right
        
    def __repr__(self):
        return f"<AssignIndex: {self.left.variable}[{self.left.index}] = {self.right}>"
    
    def print(self, indent=0):
        print("    "*indent + f"<AssignIndex: {self.left.variable.name}[{self.left.index}] = {self.right}>")
            
        
class Let:
    def __init__(self, vtype, name, initial, array, length):
        self.vtype = vtype
        self.name = name
        self.initial = initial
        self.array = array
        self.length = length
        
    def print(self, indent=0):
        print("    "*indent + f"<Let: {self.vtype.lexeme} {self.name.lexeme} = {self.initial}>")
        
    def __repr__(self):
        return f"<Let: {self.vtype.lexeme} {self.name.lexeme} = {self.initial}>"
        
class Variable:
    def __init__(self, name):
        self.name = name
        
    def print(self, indent=0):
        print(self.name)
    
    def __repr__(self):
        return f"<Variable: {self.name}>"
    
    def resolve_type(self, namespace):
        return namespace[self.name].type
    
class Index:
    def __init__(self, variable, index):
        self.variable = variable
        self.index = index
        
    def __repr__(self):
        return f"<Index: {self.variable}[{self.index}]>"
    
    def resolve_type(self, namespace):
        if namespace[self.variable.name].type == Types.STRING:
            return Types.INT
        return namespace[self.variable.name].type
        
class Literal:
    def __init__(self, value, type_):
        self.value = value
        self.type = type_
        
    def resolve_type(self, namespace):
        return self.type
    
    def __repr__(self):
        return f"<Literal: {self.value}, {self.type}>"
    
    def print(self, indent=0):
        print("    "*indent + f"<Literal {self.value}, {self.type}>")

class If:
    def __init__(self, condition, then, otherwise):
        self.condition = condition
        self.then = then
        self.otherwise = otherwise
        
    def print(self, indent=0):
        print("    "*indent + f"<If {self.condition}>")
        self.then.print(indent+1)
        if not self.otherwise is None:
            print("    "*indent + "<Otherwise>")
            self.otherwise.print(indent+1)


class Call:
    def __init__(self, callee, paren, args):
        self.callee = callee
        self.paren = paren
        self.args = args
        
    def print(self, indent=0):
        print("    "*indent + str(self))
    
    def __repr__(self):
        return f"<Call: func {self.callee}, args {self.args}>"
    
    def resolve_type(self, namespace):
        function = namespace[self.callee.name]
        if len(function.args) != len(self.args):
            raise ExpressionValidationException(f"Wrong number of args: expected {len(function.args)}, got {len(self.args)}")
        arg_pairs = zip(function.args, self.args)
        for i, (f, c) in enumerate(arg_pairs):
            if not (f.type == c.resolve_type(namespace)):
                raise ExpressionValidationException(f"Argument mismatch: arg ({i}) {f.type} != {c.resolve_type(namespace)}")
            value_is_array = isinstance(c, Array)
            if isinstance(c, Variable):
                value_is_array = value_is_array or namespace[c.name].is_array
            if f.is_array != value_is_array:
                raise ExpressionValidationException(f"Argument {i} was {'' if f.is_array else 'not '}expecting an array")
        
        return function.return_type
    
class Return:
    def __init__(self, value):
        self.value = value
        
    def resolve_type(self, namespace):
        return self.value.resolve_type(namespace)

    def print(self, indent=0):
        print("    "*indent + f"<Return: {self.value}>")
        
class Binary:
    def __init__(self, left, operator, right):
        self.left = left
        self.operator = operator
        self.right = right
        
    def resolve_type(self, namespace):
        if not self.left.resolve_type(namespace) == self.right.resolve_type(namespace):
             if (self.left.resolve_type(), self.right.resolve_type()) in [(Types.INT, Types.STRING), (Types.STRING, Types.INT)]:
                 pass
             else:
                raise ExpressionValidationException(f"Binary type mismatch {self.left.resolve_type(namespace)} != {self.right.resolve_type(namespace)}")
        if self.operator.token_type in [TokenType.EQUAL_EQUAL, TokenType.NOT_EQUAL, TokenType.GREATER_EQUAL, TokenType.LESS_EQUAL]:
            return Types.BOOL
        else:
            return self.left.resolve_type(namespace)
    
    def __repr__(self):
        return f"<Binary: {self.left} {self.operator.lexeme} {self.right}>"
    
    def print(self, indent=0):
        print("    "*indent + str(self))
    
class Unary:
    def __init__(self, operator, right):
        self.operator = operator
        self.right = right
        
    def __repr__(self):
        return f"<Unary: {self.operator.lexeme} {self.right}>"
    
class For:
    def __init__(self, declare, condition, action, block):
        self.declare = declare
        self.condition = condition
        self.action = action
        self.block = block
        
    def print(self, indent=0):
        print("    "*indent + f"<For: {self.declare}; {self.condition}; {self.action}>")
        for statement in self.block.statements:
            statement.print(indent+1)
        print("    "*indent + "}")
        
class Array:
    def __init__(self, elements, is_string=False):
        self.elements = elements
        self.is_string = is_string
        
    def __repr__(self):
        return f"<Array: {self.elements}>"
    
    def resolve_type(self, namespace):
        if self.is_string:
            return Types.STRING
        if not len(set([element.resolve_type(namespace) for element in self.elements])) == 1:
            raise ExpressionValidationException("Multiple data types in array")
        return self.elements[0].resolve_type(namespace)