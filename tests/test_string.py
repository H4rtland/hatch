import hc
import vm

hatch = """
import io;

function void main() {
    let string hello = "Hello!";
    io.print_string(hello);
    io.print_char(hello[1]);
    io.print_string("\nWorld");
    let char H = hello[0];
    io.print_char(H);
}
"""

def test_string():
    instructions = hc.compile(hatch)
    
    virtual_machine = vm.OctoEngine(True)
    virtual_machine.load(instructions)
    output = virtual_machine.run()
    assert output == list("Hello!\ne\nWorld\nH")