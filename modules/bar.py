import curses

def line(win, y,x, mx,color):
    r = mx - x
    win.addstr(y,x,' '*r, curses.color_pair(color))
    win.refresh()

class Label:
    def __init__(self,win,y=0,x=0,str="",color=[]):
        self.y = y
        self.x = x
        self.win = win
        self._str = str
        self._sym = []
        self._clr = []
        for i in color:
            self._sym.append(i[0])
            self._clr.append(i[1])
    def str(self,s,color):
        self._str = s
        for i in color:
            self._sym.append(i[0])
            self._clr.append(i[1])
    def strep(self):
        s = self._str
        for i in self._sym: s=s.replace(i,'')
        return s
    def draw(self, y=-1, x=-1):
        if y==-1: y=self.y
        if x==-1: x=self.x
        self.win.move(y,x)
        for i in range(len(self._str)):
            if not (self._str[i] in self._sym):
                self.win.addch(self._str[i])
                continue
            self.win.attron(curses.color_pair(self._clr[self._sym.index(self._str[i])]))
        self.win.refresh()

class Bar:
    def __init__(self,win,y,x,color):
        self.win = win
        self.winsz = (0,0)
        self.y=y
        self.x=x
        self.color=color
        self.elements=([],[],[])
        self.strelms = ["","",""]
        self.cursor = [0,0,0,self.x]

    def getmaxyx(self):
        self.winsz = self.win.getmaxyx()

    def draw(self):
        self.getmaxyx()
        line(self.win,self.y,self.x,self.winsz[1],self.color)
        self.win.attron(curses.color_pair(self.color))
        self.win.move(self.y,0)
        for i in self.elements[0]:
            i.draw(*self.win.getyx())
            self.win.addch(' ')

        self.win.move(self.y,self.winsz[1]//2-(len(self.strelms[1][:-1])-1)//2)
        for i in self.elements[1]:
            i.draw(*self.win.getyx())
            self.win.addch(' ')

        if self.strelms[2]:
            self.win.move(self.y,self.winsz[1]-len(self.strelms[2])+1)
            for i in range(len(self.elements[2])-1):
                self.elements[2][i].draw(*self.win.getyx())
                self.win.addch(' ')
            self.elements[2][-1].draw(*self.win.getyx())

        self.win.attroff(curses.color_pair(self.color))
        self.win.refresh()

    def align(self,to,s):
        if to == 'left': to = 0
        elif to == 'center': to = 1
        elif to == 'right': to = 2
        else: raise ValueError("Invalid argument: %s"%to)
        self.cursor[to] += len(s.strep())+1
        self.elements[to].append(s)
        self.strelms[to] += '%s '%s.strep()

    def interact(self): pass

class DisplayOpts:
    def __init__(self,win,opts,oclr,tclr):
        self.win = win
        self.y = 0
        self.x = 0
        self.opts = opts
        self.oclr=oclr  # Option color
        self.tclr=tclr  # Text color
    def __getmaxyx(self): self.y, self.x = self.win.getmaxyx()
    def __size(self,opts):
        a = 0
        for i in opts: a += len(opts[i])+3
        return a
    def __checkelm(self,x,opts):
        if x-self.__size(opts) > 0: return opts
        c = opts.copy()
        c.popitem()
        return self.__checkelm(x,c)
    def draw(self):
        self.__getmaxyx()
        opts = self.__checkelm(self.x,self.opts)
        self.win.move(self.y-1,0);self.win.clrtoeol()
        s = round((self.x-self.__size(opts))//len(opts))
        x = 0
        #self.win.addstr(5,0,f"s: {s}\nx: {self.x}\nsize: {self.__size(opts)}\nopts: {len(opts)}")
        for i in opts:
            self.win.addstr(self.y-1,x,i,curses.color_pair(self.oclr))
            try: self.win.addstr(self.y-1,x+3,opts[i],curses.color_pair(self.tclr))
            except: pass
            x += 3+len(opts[i])+s
        self.win.refresh()

if __name__=='__main__':
    def main(stdscr):
        curses.init_pair(1,0,15)
        curses.init_pair(2,160,15)
        curses.init_pair(3,40,15)
        curses.curs_set(0)
        colors = ( ('%',2), ('!',1), ('#',3) )
        bar = Bar(stdscr,0,0,1)
        bar.align('center', Label(stdscr,0,0,'Hacking-Utils',colors))
        bar.align('left', Label(stdscr,0,0,'User: %tomate!',colors))
        bar.align('right', Label(stdscr,0,0,'Online: 17 ',colors))
        bar.align('right', Label(stdscr,0,0,'Status:', colors))
        bar.align('right', Label(stdscr,0,0,'#Connected!',colors))
        bar.draw()
        opts = {'^a': 'Añadir', '^q': 'Salir', '^w': 'Websearch', '^e': 'Eliminar', '^r': 'Reload', '^t': 'Tambien', '^u': 'Unload', '^o': 'Overload', '^p': 'Portear', '^g': 'Ir a linea'}
        dp = DisplayOpts(stdscr,opts,1,0)
        dp.draw()
        while True:
            ch = stdscr.getch()
            if ch == 410:
                y,x =stdscr.getmaxyx()
                bar.draw()
                if dp.y <= y:
                    stdscr.move(dp.y-1,0)
                    stdscr.clrtoeol()
                dp.draw()
            if ch == 10:
                break
    curses.wrapper(main)
