from simulator import MachineControl, StateMachine


class BubbleSort(StateMachine):
    def __init__(self, ctl, ctx, a):
        super().__init__(ctl, ctx)

        self.a = a

        self.i = 1
        self.swappers = []
        self.max_changed = 0
        self.changed = False

        self.info = [
            ('a:%s', 'a'),
        ]

        self.init_state = self.setup

    def __repr__(self):
        return '<BubbleSort,state=%s>' % (self.current_state.__name__)

    def setup(self):
        if self.i < len(self.a):
            s = self.start_machine(Swapper, a=self.a, i=self.i)

            self.when_machine_emits('swapped', s, self.swapped)
            self.when_machine_emits('next', s, self.swap)

            self.swappers.append(s)

            self.i += 1
            return self.setup

        return self.setup_swap

    def setup_swap(self):
        self.i = 0
        self.max_changed = 0
        self.changed = False

        return self.swap

    def swap(self):
        if self.i < len(self.swappers):
            self.emit_to(self.swappers[self.i], 'swap')
            self.i += 1
            return self.listen

        return self.check_done

    def swapped(self):
        self.max_changed = self.event.value
        self.changed = True
        return self.swap

    def check_done(self):
        if self.changed:
            return self.setup_optimize

        print('Done: %s' % (str(self.a)))

        return self.halt

    def setup_optimize(self):
        self.i = len(self.swappers) - self.max_changed + 1
        return self.optimize

    def optimize(self):
        if self.i > 0:
            s = self.swappers.pop()
            self.emit_to(s, 'halt')
            self.i -= 1
            return self.optimize

        return self.setup_swap


class Swapper(StateMachine):
    def __init__(self, ctl, ctx, a, i):
        super().__init__(ctl, ctx)

        self.a = a
        self.i = i

        self.info = [
            ('i:%d', 'i'),
        ]

        self.init_state = self.setup

    def __repr__(self):
        return '<Swapper:i=%d,state=%s>' % (self.i,
                                            self.current_state.__name__)

    def setup(self):
        self.when_machine_emits('swap', self.ctx, self.swap)

    def swap(self):
        if self.a[self.i - 1] > self.a[self.i]:
            tmp = self.a[self.i]
            self.a[self.i] = self.a[self.i - 1]
            self.a[self.i - 1] = tmp

            self.emit('swapped', value=self.i)

        else:
            self.emit('next')


if __name__ == '__main__':
    ctl = MachineControl(debug=True)
    ctl.run(BubbleSort, [5, 3, 1, 8])
    ctl.run(BubbleSort, [5, 4, 3, 2, 3, 4, 5, 67, 1, 1, 6, 9])
    ctl.run(BubbleSort, list("test with string"))
    ctl.run(BubbleSort, list('zpykxcerndu'))
