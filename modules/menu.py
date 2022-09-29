##############################
# TUI Menu and Scroll Module #
# By: Darth Venom            #
##############################
import curses

def scroll(stdscr, y: int, x: int, d: dict, limit: int, aster=0) -> None:
    curses.use_default_colors()
    curses.init_pair(15,0,15)
    it = list(d.keys())
    p = 0
    e = 0
    mp = 0
    minpag = 0
    maxpag = limit-1
    for i in it[0:limit]:
        stdscr.addstr(y+p, x, i)
        p += 1
    p = 0
    stdscr.addstr(y+p, x, it[e], curses.color_pair(15))
    while True:
        k = stdscr.getch()
        if k == curses.KEY_UP:
            if e:
                if e == minpag:
                    maxpag -= 1
                    minpag -= 1
                    stdscr.move(y, x);stdscr.clrtobot()
                    mp = 0
                    for i in it[minpag:maxpag+1]:
                        stdscr.addstr(y+mp, x, i)
                        mp += 1
                else:
                    stdscr.addstr(y+p, x, it[e])
                    p -= 1
                e -= 1
                stdscr.addstr(y+p, x, it[e], curses.color_pair(15))
        if k == curses.KEY_DOWN:
            if e != len(it)-1:
                if e == maxpag:
                    maxpag += 1
                    minpag += 1
                    stdscr.move(y,x);stdscr.clrtobot()
                    mp = 0
                    for i in it[minpag:maxpag]:
                        stdscr.addstr(y+mp, x, i)
                        mp += 1
                else:
                    stdscr.addstr(y+p, x, it[e])
                    p += 1
                e += 1
                stdscr.addstr(y+p, x, it[e], curses.color_pair(15))
        if k == 10:
            res=d[it[e]]()
            if res:
                return res
            return

def menu(stdscr, y: int, x: int, d: dict, aster=0, esc_r1=0) -> None:
    curses.use_default_colors()
    curses.init_pair(15,0,15)
    it = list(d.keys())
    p = 0
    my=stdscr.getmaxyx()[0]
    for i in d:
        stdscr.addstr(y+p, x, i)
        p += 1
    p = 0
    stdscr.addstr(y+p, x, it[p], curses.color_pair(15))
    while True:
        k = stdscr.getch() # Key
        if k == 259:
            if p:
                stdscr.addstr(y+p, x, it[p])
                p -= 1
                stdscr.addstr(y+p, x, it[p], curses.color_pair(15))
        if k == 258:
            if p != len(it) - 1:
                stdscr.addstr(y+p, x, it[p])
                p += 1
                stdscr.addstr(y+p, x, it[p], curses.color_pair(15))
        if k == 27:
            stdscr.addstr(y+p, x, it[p])
            stdscr.noutrefresh()
            curses.doupdate()
            if esc_r1: return 1
            return
        if k == 10:
            stdscr.addstr(y+p, x, it[p])
            stdscr.noutrefresh()
            curses.doupdate()
            if aster:
                for i in range(my):
                    stdscr.addch(i, 0, ' ')
                    stdscr.noutrefresh()
                stdscr.addch(y+p,0,'*')
                stdscr.noutrefresh()
                curses.doupdate()
            res = d[it[p]]()
            prev_p = p
            if res:
                return res
            return

if __name__=="__main__":

    def putstr(stdscr, text):
        stdscr.addstr(0, 0, text)

    def main(stdscr):
        curses.use_default_colors()
        curses.init_pair(15,0,15)
        win=curses.newwin(10,50, 5, 0)
        d = {
                "print": lambda: putstr(stdscr, "Hello world"),
                "opinion": lambda: putstr(stdscr, "Alto menú wacho"),
                "autor": lambda: putstr(stdscr, "Darth Venom"),
                "exit": exit
            }
        while True:
            menu(win, 3, 0, d)
    curses.wrapper(main)
