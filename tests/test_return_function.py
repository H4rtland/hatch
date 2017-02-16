import sys

sys.path.append("../compiler/hc")
import hc

sys.path.append("../vm")
import vm

hatch = """
import io;

function int increment(int b) {
    return b + 1;
}

function int decrement(int b) {
    return b - 1;
}

function func inc_or_dec(int inc) {
    if (inc == 1) {
        return increment;
    } else {
        return decrement;
    }
}

function void main() {
    let int x = 5;
    x = inc_or_dec(1)(x);
    print(x);

    let int y = 22;
    y = inc_or_dec(0)(y);
    print(y);
}
"""

def test_for():
    instructions = hc.compile(hatch)
    
    virtual_machine = vm.OctoEngine(True)
    virtual_machine.load(instructions)
    output = virtual_machine.run()
    assert output == [6, 21]