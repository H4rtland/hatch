from enum import Enum, auto

class TokenType(Enum):
    EOF = auto()
    NEWLINE = auto()
    NAME = auto()
    NUMBER = auto()
    CHAR = auto()
    TYPE = auto()
    EQUAL = auto()
    EQUAL_EQUAL = auto()
    LESS_EQUAL = auto()
    GREATER_EQUAL = auto()
    NOT_EQUAL = auto()
    GREATER = auto()
    LESS = auto()
    NOT = auto()
    STRING = auto()
    SEMICOLON = auto()
    KEYWORD = auto()
    LEFT_BRACKET = auto()
    RIGHT_BRACKET = auto()
    LEFT_BRACE = auto()
    RIGHT_BRACE = auto()
    LEFT_SQUARE = auto()
    RIGHT_SQUARE = auto()
    COMMA = auto()
    DOT = auto()
    MINUS = auto()
    PLUS = auto()
    STAR = auto()
    SLASH = auto()
    
    
class Token:
    def __init__(self, token_type, lexeme, literal, line):
        self.token_type = token_type
        self.lexeme = lexeme
        self.literal = literal
        self.line = line
        self.start = 0
    
    def __repr__(self):
        return f"<Token: {self.token_type}, {self.lexeme}, {self.literal} (line {self.line})>"
    
SINGLE_CHARS = {
    "(":TokenType.LEFT_BRACKET,
    ")":TokenType.RIGHT_BRACKET,
    "{":TokenType.LEFT_BRACE,
    "}":TokenType.RIGHT_BRACE,
    "[":TokenType.LEFT_SQUARE,
    "]":TokenType.RIGHT_SQUARE,
    ",":TokenType.COMMA,
    ".":TokenType.DOT,
    "-":TokenType.MINUS,
    "+":TokenType.PLUS,
    "*":TokenType.STAR,
}
    
class Tokenizer:
    def __init__(self, hatch_source):
        self.hatch_source = hatch_source
        self.position = 0
        self.line = 0
        self.tokens = []
    
    def next(self):
        self.position += 1
        return self.hatch_source[self.position-1]
    
    def at_end(self):
        return self.position >= len(self.hatch_source)
    
    def peek_for(self, character):
        if self.at_end:
            return False
        if not self.peek(1) == character:
            return False
        self.next()
    
    def peek(self, depth):
        return self.hatch_source[self.position+depth-1]
    
    def next_token(self):
        next_char = self.next()
        if next_char in SINGLE_CHARS:
            return self.add_token(SINGLE_CHARS[next_char])
        
        if next_char == "=":
            if self.peek_for("="):
                return self.add_token(TokenType.EQUAL_EQUAL)
            return self.add_token(TokenType.EQUAL)
        
        if next_char == ">":
            if self.peek_for("="):
                return self.add_token(TokenType.GREATER_EQUAL)
            return self.add_token(TokenType.GREATER)

        if next_char == "<":
            if self.peek_for("="):
                return self.add_token(TokenType.LESS_EQUAL)
            return self.add_token(TokenType.LESS)
        
        if next_char == "!":
            if self.peek_for("="):
                return self.add_token(TokenType.NOT_EQUAL)
            return self.add_token(TokenType.NOT)
        
        if next_char == "/":
            if self.peek_for("/"):
                while (not self.at_end()) and self.peek(1) != "\n":
                    self.next()
                return
            else:
                return self.add_token(TokenType.SLASH)
            
        if next_char in (" ", "\r", "\t"):
            return
        if next_char == "\n":
            self.line += 1
            return
        
        print("Unhandled token")
    
    def tokenize(self):
        while self.position < len(self.hatch_source):
            self.start = self.position
            token = self.next_token()
        
        self.add_token(TokenType.EOF)
        
        return self.tokens
    
    def add_token(self, token_type, literal=None):
        lexeme = self.hatch_source[self.start:self.position]
        token = Token(token_type, lexeme, literal, self.line)
        self.tokens.append(token)
        return token