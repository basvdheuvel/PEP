# Purely Event-Driven Programming
For my bachelor thesis I designed a language focussed on concurrency, trying to
use an event-driven approach without losing programmer control. See [my
thesis](https://esc.fnwi.uva.nl/thesis/centraal/files/f522241892.pdf) for the
original design, and [this paper](http://arxiv.org/abs/1803.11229) for a formal
description of PEP in ACP (the Algebra of Communicating Processes).

## Python simulation
With my thesis came a Python simulation. The simulation comes with a few example
PEP programs. There is also [documentation](Python_Simulator/pydoc.pdf).

## PSF and Go
The formalisations needed testing, which was done in a formal setting using
[PSF](https://staff.fnwi.uva.nl/b.diertens/psf/) and in a parallel(!) setting
using [Go](https://golang.org/). There is a small report about my findings
[here](ReportGoPSF.pdf).
