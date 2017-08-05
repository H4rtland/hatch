import hc
import vm

hatch = """
import io;

struct Car {
    int wheels,
    int seats,
}

function int wheels_plus_seats(Car car) {
    return car.wheels + car.seats;
}

function void main() {
    let int wheels = 4;
    let Car ford = new Car(wheels, 5);
    io.print(ford.wheels);
    io.print(ford.seats);
    io.print(wheels_plus_seats(ford));
    io.print(ford.wheels == 4);
    ford.seats = 7;
    io.print(ford.seats);
}
"""


def test_binary():
    instructions = hc.compile(hatch)

    virtual_machine = vm.OctoEngine(True)
    virtual_machine.load(instructions)
    output = virtual_machine.run()

    assert output == [4, 5, 9,] + list("true") + [7,]