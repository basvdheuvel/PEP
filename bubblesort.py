from simulator import MachineControl, StateMachine


class BubbleSort(StateMachine):
    def __init__(self, ctl, ctx, a):
        super().__init__(ctl, ctx)

        self.a = a

        self.i = 1
        self.swappers = []
        self.changed = False

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
        self.changed = False

        return self.swap

    def swap(self):
        if self.i < len(self.swappers):
            self.emit_to(self.swappers[self.i], 'start')
            self.i += 1
            return self.listen

        return self.check_done

    def swapped(self):
        self.changed = True
        return self.swap

    def check_done(self):
        if self.changed:
            return self.setup_swap

        print('Done: %s' % (str(self.a)))

        self.emit('halt')

        return self.halt


class Swapper(StateMachine):
    def __init__(self, ctl, ctx, a, i):
        super().__init__(ctl, ctx)

        self.a = a
        self.i = i

        self.init_state = self.swap

    def __repr__(self):
        return '<Swapper:i=%d,state=%s>' % (self.i,
                                            self.current_state.__name__)

    def swap(self):
        if self.a[self.i - 1] > self.a[self.i]:
            tmp = self.a[self.i]
            self.a[self.i] = self.a[self.i - 1]
            self.a[self.i - 1] = tmp

            self.emit('swapped')

        else:
            self.emit('next')


if __name__ == '__main__':
    ctl = MachineControl(debug=False)
    ctl.run(BubbleSort, [5, 4, 3, 2, 3, 4, 5, 67, 1, 1, 6, 9])
