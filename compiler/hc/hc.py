from compiler.tokenizer import Tokenizer
from compiler.ast import ASTParser

if __name__ == "__main__":
    source = "function void main() {\n" \
             "    let int x = 4;\n" \
             "    let string y = \"hello, world!\";\n" \
             "    if (false) {\n" \
             "        let int number = 5;\n" \
             "    } else {\n" \
             "        let int number = 6;\n" \
             "    }" \
             "}"
    print(source)
    tokenizer = Tokenizer(source)
    tokens = tokenizer.tokenize()
    for token in tokens:
        print(token)
    
    ast = ASTParser(tokens)
    tree = ast.parse()
    
    for trunk in tree:
        trunk.print()
    