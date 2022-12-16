import curses

"""
Regla estándar
Todas las funciones para interactuar con elementos de la interfaz deben retornar int. Si deveulve 1, el bucle continúa; sino, el bucle se rompe.

Todas las funciones llamadas desde un menú deben devolver 1.

Al salir de un menú se debe devolver 0.
"""

def defwrite(win,wcaps,opts,mode,mdata,data,colors):
    # No necesita 'y' y 'x' porque son 0 y 0 respectivamente
    # O sea, desde que empieza la ventana hasta que termina

    # mode 0 - Escribir todas las opciones y dejar p en 0
    # mode 1 - Disminuir p por 1
    # mode 2 - Aumentar p por 1
    keys = list(opts.keys())
    xmargin=0
    if not mode:
        tmp = 0
        for i in keys[mdata[2]:mdata[3]]:
            win.addstr(tmp,xmargin,i,curses.color_pair(colors[0]))
            tmp += 1
        win.addstr(0,xmargin,keys[0],curses.color_pair(colors[1]))
        return
    win.addstr(mdata[0],xmargin,keys[mdata[1]],curses.color_pair(colors[0]))
    if mode == 1:
        if not mdata[0]:  # if p == minlim
            win.scroll(-1)
            mdata[1] -= 1
            mdata[2] -= 1
            mdata[3] -= 1
        else:
            mdata[1] -= 1
            mdata[0] -= 1
    else:
        if mdata[1] == mdata[3]-1:  # if p == vislim
            win.scroll(1)
            mdata[1] += 1
            mdata[2] += 1
            mdata[3] += 1
        else:
            mdata[0] += 1
            mdata[1] += 1
    win.addstr(mdata[0],xmargin,keys[mdata[1]],curses.color_pair(colors[1]))

# colors contiene fg/bg y el color de énfasis respectivamente
# data se usa cuando se necesita que wrwrap o algún binding use información de algún objeto que le pasemos al menú
def menu(win,wcaps,opts,wrwrap,emptyopts=False,bindings={},allowesc=True,colors=(0,1),data=None):
    curses.curs_set(0)
    mwin = win.derwin(*wcaps)
    mwin.keypad(1)
    mwin.bkgd(curses.color_pair(colors[0]))
    mwin.scrollok(1)
    mwin.refresh()
    mdata = [0,0,0,wcaps[0]]  # menu data: p, sp, minlim, vislim
    keys = list(opts.keys())
    if not emptyopts and not len(opts): raise ValueError("No se han especificado opciones")
    wrwrap(mwin,wcaps,opts,0,mdata,data,colors)
    #interact part
    while True:
        ch = mwin.getch()
        if ch == 27:  # ESC
            if not allowesc: continue
            del mwin
            return 0
        # mdata[1] is minlim
        # mdata[2] is vislim
        if ch == 259:  # UP
            if not mdata[1]: continue
            wrwrap(mwin,wcaps,opts,1,mdata,data,colors)
        if ch == 258:  # DOWN
            if mdata[1] == len(opts)-1: continue
            wrwrap(mwin,wcaps,opts,2,mdata,data,colors)
        if ch == 10:  # ENTER
            del mwin
            return opts[keys[mdata[1]]]()
        if not ch in bindings: continue
        bindings[ch](mwin,wcaps,opts,mdata,data)
    #Si se alcanza el límite, el scroll lo hace menu()
    #R: No, es convenible que el scroll lo haga la
    #función wrapper, ya que si hay que srollear,
    #también puede que se necesiten hacer arreglos antes
    #o después. Es mejor dejarle todo ese trabajo.

if __name__=='__main__':
    def main(stdscr):
        curses.use_default_colors()
        curses.init_pair(1,0,15)
        curses.init_pair(2,15,20)
        curses.curs_set(0)
        caps=stdscr.getmaxyx()
        opts = {"exit": exit, "continue": lambda: 1, "t1": lambda: 1, "t2": lambda: 1, "t3": lambda: 1, "t4": lambda: 1}
        while True:
            if (menu(stdscr,(4,20,caps[0]//2-2,caps[1]//2-10),opts,defwrite,allowesc=True,colors=(2,1))):
                stdscr.move(0,0);stdscr.clrtobot()
                continue
            else: break
    curses.wrapper(main)
