import hc
import vm

hatch = """
import io;

function void main() {
    let string hello = "Hello!";
    io.print(hello);
    io.print(hello[1]);
    io.print("\nWorld");
    let char H = hello[0];
    io.print(H);
}
"""

def test_string():
    instructions = hc.compile(hatch)
    
    virtual_machine = vm.OctoEngine(True)
    virtual_machine.load(instructions)
    output = virtual_machine.run()
    assert output == list("Hello!e\nWorldH")