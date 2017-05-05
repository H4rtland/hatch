from compiler.types import TypeManager, Types

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
        return self.rtype
    
    def print(self, indent=0):
        print("    "*indent + f"<Function: {self.rtype} {self.name.lexeme} ({self.args})>")
        self.body.print(indent+1)
        #print("    "*indent + "}")
        
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
        return TypeManager.get_type(namespace[self.name].vtype.lexeme)
        #return TypeManager.get_type("int")
    
class Index:
    def __init__(self, variable, index):
        self.variable = variable
        self.index = index
        
    def __repr__(self):
        return f"<Index: {self.variable}[{self.index}]>"
        
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
    
class Return:
    def __init__(self, value):
        self.value = value

    def print(self, indent=0):
        print("    "*indent + f"<Return: {self.value}>")
        
class Binary:
    def __init__(self, left, operator, right):
        self.left = left
        self.operator = operator
        self.right = right
        
    def resolve_type(self, namespace):
        return Types.BOOL
    
    def __repr__(self):
        return f"<Binary: {self.left} {self.operator.lexeme} {self.right}>"
    
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
        
class Array:
    def __init__(self, elements):
        self.elements = elements
        
    def __repr__(self):
        return f"<Array: {self.elements}>"