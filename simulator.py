from collections import deque as queue


class MachineControl:
    def __init__(self):
        # Implementation choice: simple queued execution.
        self.machines = queue()

        self.event_reactions = {}
        self.machine_reactions = {}

        self.event_buss = queue()

    def start(self, machine):
        self.machines.append(machine)

        self.add_event_reaction('start', machine, machine.init_state)

        # TODO: Create phony context for outermost machines.
        self.emit(Event('start', None, destination=machine))

    def add_event_reaction(self, typ, reactor, state):
        if typ not in self.event_reactions:
            self.event_reactions[typ] = {}

        self.event_reactions[typ][reactor] = state

    def add_machine_reaction(self, typ, emitter, reactor, state):
        index = (typ, emitter)

        if index not in self.machine_reactions:
            self.machine_reactions[index] = {}

        self.machine_reactions[index][reactor] = state

    def emit(self, event):
        self.event_buss.append(event)

    def run(self):
        while self.cycle():
            pass

    def cycle(self):
        while self.distribute_events():
            pass

        try:
            machine = self.machines.popleft()
        except IndexError:
            return False

        self.machines.append(machine)
        machine.cycle()

        return True

    def distribute_events(self):
        try:
            event = self.event_buss.popleft()
        except IndexError:
            return False

        if event.typ in self.event_reactions:
            self.distribute_reactors(self.event_reactions[event.typ], event)

        index = (event.typ, event.emitter)
        if index in self.machine_reactions:
            self.distribute_reactors(self.machine_reactions[index], event)

        return True

    def distribute_reactors(self, reactors, event):
        if event.destination is not None:
            if event.destination in reactors:
                event.destination.inbox.append(
                    Event.with_state(event, reactors[event.destination]))

        else:
            for reactor, state in reactors.items():
                reactor.inbox.append(
                    Event.with_state(event, state))

    def halt(self, machine):
        self.machines.remove(machine)


class Event:
    def __init__(self, typ, emitter, value=None, destination=None):
        self.typ = typ
        self.value = value
        self.emitter = emitter
        self.destination = destination

        self.state = None

    def __repr__(self):
        return '<Event: ' + self.typ + ', ' + str(self.emitter) + '>'

    @classmethod
    def with_state(cls, event, state):
        event_prime = cls(event.typ, event.emitter, event.value,
                          event.destination)
        event_prime.state = state
        return event_prime


class StateMachine:
    def __init__(self, ctl, ctx):
        self.ctl = ctl
        self.ctx = ctx

        self.current_state = self.listen

        self.inbox = queue()
        self.event = None

        self.init_state = self.halt

    def cycle(self):
        new_state = self.current_state()

        if new_state is None:
            new_state = self.listen

        self.current_state = new_state

    def listen(self):
        print(str(self) + ' is listening')

        try:
            self.event = self.inbox.popleft()
        except IndexError:
            return

        # TODO: This is where the ack mechanism goes

        return self.event.state

    def halt(self):
        print(str(self) + ' is halting')

        self.ctl.halt(self)
