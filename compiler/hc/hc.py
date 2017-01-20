from compiler.tokenizer import Tokenizer

if __name__ == "__main__":
    source = "function void main() {\n    int x = 4;\n    string y = \"hello, world!\";\n    if false {\n        // does nothing\n    }\n}"
    print(source)
    tokenizer = Tokenizer(source)
    tokens = tokenizer.tokenize()
    for token in tokens:
        print(token)