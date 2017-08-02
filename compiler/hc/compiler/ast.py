import sys
import os
import os.path as op
import codecs
import uuid
import collections

from compiler.tokenizer import TokenType, Tokenizer
from compiler.expressions import *
from compiler.types import Types, TypeManager

FunctionParameter = collections.namedtuple("FunctionParameter", ["type", "name", "reference", "is_array", "is_struct"])
StructMember = collections.namedtuple("StructMember", ["type", "name"])

class ASTParser:
    def __init__(self, tokens, compiler, main_file=None):
        self.tokens = tokens
        self.position = 0
        self.statements = []
        self.had_error = False
        self.compile, self.compile_file = compiler
        if not main_file is None:
            if op.exists(main_file):
                self.main_file = op.abspath(main_file)
            else:
                self.main_file = main_file
        else:
            self.main_file = None
        self.sub_trees = {}
        
    def print_error(self, token, message):
        source_line = token.source_line
        print(source_line, file=sys.stderr)
        print(" "*(token.char) + "^", file=sys.stderr)
        print(message, file=sys.stderr)
        print("", file=sys.stderr)
        self.had_error = True
    
    def check(self, *token_types):
        return self.tokens[self.position].token_type in token_types
    
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
        time.sleep(0.01)
        self.print_error(token, f"{error_message} on line {token.line} in file {token.source_file}")
    
    def previous(self):
        return self.tokens[self.position-1]
    
    def next(self):
        return self.tokens[self.position]
    
    def insert(self, tokens):
        self.tokens[self.position:self.position] = tokens
        
    
    def at_end(self):
        return self.position >= len(self.tokens) or self.tokens[self.position].token_type == TokenType.EOF

    def token_to_expression(self, token, expression):
        expression.source_line = token.source_line
        expression.source_file = token.source_file
        expression.source_line_num = token.source_line_num
        expression.is_in_main_file = token.source_file == self.main_file
        return expression
        
    def parse(self):
        # print(self.tokens)
        while not self.at_end():
            token = self.tokens[self.position]
            next_expression = self.declaration()
            if next_expression is None:
                continue
            self.token_to_expression(token, next_expression)
            self.statements.append(next_expression)
        return self.statements, self.sub_trees, self.had_error
    
    def declaration(self, no_let_semicolon=False):
        if self.match(TokenType.FUNCTION):
            return self.function()
        if self.match(TokenType.IMPORT):
            return self.import_statement()
        if self.match(TokenType.LET):
            return self.let(no_let_semicolon)
        if self.match(TokenType.RETURN):
            return self.return_statement()
        if self.match(TokenType.STRUCT):
            return self.struct()
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
        if self.check(TokenType.BREAK, TokenType.CONTINUE):
            return self.flow_control()
        
        return self.expression_statement()
    
    def find_lib(self):
        locations = ["../lib", "../../lib", "./lib"]
        for location in locations:
            if op.exists(location):
                return location
            """    if op.exists(op.join(location, filename)):
                    return location"""

    def find_module_lib(self, path):
        lib_location = self.find_lib()
        path = op.join(lib_location, *path) + ".hatch"
        if op.exists(path):
            return path

    def find_module_local(self, path):
        path = op.join(".", *path) + ".hatch"
        if op.exists(path):
            return path
    
    def import_statement(self):
        module_path = []
        while True:
            name = self.consume(TokenType.IDENTIFIER, "Expected module name")
            module_path.append(name.lexeme)
            if not self.check(TokenType.DOT):
                break
            self.consume(TokenType.DOT)
        self.consume(TokenType.SEMICOLON, "Expected semicolon following import")

        filepath = self.find_module_local(module_path) or self.find_module_lib(module_path)

        if filepath is None:
            self.print_error(name, f"Could not find module {'.'.join(module_path)}")
        else:
            filepath = op.abspath(filepath)

            with open(filepath, "r") as import_file:
                source = import_file.read()
            tokenizer = Tokenizer(source, filepath)
            tokens = tokenizer.tokenize(main=False)
            ast = ASTParser(tokens, compiler=[self.compile, self.compile_file])
            tree, sub_trees, error = ast.parse()
            if error:
                self.had_error = True
            else:
                self.sub_trees[name.lexeme] = (tree, sub_trees)
            #self.insert(tokens)

            
            #os.chdir(cwd)
    
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
            #args.append((arg_type, arg_name, reference, array))
            # will determine whether parameter is a struct at type checking time
            args.append(FunctionParameter(arg_type, arg_name, reference, array, False))
            if self.check(TokenType.RIGHT_BRACKET):
                break
            self.consume(TokenType.COMMA, "Comma expected in function args after arg{arg_num}")
            arg_num += 1
        
        self.consume(TokenType.RIGHT_BRACKET, "Expected ')' after function args")


        function_body = self.block()
        return_type = rtype#TypeManager.get_type(rtype.lexeme)

        if not name.lexeme == "main" or name.source_file != self.main_file:
            name.lexeme += f"###|{','.join([arg.type.lexeme + ('[]' if arg.is_array else '') for arg in args])}|{name.source_file}"
        function = Function(name, return_type, args, function_body, name.source_file)
        if name.lexeme == "main":
            function.main_function = True
        return function

    def struct(self):
        name = self.consume(TokenType.IDENTIFIER, "Expected name for struct").lexeme
        self.consume(TokenType.LEFT_BRACE, "Expected '{' to open struct block")
        members = []
        while True:
            if self.match(TokenType.RIGHT_BRACE):
                break
            member_type = self.consume(TokenType.IDENTIFIER, "Expected struct variable type")
            member_name = self.consume(TokenType.IDENTIFIER, "Expected struct variable name")
            members.append(StructMember(member_type.lexeme, member_name.lexeme))
            if not self.match(TokenType.COMMA):
                self.consume(TokenType.RIGHT_BRACE, "Expected right brace to close struct")
                break

        return Struct(name, members)

    def block(self):
        self.consume(TokenType.LEFT_BRACE, "Expected '{' to open block")
        statements = []
        while not self.check(TokenType.RIGHT_BRACE) and not self.at_end():
            starting_token = self.tokens[self.position]
            next_expression = self.declaration()
            self.token_to_expression(starting_token, next_expression)
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
            if isinstance(expr, Access):
                return AccessAssign(expr, value)
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
                token = self.tokens[self.position]
                args.append(self.token_to_expression(token, self.expression()))
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
            return Literal(1, Types.BOOL)
        if self.match(TokenType.FALSE):
            return Literal(0, Types.BOOL)
        
        if self.match(TokenType.STRING, TokenType.NUMBER):
            if self.previous().token_type == TokenType.NUMBER:
                if not (0 <= self.previous().literal <= 255):
                    self.print_error(self.previous(), "Integer literal outside range 0-255")
                if self.check(TokenType.IDENTIFIER):
                    if self.next().lexeme.lower() == "c":
                        char = Literal(self.previous().literal, Types.CHAR)
                        self.consume(TokenType.IDENTIFIER)
                        return char
                    elif self.next().lexeme.lower() == "b":
                        string_representation = str(self.previous().literal)
                        binary_number = int(string_representation, base=2)
                        self.consume(TokenType.IDENTIFIER)
                        return Literal(binary_number, Types.INT)
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
            if self.check(TokenType.DOT):
                # access
                hierarchy = [self.previous().lexeme,]
                while self.check(TokenType.DOT):
                    self.consume(TokenType.DOT)
                    next_name = self.consume(TokenType.IDENTIFIER, "Expected identifier for variable access")
                    hierarchy.append(next_name.lexeme)
                return Access(hierarchy)
            var = Variable(self.previous().lexeme)
            if self.check(TokenType.PLUSPLUS):
                self.consume(TokenType.PLUSPLUS)
                var.increment = True
            if self.check(TokenType.MINUSMINUS):
                self.consume(TokenType.MINUSMINUS)
                var.decrement = True
            return var

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
        if self.match(TokenType.NEW):
            if is_array:
                raise Exception("Cannot be struct and array")
            initial = self.struct_create()
        else:
            initial = self.expression()
            if vtype.lexeme == "string":
                is_array = True
                array_length = Literal(len(initial.elements), Types.INT)
            
        if not no_semicolon:
            self.consume(TokenType.SEMICOLON, "Expected semicolon following let statement")
        
        branch = Let(vtype, name, initial, is_array, array_length)
        return branch

    def struct_create(self):
        name = self.consume(TokenType.IDENTIFIER, "Expected a type for struct creation")
        self.consume(TokenType.LEFT_BRACKET, "Expected a left bracket to open struct")
        args = []
        while True:
            args.append(self.expression())
            if not self.match(TokenType.COMMA):
                break
        self.consume(TokenType.RIGHT_BRACKET, "Expected a right bracket to close struct")
        return StructCreate(name, args)
    
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

    def flow_control(self):
        if self.match(TokenType.BREAK):
            self.consume(TokenType.SEMICOLON, "Expected semicolon following break statement")
            return Break()
        if self.match(TokenType.CONTINUE):
            self.consume(TokenType.SEMICOLON, "Expected semicolon following continue statement")
            return Continue()