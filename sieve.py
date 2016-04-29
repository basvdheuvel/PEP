from simulator import MachineControl, StateMachine


class Sieve(StateMachine):
    def __init__(self, ctl, ctx, n):
        super().__init__(ctl, ctx)

        self.n = n

        self.x = 2
        self.manager = None

        self.init_state = self.setup

    def __repr__(self):
        return '<Sieve:n=%d,state=%s>' % (self.n, self.current_state.__name__)

    def setup(self):
        if self.n < 0:
            return self.halt

        self.manager = self.start_machine(PickerManager)

        self.when_machine_emits('pass', self.manager, self.prime)
        self.when_machine_emits('fail', self.manager, self.increment)

        return self.prime

    def prime(self):
        self.n -= 1

        print('FOUND PRIME %d, %d left' % (self.x, self.n))

        if self.n == 0:
            return self.halt

        self.emit_to(self.manager, 'new_prime', value=self.x)

        return self.increment

    def increment(self):
        self.x += 1

        self.emit_to(self.manager, 'new_x', value=self.x)


class PickerManager(StateMachine):
    def __init__(self, ctl, ctx):
        super().__init__(ctl, ctx)

        self.pickers = []
        self.i = 0
        self.togo = 0
        self.current_x = 0

        self.init_state = self.setup

    def __repr__(self):
        return '<PickerManager:state=%s>' % (self.current_state.__name__)

    def setup(self):
        self.when_machine_emits('new_prime', self.ctx, self.new_prime)
        self.when_machine_emits('new_x', self.ctx, self.new_x)

    def new_prime(self):
        self.pickers.append(self.start_machine(Picker, self.event.value))

    def new_x(self):
        self.i = 0
        self.togo = len(self.pickers)
        self.current_x = self.event.value

        return self.run_pickers

    def run_pickers(self):
        if self.i < len(self.pickers):
            self.emit_to(self.pickers[self.i], 'run', value=self.current_x,
                         ack_state=self.listen_picker)
            self.i += 1

            return self.run_pickers

    def listen_picker(self):
        if self.event.value == self.current_x:
            m = self.event.emitter
            self.when_machine_emits('pass', m, self.got_pass)
            self.when_machine_emits('fail', m, self.got_fail)

    def got_pass(self):
        self.togo -= 1
        if self.togo == 0:
            self.emit_to(self.ctx, 'pass')

    def got_fail(self):
        self.emit_to(self.ctx, 'fail')

        self.i = 0
        return self.unlisten_pickers

    def unlisten_pickers(self):
        if self.i < len(self.pickers):
            m = self.pickers[self.i]
            self.ignore_when_machine_emits('pass', m)
            self.ignore_when_machine_emits('fail', m)

            self.i += 1
            return self.unlisten_pickers


class Picker(StateMachine):
    def __init__(self, ctl, ctx, x):
        super().__init__(ctl, ctx)

        self.x = x

        self.count = 0
        self.init_state = self.setup

    def __repr__(self):
        return '<Picker:x=%d,count=%d,state=%s>' % (
            self.x, self.count, self.current_state.__name__)

    def setup(self):
        self.when('run', self.run)

    def run(self):
        self.count += 1

        if self.count == self.x:
            self.count = 0
            self.emit('fail')

        else:
            self.emit('pass')


if __name__ == '__main__':
    ctl = MachineControl(debug=False)
    ctl.run(Sieve, 10)
