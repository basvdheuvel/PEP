from collections import deque as queue
# TODO: 'log' function wrapper.


class MachineControl:
    def __init__(self, debug=False):
        # Implementation choice: simple queued execution.
        self.machines = queue()

        self.event_reactions = {}
        self.machine_reactions = {}

        self.event_buss = queue()

        self.ctx = None

        self.debug = debug

    def start_machine(self, machine_cls, ctx, *args, **kwargs):
        machine = machine_cls(self, ctx, *args, **kwargs)

        self.machines.append(machine)

        self.add_event_reaction('start', machine, machine.init_state)
        self.add_machine_reaction('halt', ctx, machine, machine.halt)

        self.emit(Event('start', ctx, destination=machine))

        return machine

    def add_event_reaction(self, typ, reactor, state):
        if typ not in self.event_reactions:
            self.event_reactions[typ] = {}

        self.event_reactions[typ][reactor] = state

    def remove_event_reaction(self, typ, reactor):
        try:
            del self.event_reactions[typ][reactor]
        except KeyError:
            pass

    def add_machine_reaction(self, typ, emitter, reactor, state):
        index = (typ, emitter)

        if index not in self.machine_reactions:
            self.machine_reactions[index] = {}

        self.machine_reactions[index][reactor] = state

    def remove_machine_reaction(self, typ, emitter, reactor):
        index = (typ, emitter)

        try:
            del self.machine_reactions[index][reactor]
        except KeyError:
            pass

    def emit(self, event):
        self.event_buss.append(event)

    def run(self, machine_cls, *args, **kwargs):
        self.ctx = StateMachine(self, None)
        self.start_machine(machine_cls, self.ctx, *args, **kwargs)

        while self.cycle():
            pass

    def cycle(self):
        while self.distribute_events():
            pass

        if self.debug:
            print('machines: ' + str(self.machines))

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

        if self.debug:
            print('distributing %s' % (event))

        if (event.destination is not None
                and event.destination in self.machines):
            event.destination.inbox.append(event)
            return True

        for machine in self.machines:
            machine.inbox.append(event)

        return True

    def filter_event(self, machine, event):
        if event.typ in self.event_reactions:
            try:
                return self.event_reactions[event.typ][machine]
            except KeyError:
                pass

        index = (event.typ, event.emitter)
        if index in self.machine_reactions:
            try:
                return self.machine_reactions[index][machine]
            except KeyError:
                pass

        return None

    def halt(self, machine):
        self.machines.remove(machine)


class Event:
    def __init__(self, typ, emitter, value=None, destination=None, ack=False):
        self.typ = typ
        self.value = value
        self.emitter = emitter
        self.destination = destination
        self.ack = ack

        self.state = None

    def __repr__(self):
        return '<Event:typ=%s,emitter=%s,destination=%s,ack=%s>' % (
            self.typ, self.emitter, self.destination, self.ack)

    @classmethod
    def with_state(cls, event, state):
        # Probably depracated.
        event_prime = cls(event.typ, event.emitter, event.value,
                          event.destination, event.ack)
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
        if self.ctl.debug:
            print('cycling %s' % (self))

        new_state = self.current_state()

        if new_state is None:
            new_state = self.listen

        self.current_state = new_state

    def emit(self, typ, value=None):
        self.emit_to(None, typ, value=value)

    def emit_to(self, destination, typ, value=None, ack_state=None):
        self.ctl.emit(Event(typ, self, value=value, destination=destination,
                            ack=ack_state is not None))

        if ack_state is not None:
            self.when_machine_emits(typ + '_ack', destination, ack_state)

    def start_machine(self, machine_cls, *args, **kwargs):
        return self.ctl.start_machine(machine_cls, self, *args, **kwargs)

    def when_machine_emits(self, typ, machine, state):
        self.ctl.add_machine_reaction(typ, machine, self, state)

    def when(self, typ, state):
        self.ctl.add_event_reaction(typ, self, state)

    def ignore_when_machine_emits(self, typ, machine):
        self.ctl.remove_machine_reaction(typ, machine, self)

        inbox_prime = queue()
        while True:
            try:
                event = self.inbox.popleft()
            except IndexError:
                break

            if event.typ != typ or event.emitter != machine:
                inbox_prime.append(event)

        self.inbox = inbox_prime

    def ignore_when(self, typ):
        self.ctl.remove_event_reaction(typ, self)

        inbox_prime = queue()
        while True:
            try:
                event = self.inbox.popleft()
            except IndexError:
                break

            if event.typ != typ:
                inbox_prime.append(event)

        self.inbox = inbox_prime

    def filter_event(self, event):
        return self.ctl.filter_event(self, event)

    def listen(self):
        if self.ctl.debug:
            print(str(self) + ' is listening, inbox:')
            print(self.inbox)

        try:
            self.event = self.inbox.popleft()
        except IndexError:
            return

        reaction = self.filter_event(self.event)

        if reaction is None:
            return

        if self.event.ack:
            self.emit_to(self.event.emitter, self.event.typ + '_ack',
                         value=self.event.value)

        if self.ctl.debug:
            print('going to state ' + reaction.__name__)

        return reaction

    def halt(self):
        if self.ctl.debug:
            print(str(self) + ' is halting')

        self.ctl.halt(self)
