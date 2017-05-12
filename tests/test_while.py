import hc
import vm

hatch = """
import io;

function int main() {
    let int i = 0;
    while (i < 5) {
        print(i);
        i = i + 1;
    }
    while (i >= 1) {
        print(i);
        i = i - 1;
    }
}
"""

def test_while():
    instructions = hc.compile(hatch)
    
    virtual_machine = vm.OctoEngine(True)
    virtual_machine.load(instructions)
    output = virtual_machine.run()
    assert output == [i for i in range(0, 5)] + [i for i in range(1, 6)][::-1]