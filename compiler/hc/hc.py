from compiler.tokenizer import Tokenizer
from compiler.ast import ASTParser

if __name__ == "__main__":
    with open("testfile.hatch", "r") as test_file:
        source = test_file.read()
    print(source)
    tokenizer = Tokenizer(source)
    tokens = tokenizer.tokenize()
    for token in tokens:
        print(token)
    
    ast = ASTParser(tokens)
    tree = ast.parse()
    
    for trunk in tree:
        trunk.print()
    