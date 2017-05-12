import sys
import os
import os.path as op
import codecs

from compiler.tokenizer import TokenType, Tokenizer
from compiler.expressions import *
from compiler.types import Types, TypeManager

class ASTParser:
    def __init__(self, tokens, source, filename, compiler):
        print(tokens)
        self.tokens = tokens
        self.sourcelines = source.split("\n")
        self.position = 0
        self.statements = []
        self.had_error = False
        self.filename = filename
        self.compile, self.compile_file = compiler
        
    def print_error(self, token, message):
        source_line = self.sourcelines[token.line-1]
        indentsize = len(source_line) - len(source_line.lstrip())
        source_line = source_line.lstrip()
        print(source_line, file=sys.stderr)
        print(" "*(token.char-indentsize) + "^", file=sys.stderr)
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
    
    def consume(self, token_type, error_message="Unhandled error", previous_line=False):
        if self.tokens[self.position].token_type == token_type:
            self.position += 1
            return self.tokens[self.position-1]
        
        if previous_line:
            token, line_num = self.tokens[self.position-1], self.tokens[self.position-1].line
        else:
            token, line_num = self.tokens[self.position], self.tokens[self.position].line
        
        self.print_error(token, f"{error_message} on line {line_num} in file {self.filename}")
        
        #self.position += 1
        #sys.exit(0)
        #raise Exception(f"{error_message} on line {self.tokens[self.position].line}")
    
    def previous(self):
        return self.tokens[self.position-1]
    
    def next(self):
        return self.tokens[self.position]
    
    def insert(self, tokens):
        self.tokens[self.position:self.position] = tokens
        
    
    def at_end(self):
        return self.position >= len(self.tokens) or self.tokens[self.position].token_type == TokenType.EOF
        
        
    def parse(self):
        while not self.at_end():
            token = self.tokens[self.position]
            next_expression = self.declaration()
            if not next_expression is None:
                next_expression.source_line = token.source_line
                next_expression.source_file = token.source_file
                next_expression.source_line_num = token.source_line_num
                self.statements.append(next_expression)
        return self.statements, self.had_error
    
    def declaration(self, no_let_semicolon=False):
        if self.match(TokenType.FUNCTION):
            return self.function()
        if self.match(TokenType.IMPORT):
            return self.import_statement()
        if self.match(TokenType.LET):
            return self.let(no_let_semicolon)
        if self.match(TokenType.RETURN):
            return self.return_statement()
        
        return self.statement()
    
    def statement(self):
        if self.check(TokenType.LEFT_BRACE):
            return self.block()
        if self.check(TokenType.LEFT_SQUARE):
            return self.array()
        if self.match(TokenType.IF):
            return self.if_statement()
        if self.match(TokenType.FOR):
            return self.for_()
        if self.match(TokenType.WHILE):
            return self.while_loop()
        
        return self.expression_statement()
    
    def find_lib(self, filename):
        locations = [".", "../lib", "../../lib"]
        for location in locations:
            if op.exists(location):
                if op.exists(op.join(location, filename)):
                    return location
    
    def import_statement(self):
        name = self.consume(TokenType.IDENTIFIER, "Expected module name")
        self.consume(TokenType.SEMICOLON, "Expected semicolon following import")
        
        filename = name.lexeme + ".hatch"
        cwd = os.getcwd()
        os.chdir(self.find_lib(filename))
        
        if op.exists(filename):
            with open(filename, "r") as import_file:
                source = import_file.read()
            tokenizer = Tokenizer(source, filename)
            tokens = tokenizer.tokenize(main=False)
            self.insert(tokens)
        else:
            self.print_error(name, f"Could not find module {name.lexeme}")
            
        os.chdir(cwd)
    
    def function(self):
        rtype = self.consume(TokenType.IDENTIFIER, "Expected function return type")
        name = self.consume(TokenType.IDENTIFIER, "Expected function name")
        self.consume(TokenType.LEFT_BRACKET, "Expected '(' after function name")
        args = []
        arg_num = 0
        while not self.check(TokenType.RIGHT_BRACKET):
            reference = False
            array = False
            arg_type = self.consume(TokenType.IDENTIFIER, f"Expected type for arg {arg_num}")
            if self.check(TokenType.LEFT_SQUARE):
                self.consume(TokenType.LEFT_SQUARE)
                self.consume(TokenType.RIGHT_SQUARE, "Expected closing square bracket for array argument")
                array = True
            if arg_type.lexeme == "string":
                array = True
            
            if self.check(TokenType.AMPERSAND):
                self.consume(TokenType.AMPERSAND)
                reference = True
            arg_name = self.consume(TokenType.IDENTIFIER, f"Expected name for arg {arg_num}")
            args.append((arg_type, arg_name, reference, array))
            if self.check(TokenType.RIGHT_BRACKET):
                break
            self.consume(TokenType.COMMA, "Comma expected in function args after arg{arg_num}")
            arg_num += 1
        
        self.consume(TokenType.RIGHT_BRACKET, "Expected ')' after function args")
        
        function_body = self.block()
        return_type = rtype#TypeManager.get_type(rtype.lexeme)
        return Function(name, return_type, args, function_body)
    
    def block(self):
        self.consume(TokenType.LEFT_BRACE, "Expected '{' to open block")
        statements = []
        while not self.check(TokenType.RIGHT_BRACE) and not self.at_end():
            starting_token = self.tokens[self.position]
            next_expression = self.declaration()
            next_expression.source_line = starting_token.source_line
            next_expression.source_file = starting_token.source_file
            next_expression.source_line_num = starting_token.source_line_num
            statements.append(next_expression)
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
        self.consume(TokenType.SEMICOLON, "Expected semicolon following expression", previous_line=True)
        return expr
    
    def expression(self):
        return self.assignment()
    
    def assignment(self):
        expr = self.equality()
        if self.match(TokenType.EQUAL):
            value = self.assignment()
            if isinstance(expr, Variable):
                return Assign(expr.name, value)
            if isinstance(expr, Index):
                return AssignIndex(expr, value)
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
        expr = self.array()
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
    
    def array(self):
        if self.check(TokenType.LEFT_SQUARE):
            self.consume(TokenType.LEFT_SQUARE, "Expected '[' to open array")
            elements = []
            while not self.check(TokenType.RIGHT_SQUARE) and not self.at_end():
                elements.append(self.primary())
                if not self.match(TokenType.COMMA):
                    break
            self.consume(TokenType.RIGHT_SQUARE, "Expected ']' to close array")
            return Array(elements)
        
        return self.primary()
        
    def primary(self):
        if self.match(TokenType.TRUE):
            return Literal(True, Types.BOOL)
        if self.match(TokenType.FALSE):
            return Literal(False, Types.BOOL)
        
        if self.match(TokenType.STRING, TokenType.NUMBER):
            if self.previous().token_type == TokenType.NUMBER:
                if not (0 <= self.previous().literal <= 255):
                    self.print_error(self.previous(), "Integer literal outside range 0-255")
                if self.check(TokenType.IDENTIFIER):
                    if self.next().lexeme.lower() == "c":
                        char = Literal(self.previous().literal, Types.CHAR)
                        self.consume(TokenType.IDENTIFIER)
                        return char
                return Literal(self.previous().literal, Types.INT)
            elif self.previous().token_type == TokenType.STRING:
                unescaped_string = codecs.getdecoder("unicode_escape")(self.previous().literal)[0]
                string_array = Array([Literal(byte, Types.CHAR) for byte in list(bytes(unescaped_string, "utf8"))], is_string=True)
                return string_array
        
        if self.match(TokenType.IDENTIFIER):
            if self.check(TokenType.LEFT_SQUARE):
                variable = Variable(self.previous().lexeme)
                self.consume(TokenType.LEFT_SQUARE)
                index = self.term()
                self.consume(TokenType.RIGHT_SQUARE, "Expected ']' to close index")
                return Index(variable, index)
            return Variable(self.previous().lexeme)
        
        return Literal(1, Types.INT)
        
    def let(self, no_semicolon=False):
        vtype = self.consume(TokenType.IDENTIFIER, "Expected variable type")
        is_array = False
        array_length = 1
        if self.check(TokenType.LEFT_SQUARE):
            is_array = True
            self.consume(TokenType.LEFT_SQUARE)
            #array_length = self.consume(TokenType.NUMBER, "Expected array length")
            if self.check(TokenType.RIGHT_SQUARE):
                self.print_error(self.next(), "No array length specified")
            array_length = self.primary()
            self.consume(TokenType.RIGHT_SQUARE, "Expected closing square bracket")
        name = self.consume(TokenType.IDENTIFIER, "Expected variable name")
        self.consume(TokenType.EQUAL, "Expected '=' in let statement")
        initial = self.expression()
        if vtype.lexeme == "string":
            is_array = True
            print(initial)
            array_length = Literal(len(initial.elements), Types.INT)
            
        if not no_semicolon:
            self.consume(TokenType.SEMICOLON, "Expected semicolon following let statement")
        
        branch = Let(vtype, name, initial, is_array, array_length)
        return branch
    
    def return_statement(self):
        value = None
        if not self.check(TokenType.SEMICOLON):
            value = self.expression()
        self.consume(TokenType.SEMICOLON, "Expected semicolon after return statement", previous_line=True)
        return Return(value)
    
    def for_(self):
        self.consume(TokenType.LEFT_BRACKET, "Expected '(' after for")
        declare = self.declaration(no_let_semicolon=True)
        self.consume(TokenType.SEMICOLON, "Expected ';' in for loop")
        condition = self.expression()
        self.consume(TokenType.SEMICOLON, "Expected ';' in for loop")
        action = self.expression()
        self.consume(TokenType.RIGHT_BRACKET, "Expected ')' after for")
        
        body = self.statement()

        return For(declare, condition, action, body)
    
    def while_loop(self):
        self.consume(TokenType.LEFT_BRACKET, "Expected '(' after 'while'")
        condition = self.expression()
        self.consume(TokenType.RIGHT_BRACKET, "Expected ')' to close while statement")
        
        body = self.statement()
        
        return While(condition, body)