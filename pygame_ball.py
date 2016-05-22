from simulator import StateMachine, MachineControl
import pygame


class BallMachine(StateMachine):
    def __init__(self, ctl, ctx, size=(320, 240), speed=[2, 2]):
        super().__init__(ctl, ctx)

        self.info = [
            ('event:%s', 'pg_event'),
        ]

        self.size = size
        self.width, self.height = size
        self.speed = speed

        self.black = (0, 0, 0)
        self.screen = None
        self.ball = None
        self.ballrect = None

        self.pg_event = None

        self.init_state = self.setup

    def setup(self):
        self.screen = pygame.display.set_mode(self.size)

        self.ball = pygame.image.load('simulator/ball.gif')
        self.ballrect = self.ball.get_rect()

        return self.process_events

    def process_events(self):
        while True:
            self.pg_event = pygame.event.poll()

            if self.pg_event.type == pygame.QUIT:
                return self.halt

            if self.pg_event.type == pygame.NOEVENT:
                return self.step

    def step(self):
        self.ballrect = self.ballrect.move(self.speed)

        if self.ballrect.left < 0 or self.ballrect.right > self.width:
            self.speed[0] *= -1

        if self.ballrect.top < 0 or self.ballrect.bottom > self.height:
            self.speed[1] *= -1

        return self.render

    def render(self):
        self.screen.fill(self.black)
        self.screen.blit(self.ball, self.ballrect)
        pygame.display.flip()

        return self.process_events


if __name__ == '__main__':
    ctl = MachineControl(step=False, debug=False)
    ctl.run(BallMachine)
