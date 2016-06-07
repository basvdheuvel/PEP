from simulator.debug_window import DebugWindow
from time import sleep


def main():
    dw = DebugWindow(title='First title')

    for i in range(100):
        dw.set_title('Title %d' % (i))
        dw.write('Dit is gewoon wat tekst, de %de om precies te zijn' % (i))
        sleep(1)

    dw.close()


if __name__ == '__main__':
    main()
