import hc
import vm

hatch = """
import io;

function void main() {
    let int i = 0;
    let bool print = false;
    while (true) {
        i = i + 1;
        if (i > 30) {
            break;
        }
        if (print) {
            io.print(i);
            print = false;
            continue;
        }
        print = true;
    }

    for (let int i=0; i<10; i=i+1) {
        if (i > 5) {
            break;
        }
        io.print(i);
    }
}
"""


def test_break_continue():
    instructions = hc.compile(hatch)

    virtual_machine = vm.OctoEngine(True)
    virtual_machine.load(instructions)
    output = virtual_machine.run()
    assert output == [i for i in range(2, 31, 2)] + list(range(0, 6))