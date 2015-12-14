# -*- coding: latin-1 -*-

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

"""


class Sequencer:
    def __init__(self):
        self.sequence = ""

    def insGeneric(self, ins, param):
        self.sequence += ins + " " + param + "\n"
        return self

    def LDN(self, param):
        return self.insGeneric("LDN", param)

    def STA(self, param):
        return self.insGeneric("STA", param)

    def LDA(self, param):
        return self.insGeneric("LDA", param)

    def ADDA(self, param):
        return self.insGeneric("ADDA", param)

    def SUBA(self, param):
        return self.insGeneric("SUBA", param)

    def JGE(self, param):
        return self.insGeneric("JGE", param)

    def HLT(self):
        return self.insGeneric("HLT", "")

    def generate(self):
        return self.sequence + "\n"


class Move:
    def __init__(self, direction, steps):
        self.direction = direction
        self.steps = steps


class Path:
    def __init__(self):
        self.path = []

    def up(self, steps):
        self.path.append(Move(1, steps))
        return self

    def right(self, steps):
        self.path.append(Move(2, steps))
        return self

    def down(self, steps):
        self.path.append(Move(3, steps))
        return self

    def left(self, steps):
        self.path.append(Move(4, steps))
        return self

    def hold(self, steps):
        self.path.append(Move(0, steps))
        return self

    def getPath(self):
        return self.path


def generateHeader(f):
    f.write(Sequencer().\
        LDA("[1000]").\
        ADDA("4").\
        STA("[1000]").\
        JGE("[1000]").\
        generate())


def generatePath(f,path):
    for move in path.getPath():
        if move.steps >= 1:
            f.write(Sequencer().LDA(str(move.direction)).STA("[0]").HLT().HLT().generate())
            for i in range(1, move.steps):
                f.write(Sequencer().HLT().HLT().HLT().HLT().generate())


def main():
    f = open('/Users/rodanciv/Documents/06_beOnYourToes_01.txt', 'w+')
    generateHeader(f)
    print generatePath(f, Path().hold(7).left(1).down(10).right(10).down(3).right(5).up(1))

    f.close()


if __name__ == "__main__":
    main()