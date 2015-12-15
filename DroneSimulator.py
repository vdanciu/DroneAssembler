# coding=utf-8
"""
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

MAP EXAMPLE:
{
  "simulatedDrone": {"type": "Drone", "identifier": "@", "position": {"x": 0, "y": 0}},
  "map": {
    "rows": 10,
    "cols": 10,
    "target": {"x": 5, "y": 7},
    "objects": [
      {"type": "Obstacle", "position": {"x": 2, "y": 0}},
      {"type": "Obstacle", "position": {"x": 2, "y": 1}},
      {"type": "Obstacle", "position": {"x": 2, "y": 2}}
    ]
  }
}

"""

import json

import math


class DroneMemory:
    ROWS = 1
    COLS = 2
    DX = 3
    DY = 4
    TX = 5
    TY = 6
    NOBS = 7

    def __init__(self, mapfile):
        self.memory = [0] * 1000000
        self.mapfile = mapfile
        self.cetateni = []
        self.drone = []
        self.cetidx = 0
        self.map = []
        self.loadmap(mapfile)

    def loadmap(self, mapfile):
        self.map = json.load(open(mapfile, "r"))

        self.memory[self.ROWS] = int(self.map['map']['rows'])
        self.memory[self.COLS] = int(self.map['map']['rows'])
        self.memory[self.DX]   = int(self.map['simulatedDrone']['position']['x'])
        self.memory[self.DY]   = int(self.map['simulatedDrone']['position']['y'])
        self.memory[self.TX]   = int(self.map['map']['target']['x'])
        self.memory[self.TY]   = int(self.map['map']['target']['y'])
        self.memory[self.NOBS] = len([item for item in self.map['map']['objects'] if item['type'] == 'Obstacle'])
        # load the obstacles
        idx = self.NOBS + 1
        for object in self.map['map']['objects']:
            if object['type'] == 'Obstacle':
                self.memory[idx] = int(object['position']['x'])
                self.memory[idx + 1] = int(object['position']['y'])
                idx += 2
        self.cetidx = idx
        self.cetateni = [item for item in self.map['map']['objects'] if item['type'] == 'Cetatean']
        self.drone = [item for item in self.map['map']['objects'] if item['type'] == 'Drone']

        self.update_toti_dusmanii()


    def update_toti_dusmanii(self):
        idx = self.update_inamici(self.cetidx, self.cetateni)
        idx = self.update_inamici(idx, self.drone)

    def refresh(self):
        for cetatean in self.cetateni:
            x = cetatean['position']['x']
            y = cetatean['position']['y']
            moves = {
                'RIGHT': {'x':  1, 'y':  0},
                'DOWN':  {'x':  0, 'y':  1},
                'LEFT':  {'x': -1, 'y':  0},
                'UP':    {'x':  0, 'y': -1}
            }
            cetatean['position']['x'] += moves[cetatean['direction']]['x']
            cetatean['position']['y'] += moves[cetatean['direction']]['y']
            if cetatean['position']['x'] < 0 or \
               cetatean['position']['y'] < 0 or \
               cetatean['position']['x'] >= self.memory[self.COLS] or \
               cetatean['position']['y'] >= self.memory[self.ROWS]:
                self.cetateni = [item for item in self.cetateni if item != cetatean]

        self.update_toti_dusmanii()


    def update_inamici(self, idx, inamici):
        self.memory[idx] = len(inamici)
        idx += 1
        for object in inamici:
            self.memory[idx] = int(object['position']['x'])
            self.memory[idx + 1] = int(object['position']['y'])
            idx += 2
        return idx

    @property
    def memory(self):
        return self.memory

    def dumpMemoryMatrix(self, start, rows, cols):
        for y in range(0, rows):
            line = ''
            for x in range(0, cols):
                line += '{0:>3}'.format(str(self.memory[start + y * cols + x]))
            print line



class DroneSimulator:
    def __init__(self, asm):
        self.asm = asm
        self.done = False
        self.memory = None
        self.regA = 0
        self.regN = 0
        self.__status = ''
        self.moves = 0
        self.CPU = 0

    def getscore(self, probnum):
        if probnum > 6:
            probnum *= 2
        return probnum * 10000 / math.log((self.moves**2)*self.CPU)

    @property
    def status(self):
        return self.__status

    @property
    def drone_x(self):
        return self.memory[DroneMemory.DX]

    @property
    def drone_y(self):
        return self.memory[DroneMemory.DY]

    def memupdate(self, mem):
        self.memory = mem

    def updatePosition(self):
        moves = {
            0 : {'x' :  0, 'y' :  0},
            1 : {'x' :  0, 'y' : -1},
            2 : {'x' :  1, 'y' :  0},
            3 : {'x' :  0, 'y' :  1},
            4 : {'x' : -1, 'y' :  0}
        }
        self.memory[DroneMemory.DX] += moves[self.memory[0]]['x']
        self.memory[DroneMemory.DY] += moves[self.memory[0]]['y']

    def checkTarget(self):
        return self.memory[DroneMemory.DX] == self.memory[DroneMemory.TX] and \
               self.memory[DroneMemory.DY] == self.memory[DroneMemory.TY]

    def checkBounds(self):
        return self.memory[DroneMemory.DX] < 0 or \
               self.memory[DroneMemory.DY] < 0 or \
               self.memory[DroneMemory.DX] >= self.memory[DroneMemory.COLS] or \
               self.memory[DroneMemory.DY] >= self.memory[DroneMemory.ROWS]

    def checkObstacles(self):
        obsaddress = DroneMemory.NOBS + 1
        for i in range(0, self.memory[DroneMemory.NOBS]):
            if self.memory[DroneMemory.DX] == self.memory[obsaddress + 2 * i] and \
               self.memory[DroneMemory.DY] == self.memory[obsaddress + 2 * i + 1]:
                return True
        return False

    def checkCetateni(self):
        cetaddress = DroneMemory.NOBS + self.memory[DroneMemory.NOBS] * 2 + 1
        for i in range(0, self.memory[cetaddress]):
            cetx = self.memory[cetaddress + 1 + 2 * i]
            cety = self.memory[cetaddress + 1 + 2 * i + 1]
            if abs(self.memory[DroneMemory.DX] - cetx) <= 3 and \
               abs(self.memory[DroneMemory.DY] - cety) <= 3:
                return True
        return False

    def step(self):
        self.moves += 1
        next = self.sim(self.asm[0])
        while next > -1:
            if next == 390: # crude breakpoint method: change the number and ste a breakpoint to 'pass'
                pass
            next = self.sim(self.asm[next])

        self.updatePosition()

        self.done = True
        if self.checkTarget():
            self.__status = 'Success!'
        elif self.checkBounds():
            self.__status = 'Out of map bounds!'
        elif self.checkObstacles():
            self.__status = 'Destroyed by collision with obstacle!'
        elif self.checkCetateni():
            self.__status = 'A cetatean has slingshot your ass!'
        else:
            self.done = False

    def sim(self, instr):
        self.CPU += 1
        #self.tracepresim(instr)
        return getattr(self, "sim" + instr.name)(instr)

    def tracepresim(self, instr):
        around = 2
        first = max(0, instr.lineno - around)
        last = min(len(self.asm) - 1, instr.lineno + around)
        print '\n\n'
        for i in range(first, last + 1):
            pointer = ' '
            dbgins = self.asm[i]
            if instr.lineno == i:
                pointer = '>'
            instrtext = pointer + str(dbgins.lineno) + ": " + \
                  dbgins.name + ' ' + str(dbgins.humanparam) + ':' + \
                  str(self.value(dbgins.param))
            print '{0:40} {1}'.format(instrtext, str(dbgins.macro))
        pass

    def address(self, param):
        return int(param[1:-1])

    def value(self, param):
        if param == '[N]':
            return self.memory[self.regN]
        elif isinstance(param, str) and len(param) > 0 and param[0] == '[':
            return self.memory[self.address(param)]
        else:
            try:
                return int(param)
            except ValueError:
                return -999999

    def simLDA(self, instr):
        self.regA = self.value(instr.param)
        return instr.lineno + 1

    def simSTA(self, instr):
        if instr.param == '[N]':
            self.memory[self.regN] = self.regA
        else:
            self.memory[self.address(instr.param)] = self.regA
        return instr.lineno + 1

    def simLDN(self, instr):
        self.regN = self.value(instr.param)
        return instr.lineno + 1

    def simSUBA(self, instr):
        self.regA -= self.value(instr.param)
        return instr.lineno + 1

    def simADDA(self, instr):
        self.regA += self.value(instr.param)
        return instr.lineno + 1

    def simJGE(self, instr):
        if self.regA < 0:
            return instr.lineno + 1
        else:
            return self.value(instr.param)

    def simHLT(self, instr):
        return -1
