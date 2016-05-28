from simulator import MachineControl, StateMachine
from random import randint
import datetime as dt


class Elevator(StateMachine):
    def __init__(self, ctl, ctx, n):
        super().__init__(ctl, ctx)

        self.n = n

        self.up_goal = None
        self.down_goal = None
        self.moving = 0  # 0 is not moving, 1 is up, -1 is down
        self.goals = []
        self.position = 0

        self.lift_is_open = False

        self.i = 0

        self.key_machine = None
        self.key_class = ElevatorKeys
        self.caret_machine = None
        self.caret_class = ElevatorCaret

        self.open_t = dt.timedelta(milliseconds=1500)

        self.timer_end = None

        self.init_state = self.setup

    def setup(self):
        self.key_machine = self.start_machine(self.key_class, self.n)
        self.caret_machine = self.start_machine(self.caret_class)

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
        print('%d pressed' % (goal))

        self.goals[goal] = True

        if goal > self.position and (self.up_goal is None
                                     or goal > self.up_goal):
            self.up_goal = goal
        elif goal < self.position and (self.down_goal is None
                                       or goal < self.down_goal):
            self.down_goal = goal

        # print('Current goals', [i for i, g in enumerate(self.goals)
        #                         if g])

        if self.moving == 0:
            if self.up_goal is not None or self.down_goal is not None:
                return self.not_moving

            return self.open_doors

    def not_moving(self):
        if self.up_goal is not None:
            self.moving = 1
            # print('Lift moving up')
        elif self.down_goal is not None:
            self.moving = -1
            # print('Lift moving down')
        else:
            self.moving = 0
            # print('Lift stopped')
            return self.listen

        return self.move

    def move(self):
        self.emit_to(self.caret_machine, 'move', value=self.moving)

    def reached(self):
        self.position = self.event.value
        # print('Floor %d reached' % (self.position))

        if self.goals[self.position]:
            return self.open_doors

        return self.move_on

    def open_doors(self):
        self.lift_is_open = True

        self.timer_end = dt.datetime.now() + self.open_t
        self.when_machine_emits('timer', self, self.time)
        self.when_machine_emits('timer_end', self, self.move_on)
        self.emit_to(self, 'timer')

        return self.listen

    def move_on(self):
        self.lift_is_open = False
        self.goals[self.position] = False

        if ((self.moving == 1 and self.position == self.up_goal)
                or (self.moving == -1 and self.position == self.down_goal)):
            if self.moving == 1:
                self.up_goal = None
            elif self.moving == -1:
                self.down_goal = None

            return self.not_moving

        elif self.moving == 0:
            return self.not_moving

        return self.move

    def time(self):
        if dt.datetime.now() >= self.timer_end:
            self.emit_to(self, 'timer_end')
        else:
            self.emit_to(self, 'timer')


class ElevatorCaret(StateMachine):
    def __init__(self, ctl, ctx):
        super().__init__(ctl, ctx)

        self.step = 0
        self.step_t = dt.timedelta(milliseconds=1000)
        self.position = 0
        self.direction = 0

        self.timer_start = None
        self.timer_end = None

        self.init_state = self.setup

    def setup(self):
        self.when('move', self.move)

    def move(self):
        self.direction = self.event.value
        self.step = 0

        self.timer_start = dt.datetime.now()
        self.timer_end = self.timer_start + self.step_t
        self.when_machine_emits('timer', self, self.reached)

        return self.time

    def time(self):
        if dt.datetime.now() < self.timer_end:
            return self.time

        self.emit_to(self, 'timer')

    def reached(self):
        self.position += self.direction
        self.direction = 0
        self.emit('reached', value=self.position)


class ElevatorKeys(StateMachine):
    def __init__(self, ctl, ctx, n):
        super().__init__(ctl, ctx)

        self.info = [
            ('pressed:%d', 'level')
        ]

        self.n = n

        self.press_t = dt.timedelta(milliseconds=5000)

        self.i = 0
        self.w = 0
        self.level = 0

        self.timer_end = None

        self.init_state = self.press

    def setup(self):
        self.i = 0
        return self.wait

    def wait(self):
        self.timer_end = dt.datetime.now() + self.press_t
        self.when_machine_emits('timer', self, self.press)

        return self.time

    def time(self):
        if dt.datetime.now() < self.timer_end:
            return self.time

        self.emit_to(self, 'timer')

    def press(self):
        self.level = randint(0, self.n - 1)
        print('Pressing %d' % (self.level))
        self.emit('press', value=self.level)

        return self.setup


if __name__ == '__main__':
    ctl = MachineControl(debug=False)
    ctl.run(Elevator, 10)
