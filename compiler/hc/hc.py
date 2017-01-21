from compiler.tokenizer import Tokenizer
from compiler.ast import ASTParser
from compiler.assembler import Assembler

if __name__ == "__main__":
    with open("testfile.hatch", "r") as test_file:
        source = test_file.read()
    print("Source:\n")
    print(source)
    print("-----------------------------------------\nTree:\n")
    tokenizer = Tokenizer(source)
    tokens = tokenizer.tokenize()
    #for token in tokens:
    #    print(token)
    
    ast = ASTParser(tokens)
    tree = ast.parse()
    
    for trunk in tree:
        trunk.print()
        
    assembler = Assembler(tree)
    instructions = assembler.assemble()
    
    with open("testfile.hb", "wb") as output_file:
        output_file.write(bytes(instructions))
        
    print("Compilation complete")
    