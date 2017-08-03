import hc
import vm

hatch = """
import io;

function int print_and_return(int number) {
    io.print(number);
    return number;
}

function void main() {
    let int i = 0;
    while (i++ < 10) {
        io.print(i);
    }

    i = 0;
    while (i < 10) {
        i++;
        io.print(i);
    }

    while (print_and_return(i--) > 1) {
    }

    for (let int c=100; c<111; c++) {
        io.print(c);
    }
}
"""


def test_increment():
    instructions = hc.compile(hatch)

    virtual_machine = vm.OctoEngine(True)
    virtual_machine.load(instructions)
    output = virtual_machine.run()
    assert output == [i for i in range(1, 11)] + [i for i in range(1, 11)] + [i for i in range(10, 0, -1)] + [i for i in range(100, 111)]