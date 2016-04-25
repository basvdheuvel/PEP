from simulator import MachineControl, StateMachine


class TestA(StateMachine):
    def __init__(self, ctl, ctx, n):
        super().__init__(ctl, ctx)

        self.init_state = self.init
        self.n = n

    def __repr__(self):
        return '<A:n=%d>' % (self.n)

    def init(self):
        self.ms = []
        self.i = 0
        self.j = 0
        return self.start_machines

    def start_machines(self):
        if self.i < self.n:
            m = self.start_machine(TestB, i=self.i)
            self.ms.append(m)
            self.when_machine_emits('ready', m, self.m_ready)
            self.when_machine_emits('done', m, self.m_done)

            print('created machine %d' % (self.i + 1))

            self.i += 1
            return self.start_machines

    def m_ready(self):
        m = self.event.emitter

        print('machine %d is ready' % (m.i + 1))

        self.j += 1
        if self.j == self.n:
            self.emit('run')

    def m_done(self):
        m = self.event.emitter

        print('machine %d is done' % (self.event.value))

        self.emit_to(m, 'halt', value=self.n)
        self.ms.remove(m)
        self.n = len(self.ms)

        print('%d left to halt' % (self.n))

        if self.n == 0:
            return self.halt


class TestB(StateMachine):
    def __init__(self, ctl, ctx, i):
        super().__init__(ctl, ctx)

        self.init_state = self.init
        self.i = i

    def __repr__(self):
        return '<B:i=%d>' % (self.i)

    def init(self):
        self.when('run', self.prnt)
        self.when('halt', self.halt)

        self.emit_to(self.ctx, 'ready')

    def prnt(self):
        print('i am machine %d' % (self.i))
        self.emit_to(self.ctx, 'done', value=self.i)


if __name__ == '__main__':
    ctl = MachineControl(debug=False)
    ctl.run(TestA, 5)
