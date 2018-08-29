from simulator import StateMachine, MachineControl


class Master(StateMachine):
    def __init__(self, ctl, ctx):
        super().__init__(ctl, ctx)

        self.my_slave = None

        self.init_state = self.setup

    def __repr__(self):
        return '<Master>'

    def setup(self):
        self.my_slave = self.start_machine(Slave)
        self.when_machine_emits('done', self.my_slave, self.halt)
        self.emit_to(self.my_slave, 'run')


class Slave(StateMachine):
    def __init__(self, ctl, ctx):
        super().__init__(ctl, ctx)

        self.init_state = self.setup

    def __repr__(self):
        return '<Slave>'

    def setup(self):
        self.when('run', self.run)

    def run(self):
        print('Hello world!')
        self.emit_to(self.ctx, 'done')


if __name__ == '__main__':
    ctl = MachineControl(debug=True, step=True)
    ctl.run(Master)
