OPCODES = {
    "NOP": 0b0000,
    "LDA": 0b0001,
    "LDB": 0b0010,
    "PRA": 0b0011,
    "PRB": 0b0100,
    "ADD": 0b0101,
    "HLT": 0b0110,
    "PRX": 0b0111,
}

def assemble(hasm):
    output = []
    for line in hasm:
        l = line.split()
        if len(l) == 3:
            index, op, addr = l
            output.append(OPCODES[op])
            output.append(int(addr))
        else:
            index, data = l
            output.append(int(data))
    return output


if __name__ == "__main__":
    with open("test.hasm", "r") as input_file:
        hasm = input_file.readlines()
    output = assemble(hasm)
    with open("test.hb", "wb") as output_file:
        output_file.write(bytes(output))
    print("Complete")