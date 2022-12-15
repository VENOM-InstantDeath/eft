#!/usr/bin/env python3
import curses
import socket
import select
from os import getenv, path, mkdir, listdir, getenv
from json import loads, dumps
from threading import Thread
from time import sleep
from modules.ncRead import ampsread
from modules.menu import menu,defwrite
from modules.bar import Bar, Label

def refresh(a,b=None):
    a.refresh()
    if b: b.refresh()

def genvlambda(val): return lambda: val
def topath(pathlist):
    s="/"
    for i in range(len(pathlist)-1):
        s += pathlist[i]+'/'
    s += pathlist[-1]
    return s
def cleanlines(win,mcaps):
    y = mcaps[2]
    for i in range(mcaps[0]):
        for e in range(mcaps[1]):
            win.addch(y+i,mcaps[3]+e, ' ')
            win.refresh()

def srvtarget(logwin,stop):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    logwin.addstr("Socket creado\n")
    logwin.noutrefresh()
    sock.bind(("0.0.0.0", 3332))
    logwin.addstr(f"Socket escuchando en puerto 3332\n")
    logwin.noutrefresh()
    sock.listen(1)
    sock.settimeout(2)
    logwin.addstr(f"Esperando conexiones...\n")
    logwin.noutrefresh()
    curses.doupdate()
    add = ("Nadie",)
    serv = None
    while True:
        try:
            serv,add = sock.accept()
        except TimeoutError:
            if not stop[0]: continue
        break
    logwin.addstr(f"{add[0]} se ha conectado\n")
    logwin.noutrefresh()
    curses.doupdate()
    while not stop[0]:
        if not select.select([serv],[],[],2)[0]: continue
        data = serv.recv(1024).decode()
        if not data:
            logwin.addstr("El cliente se ha desconectado.\n")
            logwin.noutrefresh()
            curses.doupdate()
            serv.close()
            sock.close()
            break
        logwin.addstr(f"Se ha recibido: {data}\n")
        logwin.noutrefresh()
        curses.doupdate()
        data = data.split()
        if data[0] == "home":
            serv.sendall(getenv("HOME").encode())
        elif data[0] == "ls":
            if len(data) == 1:
                PWD = getenv("HOME")+'/'
            else:
                PWD = data[1]+'/'
            ls = listdir(PWD)
            dls = {}
            for i in ls:
                dls[i] = path.isdir(PWD+i)
            ls = dumps(dls)
            serv.send(str(len(ls)).encode())
            serv.recv(4)
            serv.sendall(ls.encode())
        elif data[0] == "send":
            logwin.addstr("Obteniendo archivo...\n")
            logwin.noutrefresh()
            curses.doupdate()
            serv.send("OK".encode())
            size = int(serv.recv(256).decode())
            logwin.addstr(f"Tamaño en bytes: {size}\n")
            logwin.noutrefresh()
            curses.doupdate()
            cont = b''
            serv.send("OK".encode())
            while size != len(cont):
                cont += serv.recv(1024)
            serv.send("OK".encode())
            fpath = serv.recv(256).decode()
            F = open(fpath, 'wb+')
            F.write(cont)
            F.close()
            logwin.addstr(f"Archivo '{fpath}' obtenido\n")
            logwin.noutrefresh()
            curses.doupdate()
        elif data[0] == "recv":
            serv.send(b"OK") #recv
            fpath = serv.recv(256).decode() # send remotepath
            serv.send(b"OK")
            logwin.addstr(f"Enviando archivo {fpath}...\n") # send
            logwin.noutrefresh()
            curses.doupdate()
            F = open(fpath, 'rb')
            cont = F.read()
            size = len(cont)
            F.close()
            #enviar size
            logwin.addstr(f"Tamaño en bytes: {size}\n")
            logwin.noutrefresh()
            curses.doupdate()
            serv.send(str(size).encode())
            serv.recv(4) #OK
            serv.sendall(cont)
            serv.recv(4)
            logwin.addstr(f"Archivo '{fpath}' enviado\n")
            logwin.noutrefresh()
            curses.doupdate()
        elif data[0] == "debug":
            data = data[1:]
            s = ""
            for i in data:
                s += i +' '
            s += '\n'
            logwin.addstr(f"DEBUG: {s}")
            logwin.noutrefresh()
            curses.doupdate()
    if serv: serv.close()
    sock.close()
    logwin.addstr('Sesión terminada. Pulse una tecla para continuar...\n')
    logwin.noutrefresh()
    curses.doupdate()
    stop[0] = 2

def server(stdscr):
    stdscr.move(0,0);stdscr.clrtobot()
    caps = stdscr.getmaxyx()
    win = curses.newwin(12,55,caps[0]//2-6,caps[1]//2-27)
    wcaps = win.getmaxyx()
    win.bkgd(' ', curses.color_pair(2))
    refresh(stdscr,win)
    bar = Bar(win,0,0,1)
    bar.align('center', Label(win,str="Server-side"))
    bar.draw()
    win.addstr(wcaps[0]-1,1,"ESC",curses.color_pair(1))
    win.addstr(wcaps[0]-1,5,"Volver",curses.color_pair(2))
    win.refresh()
    logwin = win.derwin(9,53,2,1)
    logwin.keypad(1)
    logwin.scrollok(1)
    logwin.bkgd(' ',curses.color_pair(3))
    logwin.refresh()
    stop = [0]
    thread = Thread(target=srvtarget, args=(logwin,stop))
    thread.start()
    while True:
        ch = win.getch()
        if stop[0] == 2: return 1
        if ch == 27:
            logwin.addstr('Esperando señal del thread..\n')
            stop[0] = 1
            while stop[0] != 2:
                sleep(1)
            logwin.getch()
            return 1
        continue


def remotesel(stdscr,sock,onlydir=False):
    stdscr.move(0,0);stdscr.clrtobot()
    caps = stdscr.getmaxyx()
    win = curses.newwin(12,55,caps[0]//2-6,caps[1]//2-27)
    wcaps = win.getmaxyx()
    win.bkgd(' ', curses.color_pair(2))
    refresh(stdscr,win)
    bar = Bar(win,0,0,1)
    bar.align('center', Label(win,str="Selección remota"))
    bar.draw()
    win.addstr(wcaps[0]-1,1,"ESC",curses.color_pair(1))
    win.addstr(wcaps[0]-1,5,"Volver",curses.color_pair(2))
    win.addstr(1,0,"ncRead space")
    win.refresh()
    mcaps = (9,53,2,1)
    sock.send(b"home")
    Path = sock.recv(256).decode().split('/')[1:]
    Pathrep = topath(Path)
    sock.sendall(f"ls {Pathrep}".encode())
    ls_size = int(sock.recv(16).decode())
    sock.send("OK".encode())
    ls = loads(sock.recv(ls_size).decode())
    special = {".": lambda: '.', "..": lambda: '..'}
    opts = special.copy()
    for i in ls:
        f = i
        if ls[i]: f+='/'
        opts[f] = genvlambda(i)
    while True:
        res = menu(win,mcaps,opts,defwrite,colors=(3,1))
        if (res):
            stdscr.move(0,0);stdscr.clrtobot()
            stdscr.refresh()
            win.touchwin()
            win.refresh()
            cleanlines(win,mcaps)
            if res == '.': return topath(Path)
            elif res == '..' and Path: Path.pop()
            elif ls[res]:
                Path.append(res)
            else:
                if onlydir: continue
                Path.append(res)
                return topath(Path)
            opts = special.copy()
            Pathrep = topath(Path)
            sock.sendall(f"ls {Pathrep}/".encode())
            ls_size = int(sock.recv(16).decode())
            sock.send("OK".encode())
            ls = loads(sock.recv(ls_size).decode())
            for i in ls:
                f = i
                if ls[i]: f+='/'
                opts[f] = genvlambda(i)
            continue
        else: return 0

def localselect(stdscr,sock,onlydir=False):
    stdscr.move(0,0);stdscr.clrtobot()
    caps = stdscr.getmaxyx()
    win = curses.newwin(12,55,caps[0]//2-6,caps[1]//2-27)
    wcaps = win.getmaxyx()
    win.bkgd(' ', curses.color_pair(2))
    refresh(stdscr,win)
    bar = Bar(win,0,0,1)
    bar.align('center', Label(win,str="Selección local"))
    bar.draw()
    win.addstr(wcaps[0]-1,1,"ESC",curses.color_pair(1))
    win.addstr(wcaps[0]-1,5,"Volver",curses.color_pair(2))
    win.addstr(1,0,"ncRead space")
    win.refresh()
    mcaps = (9,53,2,1)
    Path = getenv("HOME").split('/')[1:]
    Pathrep = topath(Path)
    ls = listdir(Pathrep)
    special = {'.': lambda: '.', '..': lambda: '..'}
    opts = special.copy()
    for i in ls:
        f = i
        if path.isdir(f'{Pathrep}/{i}'): f+='/'
        opts[f] = genvlambda(i)
    while True:
        res = menu(win,mcaps,opts,defwrite,colors=(3,1))
        if (res):
            stdscr.move(0,0);stdscr.clrtobot()
            stdscr.refresh()
            win.touchwin()
            win.refresh()
            cleanlines(win,mcaps)
            if res == '.': return topath(Path)
            elif res == '..' and Path: Path.pop()
            elif path.isdir(topath(Path)+'/'+res):
                Path.append(res)
            else:
                if onlydir: continue
                Path.append(res)
                return topath(Path)
            opts = special.copy()
            Pathrep = topath(Path)
            for i in listdir(topath(Path)):
                f = i
                if path.isdir(f'{Pathrep}/{i}'): f+='/'
                opts[f] = genvlambda(i)
            continue
        else: return 0

def enviar(stdscr, win, sock):
    source = localselect(stdscr, sock)
    if not source: return 1
    stdscr.move(0,0);stdscr.clrtobot()
    stdscr.refresh()
    win.refresh()
    dest = remotesel(stdscr, sock, onlydir=True)
    if not dest: return 1
    stdscr.move(0,0);stdscr.clrtobot()
    stdscr.refresh()
    win.refresh()
    # enviar archivo
    lfile = open(source, 'rb')
    lfcont = lfile.read()
    sock.send(b"send")
    sock.recv(4)
    sock.send(str(len(lfcont)).encode())
    sock.recv(4)
    sock.sendall(lfcont)
    sock.recv(4)
    sock.sendall((dest+'/'+source.split('/')[-1]).encode())
    return 1

def recibir(stdscr, win, sock):
    source = remotesel(stdscr, sock)
    if not source: return 1
    stdscr.move(0,0);stdscr.clrtobot()
    stdscr.refresh()
    win.refresh()
    dest = localselect(stdscr, sock, onlydir=True)
    if not dest: return 1
    stdscr.move(0,0);stdscr.clrtobot()
    stdscr.refresh()
    win.refresh()
    # recibir archivo
    sock.send(b"recv")
    sock.recv(4)
    sock.send(source.encode())
    sock.recv(4)
    size = int(sock.recv(1024).decode())
    sock.send(b"OK")
    cont = b''
    while size != len(cont):
        cont += sock.recv(1024)
    sock.send(b"OK")
    file = open(dest+'/'+source.split('/')[-1], 'wb+')
    file.write(cont)
    file.close()
    return 1

def client(stdscr):
    stdscr.move(0,0);stdscr.clrtobot()
    caps=stdscr.getmaxyx()
    win = curses.newwin(8,50,caps[0]//2-4,caps[1]//2-25)
    win.keypad(1)
    win.bkgd(' ',curses.color_pair(2))
    wcaps = win.getmaxyx()
    refresh(win)
    bar = Bar(win,0,0,1)
    bar.align('center', Label(win,str="Client-side"))
    bar.draw()
    win.addstr(wcaps[0]//2,0,"Dirección IP: ")
    refresh(win)
    ip=ampsread(win,wcaps[0]//2,14,15,15)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((ip,3332))
    except Exception:
        exit(0)
    opts = {"Enviar": lambda: enviar(stdscr,win,sock),
            "Recibir": lambda: recibir(stdscr,win,sock),
            "Volver": lambda: 0}
    win.move(1,0);win.clrtobot()
    win.refresh()
    mcaps = (3,20,4,wcaps[1]//2-4)
    while True:
        if (menu(win,mcaps,opts,defwrite,colors=(2,1))):
            stdscr.move(0,0);stdscr.clrtobot()
            stdscr.refresh()
            win.touchwin()
            win.refresh()
            continue
        else: return 1
def main(stdscr):
    curses.curs_set(0)
    curses.use_default_colors()
    curses.init_pair(1,0,15)
    curses.init_pair(2,15,27)
    curses.init_pair(3,15,20)
    curses.init_pair(4,15,160)
    caps = stdscr.getmaxyx()
    win = curses.newwin(8,50,caps[0]//2-4,caps[1]//2-25)
    win.keypad(1)
    wcaps = win.getmaxyx()
    win.bkgd(' ', curses.color_pair(2))
    refresh(stdscr,win)
    bar = Bar(win,0,0,1)
    bar.align('center', Label(win,str='Erika File Transfer'))
    bar.draw()
    win.addstr(2,wcaps[1]//2-6, "Elige un modo")
    refresh(win)
    opts = {"Cliente": lambda: client(stdscr),
            "Servidor": lambda: server(stdscr),
            "Salir": exit}
    mcaps = (3,20,4,wcaps[1]//2-4)
    while True:
        if (menu(win,mcaps,opts,defwrite,colors=(2,1))):
            stdscr.move(0,0);stdscr.clrtobot()
            stdscr.refresh()
            win.touchwin()
            win.refresh()
            continue
        else: break

if __name__=='__main__':
    curses.wrapper(main)
