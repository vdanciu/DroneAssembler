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

class GetCostPointer(MACRO):
    def __init__(self, ptr, x, y):
        self.ptr = ptr
        self.x = x
        self.y = y
        
    def expand(self):
        return [
            COMMENT(str(self)),
            LETADD(self.ptr, "COSTS_ADR", self.y),
            INC(self.ptr, "1"),
            GETPTR(self.ptr, self.ptr),
            INC(self.ptr, self.x),
            INC(self.ptr, "1")
        ]
    
    def __str__(self):
        return "GetCostPointer in " + str(self.ptr) + " for x:" + str(self.x) + ", y:" + str(self.y)

class GetCostPointerNeighbor(MACRO):
    UP = 1
    RIGHT = 2
    DOWN = 3
    LEFT = 4

    def __init__(self, left, right, direction):
        self.left = left
        self.right = right
        self.dir = direction

    def expand(self):
        offset = {
            GetCostPointerNeighbor.DOWN : "fence_c",
            GetCostPointerNeighbor.LEFT : "-1",
            GetCostPointerNeighbor.RIGHT : "1"
            }
        if self.dir == GetCostPointerNeighbor.UP:
            instr = LETSUB(self.left, self.right, "fence_c")
        else:
            instr = LETADD(self.left, self.right, offset[self.dir])

        return [
            COMMENT(str(self)),
            instr
        ]

    def __str__(self):
        return "GetCostPointerNeighbor: " + str(self.left) + " for " + str(self.right) + " direction=" + str(self.dir)

class GetBestCost(MACRO):
    code = 0

    def __init__(self, left, cost, newcost):
        self.left = left
        self.cost = cost
        self.newcost = newcost

    def expand(self):
        GetBestCost.code += 1
        labelmin = "BEST COST " + str(GetBestCost.code)
        labelend = "BEST COST END " + str(GetBestCost.code)
        labelold = "BEST COST OLD " + str(GetBestCost.code)
        return [
            LDA(self.newcost),
            JGE(labelmin),
                LABEL(labelold),
                LDA(self.cost),
                JGE(labelend),

            LABEL(labelmin),
            LDA(self.newcost),
            SUBA(self.cost),
            JGE(labelold),
                LDA(self.newcost),

            LABEL(labelend),
            STA(self.left),
        ]

    def __str__(self):
        return "MaxPositive " + str(self.left) + " = " + \
               str(self.cost) + " if " + str(self.newcost) + " < 0, otherwise min of the two"

def main():
    program = [
        SYM("UP",        "1"),
        SYM("RIGHT",     "2"),
        SYM("DOWN",      "3"),
        SYM("LEFT",      "4"),
        SYM("HOLD",      "0"),
        SYM("COSTS_ADR", "4000"),

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
        SYM("maxcol",    "[3003]"),
        SYM("maxobs",    "[3004]"),
        SYM("i",         "[3005]"),
        SYM("xi",        "[3006]"),
        SYM("yi",        "[3007]"),
        SYM("cost",      "[3008]"),
        SYM("tmp",       "[3009]"),
        SYM("fence_r",   "[3010]"),
        SYM("fence_c",   "[3011]"),
        SYM("fmaxrow",   "[3012]"),
        SYM("fmaxcol",   "[3013]"),
        SYM("move",      "[3014]"),
        SYM("ncost",     "[3015]"),

        START("INIT"),

        LABEL("INIT"),
        LETSUB("maxrow",  "r", "1"),
        LETSUB("maxcol",  "r", "1"),
        LETADD("fence_r", "r", "2"),
        LETADD("fence_c", "r", "2"),
        LETADD("fmaxrow", "r", "1"),
        LETADD("fmaxcol", "r", "1"),
        LETSUB("maxobs",  "numobs", "1"),

        LETADD("offset", "COSTS_ADR", "fence_r"),

        LET("i", "0"),
        LABEL("INIT LOOP COSTS"),
            LETADD("ptr", "COSTS_ADR", "i"),
            LETPTR("ptr","offset"),

            COMMENT("mark the first and the last elements as -1 to mark the fence"),
            LETPTR("offset", "-1"),
            LETADD("tmp", "offset", "fmaxcol"),
            LETPTR("tmp", "-1"),

            INC("offset", "fence_c"),
            INC("i", "1"),
        IFLESS("fmaxrow", "i", "INIT LOOP COSTS"),

        COMMENT("Mark the first and the last row with -1 for the fence"),
        LET("i", "0"),
        LET("ptr","COSTS_ADR"),
        GETPTR("ptr", "ptr"),
        LET("tmp", "COSTS_ADR"),
        INC("tmp", "fmaxrow"),
        GETPTR("tmp", "tmp"),
        LABEL("INIT LOOP MARK FENCE"),
            LETPTR("ptr", "-1"),
            LETPTR("tmp", "-1"),
            INC("ptr", "1"),
            INC("tmp", "1"),
            INC("i", "1"),
        IFLESS("fmaxcol", "i", "INIT LOOP MARK FENCE"),


        LET("yi", "0"),
        LABEL("INIT LOOP DIST COSTS Y"),
            LET("xi", "0"),
            LABEL("INIT LOOP DIST COSTS X"),
                # cost = abs(tx - xi) + abs(ty - yi)
                LETSUB("cost", "tx", "xi"),
                ABS("cost", "cost"),
                LETSUB("tmp", "ty", "yi"),
                ABS("tmp", "tmp"),
                LETADD("cost", "cost", "tmp"),
                GetCostPointer("ptr", "xi", "yi"),
                LETPTR("ptr", "cost"),
                INC("xi", "1"),
            IFLESS("maxcol", "xi", "INIT LOOP DIST COSTS X"),
            INC("yi", "1"),
        IFLESS("maxrow", "yi", "INIT LOOP DIST COSTS Y"),

        LET("i", "0"),
        LABEL("INIT LOOP OBST"),
            LETADD("ptr", "8", "i"),
            INC("ptr", "i"),
            GETPTR("xi", "ptr"),

            INC("ptr", "1"),
            GETPTR("yi", "ptr"),
            GetCostPointer("ptr", "xi", "yi"),
            LETPTR("ptr", "-2"),

            INC("i", "1"),
        IFLESS("maxobs", "i", "INIT LOOP OBST"),

        LABEL ("MOVE"),
        CHANGE_START("MOVE"),
        GetCostPointer("ptr", "x", "y"),
        GETPTR("cost", "ptr"),

        LET("move", "0"),
        LET("cost", "999999"),
        GetCostPointerNeighbor("tmp", "ptr", GetCostPointerNeighbor.RIGHT),
        GETPTR("ncost", "tmp"),
        GetBestCost("ncost", "cost", "ncost"),
        IFLESS("ncost", "cost", "MOVE DOWN"),
            LET("cost", "ncost"),
            LET("move", "2"),

        LABEL("MOVE DOWN"),
        GetCostPointerNeighbor("tmp", "ptr", GetCostPointerNeighbor.DOWN),
        GETPTR("ncost", "tmp"),
        GetBestCost("ncost", "cost", "ncost"),
        IFLESS("ncost", "cost", "MOVE LEFT"),
            LET("cost", "ncost"),
            LET("move", "3"),

        LABEL("MOVE LEFT"),
        GetCostPointerNeighbor("tmp", "ptr", GetCostPointerNeighbor.LEFT),
        GETPTR("ncost", "tmp"),
        GetBestCost("ncost", "cost", "ncost"),
        IFLESS("ncost", "cost", "MOVE UP"),
            LET("cost", "ncost"),
            LET("move", "4"),

        LABEL("MOVE UP"),
        GetCostPointerNeighbor("tmp", "ptr", GetCostPointerNeighbor.UP),
        GETPTR("ncost", "tmp"),
        GetBestCost("ncost", "cost", "ncost"),
        IFLESS("ncost", "cost", "MAKE MOVE"),
            LET("cost", "ncost"),
            LET("move", "1"),

        LABEL("MAKE MOVE"),
        IFLESS("0", "move", "MOVE AND HALT"),
            GETPTR("cost", "ptr"),
            INC("cost", "5"),
            LETPTR("ptr", "cost"),
        LABEL("MOVE AND HALT"),
        MOVE_HLT("move"),
    ]

    asm = DroneAssembler(program).\
        compile().\
        spit().\
        save('/Users/rodanciv/Documents/04_gottaCircleAround_auto.txt').\
        assembly

    dronemem = DroneMemory('/Users/rodanciv/Documents/04_gottaCircleAround.txt')
    sim = DroneSimulator(asm)
    while not sim.done:
        sim.memupdate(dronemem.memory)
        sim.step()
        print "x: " + str(sim.drone_x) + ", y: " + str(sim.drone_y)
#        dronemem.refresh()

    print sim.status
    print "score: " + str(sim.getscore(4))


if __name__ == "__main__":
    main()