import sys

from compiler.tokenizer import TokenType
from compiler.expressions import *

class ASTParser:
    def __init__(self, tokens, source):
        self.tokens = tokens
        self.sourcelines = source.split("\n")
        self.position = 0
        self.statements = []
        self.had_error = False
        
    def print_error(self, token, message):
        print(self.sourcelines[token.line-1].lstrip(), file=sys.stderr)
        print(message, file=sys.stderr)
        print("", file=sys.stderr)
        self.had_error = True
    
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
        
        self.print_error(self.tokens[self.position], f"{error_message} on line {self.tokens[self.position-1].line-1}")
        
        #sys.exit(0)
        #raise Exception(f"{error_message} on line {self.tokens[self.position].line}")
    
    def previous(self):
        return self.tokens[self.position-1]
        
    
    def at_end(self):
        return self.tokens[self.position].token_type == TokenType.EOF
        
        
    def parse(self):
        while not self.at_end():
            self.statements.append(self.declaration())
        return self.statements, self.had_error
    
    def declaration(self):
        if self.match(TokenType.FUNCTION):
            return self.function()
        if self.match(TokenType.LET):
            return self.let()
        if self.match(TokenType.RETURN):
            return self.return_statement()
        
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
            if self.check(TokenType.RIGHT_BRACKET):
                break
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
        self.consume(TokenType.LEFT_BRACKET, "Expected '(' after if")
        condition = self.expression()
        self.consume(TokenType.RIGHT_BRACKET, "Expected ')' after if condition")
        
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
        expr = self.equality()
        if self.match(TokenType.EQUAL):
            value = self.assignment()
            if (expr, Variable):
                return Assign(expr.name, value)
        return expr
    
    def equality(self):
        expr = self.comparison()
        
        while self.match(TokenType.EQUAL_EQUAL, TokenType.NOT_EQUAL):
            operator = self.previous()
            right = self.comparison()
            expr = Binary(expr, operator, right)
        
        return expr
    
    def comparison(self):
        expr = self.term()
        while self.match(TokenType.GREATER_EQUAL, TokenType.GREATER, TokenType.LESS, TokenType.LESS_EQUAL):
            operator = self.previous()
            right = self.term()
            expr = Binary(expr, operator, right)
        return expr
    
    
    def term(self):
        expr = self.factor()
        while self.match(TokenType.PLUS, TokenType.MINUS):
            operator = self.previous()
            right = self.factor()
            expr = Binary(expr, operator, right)
        return expr
    
    def factor(self):
        expr = self.unary()
        while self.match(TokenType.STAR, TokenType.SLASH):
            operator = self.previous()
            right = self.unary()
            if operator.token_type == TokenType.SLASH:
                if isinstance(right, Literal):
                    if right.value == 0:
                        raise Exception(f"Division by zero on line {self.tokens[self.position].line}")
            expr = Binary(expr, operator, right)
        return expr
    
    
    def unary(self):
        if self.match(TokenType.MINUS):
            operator = self.previous()
            right = self.unary()
            expr = Binary(operator, right)
        return self.call()
    
    
    def call(self):
        expr = self.primary()
        while True:
            if self.match(TokenType.LEFT_BRACKET):
                expr = self.finish_call(expr)
            else:
                break
        return expr
    
    def finish_call(self, callee):
        args = []
        if not self.check(TokenType.RIGHT_BRACKET):
            while True:
                args.append(self.expression())
                if not self.match(TokenType.COMMA):
                    break
        paren = self.consume(TokenType.RIGHT_BRACKET, "Expected ')' to close function call")
        
        return Call(callee, paren, args)
        
    def primary(self):
        if self.match(TokenType.TRUE):
            return Literal(True)
        if self.match(TokenType.FALSE):
            return Literal(False)
        
        if self.match(TokenType.STRING, TokenType.NUMBER):
            if not (0 <= self.previous().literal <= 255):
                self.print_error(self.previous(), "Integer literal outside range 0-255")
            return Literal(self.previous().literal)
        
        if self.match(TokenType.IDENTIFIER):
            return Variable(self.previous().lexeme)
        
        return Literal(0)
        
    def let(self):
        vtype = self.consume(TokenType.IDENTIFIER, "Expected variable type")
        name = self.consume(TokenType.IDENTIFIER, "Expected variable name")
        self.consume(TokenType.EQUAL, "Expected '=' in let statement")
        initial = self.expression()
        self.consume(TokenType.SEMICOLON, "Expected semicolon following let statement")
        return Let(vtype, name, initial)
    
    def return_statement(self):
        value = None
        if not self.check(TokenType.SEMICOLON):
            value = self.expression()
        self.consume(TokenType.SEMICOLON, "Expected semicolon after return statement")
        return Return(value)