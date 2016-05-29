from simulator import MachineControl, StateMachine
from elevator import Elevator, ElevatorCaret
import pygame
import datetime as dt
from math import floor


class PygameElevator(Elevator):
    def __init__(self, ctl, ctx, size=(566, 870)):
        super().__init__(ctl, ctx, 7)

        self.size = size
        self.width, self.height = size

        self.black = (0, 0, 0)
        self.screen = None
        self.pygame_objects = []

        self.lift_open = None
        self.lift_closed = None

        self.caret_class = PygameElevatorCaret
        self.key_class = PygameElevatorKeys

    def setup(self):
        self.screen = pygame.display.set_mode(self.size)
        pygame.display.set_caption('Purely event-driven elevator in Pygame')

        self.lift_open = pygame.image.load('simulator/img/elevator_open.png')
        self.lift_closed = pygame.image.load(
            'simulator/img/elevator_closed.png')

        # Elevator relies on the listen state, so we can't loop without listen.
        self.when_machine_emits('render', self, self.render)
        self.emit_to(self, 'render')

        self.when('pg_obj_ready', self.pg_obj_ready)

        return super().setup()

    def render(self):
        if self.lift_is_open:
            self.screen.blit(self.lift_open, (0, 0))
        else:
            self.screen.blit(self.lift_closed, (0, 0))

        for pg_obj in self.pygame_objects:
            self.screen.blit(*pg_obj)

        pygame.display.flip()

        self.emit_to(self, 'render')

    def pg_obj_ready(self):
        self.pygame_objects.append(self.event.value)


class PygameElevatorCaret(ElevatorCaret):
    def __init__(self, ctl, ctx):
        super().__init__(ctl, ctx)

        self.numbers = None
        self.numbersrect = None
        self.numbersarea = None

        self.difference = None

    def setup(self):
        self.numbers = pygame.image.load('simulator/img/elevator_numbers.png')
        self.numbersrect = self.numbers.get_rect()
        self.numbersrect.x = 249
        self.numbersrect.y = 24
        self.numbersarea = pygame.Rect(0, 6 * 32, 63, 32)

        self.emit_to(self.ctx, 'pg_obj_ready',
                     value=(self.numbers, self.numbersrect, self.numbersarea))

        return super().setup()

    def time(self):
        self.difference = (dt.datetime.now() - self.timer_start) / self.step_t
        self.numbersarea.y = (6 - self.position +
                              self.direction * -1 * self.difference) * 32

        return super().time()


class PygameElevatorKeys(StateMachine):
    def __init__(self, ctl, ctx, n):
        super().__init__(ctl, ctx)

        self.info = [
            ('ev:%s', 'pg_event'),
        ]

        self.n = n - 1

        self.keys = None
        self.keys_x = 505
        self.keys_y = 200
        self.keys_size = 50
        self.key = None

        self.pg_event = None

        self.init_state = self.setup

    def setup(self):
        pygame.event.set_allowed(None)
        pygame.event.set_allowed(pygame.MOUSEBUTTONUP)

        self.keys = pygame.image.load('simulator/img/elevator_keys.png')
        self.emit_to(self.ctx, 'pg_obj_ready',
                     value=(self.keys, (self.keys_x, self.keys_y)))

        return self.handle_event

    def handle_event(self):
        self.pg_event = pygame.event.poll()

        if self.pg_event.type == pygame.MOUSEBUTTONUP:
            return self.clicked

        return self.handle_event

    def clicked(self):
        if (self.pg_event.pos[0] < self.keys_x or
                self.pg_event.pos[0] > self.keys_x + self.keys_size):
            return self.handle_event

        self.key = self.n - floor(
            (self.pg_event.pos[1] - self.keys_y) / self.keys_size)
        if self.key < 0 or self.key > self.n:
            return self.handle_event

        self.emit_to(self.ctx, 'press', value=self.key)
        return self.handle_event


if __name__ == '__main__':
    # ctl = MachineControl(debug=True)
    ctl = MachineControl(debug=False)
    ctl.run(PygameElevator)
