from simulator import MachineControl, Event, StateMachine


class TestA(StateMachine):
    def __init__(self, ctl, ctx):
        super().__init__(ctl, ctx)

        self.init_state = self.a

    def a(self):
        print('A: a')
        return self.b

    def b(self):
        print('A: b')
        self.m = TestB(self.ctl, self)
        self.ctl.start(self.m)

        self.ctl.add_machine_reaction('okay', self.m, self, self.c)

    def c(self):
        print('A: c')
        self.ctl.emit(Event('test', self))
        return self.b_halt

    def b_halt(self):
        print('A: going to halt after this')
        return self.halt


class TestB(StateMachine):
    def __init__(self, ctl, ctx):
        super().__init__(ctl, ctx)

        self.init_state = self.a

    def a(self):
        print('B: a')
        self.ctl.add_event_reaction('test', self, self.b_halt)
        self.ctl.emit(Event('okay', self, destination=self.ctx))

    def b_halt(self):
        print('B: going to halt after this')
        return self.halt


if __name__ == '__main__':
    ctl = MachineControl()

    ctl.start(TestA(ctl, None))
    ctl.run()
