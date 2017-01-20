from compiler.tokenizer import Tokenizer

if __name__ == "__main__":
    source = "void main() {\nint x = 4;\nint y = 5;}"
    
    tokenizer = Tokenizer(source)
    tokens = tokenizer.tokenize()
    for token in tokens:
        print(token)
    
    