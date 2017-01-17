OPCODES = {
    "NOP": 0b0000,
    "LDA": 0b0001,
    "LDB": 0b0010,
    "PRA": 0b0011,
    "PRB": 0b0100,
    "ADD": 0b0101,
    "HLT": 0b0110,
    "PRX": 0b0111,
    "JMP": 0b1000,
    "STA": 0b1001,
    "STB": 0b1010,
    "INC": 0b1011,
    "MOV": 0b1100,
    "CMP": 0b1101,
    "JE":  0b1110,
}

RESERVED_MEMORY = {
    "AX": 255,
    "BX": 254,
    "CX": 253,
}

def assemble(hasm):
    output = []
    labels = {}
    for line in hasm:
        line = line.split(";")[0]
        line = line.replace(",", " ")
        if line.startswith("."):
            labels[line.split()[0]] = len(output)
            line = " ".join(line.split()[1:])
        l = line.split()
        if len(l) == 0:
            continue
        if len(l) == 3:
            op, addr1, addr2 = l
            
            if addr1 in RESERVED_MEMORY:
                addr1 = RESERVED_MEMORY[addr1]
            else:
                raise Exception("MOV accessing non register memory")
                
            if addr2 in RESERVED_MEMORY:
                addr2 = RESERVED_MEMORY[addr2]
            else:
                raise Exception("MOV accessing non register memory")
            
            byte = ((255-addr1) << 4) + (255-addr2)
            
            output.append(OPCODES[op])
            output.append(byte)
        elif len(l) == 2:
            op, addr = l
            if addr.startswith("."):
                pass
            elif addr in RESERVED_MEMORY:
                addr = RESERVED_MEMORY[addr]
            else:
                addr = int(addr)
            output.append(OPCODES[op])
            output.append(addr)
        else:
            op = l[0]
            if op in OPCODES:
                output.append(int(OPCODES[op]))
                output.append(0)
            else:
                # data
                output.append(int(op))
    
    # Substitute labels
    for index, value in enumerate(output):
        if isinstance(value, str):
            if value.startswith("."):
                if not value in labels:
                    raise Exception(f"Bad label reference ({addr})")
                else:
                    output[index] = labels[value]
    return output


if __name__ == "__main__":
    with open("test.hasm", "r") as input_file:
        hasm = input_file.readlines()
    output = assemble(hasm)
    with open("test.hb", "wb") as output_file:
        output_file.write(bytes(output))
    print("Complete")