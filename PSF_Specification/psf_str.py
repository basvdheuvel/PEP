import sys


def main():
    infname = sys.argv[1]
    outfname = infname.rstrip('_str')

    with open(outfname, 'w') as outf:
        with open(infname, 'r') as inf:
            for inline in inf:
                outline = ''
                state = 'read'

                for char in inline:
                    if state == 'read':
                        if char == '"':
                            state = 'convert'
                            outline += 'mt'
                        else:
                            outline += char

                    elif state == 'convert':
                        if char == '"':
                            state = 'read'
                        else:
                            outline += '^\'' + char + '\''

                print(outline, end='', file=outf)


if __name__ == '__main__':
    main()
