"""Simulates a purely event-driven programming language.

This simulator is part of a computer science bachelor's thesis for the
University of Amsterdam, by Bas van den Heuvel. It follows all concepts
introduced in this thesis. The purpose is to be able to test and refine those
concepts.

The scheduling method is deterministicly sequential. No concurrent execution is
implemented.

Classes:
MachineControl -- manages and schedules state machines and events
Event -- event for communication between state machines
StateMachine -- superclass for all possible state machines
"""
from collections import deque as queue


class MachineControl:
    """Manage and schedule state machines and events.

    Every program created with this simulator should have an instance of this
    class. Starting a program goes through this instance, as well as
    instantiating state machines and sending events.

    Execution of its machine's states happens through cycles. The scheduling
    for this is sequential and very minimalistic: the first machine in its
    queue gets cycled after which it gets replaced at the end of the queue.

    It can be said that there is no event scheduling. Before each state cycle,
    all events in the event buss are distributed to their respective state
    machines.
    """

    def __init__(self, debug=False):
        """Initialize a machine control.

        It setups up a machine list, which in this implementation is a queue.
        Reaction maps are created as dictionaries, and the event buss is
        another queue.

        The `ctx` variable is not yet set. This happens when the simulator is
        started.

        Keyword arguments:
        debug -- prints state machine and event buss information if True
            (default True)
        """
        self.machines = queue()

        self.event_reactions = {}
        self.machine_reactions = {}

        self.event_buss = queue()

        self.ctx = None

        self.debug = debug

    def start_machine(self, machine_cls, ctx, *args, **kwargs):
        """Start a state machine.

        Initializes a machine, given arbitrary arguments, and adds it to the
        machine queue. After this, some event reactions are added for this
        machine, the `start' and the `halt' events. Finally, a `start' event is
        emitted to the newly created machine.

        Arguments:
        machine_cls -- a StateMachine subclass
        ctx -- the state machine that starts this new machine
        *args/**kwargs -- any arguments the state machine takes
        """
        machine = machine_cls(self, ctx, *args, **kwargs)

        self.machines.append(machine)

        self.add_machine_reaction('start', ctx, machine, machine.init_state)
        self.add_machine_reaction('halt', ctx, machine, machine.halt)

        self.emit(Event('start', ctx, destination=machine))

        return machine

    def add_event_reaction(self, typ, reactor, state):
        """Add a reaction to an event.

        Arguments:
        typ -- the event's type string
        reactor -- the StateMachine that should react
        state -- the state the machine should transition to, a method
        """
        if typ not in self.event_reactions:
            self.event_reactions[typ] = {}

        self.event_reactions[typ][reactor] = state

    def remove_event_reaction(self, typ, reactor):
        """Remove a reaction to an event.

        Arguments:
        typ -- the event's type string
        reactor -- the StateMachine that should ignore the event
        """
        try:
            del self.event_reactions[typ][reactor]
        except KeyError:
            pass

    def add_machine_reaction(self, typ, emitter, reactor, state):
        """Add a reaction to a state machine's event.

        Arguments:
        typ -- the event's type string
        emitter -- the event's emitting StateMachine
        reactor -- the StateMachine that should react
        state -- the state the machine should transition to, a method
        """
        index = (typ, emitter)

        if index not in self.machine_reactions:
            self.machine_reactions[index] = {}

        self.machine_reactions[index][reactor] = state

    def remove_machine_reaction(self, typ, emitter, reactor):
        """Remove a reaction to a state machine's event.

        Arguments:
        typ -- the event's type string
        emitter -- the event's emitting StateMachine
        reactor -- the StateMachine that should ignore the event
        """
        index = (typ, emitter)

        try:
            del self.machine_reactions[index][reactor]
        except KeyError:
            pass

    def emit(self, event):
        """Add an event to the event buss.

        Arguments:
        event -- the to be emitted Event
        """
        self.event_buss.append(event)

    def run(self, machine_cls, *args, **kwargs):
        """Start a state machine and cycle until all machines have halted.

        A context is created for this first machine, by instantiating the
        StateMachine superclass without a context.

        Arguments:
        machine_cls -- a StateMachine subclass
        *args/**kwargs -- any arguments the state machine takes
        """
        self.ctx = StateMachine(self, None)
        self.start_machine(machine_cls, self.ctx, *args, **kwargs)

        while self.cycle():
            pass

    def cycle(self):
        """Distribute events, cycle a machine and return whether any are left.

        When the machine queue is empty, False is returned. Otherwise, True is
        returned.
        """
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
        """Distribute an event to machines and return whether any are left.

        If an event has a destination and that destination is still alive (i.e.
        not halted), the event is put into that machine's inbox.  Otherwise,
        the event is put into the inbox of all live machines, except the
        event's emitter.

        If an event has been distributed, True is returned. Otherwise, False is
        returned.
        """
        try:
            event = self.event_buss.popleft()
        except IndexError:
            return False

        if self.debug:
            print('distributing %s' % (event))

        if event.destination is not None:
            if event.destination in self.machines:
                event.destination.inbox.append(event)
            return True

        for machine in self.machines:
            if machine == event.emitter:
                continue
            machine.inbox.append(event)

        return True

    def filter_event(self, machine, event):
        """Returns a state if a machine should react to an event.

        If a reaction exists, the machine's reaction state is returned.
        Otherwise, None is returned.

        Arguments:
        machine -- the reacting state machine, a StateMachine
        event -- the event to be checked, an Event
        """
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
        """Halt a machine."""
        self.machines.remove(machine)


class Event:
    """An event for interaction between state machines."""

    def __init__(self, typ, emitter, value=None, destination=None, ack=False):
        """Initialize the event.

        Arguments:
        typ -- the event's type string
        emitter -- the StateMachine emitting the event

        Keyword arguments:
        value -- value to transmit (default None)
        destination -- the StateMachine the event should end up with
            (default None)
        ack -- whether the receiving machine should emit an acknowledgement
            (default False)
        """
        self.typ = typ
        self.value = value
        self.emitter = emitter
        self.destination = destination
        self.ack = ack

        self.state = None

    def __repr__(self):
        return '<Event:typ=%s,emitter=%s,destination=%s,ack=%s>' % (
            self.typ, self.emitter, self.destination, self.ack)


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

        self.emit('halt')
        self.ctl.halt(self)
