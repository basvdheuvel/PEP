package main

import "fmt"
import "sync"
import "math/rand"
import "time"

type event struct {
	s int
	d int
	t string
	a bool
}

type curev struct {
	s int
	t string
}

type reaction struct {
	ce curev
	s  string
}

type variable struct {
	name string
	id   int
}

type MprogFunc func(*sync.WaitGroup, int, int, chan<- event, <-chan event,
	<-chan bool, chan<- variable, <-chan int, chan<- int,
	chan<- bool, chan<- bool, chan<- bool, chan<- bool)

func Q(wg *sync.WaitGroup,
	deq chan<- event, qempty chan<- bool, enq <-chan event,
	haltq <-chan bool) {
	l := []event{}

Qloop:
	for {
		if len(l) == 0 {
			select {
			case qempty <- true:
			case e := <-enq:
				l = append(l, e)
			case <-haltq:
				break Qloop
			}
		} else {
			select {
			case deq <- l[0]:
				l = l[1:]
			case e := <-enq:
				l = append(l, e)
			case <-haltq:
				break Qloop
			}
		}
	}

	defer wg.Done()
}

// func Treactions(tbl map[curev]string, get chan reaction, set <-chan reaction,
//                 unset <-chan curev, halt chan bool) {
//     TreactionsLoop:
//     for {
//         select {
//         case qry := <-get:
//             get <- reaction{qry.ce, tbl[qry.ce]}
//         case r := <-set:
//             tbl[r.ce] = r.s
//         case ce := <-unset:
//             delete(tbl, ce)
//         case <-halt:
//             fmt.Println("Treactions.halt")
//             break TreactionsLoop
//         }
//     }
//     fmt.Println("Treactions quitting")
// }

// func Tvars(tbl map[string]int, get chan variable, set <-chan variable,
//                 unset <-chan string, halt chan bool) {
//     TvarsLoop:
//     for {
//         select {
//         case qry := <-get:
//             get <- variable{qry.name, tbl[qry.name]}
//         case v := <-set:
//             tbl[v.name] = v.id
//         case name := <-unset:
//             delete(tbl, name)
//         case <-halt:
//             fmt.Println("Tvars.halt")
//             break TvarsLoop
//         }
//     }
//     fmt.Println("Tvars quitting")
// }

func Mcom(wg *sync.WaitGroup,
	input <-chan event, output chan<- event, halt <-chan bool) {
McomLoop:
	for {
		select {
		case e := <-input:
			//fmt.Println("com'ing", e)
			select {
			case output <- e:
				continue McomLoop
			case <-halt:
				break McomLoop
			}
		case <-halt:
			break McomLoop
		}
	}

	defer wg.Done()
}

//func Mout(deq <-chan event, out chan<- event, halt <-chan bool) {
//MoutLoop:
//for {
//select {
//case e := <-deq:
//fmt.Println("Mout.out")
//out <- e
//case <-halt:
//fmt.Println("Mout.halt")
//break MoutLoop
//}
//}
//fmt.Println("Mout quitting")
//}

//func Min(distrib <-chan event, enq chan<- event, halt <-chan bool) {
//MinLoop:
//for {
//select {
//case e := <-distrib:
//enq <- e
//case <-halt:
//break MinLoop
//}
//}
//}

func Machine(wg *sync.WaitGroup, mProg MprogFunc,
	out chan<- event, distrib <-chan event, start_M chan<- variable,
	new_id <-chan int, halt_M chan<- int, id int, ctxid int) {
	// Setup to wait for all subroutines to finish.
	var waitGroup sync.WaitGroup
	waitGroup.Add(4)

	haltq_in := make(chan bool)
	deq_in := make(chan event)
	qempty_in := make(chan bool)
	enq_in := make(chan event)

	go Q(&waitGroup, deq_in, qempty_in, enq_in, haltq_in)

	haltq_out := make(chan bool)
	deq_out := make(chan event)
	qempty_out := make(chan bool)
	enq_out := make(chan event)

	go Q(&waitGroup, deq_out, qempty_out, enq_out, haltq_out)

	halt_Mout := make(chan bool)
	//out := make(chan event)

	//go Mout(deq_out, out, halt_Mout)
	go Mcom(&waitGroup, deq_out, out, halt_Mout)

	halt_Min := make(chan bool)
	//distrib := make(chan event)

	//go Min(distrib, enq_in, halt_Min)
	go Mcom(&waitGroup, distrib, enq_in, halt_Min)

	mProg(&waitGroup, id, ctxid, enq_out, deq_in, qempty_in, start_M, new_id,
		halt_M, haltq_in, haltq_out, halt_Min, halt_Mout)

	// Wait for all to halt
	waitGroup.Wait()
	defer wg.Done()
}

func MCin(wg *sync.WaitGroup,
	out <-chan event, enq chan<- event, halt <-chan bool) {
MCinLoop:
	for {
		select {
		case e := <-out:
			enq <- e
		case <-halt:
			break MCinLoop
		}
	}

	defer wg.Done()
}

func send_halt(wg *sync.WaitGroup, halt chan<- bool) {
	halt <- true
	wg.Done()
}

func merge_distrib(wg *sync.WaitGroup, c chan<- event, e event) {
	c <- e
	wg.Done()
}

func MCsched(wg *sync.WaitGroup, out chan event,
	deq <-chan event, enq chan<- event, distrib map[int](chan event),
	start_M chan variable, new_id chan int,
	halt_M chan int, halt_MCin chan<- bool, haltq chan<- bool,
	n int, l map[int]bool) {
	Mprogs := map[string]MprogFunc{"CPU": CPU, "HD": HD, "HDHead": HDHead,
		"ProgA": ProgA, "ProgB": ProgB}

MCschedLoop:
	for {
		select {
		case e := <-deq:
			//fmt.Println("MC deq'd", e)
			if e.d == 0 {
				// No destination
				var waitGroup sync.WaitGroup

				waitGroup.Add(len(l))
				for i := 1; i <= n; i++ {
					if l[i] == false {
						continue
					}
					//fmt.Println("distrib'ing", e, "to", i)
					go merge_distrib(&waitGroup, distrib[i], e)
				}

				waitGroup.Wait()

			} else {
				// Destination
				//fmt.Println("distrib'ing", e, "to", e.d)
				distrib[e.d] <- e
			}

		case start_req := <-start_M:
			n = n + 1
			new_id <- n

			l[n] = true
			new_distrib := make(chan event)
			distrib[n] = new_distrib

			wg.Add(1)
			go Machine(wg, Mprogs[start_req.name], out, new_distrib, start_M,
				new_id, halt_M, n, start_req.id)

		case id := <-halt_M:
			fmt.Println(id, "is halting")
			enq <- event{id, 0, "halt", false}

			delete(l, id)

			if len(l) == 0 {
				fmt.Println("That's the end")
				var waitGroup sync.WaitGroup
				waitGroup.Add(2)

				go send_halt(&waitGroup, halt_MCin)
				go send_halt(&waitGroup, haltq)

				waitGroup.Wait()
				break MCschedLoop
			}
		}
	}

	defer wg.Done()
}

func MC(wg *sync.WaitGroup,
	out chan event, distrib map[int](chan event), start_M chan variable,
	new_id chan int, halt_M chan int,
	n int, l map[int]bool) {
	var waitGroup sync.WaitGroup
	waitGroup.Add(3)

	haltq := make(chan bool)
	deq := make(chan event)
	qempty := make(chan bool)
	enq := make(chan event)
	go Q(&waitGroup, deq, qempty, enq, haltq)

	halt_MCin := make(chan bool)
	//go MCin(&waitGroup, out, enq, halt_MCin)
	go Mcom(&waitGroup, out, enq, halt_MCin)

	go MCsched(&waitGroup, out, deq, enq, distrib, start_M, new_id, halt_M,
		halt_MCin, haltq, n, l)

	waitGroup.Wait()
	defer wg.Done()
}

func Template(wg *sync.WaitGroup, id int, ctxid int,
	enq chan<- event, deq <-chan event, qempty <-chan bool,
	start_M chan<- variable, new_id <-chan int,
	halt_M chan<- int, haltq_in chan<- bool, haltq_out chan<- bool,
	halt_Min chan<- bool, halt_Mout chan<- bool) {

	//vars := map[string]int{"ctx": ctxid}
	reactions := map[curev]string{}

	if ctxid != 0 {
		reactions[curev{ctxid, "halt"}] = "halt"
	}

	current_state := "halt"
	current_event := event{0, 0, "", false}
	if current_event != current_event {
		current_event = event{0, 0, "", false}
	}

TemplateLoop:
	for {
		switch current_state {
		case "listen":
			select {
			case <-qempty:
				continue TemplateLoop

			case e := <-deq:
				state, present := reactions[curev{e.s, e.t}]
				if present {
					if e.a {
						enq <- event{id, e.s, e.t + "ack", false}
					}

					current_event = e
					current_state = state
				} else {
					state, present = reactions[curev{0, e.t}]
					if present {
						if e.a {
							enq <- event{id, e.s, e.t + "ack", false}
						}

						current_event = e
						current_state = state
					} else {
						current_state = "listen"
					}
				}

				if current_state != "listen" {
					fmt.Println(id, "'s new state:", current_state)
				}
			}

		case "halt":
			halt_M <- id
			wg.Add(4)
			go send_halt(wg, haltq_in)
			go send_halt(wg, haltq_out)
			go send_halt(wg, halt_Min)
			go send_halt(wg, halt_Mout)

			break TemplateLoop
		}
	}
}

func CPU(wg *sync.WaitGroup, id int, ctxid int,
	enq chan<- event, deq <-chan event, qempty <-chan bool,
	start_M chan<- variable, new_id <-chan int,
	halt_M chan<- int, haltq_in chan<- bool, haltq_out chan<- bool,
	halt_Min chan<- bool, halt_Mout chan<- bool) {

	vars := map[string]int{"ctx": ctxid}
	reactions := map[curev]string{}

	if ctxid != 0 {
		reactions[curev{ctxid, "halt"}] = "halt"
	}

	current_state := "setup"
	current_event := event{0, 0, "", false}
	if current_event != current_event {
		current_event = event{0, 0, "", false}
	}

CPULoop:
	for {
		switch current_state {
		case "setup":
			start_M <- variable{"HD", id}
			vars["hd"] = <-new_id

			start_M <- variable{"ProgA", id}
			vars["prog_a"] = <-new_id

			start_M <- variable{"ProgB", id}
			vars["prog_b"] = <-new_id

			reactions[curev{0, "cycle"}] = "cycle"
			reactions[curev{0, "read"}] = "hd_read"
			reactions[curev{0, "shutdown"}] = "halt"

			current_state = "listen"

		case "cycle":
			fmt.Println("<cycle>")
			current_state = "listen"

		case "hd_read":
			vars["hd_reader"] = current_event.s
			enq <- event{id, vars["hd"], "read", false}
			reactions[curev{vars["hd"], "interrupt"}] = "hd_interrupt"
			current_state = "listen"

		case "hd_interrupt":
			enq <- event{id, vars["hd_reader"], "return", false}
			delete(reactions, curev{vars["hd"], "interrupt"})
			current_state = "listen"

		case "listen":
			select {
			case <-qempty:
				continue CPULoop

			case e := <-deq:
				state, present := reactions[curev{e.s, e.t}]
				if present {
					if e.a {
						enq <- event{id, e.s, e.t + "ack", false}
					}

					current_event = e
					current_state = state
				} else {
					state, present = reactions[curev{0, e.t}]
					fmt.Println("REACTION", state, present)
					if present {
						if e.a {
							enq <- event{id, e.s, e.t + "ack", false}
						}

						current_event = e
						current_state = state
					} else {
						current_state = "listen"
					}
				}

				if current_state != "listen" {
					fmt.Println(id, "'s new state:", current_state)
				}
			}

		case "halt":
			halt_M <- id
			wg.Add(4)
			go send_halt(wg, haltq_in)
			go send_halt(wg, haltq_out)
			go send_halt(wg, halt_Min)
			go send_halt(wg, halt_Mout)

			break CPULoop
		}
	}
}

func HD(wg *sync.WaitGroup, id int, ctxid int,
	enq chan<- event, deq <-chan event, qempty <-chan bool,
	start_M chan<- variable, new_id <-chan int,
	halt_M chan<- int, haltq_in chan<- bool, haltq_out chan<- bool,
	halt_Min chan<- bool, halt_Mout chan<- bool) {

	vars := map[string]int{"ctx": ctxid}
	reactions := map[curev]string{}

	if ctxid != 0 {
		reactions[curev{ctxid, "halt"}] = "halt"
	}

	current_state := "setup"
	current_event := event{0, 0, "", false}
	if current_event != current_event {
		current_event = event{0, 0, "", false}
	}

HDLoop:
	for {
		switch current_state {
		case "setup":
			start_M <- variable{"HDHead", id}
			vars["hd_head"] = <-new_id
			reactions[curev{vars["ctx"], "read"}] = "seek"
			current_state = "listen"

		case "seek":
			delete(reactions, curev{vars["ctx"], "read"})
			enq <- event{id, vars["hd_head"], "seek", false}
			reactions[curev{vars["hd_head"], "found_data"}] = "found_data"
			current_state = "listen"

		case "found_data":
			delete(reactions, curev{vars["hd_head"], "found_data"})
			reactions[curev{vars["ctx"], "read"}] = "seek"
			enq <- event{id, vars["ctx"], "interrupt", false}
			current_state = "listen"

		case "listen":
			select {
			case <-qempty:
				continue HDLoop

			case e := <-deq:
				state, present := reactions[curev{e.s, e.t}]
				if present {
					if e.a {
						enq <- event{id, e.s, e.t + "ack", false}
					}

					current_event = e
					current_state = state
				} else {
					state, present = reactions[curev{0, e.t}]
					if present {
						if e.a {
							enq <- event{id, e.s, e.t + "ack", false}
						}

						current_event = e
						current_state = state
					} else {
						current_state = "listen"
					}
				}

				if current_state != "listen" {
					fmt.Println(id, "'s new state:", current_state)
				}
			}

		case "halt":
			halt_M <- id
			wg.Add(4)
			go send_halt(wg, haltq_in)
			go send_halt(wg, haltq_out)
			go send_halt(wg, halt_Min)
			go send_halt(wg, halt_Mout)

			break HDLoop
		}
	}
}

func HDHead(wg *sync.WaitGroup, id int, ctxid int,
	enq chan<- event, deq <-chan event, qempty <-chan bool,
	start_M chan<- variable, new_id <-chan int,
	halt_M chan<- int, haltq_in chan<- bool, haltq_out chan<- bool,
	halt_Min chan<- bool, halt_Mout chan<- bool) {

	vars := map[string]int{"ctx": ctxid}
	reactions := map[curev]string{}

	if ctxid != 0 {
		reactions[curev{ctxid, "halt"}] = "halt"
	}

	current_state := "setup"
	current_event := event{0, 0, "", false}
	if current_event != current_event {
		current_event = event{0, 0, "", false}
	}

	rand.Seed(time.Now().UnixNano())
	var hardness float32 = .8

HDHeadLoop:
	for {
		switch current_state {
		case "setup":
			reactions[curev{vars["ctx"], "seek"}] = "seek"
			current_state = "listen"

		case "seek":
			if rand.Float32() >= hardness {
				enq <- event{id, vars["ctx"], "found_data", false}
				current_state = "listen"
			} else {
				fmt.Println("<seek>")
				current_state = "seek"
			}

		case "listen":
			select {
			case <-qempty:
				continue HDHeadLoop

			case e := <-deq:
				state, present := reactions[curev{e.s, e.t}]
				if present {
					if e.a {
						enq <- event{id, e.s, e.t + "ack", false}
					}

					current_event = e
					current_state = state
				} else {
					state, present = reactions[curev{0, e.t}]
					if present {
						if e.a {
							enq <- event{id, e.s, e.t + "ack", false}
						}

						current_event = e
						current_state = state
					} else {
						current_state = "listen"
					}
				}

				if current_state != "listen" {
					fmt.Println(id, "'s new state:", current_state)
				}
			}

		case "halt":
			halt_M <- id
			wg.Add(4)
			go send_halt(wg, haltq_in)
			go send_halt(wg, haltq_out)
			go send_halt(wg, halt_Min)
			go send_halt(wg, halt_Mout)

			break HDHeadLoop
		}
	}
}

func ProgA(wg *sync.WaitGroup, id int, ctxid int,
	enq chan<- event, deq <-chan event, qempty <-chan bool,
	start_M chan<- variable, new_id <-chan int,
	halt_M chan<- int, haltq_in chan<- bool, haltq_out chan<- bool,
	halt_Min chan<- bool, halt_Mout chan<- bool) {

	vars := map[string]int{"ctx": ctxid}
	reactions := map[curev]string{}

	if ctxid != 0 {
		reactions[curev{ctxid, "halt"}] = "halt"
	}

	current_state := "program"
	current_event := event{0, 0, "", false}
	// Dirty hack to please the compiler...
	if current_event != current_event {
		current_event = event{0, 0, "", false}
	}

ProgALoop:
	for {
		switch current_state {
		case "program":
			enq <- event{id, vars["ctx"], "read", false}
			reactions[curev{vars["ctx"], "return"}] = "finish"
			current_state = "listen"

		case "finish":
			delete(reactions, curev{vars["ctx"], "return"})
			enq <- event{id, vars["ctx"], "shutdown", false}
			current_state = "listen"

		case "listen":
			select {
			case <-qempty:
				continue ProgALoop

			case e := <-deq:
				state, present := reactions[curev{e.s, e.t}]
				if present {
					if e.a {
						enq <- event{id, e.s, e.t + "ack", false}
					}

					current_event = e
					current_state = state
				} else {
					state, present = reactions[curev{0, e.t}]
					if present {
						if e.a {
							enq <- event{id, e.s, e.t + "ack", false}
						}

						current_event = e
						current_state = state
					} else {
						current_state = "listen"
					}
				}

				if current_state != "listen" {
					fmt.Println(id, "'s new state:", current_state)
				}
			}

		case "halt":
			halt_M <- id
			wg.Add(4)
			go send_halt(wg, haltq_in)
			go send_halt(wg, haltq_out)
			go send_halt(wg, halt_Min)
			go send_halt(wg, halt_Mout)

			break ProgALoop
		}
	}
}

func ProgB(wg *sync.WaitGroup, id int, ctxid int,
	enq chan<- event, deq <-chan event, qempty <-chan bool,
	start_M chan<- variable, new_id <-chan int,
	halt_M chan<- int, haltq_in chan<- bool, haltq_out chan<- bool,
	halt_Min chan<- bool, halt_Mout chan<- bool) {

	vars := map[string]int{"ctx": ctxid}
	reactions := map[curev]string{}

	if ctxid != 0 {
		reactions[curev{ctxid, "halt"}] = "halt"
	}

	current_state := "cycle"
	current_event := event{0, 0, "", false}
	if current_event != current_event {
		current_event = event{0, 0, "", false}
	}

ProgBLoop:
	for {
		switch current_state {
		case "cycle":
			enq <- event{id, vars["ctx"], "cycle", true}
			reactions[curev{vars["ctx"], "cycle_ack"}] = "cycle"
			current_state = "listen"

		case "listen":
			select {
			case <-qempty:
				continue ProgBLoop

			case e := <-deq:
				state, present := reactions[curev{e.s, e.t}]
				if present {
					if e.a {
						enq <- event{id, e.s, e.t + "ack", false}
					}

					current_event = e
					current_state = state
				} else {
					state, present = reactions[curev{0, e.t}]
					if present {
						if e.a {
							enq <- event{id, e.s, e.t + "ack", false}
						}

						current_event = e
						current_state = state
					} else {
						current_state = "listen"
					}
				}

				if current_state != "listen" {
					fmt.Println(id, "'s new state:", current_state)
				}
			}

		case "halt":
			halt_M <- id
			wg.Add(4)
			go send_halt(wg, haltq_in)
			go send_halt(wg, haltq_out)
			go send_halt(wg, halt_Min)
			go send_halt(wg, halt_Mout)

			break ProgBLoop
		}
	}
}

func main() {
	var waitGroup sync.WaitGroup
	waitGroup.Add(2)

	out := make(chan event)
	halt_M := make(chan int)
	start_M := make(chan variable)
	new_id := make(chan int)

	distrib := make(chan event)
	go Machine(&waitGroup, CPU, out, distrib, start_M, new_id, halt_M, 1, 0)

	distribs := map[int](chan event){1: distrib}

	go MC(&waitGroup, out, distribs, start_M, new_id, halt_M, 1,
		map[int]bool{1: true})

	waitGroup.Wait()
}
