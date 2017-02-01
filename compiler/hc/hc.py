import sys

from compiler.tokenizer import Tokenizer
from compiler.ast import ASTParser
from compiler.assembler import Assembler

if __name__ == "__main__":
    with open("testfile.hatch", "r") as test_file:
        source = test_file.read()
    #print("Source:\n")
    #print(source)
    #print("-----------------------------------------\nTree:\n")
    tokenizer = Tokenizer(source)
    tokens = tokenizer.tokenize()
    #for token in tokens:
    #    print(token)
    
    ast = ASTParser(tokens, source)
    tree, error = ast.parse()
    
    if error:
        sys.exit()
    
    for trunk in tree:
        trunk.print()
        
    assembler = Assembler(tree)
    instructions = assembler.assemble()
    
    with open("testfile.hb", "wb") as output_file:
        output_file.write(bytes(instructions))
        
    with open("testfile.hasm", "w") as output_file:
        output_file.writelines(map(lambda x: str(bin(x)[2:]).zfill(8) + "\n", instructions))
        
    print("Compilation complete")
    