from simulator import MachineControl, StateMachine
from random import randint

# TODO: Fix "turning problem"


class Elevator(StateMachine):
    def __init__(self, ctl, ctx, n):
        super().__init__(ctl, ctx)

        self.n = n

        self.up_goal = None
        self.down_goal = None
        self.moving = 0  # 0 is not moving, 1 is up, -1 is down
        self.goals = []
        self.position = 0

        self.i = 0

        self.key_machine = None
        self.caret_machine = None

        self.init_state = self.setup

    def setup(self):
        self.key_machine = self.start_machine(ElevatorKeys, self.n)
        self.caret_machine = self.start_machine(ElevatorCaret)

        self.when_machine_emits('press', self.key_machine, self.press)
        self.when_machine_emits('reached', self.caret_machine, self.reached)

        return self.build

    def build(self):
        if self.i < self.n:
            self.goals.append(False)
            self.i += 1
            return self.build

    def press(self):
        goal = self.event.value
        self.goals[goal] = True

        if goal > self.position and (self.up_goal is None
                                     or goal > self.up_goal):
            self.up_goal = goal
        elif goal < self.position and (self.down_goal is None
                                       or goal < self.down_goal):
            self.down_goal = goal

        print('Current goals', [i for i, g in enumerate(self.goals)
                                if g])

        if self.moving == 0 and (self.up_goal is not None
                                 or self.down_goal is not None):
            return self.not_moving

    def not_moving(self):
        if self.up_goal is not None:
            self.moving = 1
            print('Lift moving up')
        elif self.down_goal is not None:
            self.moving = -1
            print('Lift moving down')
        else:
            self.moving = 0
            print('Lift stopped')
            return self.listen

        return self.move

    def move(self):
        self.emit_to(self.caret_machine, 'move', value=self.moving)

    def reached(self):
        self.position = self.event.value
        print('Floor %d reached' % (self.position))

        if self.goals[self.position]:
            print('Opening doors')
        self.goals[self.position] = False

        if ((self.moving == 1 and self.position == self.up_goal)
                or (self.moving == -1 and self.position == self.down_goal)):
            if self.moving == 1:
                self.up_goal = None
            elif self.moving == -1:
                self.down_goal = None

            return self.not_moving

        return self.move


class ElevatorCaret(StateMachine):
    def __init__(self, ctl, ctx):
        super().__init__(ctl, ctx)

        self.step = 0
        self.steps = 500000
        self.position = 0
        self.direction = 0

        self.init_state = self.setup

    def setup(self):
        self.when('move', self.move)

    def move(self):
        self.direction = self.event.value
        self.step = 0

        return self.do_step

    def do_step(self):
        if self.step < self.steps:
            self.step += 1
            return self.do_step

        return self.reached

    def reached(self):
        self.position += self.direction
        self.direction = 0
        self.emit('reached', value=self.position)


class ElevatorKeys(StateMachine):
    def __init__(self, ctl, ctx, n):
        super().__init__(ctl, ctx)

        self.n = n

        self.period = 1000000
        self.var = 2

        self.i = 0
        self.w = 0
        self.level = 0

        self.init_state = self.press

    def setup(self):
        self.i = 0
        self.w = self.period - self.var + randint(0, self.var * 2 - 1)

        return self.wait

    def wait(self):
        if self.i < self.w:
            self.i += 1
            return self.wait

        return self.press

    def press(self):
        self.level = randint(0, self.n - 1)
        print('Pressing %d' % (self.level))
        self.emit('press', value=self.level)

        return self.setup


if __name__ == '__main__':
    ctl = MachineControl(debug=False)
    ctl.run(Elevator, 10)
