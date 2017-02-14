import sys
import os.path

from compiler.tokenizer import Tokenizer
from compiler.ast import ASTParser
from compiler.assembler import Assembler

def compile(source, debug=False, filename="<source>"):
    tokenizer = Tokenizer(source)
    tokens = tokenizer.tokenize()
    
    ast = ASTParser(tokens, source, filename, compiler=[compile, compile_file])
    tree, error = ast.parse()
    
    if error:
        sys.exit()
    
    if debug:
        for trunk in tree:
            trunk.print()
        
    assembler = Assembler(tree)
    instructions = assembler.assemble()
    
    return instructions

def compile_file(filename, debug):
    filename = os.path.abspath(filename)
    with open(filename, "r") as source_file:
        source = source_file.read()
    return compile(source, debug=debug, filename=filename)

if __name__ == "__main__":
    instructions = compile_file("testfile.hatch", True)
    
    with open("testfile.hb", "wb") as output_file:
        output_file.write(bytes(instructions))
        
    with open("testfile.hasm", "w") as output_file:
        output_file.writelines(map(lambda x: str(bin(x)[2:]).zfill(8) + "\n", instructions))
        
    print("Compilation complete")
