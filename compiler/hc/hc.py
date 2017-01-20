from compiler.tokenizer import Tokenizer

if __name__ == "__main__":
    source = "void main() {\nint x = 4;\nstring y = \"hello, world!\"\nif false {};}"
    
    tokenizer = Tokenizer(source)
    tokens = tokenizer.tokenize()
    for token in tokens:
        print(token)