# coding=utf-8
"""

LDN  constantă/referință - încarcă registrul N cu o constantă (ex. LDN 3 încarcă 3 în N) sau cu o valoare din memoria dronei de la
     adresa specificată (ex LDN [3] încarcă în N valoarea din memorie de la adresa 3).

STA  referință/reg - stochează valoarea din registrul A în memoria dronei la adresa ref (ex. STA [3] stochează valoarea
     registrului A în memorie la adresa 3) sau la adresa specificată de registrul N (ex. LDN 3 urmata de STA [N] va stoca valoarea
     registrului A în memorie la adresa 3)

LDA  constantă/referință/reg - încarcă în registrul A valoarea unei constante (ex. LDA 5 încarcă 5 în A) sau valoarea din memoria
     dronei de la adresa referință/reg (ex. LDA [6] încarcă în A valoarea memoriei de la adresa 6 iar LDA [N] încarcă în A valoarea
     memoriei pointata de N)

ADDA constantă/referință - sumează valoarea registrului A cu o constantă (ex. ADDA 3 aduna 3 la valoare din registrul A) sau cu
     valoarea din memoria dronei de la adresa referință (ex. ADDA [4] adaugă la A valoarea memoriei de la adresa 4).

SUBA constantă/referință - scade valoarea registrului A cu o constantă (ex. SUBA 3 scade 3 din valoarea registrului A) sau cu
     valoarea din memoria dronei de la adresa referință (ex. SUBA [7] scade din valoarea registrului A valoarea memoriei de la adresa 7).

JGE  constantă/referință – continua execuția programului cu linia din program specificată de const/ref dacă valoarea registrului A este
     mai mare sau egală cu 0 (ex. JGE 8 sare la linia 8; JGE [2] sare la linia specificată de valoarea din memorie de la adresa 2).

HLT  termină ciclul curent de execuție

Limite:
    Rows, Cols <= 50
    NR_OBSTACOLE < (R x C) / 2
    NR_CETATENI <= 50
    NR_DRONE <= 50
    Se poate face upload la o soluție per hartă o dată la 10 secunde.
    Nu pot exista mai mult de 10 000 de soluții per hartă.

Configurație hartă:
Harta este disponibilă începând cu adresa 1 din memoria dronei. La fiecare pas harta este actualizată cu noile obiecte de pe hartă,
deci harta poate să ocupe mai mult sau mai puțină memorie de la pas la pas dacă apar sau dispar obiecte de pe ea (drone
sau cetățeni). Maximul pe care poate să îl ocupe harta în memorie este determinat de câte obstacole sunt pe hartă și câți cetățeni
și drone pot exista pe hartă la un moment dat (Vezi limitele problemei).

Structura:
    Rows, Cols:     dimensiunile hărții, nu se schimbă
    X, Y:           coordonatele curente ale dronei
    Tx, Ty:         coordonatele target-ului (nu se schimbă de-a lungul simulării)
    NR_OBSTACOLE,   urmează 2 x NR_OBSTACOLE cu coordonatele lor (nu se schimbă de-a lungul simulării)
    NR_CETATENI,    urmează 2 x NR_CETATENI cu coordonatele lor
    NR_DRONE,       urmează 2 x NR_DRONE celule cu coordonatele lor

[1]              ROWS
[2]              COLS
[3]              x
[4]              y
[5]              Tx
[6]              Ty
[7]              No
[8] - [&Nc]      2xNo of < x,y> obstacole (&Nc = 8 + No + No)
[&Nc]            Nc
[&Nc+1] - [&Nd]  2xNc of < x,y> cetateni (&Nd = &Nc + 1 + Nc + Nc
[&Nd]            Nd
[&Nd+1] - [END]  2xNd of < x,y> drone

Memoria program:
[2900]  - jump offset

"""

from DroneAssembley import *
from DroneSimulator import *

# [2900] - [3000] - rezervata pentru asamblor

def main():
    program = [
        SYM("UP",        "1"),
        SYM("RIGHT",     "2"),
        SYM("DOWN",      "3"),
        SYM("LEFT",      "4"),
        SYM("HOLD",      "0"),
        SYM("costs_adr", "4000"),

        SYM("r",         "[1]"),
        SYM("c",         "[2]"),
        SYM("x",         "[3]"),
        SYM("y",         "[4]"),
        SYM("tx",        "[5]"),
        SYM("ty",        "[6]"),
        SYM("numobs",    "[7]"),
        SYM("ptr",       "[3000]"),
        SYM("offset",    "[3001]"),
        SYM("maxrow",    "[3002]"),
        SYM("maxobs",    "[3003]"),
        SYM("i",         "[3004]"),
        SYM("xi",        "[3005]"),
        SYM("yi",        "[3006]"),
        SYM("cost",      "[3007]"),

        START("INIT"),

        LABEL("INIT"),
        LETSUB("maxrow", "r", "1"),
        LETADD("offset", "costs_adr", "r"),

        LABEL("INIT LOOP"),
            LETADD("ptr", "costs_adr", "i"),
            LETPTR("ptr","offset"),
            INC("offset", "c"),
            INC("i", "1"),
        IFLESS("maxrow", "i","INIT LOOP"),

        LET("i", "0"),
        LETSUB("maxobs", "numobs", "1"),

        LABEL("INIT LOOP2"),
            LETADD("ptr", "8", "i"),
            INC("ptr", "i"),
            GETPTR("xi", "ptr"),

            INC("ptr", "1"),
            GETPTR("yi", "ptr"),

            LETADD("ptr", "costs_adr", "yi"),
            GETPTR("ptr", "ptr"),
            INC("ptr", "xi"),
            LETPTR("ptr", "-1"),

            INC("i", "1"),
        IFLESS("maxobs", "i", "INIT LOOP2"),

        LABEL("SWITCH TO X"),
        CHANGE_START("MOVE X"),

        LABEL("MOVE X"),
        IFLESS("tx", "x", "TX GE X"),
            LETSUB("xi", "x", "1"),
            LETADD("ptr", "costs_adr", "y"),
            GETPTR("ptr", "ptr"),
            INC("ptr", "xi"),
            GETPTR("cost", "ptr"),
            IFLESS("-1", "cost", "SWITCH TO Y"),
                MOVE_HLT("LEFT"),

        LABEL("TX GE X"),
        IFLESS("x", "tx", "SWITCH TO Y"),
            LETADD("xi", "x", "1"),
            LETADD("ptr", "costs_adr", "y"),
            GETPTR("ptr", "ptr"),
            INC("ptr", "xi"),
            GETPTR("cost", "ptr"),
            IFLESS("-1", "cost", "SWITCH TO Y"),
                MOVE_HLT("RIGHT"),

        LABEL("SWITCH TO Y"),
        CHANGE_START("MOVE Y"),

        LABEL("MOVE Y"),
        IFLESS("ty", "y", "TY GE Y"),
            LETSUB("yi", "y", "1"),
            LETADD("ptr", "costs_adr", "yi"),
            GETPTR("ptr", "ptr"),
            INC("ptr", "x"),
            GETPTR("cost", "ptr"),
            IFLESS("-1", "cost", "SWITCH TO X"),
                MOVE_HLT("UP"),

        LABEL("TY GE Y"),
        IFLESS("y", "ty", "SWITCH TO X"),
            LETADD("yi", "y", "1"),
            LETADD("ptr", "costs_adr", "yi"),
            GETPTR("ptr", "ptr"),
            INC("ptr", "x"),
            GETPTR("cost", "ptr"),
            IFLESS("-1", "cost", "SWITCH TO X"),
                MOVE_HLT("DOWN")
    ]

    asm = DroneAssembler(program).\
        compile().\
        save('/Users/rodanciv/Documents/07_intoTheDark.txt').\
        assembly

    dronemem = DroneMemory('/Users/rodanciv/Documents/01_letsGetToKnowEachOther.txt')
    sim = DroneSimulator(asm)
    while not sim.done:
        sim.memupdate(dronemem.memory)
        sim.step()
        print "x: " + str(sim.drone_x) + ", y: " + str(sim.drone_y)
#        dronemem.refresh()

    print sim.status

if __name__ == "__main__":
    main()