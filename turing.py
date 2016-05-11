from simulator import StateMachine, MachineControl


class TuringMachine(StateMachine):
    def __init__(self, ctl, ctx, table, init_state, default=None,
                 show_steps=True):
        super().__init__(ctl, ctx)

        self.table = table
        self.state = init_state
        self.default = default
        self.show_steps = show_steps

        self.tape = None

        self.action = None
        self.write = None
        self.next_state = None

        self.init_state = self.setup

    def __repr__(self):
        return '<TM: %s>' % (self.current_state.__name__)

    def setup(self):
        self.tape = self.start_machine(TuringTape, self.default,
                                       self.show_steps)
        self.when_machine_emits('read', self.tape, self.step)

    def step(self):
        if self.show_steps:
            print('State: %s, read: %s' % (self.state, self.event.value))

        try:
            self.action, self.write, self.next_state = (
                self.table[self.state][self.event.value])
        except KeyError:
            print('Don\'t know what to do, halting!')
            return self.halt

        if self.show_steps:
            print('Action: %s, write: %s, next state: %s' % (
                self.action, self.write, self.next_state))

        self.emit_to(self.tape, self.action, value=self.write)

        if self.next_state == 'halt':
            return self.halt

        self.state = self.next_state


class TuringTape(StateMachine):
    def __init__(self, ctl, ctx, default, show_steps, dsp_width=5):
        super().__init__(ctl, ctx)

        self.default = default
        self.show_steps = show_steps
        self.dsp_w = dsp_width

        self.tape = [default]*(2 * dsp_width + 1)
        self.i = dsp_width

        self.init_state = self.setup

    def __repr__(self):
        return '<TT: %s>' % (self.current_state.__name__)

    def setup(self):
        self.when('L', self.action)
        self.when('R', self.action)
        self.when('N', self.action)

        self.when('halt', self.dump)

        return self.read

    def read(self):
        if self.show_steps:
            print('Tape',
                  self.tape[(self.i - self.dsp_w):(self.i + self.dsp_w + 1)])

        self.emit_to(self.ctx, 'read', value=self.tape[self.i])

    def action(self):
        self.tape[self.i] = self.event.value

        if self.event.typ == 'L':
            return self.move_left
        if self.event.typ == 'R':
            return self.move_right
        if self.event.typ == 'N':
            return self.read
        if self.event.typ == 'halt':
            return self.listen

        # TODO: emit crash to ctx.
        print('Unkown action, halting!')

        return self.halt

    def move_left(self):
        self.i -= 1

        if self.i < self.dsp_w:
            self.tape = [self.default] + self.tape
            self.i += 1

        return self.read

    def move_right(self):
        self.i += 1

        if (self.i + self.dsp_w) == len(self.tape):
            self.tape.append(self.default)

        return self.read

    def dump(self):
        print('Full tape')
        print(self.tape)
        return self.halt


if __name__ == '__main__':
    ctl = MachineControl()

    # Test.
    # ctl.run(TuringMachine, {
    #     'A': {None: ('R', '1', 'B'),
    #           '1': ('R', '0', 'B'), },
    #     'B': {None: ('L', '1', 'A'),
    #           '1': ('N', '1', 'halt'), },
    # }, 'A')

    # Busy beaver 1.
    # ctl.run(TuringMachine, {
    #     'A': {'0': ('R', '1', 'B'),
    #           '1': ('L', '1', 'B')},
    #     'B': {'0': ('L', '1', 'A'),
    #           '1': ('L', '0', 'C')},
    #     'C': {'0': ('R', '1', 'halt'),
    #           '1': ('L', '1', 'D')},
    #     'D': {'0': ('R', '1', 'D'),
    #           '1': ('R', '0', 'A')},
    # }, 'A', default='0')

    # Busy beaver 2.
    # ctl.run(TuringMachine, {
    #     'A': {'0': ('R', '1', 'B'),
    #           '1': ('L', '1', 'B')},
    #     'B': {'0': ('L', '1', 'A'),
    #           '1': ('R', '1', 'halt')},
    # }, 'A', default='0')

    # Busy beaver 3. This one is insane.
    # ctl.run(TuringMachine, {
    #     'A': {'0': ('R', '1', 'B'),
    #           '1': ('L', '1', 'E')},
    #     'B': {'0': ('R', '1', 'C'),
    #           '1': ('R', '1', 'F')},
    #     'C': {'0': ('L', '1', 'D'),
    #           '1': ('R', '0', 'B')},
    #     'D': {'0': ('R', '1', 'E'),
    #           '1': ('L', '0', 'C')},
    #     'E': {'0': ('L', '1', 'A'),
    #           '1': ('R', '0', 'D')},
    #     'F': {'0': ('L', '1', 'halt'),
    #           '1': ('R', '1', 'C')},
    # }, 'A', default='0', show_steps=False)

    # Busy beaver 4.
    ctl.run(TuringMachine, {
        'A': {'0': ('R', '1', 'B'),
              '1': ('L', '1', 'C')},
        'B': {'0': ('R', '1', 'C'),
              '1': ('R', '1', 'B')},
        'C': {'0': ('R', '1', 'D'),
              '1': ('L', '0', 'E')},
        'D': {'0': ('L', '1', 'A'),
              '1': ('L', '1', 'D')},
        'E': {'0': ('R', '1', 'halt'),
              '1': ('L', '0', 'A')},
    }, 'A', default='0', show_steps=False)
