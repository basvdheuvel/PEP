from simulator import MachineControl, StateMachine
from random import randint


class CPU(StateMachine):
    def __init__(self, ctl, ctx):
        super().__init__(ctl, ctx)

        self.hd = None
        self.prog_a = None
        self.prog_b = None

        self.hd_reader = None

        self.init_state = self.setup

    def setup(self):
        print('In setup')
        self.hd = self.start_machine(HD)
        self.prog_a = self.start_machine(ProgA)
        self.prog_b = self.start_machine(ProgB)

        self.when('cycle', self.do_cycle)
        self.when('read', self.hd_read)
        self.when('shutdown', self.halt)

    def do_cycle(self):
        print('CPU performs cycle')

    def hd_read(self):
        print('Requesting HD to read')
        self.hd_reader = self.event.emitter
        self.emit_to(self.hd, 'read')
        self.when_machine_emits('interrupt', self.hd, self.hd_interrupt)

    def hd_interrupt(self):
        print('Interrupted, returning')
        self.emit_to(self.hd_reader, 'return')
        self.ignore_when_machine_emits('interrupt', self.hd)


class HD(StateMachine):
    def __init__(self, ctl, ctx):
        super().__init__(ctl, ctx)

        self.hd_head = None

        self.init_state = self.setup

    def setup(self):
        self.hd_head = self.start_machine(HDHead)

        self.when_machine_emits('read', self.ctx, self.seek)

    def seek(self):
        print('Requesting head to seek')
        self.ignore_when_machine_emits('read', self.ctx)

        self.emit_to(self.hd_head, 'seek')
        self.when_machine_emits('found_data', self.hd_head, self.found_data)

    def found_data(self):
        print('Data found')
        self.ignore_when_machine_emits('found_data', self.hd_head)
        self.when('read', self.seek)

        self.emit_to(self.ctx, 'interrupt')


class HDHead(StateMachine):
    def __init__(self, ctl, ctx):
        super().__init__(ctl, ctx)

        self.init_state = self.setup

    def setup(self):
        self.when_machine_emits('seek', self.ctx, self.seek)

    def seek(self):
        print('Seeking...')

        if randint(0, 1) == 0:
            self.emit_to(self.ctx, 'found_data')

        else:
            return self.seek


class ProgA(StateMachine):
    def __init__(self, ctl, ctx):
        super().__init__(ctl, ctx)

        self.init_state = self.program

    def program(self):
        print('Requesting to read')
        self.emit_to(self.ctx, 'read')
        self.when_machine_emits('return', self.ctx, self.finish)

    def finish(self):
        print('Shutting down PC')
        self.ignore_when_machine_emits('return', self.ctx)
        self.emit_to(self.ctx, 'shutdown')


class ProgB(StateMachine):
    def __init__(self, ctl, ctx):
        super().__init__(ctl, ctx)

        self.init_state = self.do_cycle

    def do_cycle(self):
        print('Requesting cycle')
        self.emit_to(self.ctx, 'cycle', ack_state=self.do_cycle)


if __name__ == '__main__':
    ctl = MachineControl()
    ctl.run(CPU)
