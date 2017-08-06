import time

import sys

from compiler.tokenizer import TokenType
from compiler.types import TypeManager, Types, Type

class FunctionCounter:
    times_function_called = {}
    current_name = "main"
    @staticmethod
    def call_function(name):
        #if not FunctionCounter.current_name in FunctionCounter.times_function_called:
        #    return
        if name in FunctionCounter.times_function_called:
            FunctionCounter.times_function_called[name] += 1
        else:
            FunctionCounter.times_function_called[name] = 1

    @staticmethod
    def get_times_called(name):
        if name in FunctionCounter.times_function_called:
            return FunctionCounter.times_function_called[name]
        return 0

class ExpressionValidationException(Exception):
    pass

class Expression:
    def resolve_type(self, namespace, type_manager):
        raise ExpressionValidationException("Resolving type on unimplemented expression")

    def resolve_array(self, namespace):
        return False

    def optimise(self):
        return self

class Block(Expression):
    def __init__(self, statements):
        self.statements = statements
    
    def print(self, indent=0):
        print("    "*indent + "<Block> {")
        for statement in self.statements:
            statement.print(indent+1)
        print("    "*indent + "}")

    def optimise(self):
        for index, statement in enumerate(self.statements):
            self.statements[index] = statement.optimise()
        return self

class Function(Expression):
    def __init__(self, name, rtype, args, body, filename):
        self.name = name
        self.rtype = rtype
        self.args = args
        self.body = body
        self.filename = filename
        self.main_function = False
        # function can be uniquely identified by filename and function name
        
    def resolve_type(self, namespace, type_manager):
        return type_manager.get_type(self.rtype.lexeme)

    def optimise(self):
        self.body.optimise()
        return self
    
    def print(self, indent=0):
        args = ", ".join([type_.lexeme + " " + name.lexeme for (type_, name, *_) in self.args])
        print("    "*indent + f"<Function: {self.rtype.lexeme} {self.name.lexeme} ({args})>")
        self.body.print(indent+1)
        
    def __repr__(self):
        args = ", ".join([type_.lexeme + " " + name.lexeme for (type_, name, *_) in self.args])
        return f"<Function: {self.rtype.lexeme} {self.name.lexeme} ({args})>"

        
class Assign(Expression):
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def optimise(self):
        self.value = self.value.optimise()
        return self
    
    def print(self, indent=0):
        print("    "*indent + f"<Assign: {self.name} = {self.value}>")
    
    def __repr__(self):
        return f"<Assign: {self.name} = {self.value}>"
    
class AssignIndex(Expression):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def optimise(self):
        self.left = self.left.optimise()
        self.right = self.right.optimise()
        return self
        
    def __repr__(self):
        return f"<AssignIndex: {self.left.variable}[{self.left.index}] = {self.right}>"
    
    def print(self, indent=0):
        print("    "*indent + f"<AssignIndex: {self.left.variable.name}[{self.left.index}] = {self.right}>")
            
        
class Let(Expression):
    def __init__(self, vtype, name, initial, array, length):
        self.vtype = vtype
        self.name = name
        self.initial = initial
        self.array = array
        self.length = length

    def optimise(self):
        self.initial = self.initial.optimise()
        return self
        
    def print(self, indent=0):
        print("    "*indent + f"<Let: {self.vtype.lexeme} {self.name.lexeme} = {self.initial}>")
        
    def __repr__(self):
        return f"<Let: {self.vtype.lexeme} {self.name.lexeme} = {self.initial}>"
        
class Variable(Expression):
    def __init__(self, name):
        self.name = name
        self.increment = False
        self.decrement = False
        self.position_on_stack = None
        
    def print(self, indent=0):
        print("    "*indent + str(self))
    
    def __repr__(self):
        if self.increment:
            return f"<Variable: {self.name}++>"
        if self.decrement:
            return f"<Variable: {self.name}-->"
        return f"<Variable: {self.name}>"
    
    def resolve_type(self, namespace, type_manager):
        if not namespace.contains(self.name):
            raise ExpressionValidationException(f"Use of undefined variable '{self.name}'")
        return namespace.get(self.name).type

    def resolve_array(self, namespace):
        return namespace.get(self.name).is_array
    
class Index(Expression):
    def __init__(self, variable, index):
        self.variable = variable
        self.index = index

    def optimise(self):
        self.index = self.index.optimise()
        return self
        
    def __repr__(self):
        return f"<Index: {self.variable}[{self.index}]>"
    
    def resolve_type(self, namespace, type_manager):
        if namespace.get(self.variable.name).type == Types.STRING:
            return Types.CHAR
        return namespace.get(self.variable.name).type
        
class Literal(Expression):
    def __init__(self, value, type_):
        self.value = value
        self.type = type_
        
    def resolve_type(self, namespace, type_manager):
        return self.type
    
    def __repr__(self):
        return f"<Literal: {self.value}, {self.type}>"
    
    def print(self, indent=0):
        print("    "*indent + f"<Literal {self.value}, {self.type}>")

class If(Expression):
    def __init__(self, condition, then, otherwise):
        self.condition = condition
        self.then = then
        self.otherwise = otherwise

    def optimise(self):
        self.condition = self.condition.optimise()
        self.then = self.then.optimise()
        if not self.otherwise is None:
            self.otherwise = self.otherwise.optimise()
        if isinstance(self.condition, Literal):
            if self.condition.value == True:
                return self.then
            elif self.condition.value == False:
                return self.otherwise
        return self
        
    def print(self, indent=0):
        print("    "*indent + f"<If {self.condition}>")
        self.then.print(indent+1)
        if not self.otherwise is None:
            print("    "*indent + "<Otherwise>")
            self.otherwise.print(indent+1)


class Call(Expression):
    def __init__(self, callee, paren, args):
        self.callee = callee
        self.paren = paren
        self.args = args

    def optimise(self):
        for index, arg in enumerate(self.args):
            self.args[index] = arg.optimise()
        return self
        
    def print(self, indent=0):
        print("    "*indent + str(self))
    
    def __repr__(self):
        return f"<Call: func {self.callee}, args {self.args}>"

    def get_parameter_types(self, namespace, type_manager):
        types = [a.resolve_type(namespace, type_manager) for a in self.args]
        arrays = [a.resolve_array(namespace) for a in self.args]
        return list(zip(types, arrays))

    def format_parameter_types(self, namespace, type_manager):
        types = []
        for t, a in self.get_parameter_types(namespace, type_manager):
            types.append(t.name + ("[]" if a else ""))
        return ", ".join(types)

    def get_calling_to(self, namespace, type_manager):
        if isinstance(self.callee, Variable):
            if not namespace.has_matching_function([self.callee.name,], self.get_parameter_types(namespace, type_manager)):
                raise ExpressionValidationException(f"Call to undefined function {self.callee.name}({self.format_parameter_types(namespace, type_manager)})")
            function = namespace.get_matching_function([self.callee.name,], self.get_parameter_types(namespace, type_manager))
        elif isinstance(self.callee, Access):
            if not namespace.has_matching_function(self.callee.hierarchy, self.get_parameter_types(namespace, type_manager)):
                raise ExpressionValidationException(f"Call to undefined function {self.callee.joined_name()}({self.format_parameter_types(namespace, type_manager)})")
            function = namespace.get_matching_function(self.callee.hierarchy, self.get_parameter_types(namespace, type_manager))
        else:
            # Shouldn't be anything else
            time.sleep(0.01)
            raise Exception

        return function

    def get_calling_to_name(self, namespace, type_manager):
        if isinstance(self.callee, Access):
            func_name = namespace.get_matching_function_name(self.callee.hierarchy, self.get_parameter_types(namespace, type_manager))
            self.callee.hierarchy[-1] = func_name
        elif isinstance(self.callee, Variable):
            func_name = namespace.get_matching_function_name([self.callee.name,], self.get_parameter_types(namespace, type_manager))
            self.callee.name = func_name
        return func_name

    
    def resolve_type(self, namespace, type_manager):
        func = self.get_calling_to(namespace, type_manager)

        if len(func.args) != len(self.args):
            raise ExpressionValidationException(f"Wrong number of args: expected {len(func.args)}, got {len(self.args)}")
        arg_pairs = zip(func.args, self.args)
        for i, (f, c) in enumerate(arg_pairs):
            if not (f.type == c.resolve_type(namespace, type_manager)):
                raise ExpressionValidationException(f"Argument mismatch: arg ({i}) {f.type} != {c.resolve_type(namespace, type_manager)}")
            value_is_array = isinstance(c, Array)
            if isinstance(c, Variable):
                value_is_array = value_is_array or namespace.get(c.name).is_array
            if f.is_array != value_is_array:
                raise ExpressionValidationException(f"Argument {i} was {'' if f.is_array else 'not '}expecting an array")
        
        return func.return_type
    
class Return(Expression):
    def __init__(self, value):
        self.value = value
        
    def resolve_type(self, namespace, type_manager):
        return self.value.resolve_type(namespace, type_manager)

    def optimise(self):
        self.value = self.value.optimise()
        return self

    def print(self, indent=0):
        print("    "*indent + f"<Return: {self.value}>")

    def __repr__(self):
        return f"<Return: {self.value}>"
        
class Binary(Expression):
    def __init__(self, left, operator, right):
        self.left = left
        self.operator = operator
        self.right = right
        
    def resolve_type(self, namespace, type_manager):
        if not self.left.resolve_type(namespace, type_manager) == self.right.resolve_type(namespace, type_manager):
             if (self.left.resolve_type(namespace, type_manager), self.right.resolve_type(namespace, type_manager)) in [(Types.INT, Types.STRING), (Types.STRING, Types.INT)]:
                 pass
             else:
                 raise ExpressionValidationException(f"Comparison type mismatch {self.left.resolve_type(namespace, type_manager)} != {self.right.resolve_type(namespace, type_manager)}")
        if self.operator.token_type in [TokenType.EQUAL_EQUAL, TokenType.NOT_EQUAL,
                                        TokenType.GREATER_EQUAL, TokenType.LESS_EQUAL,
                                        TokenType.LESS, TokenType.GREATER]:
            return Types.BOOL
        else:
            return self.left.resolve_type(namespace, type_manager)

    def optimise(self):
        self.left = self.left.optimise()
        self.right = self.right.optimise()
        if isinstance(self.left, Literal) and isinstance(self.right, Literal) and self.operator.token_type in (TokenType.PLUS, TokenType.MINUS, TokenType.STAR, TokenType.SLASH):
            value = {
                TokenType.PLUS: self.left.value + self.right.value,
                TokenType.MINUS: self.left.value - self.right.value,
                TokenType.STAR: self.left.value * self.right.value,
                TokenType.SLASH: self.left.value // self.right.value,
            }[self.operator.token_type]
            return Literal(value, Types.VOID)
        return self
    
    def __repr__(self):
        return f"<Binary: {self.left} {self.operator.lexeme} {self.right}>"
    
    def print(self, indent=0):
        print("    "*indent + str(self))
    
class Unary(Expression):
    def __init__(self, operator, right):
        self.operator = operator
        self.right = right
        
    def __repr__(self):
        return f"<Unary: {self.operator.lexeme} {self.right}>"
    
class For(Expression):
    def __init__(self, declare, condition, action, block):
        self.declare = declare
        self.condition = condition
        self.action = action
        self.block = block

    def optimise(self):
        self.block = self.block.optimise()
        return self
        
    def print(self, indent=0):
        print("    "*indent + f"<For: {self.declare}; {self.condition}; {self.action}>")
        for statement in self.block.statements:
            statement.print(indent+1)
        print("    "*indent + "}")
        
class While(Expression):
    def __init__(self, condition, block):
        self.condition = condition
        self.block = block

    def optimise(self):
        self.block = self.block.optimise()
        return self

    def print(self, indent=0):
        print("    "*indent + f"<While: {self.condition}>")
        for statement in self.block.statements:
            statement.print(indent+1)
        print("    "*indent + "}")
        
class Array(Expression):
    def __init__(self, elements, is_string=False):
        self.elements = elements
        self.is_string = is_string
        
    def __repr__(self):
        return f"<Array: {self.elements}>"
    
    def resolve_type(self, namespace, type_manager):
        if self.is_string:
            return Types.STRING
        if not len(set([element.resolve_type(namespace, type_manager) for element in self.elements])) == 1:
            raise ExpressionValidationException("Multiple data types in array")
        return self.elements[0].resolve_type(namespace, type_manager)

    def resolve_array(self, namespace):
        return True
    
class Access(Expression):
    def __init__(self, hierarchy):
        self.hierarchy = hierarchy
        
    def resolve_type(self, namespace, type_manager):
        #return namespace[self.hierarchy[0]].get(*self.hierarchy[1:]).type
        group = namespace.get(*self.hierarchy[:-1])
        if hasattr(group, "internal_structure"):
            if not group.contains(self.hierarchy[-1]):
                raise ExpressionValidationException(f"Value {self.hierarchy[-2]} has no attribute \"{self.hierarchy[-1]}\"")
            self.access_at_position = group.internal_structure[self.hierarchy[-1]][0]
        return namespace.get(*self.hierarchy).type
        
    def __repr__(self):
        return f"<Access: {'.'.join(self.hierarchy)}>"

    def joined_name(self):
        return ".".join(self.hierarchy)
        
    def print(self, indent=0):
        print("    "*indent + f"<Access: {'.'.join(self.hierarchy)}>")
        
class AccessAssign(Expression):
    def __init__(self, access, value):
        self.access = access
        self.value = value

    def resolve_type(self, namespace, type_manager):
        group = namespace.get(*self.access.hierarchy[:-1])
        if hasattr(group, "internal_structure"):
            if not group.contains(self.access.hierarchy[-1]):
                raise ExpressionValidationException(f"Value {self.access.hierarchy[-2]} has no attribute \"{self.access.hierarchy[-1]}\"")
            self.access_at_position = group.internal_structure[self.access.hierarchy[-1]][0]

    def optimise(self):
        self.value = self.value.optimise()
        return self

    def __repr__(self):
        return f"<AccessAssign: {'.'.join(self.access.hierarchy)} = {self.value}>"
        
    def print(self, indent=0):
        print("    "*indent + f"<AccessAssign: {'.'.join(self.access.hierarchy)} = {self.value}>")

class Struct(Expression):
    def __init__(self, name, members):
        self.name = name
        self.members = members

    def __repr__(self):
        return f"<Struct: {self.name} {self.members}"

    def print(self, indent=0):
        print("    "*indent + "<Struct:\n" + ",\n".join(["    "*(indent+1) + t + " " + n for t, n in self.members]) + "\n" + "    "*indent + ">")

class StructCreate(Expression):
    def __init__(self, struct_type, args):
        self.struct_type = struct_type
        self.args = args

    def resolve_type(self, namespace, type_manager):
        self.actual_type = type_manager.get_type(self.struct_type.lexeme)
        return type_manager.get_type(self.struct_type.lexeme)

    def optimise(self):
        for index, arg in enumerate(self.args):
            self.args[index] = arg.optimise()
        return self

    def __repr__(self):
        return f"<StructCreate: {self.struct_type.lexeme}({', '.join([str(arg) for arg in self.args])})"

class Break(Expression):
    def __init__(self):
        pass

    def __repr__(self):
        return "<Break>"

    def print(self, indent=0):
        print("    "*indent + str(self))

class Continue(Expression):
    def __init__(self):
        pass

    def __repr__(self):
        return "<Continue>"

    def print(self, indent=0):
        print("    "*indent + str(self))

class Cast(Expression):
    def __init__(self, variable, cast_to):
        self.variable = variable
        self.cast_to = cast_to

    def resolve_type(self, namespace, type_manager):
        if not type_manager.is_cast_allowed(self.variable.resolve_type(namespace, type_manager), type_manager.get_type(self.cast_to)):
            raise ExpressionValidationException(
                f"Cast from type {self.variable.resolve_type(namespace, type_manager)} to type {type_manager.get_type(self.cast_to)} is not possible")
        return type_manager.get_type(self.cast_to)

    def optimise(self):
        return self.variable

    def __repr__(self):
        return f"<Cast {self.variable} -> {self.cast_to}>"

    def print(self, indent=0):
        print("    "*indent + str(self))