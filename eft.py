#!/usr/bin/env python3
import curses
import socket
from os import getenv, path, mkdir, listdir
from json import loads, dumps
from modules.ncRead import ampsread
from modules.menu import menu

def refresh(a,b=None):
    a.refresh()
    if b: b.refresh()

def line(win, y, mx):
    r = mx-0
    win.addstr(y,0,' '*r, curses.color_pair(1))
    refresh(win)

def server(win,ow):
    del ow
    win.touchwin()
    refresh(win)
    win_caps = win.getmaxyx()
    win1 = curses.newwin(12,55, win_caps[0]//2-6, win_caps[1]//2-27)
    win1_caps = win1.getmaxyx()
    win1.bkgd(' ', curses.color_pair(2))
    win1.scrollok(1)
    refresh(win,win1)
    line(win1, 0, win1_caps[1])
    refresh(win1)
    title = "Erika File Transfer"
    win1.addstr(0,win1_caps[1]//2-len(title)//2,title,curses.color_pair(1))
    s1 = "Server"
    win1.addstr(1,win1_caps[1]//2-len(s1)//2, s1)
    refresh(win1)
    win2 = curses.newwin(win1_caps[0]-3,win1_caps[1]-2, (win_caps[0]//2-6)+2, (win_caps[1]//2-27)+1)
    win2.bkgd(' ', curses.color_pair(3))
    win2.scrollok(1)
    refresh(win1,win2)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    win2.addstr("Socket creado\n")
    refresh(win2)
    sock.bind((0.0.0.0, 3332))
    win2.addstr(f"Socket escuchando en puerto 3332\n")
    refresh(win2)
    sock.listen()
    win2.addstr(f"Esperando conexiones...\n")
    refresh(win2)
    serv,add = sock.accept()
    win2.addstr(f"{add[0]} se ha conectado\n")
    refresh(win2)
    while True:
        data = serv.recv(1024).decode()
        if not data:
            win2.addstr("El cliente se ha desconectado. Sesión terminada\n")
            refresh(win2)
            serv.close()
            sock.close()
            break
        win2.addstr(f"Se ha recibido: {data}\n")
        refresh(win2)
        data = data.split()
        if data[0] == "home":
            serv.sendall((getenv("HOME")+'/').encode())
        elif data[0] == "ls":
            if len(data) == 1:
                PWD = getenv("HOME")+'/'
            else:
                PWD = data[1]
            ls = listdir(PWD)
            dls = {}
            for i in ls:
                dls[i] = path.isdir(PWD+i)
            ls = dumps(dls)
            serv.send(str(len(ls)).encode())
            serv.recv(4)
            serv.sendall(ls.encode())
        elif data[0] == "send":
            win2.addstr("Obteniendo archivo...\n")
            refresh(win2)
            serv.send("OK".encode())
            size = int(serv.recv(256).decode())
            win2.addstr(f"Tamaño en bytes: {size}\n")
            refresh(win2)
            cont = b''
            serv.send("OK".encode())
            while size != len(cont):
                cont += serv.recv(1024)
            serv.send("OK".encode())
            fpath = serv.recv(256).decode()
            F = open(fpath, 'wb+')
            F.write(cont)
            F.close()
            win2.addstr(f"Archivo '{fpath}' obtenido\n")
            refresh(win2)
        elif data[0] == "recv":
            serv.send(b"OK") #recv
            fpath = serv.recv(256).decode() # send remotepath
            serv.send(b"OK")
            win2.addstr(f"Enviando archivo {fpath}...\n") # send
            refresh(win2)
            F = open(fpath, 'rb')
            cont = F.read()
            size = len(cont)
            F.close()
            #enviar size
            win2.addstr(f"Tamaño en bytes: {size}\n")
            refresh(win2)
            serv.send(str(size).encode())
            serv.recv(4) #OK
            serv.sendall(cont)
            serv.recv(4)
            win2.addstr(f"Archivo '{fpath}' enviado\n")
            refresh(win2)
        elif data[0] == "debug":
            data = data[1:]
            s = ""
            for i in data:
                s += i +' '
            s += '\n'
            win2.addstr(f"DEBUG: {s}")
            refresh(win)

def remotesel(win2,win2_caps,sock,src=None):
    sock.send(b"home")
    PWD = sock.recv(256).decode()
    sock.sendall(f"ls {PWD}".encode())
    ls_size = int(sock.recv(16).decode())
    sock.send("OK".encode())
    ls = loads(sock.recv(ls_size).decode())
    pair = (list(ls.keys()),list(ls.values()))
    ls = {".": True, "..": True}
    for i in range(len(pair[0])):
        ls[pair[0][i]] = pair[1][i]
    out = list(ls.keys())
    # modify copy from localsel
    for i in range(len(out[0:win2_caps[0]])):
        win2.addstr(i,0,out[0:win2_caps[0]][i])
        refresh(win2)
        if ls[out[0:win2_caps[0]][i]]:
            win2.addstr('/')
            refresh(win2)
    win2.addstr(0,0,out[0],curses.color_pair(1))
    p = 0
    e = 0
    sc = 0
    while True:
        k = win2.getch()
        if k == curses.KEY_UP:
            if not p:
                if not e:
                    continue
                win2.addstr(p,0,out[sc:win2_caps[0]+sc][p])
                if ls[out[sc:win2_caps[0]+sc][p]]:
                    win2.addstr('/')
                win2.scroll(-1)
                refresh(win2)
                sc -= 1; e -= 1
                win2.addstr(p,0,out[sc:win2_caps[0]+sc][p],curses.color_pair(1))
                if ls[out[sc:win2_caps[0]+sc][p]]:
                    win2.addstr('/',curses.color_pair(1))
                refresh(win2)
                continue
            win2.addstr(p,0,out[sc:win2_caps[0]+sc][p])
            if ls[out[sc:win2_caps[0]+sc][p]]:
                win2.addstr('/')
            p -= 1; e -= 1
            win2.addstr(p,0,out[sc:win2_caps[0]+sc][p],curses.color_pair(1))
            if ls[out[sc:win2_caps[0]+sc][p]]:
                win2.addstr('/',curses.color_pair(1))
            refresh(win2)
        if k == curses.KEY_DOWN:
            if e == len(out)-1:
                continue
            if p == win2_caps[0]-1:
                win2.addstr(p,0,out[sc:win2_caps[0]+sc][p])
                if ls[out[sc:win2_caps[0]+sc][p]]:
                    win2.addstr('/')
                win2.scroll(1)
                refresh(win2)
                sc += 1; e += 1
                win2.addstr(p,0,out[sc:win2_caps[0]+sc][p],curses.color_pair(1))
                if ls[out[sc:win2_caps[0]+sc][p]]:
                    win2.addstr('/',curses.color_pair(1))
                refresh(win2)
                continue
            win2.addstr(p,0,out[sc:win2_caps[0]+sc][p])
            if ls[out[sc:win2_caps[0]+sc][p]]:
                win2.addstr('/')
            p += 1; e += 1
            win2.addstr(p,0,out[sc:win2_caps[0]+sc][p],curses.color_pair(1))
            if ls[out[sc:win2_caps[0]+sc][p]]:
                win2.addstr('/',curses.color_pair(1))
            refresh(win2)
        if k == 10:
            if out[sc:win2_caps[0]+sc][p] == '.':
                if src:
                    return PWD + src.split('/')[-1]
                return PWD
            if not ls[out[sc:win2_caps[0]+sc][p]]:
                return PWD+out[sc:win2_caps[0]+sc][p]
            win2.move(0,0);win2.clrtobot()
            refresh(win2)
            PWD += out[sc:win2_caps[0]+sc][p]+'/'

            sock.sendall(f"ls {PWD}".encode())
            ls_size = int(sock.recv(16).decode())
            sock.send("OK".encode())
            ls = loads(sock.recv(ls_size).decode())
            pair = (list(ls.keys()),list(ls.values()))
            ls = {".": True, "..": True}
            for i in range(len(pair[0])):
                ls[pair[0][i]] = pair[1][i]
            out = list(ls.keys())

            p = 0;sc= 0;e= 0
            for i in range(len(out[0:win2_caps[0]])):
                win2.addstr(i,0,out[0:win2_caps[0]][i])
                refresh(win2)
                if ls[out[0:win2_caps[0]][i]]:
                    win2.addstr('/')
                    refresh(win2)
            win2.addstr(0,0,out[0],curses.color_pair(1))
            if ls[out[0]]:
                win2.addstr('/',curses.color_pair(1))
                refresh(win2)

    # end
    # ended
    # ended

def localsel(win2,win2_caps,src=None):
    PWD = getenv("HOME")+'/'
    out = ['.','..'] + listdir(PWD)
    for i in range(len(out[0:win2_caps[0]])):
        win2.addstr(i,0,out[0:win2_caps[0]][i])
        refresh(win2)
        if path.isdir(PWD+out[0:win2_caps[0]][i]):
            win2.addstr('/')
            refresh(win2)
    win2.addstr(0,0,out[0],curses.color_pair(1))
    p = 0
    e = 0
    sc = 0
    while True:
        k = win2.getch()
        if k == curses.KEY_UP:
            if not p:
                if not e:
                    continue
                win2.addstr(p,0,out[sc:win2_caps[0]+sc][p])
                if path.isdir(PWD+out[sc:win2_caps[0]+sc][p]):
                    win2.addstr('/')
                win2.scroll(-1)
                refresh(win2)
                sc -= 1; e -= 1
                win2.addstr(p,0,out[sc:win2_caps[0]+sc][p],curses.color_pair(1))
                if path.isdir(PWD+out[sc:win2_caps[0]+sc][p]):
                    win2.addstr('/',curses.color_pair(1))
                refresh(win2)
                continue
            win2.addstr(p,0,out[sc:win2_caps[0]+sc][p])
            if path.isdir(PWD+out[sc:win2_caps[0]+sc][p]):
                win2.addstr('/')
            p -= 1; e -= 1
            win2.addstr(p,0,out[sc:win2_caps[0]+sc][p],curses.color_pair(1))
            if path.isdir(PWD+out[sc:win2_caps[0]+sc][p]):
                win2.addstr('/',curses.color_pair(1))
            refresh(win2)
        if k == curses.KEY_DOWN:
            if e == len(out)-1:
                continue
            if p == win2_caps[0]-1:
                win2.addstr(p,0,out[sc:win2_caps[0]+sc][p])
                if path.isdir(PWD+out[sc:win2_caps[0]+sc][p]):
                    win2.addstr('/')
                win2.scroll(1)
                refresh(win2)
                sc += 1; e += 1
                win2.addstr(p,0,out[sc:win2_caps[0]+sc][p],curses.color_pair(1))
                if path.isdir(PWD+out[sc:win2_caps[0]+sc][p]):
                    win2.addstr('/',curses.color_pair(1))
                refresh(win2)
                continue
            win2.addstr(p,0,out[sc:win2_caps[0]+sc][p])
            if path.isdir(PWD+out[sc:win2_caps[0]+sc][p]):
                win2.addstr('/')
            p += 1; e += 1
            win2.addstr(p,0,out[sc:win2_caps[0]+sc][p],curses.color_pair(1))
            if path.isdir(PWD+out[sc:win2_caps[0]+sc][p]):
                win2.addstr('/',curses.color_pair(1))
            refresh(win2)
        if k == 10:
            if out[sc:win2_caps[0]+sc][p] == '.':
                if src:
                    return PWD + src.split('/')[-1]
                return PWD
            if not path.isdir(PWD+out[sc:win2_caps[0]+sc][p]):
                    return PWD+out[sc:win2_caps[0]+sc][p]
            win2.move(0,0);win2.clrtobot()
            refresh(win2)
            PWD += out[sc:win2_caps[0]+sc][p]+'/'
            out = ['.','..'] + listdir(PWD)
            p = 0;sc= 0;e= 0
            for i in range(len(out[0:win2_caps[0]])):
                win2.addstr(i,0,out[0:win2_caps[0]][i])
                refresh(win2)
                if path.isdir(PWD+out[0:win2_caps[0]][i]):
                    win2.addstr('/')
                    refresh(win2)
            win2.addstr(0,0,out[0],curses.color_pair(1))
            if path.isdir(PWD+out[0]):
                win2.addstr('/',curses.color_pair(1))
                refresh(win2)

def enviar(std,win,sock):
    std_caps = std.getmaxyx()
    win1 = curses.newwin(12,55, std_caps[0]//2-6, std_caps[1]//2-27)
    win1_caps = win1.getmaxyx()
    win1.bkgd(' ', curses.color_pair(2))
    refresh(std,win1)
    line(win1, 0, win1_caps[1])
    refresh(win1)
    title = "Erika File Transfer"
    win1.addstr(0,win1_caps[1]//2-len(title)//2,title,curses.color_pair(1))
    s1 = "Selecciona el archivo para enviar"
    win1.addstr(1,win1_caps[1]//2-len(s1)//2,s1)
    refresh(win1)
    win2 = curses.newwin(win1_caps[0]-3,win1_caps[1]-2, (std_caps[0]//2-6)+2, (std_caps[1]//2-27)+1)
    win2_caps = win2.getmaxyx()
    win2.bkgd(' ', curses.color_pair(3))
    win2.keypad(1)
    win2.scrollok(1)
    refresh(std,win2)
    src = localsel(win2,win2_caps)
    win1.move(1,0);win1.clrtoeol()
    s1 = "Selecciona la ruta de destino"
    win1.addstr(1,win1_caps[1]//2-len(s1)//2,s1)
    refresh(win1)
    #specialinter
    #end
    win2.move(0,0);win2.clrtobot()
    refresh(win2)
    dest = remotesel(win2,win2_caps,sock,src)
    src_fd = open(src, 'rb')
    src_fcnt = src_fd.read()
    sock.send(b"send")
    sock.recv(4)
    sock.send(str(len(src_fcnt)).encode())
    sock.recv(4)
    sock.sendall(src_fcnt)
    sock.recv(4)
    sock.sendall(dest.encode())
    del win2
    win1.touchwin()
    win1.move(1,0);win1.clrtoeol()
    refresh(win1)

def recibir(std,win,sock):
    std_caps = std.getmaxyx()
    win1 = curses.newwin(12,55, std_caps[0]//2-6, std_caps[1]//2-27)
    win1_caps = win1.getmaxyx()
    win1.bkgd(' ', curses.color_pair(2))
    refresh(std,win1)
    line(win1, 0, win1_caps[1])
    refresh(win1)
    title = "Erika File Transfer"
    win1.addstr(0,win1_caps[1]//2-len(title)//2,title,curses.color_pair(1))
    s1 = "Selecciona el archivo a descargar"
    win1.addstr(1,win1_caps[1]//2-len(s1)//2,s1)
    refresh(win1)
    win2 = curses.newwin(win1_caps[0]-3,win1_caps[1]-2, (std_caps[0]//2-6)+2, (std_caps[1]//2-27)+1)
    win2_caps = win2.getmaxyx()
    win2.bkgd(' ', curses.color_pair(3))
    win2.keypad(1)
    win2.scrollok(1)
    refresh(std,win2)
    src = remotesel(win2,win2_caps,sock)
    win1.move(1,0);win1.clrtoeol()
    s1 = "Selecciona la ruta de destino"
    win1.addstr(1,win1_caps[1]//2-len(s1)//2,s1)
    refresh(win1)
    #specialinter
    #end
    win2.move(0,0);win2.clrtobot()
    refresh(win2)
    dest = localsel(win2,win2_caps,src)
    dest_fd = open(dest, 'wb+')
    # DESDE ACÁ
    sock.send(b"recv")
    sock.recv(4)
    sock.send(src.encode())
    sock.recv(4)
    size = int(sock.recv(1024).decode())
    sock.send(b"OK")
    cont = b''
    while size != len(cont):
        cont += sock.recv(1024)
    sock.send(b"OK")
    dest_fd.write(cont)
    dest_fd.close()
    # HASTA ACÁ
    del win2
    win1.touchwin()
    win1.move(1,0);win1.clrtoeol()
    refresh(win1)

def client(std,win1):
    win1.keypad(1)
    win1.move(1,0);win1.clrtobot()
    win1_caps = win1.getmaxyx()
    refresh(win1)
    win1.addstr(win1_caps[0]//2,0,"Dirección IP: ")
    refresh(win1)
    ip=ampsread(win1,win1_caps[0]//2,14,15,15)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((ip,3332))
    except Exception:
        exit(0)
    fundict = {"Enviar": lambda: enviar(std,win1,sock),
            "Recibir": lambda: recibir(std,win1,sock),
            "Salir": exit}
    win1.attron(curses.color_pair(2))
    while True:
        win1.move(1,0);win1.clrtobot()
        refresh(win1)
        menu(win1, 3, win1_caps[1]//2-len("Recibir")//2, fundict)

def main(stdscr):
    curses.curs_set(0)
    curses.use_default_colors()
    curses.init_pair(1,0,15)
    curses.init_pair(2,15,27)
    curses.init_pair(3,15,20)
    y,x = stdscr.getmaxyx()
    win1 = curses.newwin(8,50, y//2-4,x//2-25)
    win1.keypad(1)
    win1_caps = win1.getmaxyx()
    win1.bkgd(' ', curses.color_pair(2))
    refresh(stdscr,win1)
    line(win1,0,win1_caps[1])
    refresh(win1)
    title = "Erika File Transfer"
    win1.addstr(0,win1_caps[1]//2-len(title)//2,title,curses.color_pair(1))
    refresh(win1)
    s1 = "Elige un modo"
    win1.addstr(2,win1_caps[1]//2-len(s1)//2, s1)
    refresh(win1)
    fundict = {"Cliente": lambda: client(stdscr,win1),
            "Servidor": lambda: server(stdscr,win1),
            "Salir": exit}
    menu(win1, 4,win1_caps[1]//2-len("servidor")//2, fundict)
    stdscr.getch()

if __name__=='__main__':
    curses.wrapper(main)
