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

class CONSTANTS:
    BLOW0 = "499"
    BLOW1 = "498"
    BLOW2 = "497"
    BLOW3 = "496"
    PENEDGE0 = "0"
    PENEDGE1 = "0"
    PENEDGE2 = "0"
    PENTHRS0 = "10"
    PENTHRS1 = "12"
    PENTHRS2 = "14"
    BFSSKIPS = "0"


class Labeler():
    code = 0
    def __init__(self, labelroot):
        Labeler.code += 1
        self.label = labelroot + str(Labeler.code)

    def __str__(self):
        return self.label

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

class AssignCost(MACRO):
    code = 0

    def __init__(self, direction):
        self.direction = direction

    def expand(self):
        AssignCost.code += 1
        labelend = "ASSIGNCOSTEND-" + str(AssignCost.code)
        return [
            GetCostPointerNeighbor("tmp", "ptr", self.direction),
            GETPTR("cost", "tmp"),
            IFEQ("cost", "0", labelend),
                LETPTR("tmp", "ncost"),
                Push("endq", "tmp"),
            LABEL(labelend)
        ]

    def __str__(self):
        return "AssignCost direction: " + str(self.direction)

class Push(MACRO):
    def __init__(self, qptr, cptr):
        self.qptr = qptr
        self.cptr = cptr


    def expand(self):
        return [
            COMMENT(str(self)),
            LETPTR(self.qptr, self.cptr),
            INC(self.qptr, "1"),
        ]

    def __str__(self):
        return "Push in " + str(self.qptr) + " address:" + str(self.cptr)

class Pop(MACRO):
    def __init__(self, qptr, cptr):
        self.qptr = qptr
        self.cptr = cptr

    def expand(self):
        return [
            COMMENT(str(self)),
            GETPTR(self.cptr, self.qptr),
            INC(self.qptr, "1"),

        ]

    def __str__(self):
        return "Pop from " + str(self.qptr) + " in:" + str(self.cptr)


class FillArea(MACRO):
    def __init__(self, x1, y1, x2, y2, value):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.value = value

    def expand(self):
        labelLOOPY = str(Labeler("LOOPY"))
        labelLOOPX = str(Labeler("LOOPX"))
        return [
            COMMENT(str(self)),
            LET("yiii", "yi"),
            LABEL(labelLOOPY),
                LET("xiii", "xi"),
                GetCostPointer("tmp", "xiii", "yiii"),
                LABEL(labelLOOPX),
                    LETPTR("tmp", self.value),
                    INC("tmp", "1"),
                    INC("xiii", "1"),
                IFLESS("xii", "xiii", labelLOOPX),
                INC("yiii", "1"),
            IFLESS("yii", "yiii", labelLOOPY),
        ]

    def __str__(self):
        return "FillArea with: " + str(self.value)

class FillAreaCheckBounds(MACRO):
    def __init__(self, x1, y1, x2, y2, value):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.value = value

    def expand(self):
        labelX1OK = str(Labeler("X1-OK"))
        labelY1OK = str(Labeler("Y1-OK"))
        labelX2OK = str(Labeler("X2-OK"))
        labelY2OK = str(Labeler("Y2-OK"))

        return [
            COMMENT(str(self)),
            IFLESS(self.x1, "0", labelX1OK),
                LET(self.x1, "0"),
            LABEL(labelX1OK),
            IFLESS(self.y1, "0", labelY1OK),
                LET(self.y1, "0"),
            LABEL(labelY1OK),
            IFLESS("maxcol", self.x2, labelX2OK),
                LET(self.x2, "maxcol"),
            LABEL(labelX2OK),
            IFLESS("maxrow", self.y2, labelY2OK),
                LET(self.y2, "maxrow"),
            LABEL(labelY2OK),

            FillArea(self.x1, self. x2, self.y1, self.y2, self.value),
        ]

    def __str__(self):
        return "FillAreaCheckBounds with: " + str(self.value)

class LetPtrIfGez(MACRO):
    def __init__(self, ptr, cost):
        self.ptr = ptr
        self.cost = cost

    def expand(self):
        labelend = str(Labeler("LETPPTRIGZ-END"))
        labelet = str(Labeler("LETPPTRIGZ-LET"))
        return [
            COMMENT(str(self)),
            GETPTR("mvar2", self.ptr),
            INC("mvar2", 1),
            IFLESS("0", "mvar2", labelend),
                LETPTR(self.ptr, self.cost),
            LABEL(labelend)
        ]

    def __str__(self):
        return "LetPtrIfGez ptr: " + str(self.ptr) + ", cost: " + str(self.cost)

class BlowHorizontal(MACRO):

    def __init__(self, x, y, side, increment):
        self.x = x
        self.y = y
        self.side = side
        self.increment = increment

    def expand(self):
        labelend = str(Labeler("BLOWH-END-"))
        label0 = str(Labeler("BLOWH0-"))
        label1 = str(Labeler("BLOWH1-"))
        label2 = str(Labeler("BLOWH2-"))
        label3 = str(Labeler("BLOWH3-"))
        if self.increment == -1:
            ComputeBlowDepth = LETSUB("blowdepth", "mvar", "0")
        else:
            ComputeBlowDepth = LETSUB("blowdepth", "maxcol", "mvar")

        return [
            COMMENT(str(self)),
            LETADD("mvar", self.x, self.side),
            ComputeBlowDepth,

            IFLESS("blowdepth", "0", label0),
                JMP(labelend),

            LABEL(label0),
            LETSUB("mvar", self.y, "3"),
            GetCostPointer("ptr", self.x, "mvar"),
            LET("mvar", "ptr"),
            INC("mvar", self.side),
            LetPtrIfGez("mvar", CONSTANTS.BLOW0),
            GetCostPointerNeighbor("mvar", "mvar", GetCostPointerNeighbor.DOWN),
            LetPtrIfGez("mvar", CONSTANTS.BLOW0),
            LETADD("ptr","mvar", self.increment),
            GetCostPointerNeighbor("mvar", "mvar", GetCostPointerNeighbor.DOWN),
            LetPtrIfGez("mvar", CONSTANTS.BLOW0),
            GetCostPointerNeighbor("mvar", "mvar", GetCostPointerNeighbor.DOWN),
            LetPtrIfGez("mvar", CONSTANTS.BLOW0),
            GetCostPointerNeighbor("mvar", "mvar", GetCostPointerNeighbor.DOWN),
            LetPtrIfGez("mvar", CONSTANTS.BLOW0),
            GetCostPointerNeighbor("mvar", "mvar", GetCostPointerNeighbor.DOWN),
            LetPtrIfGez("mvar", CONSTANTS.BLOW0),
            GetCostPointerNeighbor("mvar", "mvar", GetCostPointerNeighbor.DOWN),
            LetPtrIfGez("mvar", CONSTANTS.BLOW0),
            GetCostPointerNeighbor("mvar", "mvar", GetCostPointerNeighbor.DOWN),

            IFLESS("blowdepth", "1", label1),
                JMP(labelend),

            LABEL(label1),
            LET("mvar","ptr"),
            LetPtrIfGez("mvar", CONSTANTS.BLOW1),
            GetCostPointerNeighbor("mvar", "mvar", GetCostPointerNeighbor.DOWN),
            LetPtrIfGez("mvar", CONSTANTS.BLOW1),
            LETADD("ptr","mvar", self.increment),
            GetCostPointerNeighbor("mvar", "mvar", GetCostPointerNeighbor.DOWN),
            LetPtrIfGez("mvar", CONSTANTS.BLOW1),
            GetCostPointerNeighbor("mvar", "mvar", GetCostPointerNeighbor.DOWN),
            LetPtrIfGez("mvar", CONSTANTS.BLOW1),
            GetCostPointerNeighbor("mvar", "mvar", GetCostPointerNeighbor.DOWN),
            LetPtrIfGez("mvar", CONSTANTS.BLOW1),

            IFLESS("blowdepth", "2", label2),
                JMP(labelend),

            LABEL(label2),
            LET("mvar","ptr"),
            LetPtrIfGez("mvar", CONSTANTS.BLOW2),
            GetCostPointerNeighbor("mvar", "mvar", GetCostPointerNeighbor.DOWN),
            LetPtrIfGez("mvar", CONSTANTS.BLOW2),
            LETADD("ptr","mvar", self.increment),
            GetCostPointerNeighbor("mvar", "mvar", GetCostPointerNeighbor.DOWN),
            LetPtrIfGez("mvar", CONSTANTS.BLOW2),

            IFLESS("blowdepth", "3", label3),
                JMP(labelend),

            LABEL(label3),
            LetPtrIfGez("ptr", CONSTANTS.BLOW3),

            LABEL(labelend)
       ]

    def __str__(self):
        return "BlowHorizontal for x: " + str(self.x) + ", y: " + str(self.y)

class BlowVertical(MACRO):

    def __init__(self, x, y, side, direction):
        self.x = x
        self.y = y
        self.side = side
        self.direction = direction

    def expand(self):
        labelend = str(Labeler("BLOWV-END-"))
        label0 = str(Labeler("BLOWV0-"))
        label1 = str(Labeler("BLOWV1-"))
        label2 = str(Labeler("BLOWV2-"))
        label3 = str(Labeler("BLOWV3-"))

        if self.direction == GetCostPointerNeighbor.UP:
            ComputeBlowDepth = LETSUB("blowdepth", "mvar", "0")
        else:
            ComputeBlowDepth = LETSUB("blowdepth", "maxrow", "mvar")

        return [
           COMMENT(str(self)),
           LET("mvar", self.y),
           INC("mvar", self.side),
           ComputeBlowDepth,

           IFLESS("blowdepth", "0", label0),
                JMP(labelend),

           LABEL(label0),
           GetCostPointer("ptr", self.x, "mvar"),
           INC("ptr", "-3"),
           LetPtrIfGez("ptr", CONSTANTS.BLOW0),
           INC("ptr", "1"),
           LetPtrIfGez("ptr", CONSTANTS.BLOW0),
           INC("ptr", "1"),
           LetPtrIfGez("ptr", CONSTANTS.BLOW0),
           INC("ptr", "1"),
           LetPtrIfGez("ptr", CONSTANTS.BLOW0),
           INC("ptr", "1"),
           LetPtrIfGez("ptr", CONSTANTS.BLOW0),
           INC("ptr", "1"),
           LetPtrIfGez("ptr", CONSTANTS.BLOW0),
           INC("ptr", "1"),
           LetPtrIfGez("ptr", CONSTANTS.BLOW0),

           IFLESS("blowdepth", "1", label1),
                JMP(labelend),

           LABEL(label1),
           GetCostPointerNeighbor("ptr", "ptr", self.direction),
           INC("ptr", "-1"),
           LetPtrIfGez("ptr", CONSTANTS.BLOW1),
           INC("ptr", "-1"),
           LetPtrIfGez("ptr", CONSTANTS.BLOW1),
           INC("ptr", "-1"),
           LetPtrIfGez("ptr", CONSTANTS.BLOW1),
           INC("ptr", "-1"),
           LetPtrIfGez("ptr", CONSTANTS.BLOW1),
           INC("ptr", "-1"),
           LetPtrIfGez("ptr", CONSTANTS.BLOW1),

           IFLESS("blowdepth", "2", label2),
                JMP(labelend),

           LABEL(label2),
           GetCostPointerNeighbor("ptr", "ptr", self.direction),
           INC("ptr", "1"),
           LetPtrIfGez("ptr", CONSTANTS.BLOW2),
           INC("ptr", "1"),
           LetPtrIfGez("ptr", CONSTANTS.BLOW2),
           INC("ptr", "1"),
           LetPtrIfGez("ptr", CONSTANTS.BLOW2),

           IFLESS("blowdepth", "3", label3),
                JMP(labelend),

           LABEL(label3),
           GetCostPointerNeighbor("ptr", "ptr", self.direction),
           INC("ptr", "-1"),
           LetPtrIfGez("ptr", CONSTANTS.BLOW3),

           LABEL(labelend)
       ]

    def __str__(self):
        return "BlowVertical for x: " + str(self.x) + ", y: " + str(self.y)

class MoveBiasedHorizontal(MACRO):
    def __init__(self):
        pass
    def expand(self):
        labelend = str(Labeler("MOVEBIASEDHORIZ-"))
        labelMoveDown = str(Labeler("VB-MOVE-DOWN-"))
        labelMoveRight = str(Labeler("VB-MOVE-RIGHT-"))
        labelMoveUp = str(Labeler("VB-MOVE-UP-"))

        return [
            GetCostPointerNeighbor("tmp", "ptr", GetCostPointerNeighbor.LEFT),
            GETPTR("ncost", "tmp"),
            GetBestCost("ncost", "cost", "ncost"),
            IFLESS("ncost", "cost", labelMoveRight),
                LET("cost", "ncost"),
                LET("move", "4"),

            LABEL(labelMoveRight),
            GetCostPointerNeighbor("tmp", "ptr", GetCostPointerNeighbor.RIGHT),
            GETPTR("ncost", "tmp"),
            GetBestCost("ncost", "cost", "ncost"),
            IFLESS("ncost", "cost", labelMoveUp),
                LET("cost", "ncost"),
                LET("move", "2"),

            LABEL(labelMoveUp),
            GetCostPointerNeighbor("tmp", "ptr", GetCostPointerNeighbor.UP),
            GETPTR("ncost", "tmp"),
            GetBestCost("ncost", "cost", "ncost"),
            IFLESS("ncost", "cost", labelMoveDown),
                LET("cost", "ncost"),
                LET("move", "1"),

            LABEL(labelMoveDown),
            GetCostPointerNeighbor("tmp", "ptr", GetCostPointerNeighbor.DOWN),
            GETPTR("ncost", "tmp"),
            GetBestCost("ncost", "cost", "ncost"),
            IFLESS("ncost", "cost", labelend),
                LET("cost", "ncost"),
                LET("move", "3"),

            LABEL(labelend)
        ]
    def __str__(self):
        return "MoveBiasedHorizontal"

class MoveBiasedVertical(MACRO):
    def __init__(self):
        pass
    def expand(self):
        labelend = str(Labeler("MOVEBIASEDVERT-"))
        labelMoveRight = str(Labeler("HB-MOVE-RIGHT-"))
        labelMoveDown = str(Labeler("HB-MOVE-DOWN-"))
        labelMoveLeft = str(Labeler("HB-MOVE-LEFT-"))

        return [
            GetCostPointerNeighbor("tmp", "ptr", GetCostPointerNeighbor.UP),
            GETPTR("ncost", "tmp"),
            GetBestCost("ncost", "cost", "ncost"),
            IFLESS("ncost", "cost", labelMoveDown),
                LET("cost", "ncost"),
                LET("move", "1"),

            LABEL(labelMoveDown),
            GetCostPointerNeighbor("tmp", "ptr", GetCostPointerNeighbor.DOWN),
            GETPTR("ncost", "tmp"),
            GetBestCost("ncost", "cost", "ncost"),
            IFLESS("ncost", "cost", labelMoveLeft),
                LET("cost", "ncost"),
                LET("move", "3"),

            LABEL(labelMoveLeft),
            GetCostPointerNeighbor("tmp", "ptr", GetCostPointerNeighbor.LEFT),
            GETPTR("ncost", "tmp"),
            GetBestCost("ncost", "cost", "ncost"),
            IFLESS("ncost", "cost", labelMoveRight),
                LET("cost", "ncost"),
                LET("move", "4"),

            LABEL(labelMoveRight),
            GetCostPointerNeighbor("tmp", "ptr", GetCostPointerNeighbor.RIGHT),
            GETPTR("ncost", "tmp"),
            GetBestCost("ncost", "cost", "ncost"),
            IFLESS("ncost", "cost", labelend),
                LET("move", "2"),

            LABEL(labelend)
        ]
    def __str__(self):
        return "MoveBiasedVertical"

class BuildCostFence(MACRO):
    def __init__(self):
        pass

    def expand(self):
        return [
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

        ]

    def __str__(self):
        return "BuildCostFence"

class PenalizeCost(MACRO):
    def __init__(self, ptr, penalty, threshold):
        self.ptr = ptr
        self.penalty = penalty
        self.threshold = threshold

    def expand(self):
        labelend = str(Labeler("END"))
        return [
            GETPTR("cost", self.ptr),
            IFLESS("3", "cost", labelend),
                INC("cost", self.penalty),
                LETPTR(self.ptr, "cost"),
            LABEL(labelend)
        ]

    def __str__(self):
        return "PenalizeCost"

class PenalizeEdges(MACRO):
    def __init__(self):
        pass

    def expand(self):
        looplbl1 = str(Labeler("loop"))
        looplbl2 = str(Labeler("loop"))

        return [
            COMMENT(str(self)),
            GetCostPointer("p1", "0", "0"),
            GetCostPointer("p2", "0", "1"),
            GetCostPointer("p3", "0", "2"),
            LET("tmp", "maxrow"),
            GetCostPointer("p4", "0", "tmp"),
            INC("tmp", "-1"),
            GetCostPointer("p5", "0", "tmp"),
            INC("tmp", "-1"),
            GetCostPointer("p6", "0", "tmp"),
            LET("xi", "0"),

            LABEL(looplbl1),
                PenalizeCost("p1", CONSTANTS.PENEDGE0, CONSTANTS.PENTHRS0),
                INC("p1", "1"),
                PenalizeCost("p2", CONSTANTS.PENEDGE1, CONSTANTS.PENTHRS1),
                INC("p2", "1"),
                PenalizeCost("p3", CONSTANTS.PENEDGE2, CONSTANTS.PENTHRS2),
                INC("p3", "1"),
                PenalizeCost("p4", CONSTANTS.PENEDGE0, CONSTANTS.PENTHRS0),
                INC("p4", "1"),
                PenalizeCost("p5", CONSTANTS.PENEDGE1, CONSTANTS.PENTHRS1),
                INC("p5", "1"),
                PenalizeCost("p6", CONSTANTS.PENEDGE2, CONSTANTS.PENTHRS2),
                INC("p6", "1"),
                INC("xi", "1"),
            IFLESS("maxcol", "xi", looplbl1),

            GetCostPointer("p1", "0", "0"),
            GetCostPointer("p2", "1", "0"),
            GetCostPointer("p3", "2", "0"),
            LET("tmp", "maxcol"),
            GetCostPointer("p4", "tmp", "0"),
            INC("tmp", "-1"),
            GetCostPointer("p5", "tmp", "0"),
            INC("tmp", "-1"),
            GetCostPointer("p6", "tmp", "0"),

            LET("yi", "0"),
            LABEL(looplbl2),
                PenalizeCost("p1", CONSTANTS.PENEDGE0, CONSTANTS.PENTHRS0),
                GetCostPointerNeighbor("p1", "p1", GetCostPointerNeighbor.DOWN),
                PenalizeCost("p2", CONSTANTS.PENEDGE1, CONSTANTS.PENTHRS1),
                GetCostPointerNeighbor("p2", "p2", GetCostPointerNeighbor.DOWN),
                PenalizeCost("p3", CONSTANTS.PENEDGE2, CONSTANTS.PENTHRS2),
                GetCostPointerNeighbor("p3", "p3", GetCostPointerNeighbor.DOWN),
                PenalizeCost("p4", CONSTANTS.PENEDGE0, CONSTANTS.PENTHRS0),
                GetCostPointerNeighbor("p4", "p4", GetCostPointerNeighbor.DOWN),
                PenalizeCost("p5", CONSTANTS.PENEDGE1, CONSTANTS.PENTHRS1),
                GetCostPointerNeighbor("p5", "p5", GetCostPointerNeighbor.DOWN),
                PenalizeCost("p6", CONSTANTS.PENEDGE2, CONSTANTS.PENTHRS2),
                GetCostPointerNeighbor("p6", "p6", GetCostPointerNeighbor.DOWN),
                INC("yi", "1"),
            IFLESS("maxrow", "yi", looplbl2),


        ]

    def __str__(self):
        return "PenalizeEdges"

class FillMapZeros(MACRO):
    def __init__(self):
        pass

    def expand(self):
        return [
            LET("xi",  "0"),
            LET("yi",  "0"),
            LET("xii", "maxcol"),
            LET("yii", "maxrow"),
            FillArea("xi", "yi", "xii", "yii", "0"),
        ]

    def __str__(self):
        return "FillMapZeros"

class MarkObstacles(MACRO):
    def __init__(self):
        pass

    def expand(self):
        return [
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
        ]

    def __str__(self):
        return "MarkObstacles"

class ReadEnemyVars(MACRO):
    def __init__(self):
        pass

    def expand(self):
        return [
            LET("cetstart", "8"),
            INC("cetstart", "numobs"),
            INC("cetstart", "numobs"),
            GETPTR("numcet", "cetstart"),
            LETSUB("maxcet", "numcet", "1"),
            INC("cetstart", "1"),

            LET("dronestart", "cetstart"),
            INC("dronestart", "numcet"),
            INC("dronestart", "numcet"),
            GETPTR("maxdrone", "dronestart"),
            INC("maxdrone", "-1"),
            INC("dronestart", "1"),
        ]

    def __str__(self):
        return ""

class MarkDrones(MACRO):
    def __init__(self):
        pass

    def expand(self):
        return [
            LABEL("INIT DRONE"),
            LET("i", "0"),
            LABEL("INIT LOOP DRONE"),
                LETADD("ptr", "dronestart", "i"),
                INC("ptr", "i"),
                GETPTR("xi", "ptr"),

                INC("ptr", "1"),
                GETPTR("yi", "ptr"),

                IFEQ("x", "xi", "DRONE LOOP FILL"),
                    IFEQ("y", "yi", "DRONE LOOP FILL"),
                        LDA("0"),
                        JGE("DRONE LOOP END"),

                LABEL("DRONE LOOP FILL"),
                LETADD("xii", "xi", "0"),
                LETADD("yii", "yi", "0"),
                INC("xi", "-0"),
                INC("yi", "-0"),
                FillAreaCheckBounds("xi", "yi", "xii", "yii", "-4"),

                LABEL("DRONE LOOP END"),
                INC("i", "1"),
            IFLESS("maxdrone", "i", "INIT LOOP DRONE"),
        ]

    def __str__(self):
        return "MarkDrones"

class MarkPasthBFS(MACRO):
    def __init__(self):
        pass

    def expand(self):
        labelInit = str(Labeler("INIT"))
        labelLoop = str(Labeler("LOOP"))

        return [
            LET("startq", "QUEUE_ADR"),
            LET("endq", "QUEUE_ADR"),

            # make sure it's not a negative value so we get stuck
            GetCostPointer("ptr", "x", "y"),
            GETPTR("cost", "ptr"),
            IFLESS("cost", "0", labelInit),
                LETPTR("ptr", "0"),

            LABEL(labelInit),
            GetCostPointer("ptr", "tx", "ty"),
            Push("endq", "ptr"),
            LETPTR("ptr", "1"),

            LABEL(labelLoop),
                Pop("startq", "ptr"),
                GETPTR("cost", "ptr"),
                LETADD("ncost", "cost", "1"),

                AssignCost(GetCostPointerNeighbor.RIGHT),
                AssignCost(GetCostPointerNeighbor.DOWN),
                AssignCost(GetCostPointerNeighbor.LEFT),
                AssignCost(GetCostPointerNeighbor.UP),

                LETSUB("lastq", "endq", "1"),
            IFLESS("lastq", "startq", labelLoop),
        ]

    def __str__(self):
        return "MarkPasthBFS"

class MarkCitizens(MACRO):
    def __init__(self):
        pass

    def expand(self):
        labelend = str(Labeler("END-"))
        return [
            IFLESS("0", "numcet", labelend),
                LET("dirstatus", "DIR_UPDATE"),
                GETPTR("numdir", "CETDIR_ADR"),
                IFNEQ("numcet", "numdir", "INIT CETATENI"),
                    LETPTR("CETDIR_ADR", "numcet"),
                    LET("dirstatus", "DIR_NEW"),

                LABEL("INIT CETATENI"),
                LET("i", "0"),
                LABEL("INIT LOOP CETATENI"),
                    LETADD("ptr", "cetstart", "i"),
                    INC("ptr", "i"),
                    GETPTR("xi", "ptr"),

                    INC("ptr", "1"),
                    GETPTR("yi", "ptr"),

                    # update directions
                    LET("ptr", "CETDIR_ADR"),
                    INC("ptr", "1"),
                    INC("ptr", "i"),
                    INC("ptr", "i"),
                    LET("tmp", "ptr"),
                    INC("tmp", "1"),
                    # IFEQ("dirstatus", "DIR_NEW", "DIR UPDATE"),
                    #     LDA("0"),
                    #     JGE("FILL AREA"),
                    LABEL("DIR UPDATE"),
                    GETPTR("xiii", "ptr"),
                    GETPTR("yiii", "tmp"),
                    LETPTR("ptr", "xi"),
                    LETPTR("tmp", "yi"),
                    LETSUB("xiii", "xi", "xiii"),
                    LETSUB("yiii", "yi", "yiii"),
                    ABS("tmp", "xiii"),
                    ABS("tmp2", "yiii"),
                    INC("tmp", "tmp2"),
                    IFEQ("tmp", "1", "FILL AREA"),
                        IFLESS("0", "xiii", "DIR CHECK DOWN"),
                            BlowHorizontal("xi", "yi", "4", "1"),
                            JMP("FILL AREA"),

                        LABEL("DIR CHECK DOWN"),
                        IFLESS("0", "yiii", "DIR CHECK LEFT"),
                            BlowVertical("xi", "yi", "4", GetCostPointerNeighbor.DOWN),
                            JMP("FILL AREA"),

                        LABEL("DIR CHECK LEFT"),
                        IFLESS("xiii", "0", "DIR CHECK UP"),
                            BlowHorizontal("xi", "yi", "-4", "-1"),
                            JMP("FILL AREA"),

                        LABEL("DIR CHECK UP"),
                        IFLESS("yiii", "0", "FILL AREA"),
                            BlowVertical("xi", "yi", "-4", GetCostPointerNeighbor.UP),

                    LABEL("FILL AREA"),
                    LETADD("xii", "xi", "3"),
                    LETADD("yii", "yi", "3"),
                    INC("xi", "-3"),
                    INC("yi", "-3"),

                    FillAreaCheckBounds("xi", "yi", "xii", "yii", "-3"),

                    INC("i", "1"),
                IFLESS("maxcet", "i", "INIT LOOP CETATENI"),
                LABEL(labelend)
        ]

    def __str__(self):
        return "MarkCitizens"

class InitSymbols(MACRO):
    def __init__(self):
        pass

    def expand(self):
        return [
            SYM("UP",             "1"),
            SYM("RIGHT",          "2"),
            SYM("DOWN",           "3"),
            SYM("LEFT",           "4"),
            SYM("HOLD",           "0"),
            SYM("COSTS_ADR",   "4000"),
            SYM("QUEUE_ADR", "100000"),
            SYM("CETDIR_ADR", "70000"),
            SYM("DIR_NEW",        "1"),
            SYM("DIR_UPDATE",        "2"),

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
            SYM("startq",    "[3016]"),
            SYM("endq",      "[3017]"),
            SYM("lastq",     "[3018]"),
            SYM("cetstart",  "[3019]"),
            SYM("maxcet",    "[3020]"),
            SYM("xii",       "[3021]"),
            SYM("yii",       "[3022]"),
            SYM("xiii",      "[3023]"),
            SYM("yiii",      "[3024]"),
            SYM("dronestart","[3025]"),
            SYM("maxdrone",  "[3026]"),
            SYM("numcet",    "[3027]"),
            SYM("numdir",    "[3028]"),
            SYM("maxdir",    "[3029]"),
            SYM("dirstatus", "[3030]"),
            SYM("tmp2",      "[3031]"),
            SYM("mvar",      "[3032]"), #z to be used by convention only in macros
            SYM("mvar2",     "[3033]"), #z to be used by convention only in macros
            SYM("blowdepth", "[3034]"),
            SYM("movebias",  "[3035]"),
            SYM("p1",        "[3036]"),
            SYM("p2",        "[3037]"),
            SYM("p3",        "[3038]"),
            SYM("p4",        "[3039]"),
            SYM("p5",        "[3040]"),
            SYM("p6",        "[3041]"),
            SYM("citpath",   "[3042]"),
            SYM("skipped",   "[3043]"),

            LETSUB("maxrow",  "r", "1"),
            LETSUB("maxcol",  "c", "1"),
            LETADD("fence_r", "r", "2"),
            LETADD("fence_c", "c", "2"),
            LETADD("fmaxrow", "r", "1"),
            LETADD("fmaxcol", "c", "1"),
            LETSUB("maxobs",  "numobs", "1")
        ]

    def __str__(self):
        return "InitSymbols"


def main():
    program = [
        InitSymbols(),

        START("INIT"),

        LABEL("INIT"),
        BuildCostFence(),

        LABEL ("COMPUTE COSTS"),
        CHANGE_START("COMPUTE COSTS"),

        FillMapZeros(),
        MarkObstacles(),
        ReadEnemyVars(),
        MarkDrones(),

        LET("citpath", "-1"),
        IFLESS("0", "numcet", "END COLLISION CHECK"),
            LET("i", "0"),
            LABEL("LOOP COLLISION"),
                LETADD("ptr", "cetstart", "i"),
                INC("ptr", "i"),
                GETPTR("xi", "ptr"),

                INC("ptr", "1"),
                GETPTR("yi", "ptr"),

                LETSUB("xii", "x", "xi"),
                ABS("xii", "xii"),
                IFLESS("xii", "4", "CHECK TARGET COLLISION"),
                    LETSUB("yii", "y", "yi"),
                    ABS("yii", "yii"),
                    IFLESS("yii", "4", "CHECK TARGET COLLISION"),
                        LET("citpath", "1"),
                        JMP("END COLLISION CHECK"),

                LABEL("CHECK TARGET COLLISION"),
                LETSUB("xii", "tx", "xi"),
                ABS("xii", "xii"),
                IFLESS("xii", "4", "LOOP COLLISION INC"),
                    LETSUB("yii", "ty", "yi"),
                    ABS("yii", "yii"),
                    IFLESS("yii", "4", "LOOP COLLISION INC"),
                        LET("citpath", "1"),
                        JMP("END COLLISION CHECK"),

                LABEL("LOOP COLLISION INC"),
                INC("i", "1"),
            IFLESS("maxcet", "i", "LOOP COLLISION"),
        LABEL("END COLLISION CHECK"),

        IFLESS("0", "citpath", "MARK CITIZENS"),
            MarkPasthBFS(),

        LABEL("MARK CITIZENS"),
        MarkCitizens(),
        IFLESS("citpath", "0", "PENALIZE"),
            MarkPasthBFS(),

        LABEL("PENALIZE"),
        PenalizeEdges(),

        LABEL ("MOVE"),
        GetCostPointer("ptr", "x", "y"),
        GETPTR("cost", "ptr"),
        LET("cost", "10000"),
        LET("move", "0"),
        IFLESS("movebias", "0", "MOVE BIASED VERTICAL"),
            MoveBiasedHorizontal(),
            LET("movebias", "0"),
            JMP("MAKE MOVE"),

        LABEL("MOVE BIASED VERTICAL"),
        MoveBiasedVertical(),
        LET("movebias", "-1"),

        LABEL("MAKE MOVE"),
        MOVE_HLT("move"),
    ]

    asm = DroneAssembler(program).\
        compile().\
        spit().\
        save('/Users/rodanciv/Documents/01_letsGetToKnowEachOther_v9.txt').\
        save('/Users/rodanciv/Documents/02_dontGetShot_v9.txt').\
        save('/Users/rodanciv/Documents/03_shortestPath_v9.txt').\
        save('/Users/rodanciv/Documents/04_gottaCircleAround_v9.txt').\
        save('/Users/rodanciv/Documents/05_thinkAhead_v9.txt').\
        save('/Users/rodanciv/Documents/06_beOnYourToes_v9.txt').\
        save('/Users/rodanciv/Documents/07_intoTheDark_v9.txt').\
        save('/Users/rodanciv/Documents/08_mazeOfDrones_v9.txt').\
        save('/Users/rodanciv/Documents/09_theyJustKeepOnComing_v9.txt').\
        save('/Users/rodanciv/Documents/10_labyrinth_v9.txt').\
        save('/Users/rodanciv/Documents/11_whatsTheName_v9.txt').\
        save('/Users/rodanciv/Documents/12_noWayToTarget_v9.txt').\
        assembly

    dronemem = DroneMemory('/Users/rodanciv/Documents/Maze.txt')
    sim = DroneSimulator(asm)
    while not sim.done:
        sim.memupdate(dronemem.memory)
        sim.step()
        dronemem.dumpMemoryMatrix(4000 + dronemem.memory[1] + 2, dronemem.memory[1] + 2, dronemem.memory[2] + 2)
        print "x: " + str(sim.drone_x) + ", y: " + str(sim.drone_y)
        dronemem.refresh()

    print sim.status
    print "score: " + str(sim.getscore(12))


if __name__ == "__main__":
    main()