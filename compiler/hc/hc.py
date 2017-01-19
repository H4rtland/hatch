from enum import Enum

class Token(Enum):
    EOF = 0
    NEWLINE = 1
    NAME = 2
    NUMBER = 3
    CHAR = 4
    TYPE = 5
    BRACKET = 6
    EQUAL = 7
    
TYPES = ["void", "int"]

def get_token(hatch_chars):
    last_char = " "
    while last_char == " ":
        last_char = hatch_chars.pop(0)
        
    if last_char == "\n":
        return (Token.NEWLINE,)
    
    if last_char == "/":
        if hatch_chars[0] == "/":
            # comment until end of line
            while hatch_chars.pop(0) != "\n":
                continue
            return (Token.NEWLINE,)
    
    if last_char.isalnum():
        identifier = last_char
        while len(hatch_chars) > 0 and hatch_chars[0].isalnum():
            next_char = hatch_chars.pop(0)
            identifier += next_char
            
        if identifier.isdigit():
            return (Token.NUMBER, int(identifier))
        if identifier in TYPES:
            return (Token.TYPE, identifier)
        return (Token.NAME, identifier)
    
    if last_char in "()[]{}":
        return (Token.BRACKET, last_char)
    
    if last_char == "=":
        return (Token.EQUAL,)
        
    return (Token.CHAR, last_char)
    
    
        
            
    


def tokenize(hatch_code):
    hatch_chars = list(hatch_code)
    while len(hatch_chars) > 0:
        yield get_token(hatch_chars)
    yield (Token.EOF,)

        
if __name__ == "__main__":
    for token in tokenize("void main() {\nint number = 5;\n}"):
        print(token)