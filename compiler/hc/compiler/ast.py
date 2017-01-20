from compiler.tokenizer import TokenType

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
    
    def print(self, indent=0):
        print("    "*indent + f"function {self.rtype.lexeme} {self.name.lexeme} ({self.args}) {{")
        self.body.print(indent+1)
        print("    "*indent + "}")
        
class Expression:
    def __init__(self, expression):
        self.expression = expression
        
class Variable:
    def __init__(self, vtype, name, initial):
        self.vtype = vtype
        self.name = name
        self.initial = initial
    
    def print(self, indent=0):
        print("    "*indent + f"<Variable: let {self.vtype.lexeme} {self.name.lexeme} = {self.initial};>")
        
class Literal:
    def __init__(self, value):
        self.value = value
    
    def __repr__(self):
        return f"<Literal: {self.value}>"

class If:
    def __init__(self, condition, then, otherwise):
        self.condition = condition
        self.then = then
        self.otherwise = otherwise
        
    def print(self, indent=0):
        print("    "*indent + f"<If {self.condition}>")
        self.then.print(indent+1)
        if not self.otherwise is None:
            print("    "*indent + f"Otherwise:")
            self.otherwise.print(indent+1)

        
class ASTParser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.position = 0
        self.statements = []
    
    def check(self, token_type):
        return self.tokens[self.position].token_type == token_type
    
    def match(self, *token_types):
        if self.tokens[self.position].token_type in token_types:
            self.position += 1
            return True
        return False
    
    def consume(self, token_type, error_message="Unhandled error"):
        if self.tokens[self.position].token_type == token_type:
            self.position += 1
            return self.tokens[self.position-1]
        
        raise Exception(f"{error_message} on line {self.tokens[self.position].line}")
    
    def previous(self):
        return self.tokens[self.position-1]
        
    
    def at_end(self):
        return self.tokens[self.position].token_type == TokenType.EOF
        
        
    def parse(self):
        while not self.at_end():
            self.statements.append(self.declaration())
        return self.statements
    
    def declaration(self):
        if self.match(TokenType.FUNCTION):
            return self.function()
        if self.match(TokenType.LET):
            return self.let()
        
        return self.statement()
    
    def statement(self):
        if self.check(TokenType.LEFT_BRACE):
            return self.block()
        if self.match(TokenType.IF):
            return self.if_statement()
        
        return self.expression_statement()
    
    def function(self):
        rtype = self.consume(TokenType.IDENTIFIER, "Expected function return type")
        name = self.consume(TokenType.IDENTIFIER, "Expected function name")
        self.consume(TokenType.LEFT_BRACKET, "Expected '(' after function name")
        args = []
        arg_num = 0
        while not self.check(TokenType.RIGHT_BRACKET):
            arg_type = self.consume(TokenType.IDENTIFIER, f"Expected type for arg {arg_num}")
            arg_name = self.consume(TokenType.IDENTIFIER, f"Expected name for arg {arg_num}")
            args.append((arg_type, arg_name))
            self.consume(TokenType.COMMA, "Comma expected in function args after arg{arg_num}")
            arg_num += 1
        
        self.consume(TokenType.RIGHT_BRACKET, "Expected ')' after function args")
        
        function_body = self.block()
        return Function(name, rtype, args, function_body)
    
    def block(self):
        self.consume(TokenType.LEFT_BRACE, "Expected '{' to open block")
        statements = []
        while not self.check(TokenType.RIGHT_BRACE) and not self.at_end():
            statements.append(self.declaration())
        self.consume(TokenType.RIGHT_BRACE, "Expected '}' to close block")
        return Block(statements)
    
    def if_statement(self):
        self.consume(TokenType.LEFT_BRACKET)
        condition = self.expression()
        self.consume(TokenType.RIGHT_BRACKET)
        
        then = self.statement()
        if self.match(TokenType.ELSE):
            otherwise = self.statement()
        else:
            otherwise = None
        return If(condition, then, otherwise)
            
    def expression_statement(self):
        expr = self.expression()
        self.consume(TokenType.SEMICOLON, "Expected semicolon following expression")
        return expr
    
    def expression(self):
        return self.assignment()
    
    def assignment(self):
        return self.primary()
        
    def primary(self):
        if self.match(TokenType.TRUE):
            return Literal(True)
        if self.match(TokenType.FALSE):
            return Literal(False)
        
        if self.match(TokenType.STRING, TokenType.NUMBER):
            return Literal(self.previous().literal)
        
    def let(self):
        vtype = self.consume(TokenType.IDENTIFIER, "Expected variable type")
        name = self.consume(TokenType.IDENTIFIER, "Expected variable name")
        self.consume(TokenType.EQUAL, "Expected '=' in let statement")
        initial = self.expression()
        self.consume(TokenType.SEMICOLON, "Expected semicolon following let statement")
        return Variable(vtype, name, initial)
        