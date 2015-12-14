class COMMENT:
    param = ''
    def __init__(self, param):
        self.param = param

class LABEL:
    lineno = -1

    def __init__(self, label):
        assert isinstance(label, str)
        self.label = label


class MACRO:
    def __init__(self):
        pass


class SYM:
    name = ''
    value = ''

    def __init__(self, name, value):
        self.name = name
        self.value = value


class START(MACRO):
    startLabel = ''

    def __init__(self, start):
        self.startLabel = start

    def expand(self):
        return [
            COMMENT("Reads the entry point and jumps to it"),
            SYM("__entry", "[2900]"),
            SYM("__start", self.startLabel),
            LDA("__entry"),
            ADDA("__start"),
            STA("[2901]"),
            JGE("[2901]"),
        ]

    def __str__(self):
        return "START"

class CHANGE_START(MACRO):
    startLabel = ''

    def __init__(self, start):
        self.startLabel = start

    def expand(self):
        return [
            COMMENT("Change the entry point next run to: " + self.startLabel),
            LDA(self.startLabel),
            SUBA("__start"),
            STA("__entry"),
        ]

    def __str__(self):
        return "CHANGE_START " + self.startLabel


class IFLESS(MACRO):
    a = ''
    b = ''
    jmp = ''

    def __init__(self, a, b, jmp):
        self.a = a
        self.b = b
        self.jmp = jmp

    def expand(self):
        return [
            COMMENT("if " + self.a + " < " + self.b + " (else jump to: " + self.jmp + ")"),
            LDA(self.a),
            SUBA(self.b),
            JGE(self.jmp),
            COMMENT("then:")
        ]

    def __str__(self):
        return "IFLESS: " + str(self.a) + " < " + str(self.b) + " else jump to " + str(self.jmp)


class MOVE_HLT(MACRO):
    direction = -1

    def __init__(self, direction):
        self.direction = direction

    def expand(self):
        return [
            COMMENT("MOVE " + self.direction + " and HALT"),
            LDA(self.direction),
            STA("[0]"),
            HLT()]

    def __str__(self):
        return "MOVE_HLT: " + str(self.direction)


class LET(MACRO):
    left = ''
    right = ''

    def __init__(self, left, right):
        self.left = str(left)
        self.right = str(right)

    def expand(self):
        return [
            COMMENT("LET " + self.left + " = " + self.right),
            LDA(self.right),
            STA(self.left)
        ]

    def __str__(self):
        return "LET: " + str(self.left) + " = " + str(self.right)

class LETSUB(MACRO):
    left = ''
    a = ''
    b = ''

    def __init__(self, left, a, b):
        self.left = str(left)
        self.a = str(a)
        self.b = str(b)

    def expand(self):
        return [
            COMMENT("LET " + self.left + " = " + self.a + " - " + self.b),
            LDA(self.a),
            SUBA(self.b),
            STA(self.left)
        ]

    def __str__(self):
        return "LETSUB: " + str(self.left) + " = " + str(self.a) + " - " + str(self.b)


class LETADD(MACRO):
    left = ''
    a = ''
    b = ''

    def __init__(self, left, a, b):
        self.left = str(left)
        self.a = str(a)
        self.b = str(b)

    def expand(self):
        return [
            COMMENT("LET " + self.left + " = " + self.a + " + " + self.b),
            LDA(self.a),
            ADDA(self.b),
            STA(self.left)
        ]

    def __str__(self):
        return "LETADD: " + str(self.left) + " = " + str(self.a) + " + " + str(self.b)


class INC(MACRO):
    left = ''
    a = ''

    def __init__(self, left, a):
        self.left = str(left)
        self.a = str(a)

    def expand(self):
        return [
            COMMENT("INC: " + str(self.left) + " += " + str(self.a)),
            LDA(self.left),
            ADDA(self.a),
            STA(self.left)
        ]

    def __str__(self):
        return "INC: " + str(self.left) + " += " + str(self.a)


class LETPTR(MACRO):
    left = ''
    right = ''

    def __init__(self, left, right):
        self.left = str(left)
        self.right = str(right)

    def expand(self):
        return [
            COMMENT("LET PTR [" + self.left + "] = " + self.right),
            LDN(self.left),
            LDA(self.right),
            STA("[N]")
        ]

    def __str__(self):
        return "LET PTR [" + self.left + "] = " + self.right


class GETPTR(MACRO):
    left = ''
    right = ''

    def __init__(self, left, right):
        self.left = str(left)
        self.right = str(right)

    def expand(self):
        return [
            COMMENT("GET PTR " + self.left + " = [" + self.right + "]"),
            LDN(self.right),
            LDA("[N]"),
            STA(self.left)
        ]

    def __str__(self):
        return "GET PTR " + self.left + " = [" + self.right + "]"


class Instruction:
    param = ''
    humanparam = ''
    name = ''
    lineno = -1
    macro = None

    def __init__(self, name, param):
        self.param = str(param)
        self.humanparam = self.param
        self.name = name

    def __str__(self):
        return self.name + ' ' + str(self.param)


class LDN(Instruction):
    def __init__(self, param):
        Instruction.__init__(self, 'LDN', param)


class STA(Instruction):
    def __init__(self, param):
        Instruction.__init__(self, 'STA', param)


class LDA(Instruction):
    def __init__(self, param):
        Instruction.__init__(self, 'LDA', param)


class ADDA(Instruction):
    def __init__(self, param):
        Instruction.__init__(self, 'ADDA', param)


class SUBA(Instruction):
    def __init__(self, param):
        Instruction.__init__(self, 'SUBA', param)


class JGE(Instruction):
    def __init__(self, param):
        Instruction.__init__(self, 'JGE', param)


class HLT(Instruction):
    def __init__(self, ):
        Instruction.__init__(self, 'HLT', '')


class DroneAssembler:
    program = []

    def __init__(self, program):
        self.program = program

    def compile(self):
        self.__expandMacros()
        self.__number()
        self.__resolveSymbols()
        self.__resolveJumps()

        return self

    def spit(self):
        for line in self.program:
            if isinstance(line, Instruction):
                print str(line) + "\t\t// " + str(line.lineno)
            elif isinstance(line, LABEL):
                print "// LABEL: " + line.label
            elif isinstance(line, COMMENT):
                print "// " + line.param
        return self

    def save(self, fileName):
        f = open(fileName, 'w+')
        for line in self.program:
            if isinstance(line, Instruction):
                f.write(str(line) + "\t\t// " + str(line.lineno) + '\n')
            elif isinstance(line, LABEL):
                f.write("// LABEL: " + line.label + '\n')
            elif isinstance(line, COMMENT):
                f.write("// " + line.param + '\n')
        return self

    @property
    def assembly(self):
        return [line for line in self.program if isinstance(line, Instruction)]

    def __resolveSymbols(self):
        symbols = {}
        for line in self.program:
            if isinstance(line, SYM):
                symbols[line.name] = line.value
        for line in self.program:
            if isinstance(line, Instruction):
                if line.param in symbols:
                    line.param = symbols[line.param]

    def __expandMacros(self):
        expanded = []
        for line in self.program:
            if isinstance(line, MACRO):
                macroprog = line.expand()
                for instr in macroprog:
                    instr.macro = line
                expanded.extend(macroprog)
            else:
                expanded.append(line)
        self.program = expanded

    def __resolveJumps(self):
        label = None
        labels = {}
        for line in self.program:
            if isinstance(line, LABEL):
                label = line
            elif isinstance(line, Instruction):
                if label is not None:
                    label.lineno = line.lineno
                    labels[label.label] = label.lineno
                    label = None
        for line in self.program:
            if isinstance(line, Instruction) and line.param in labels:
                line.param = labels[line.param]

    def __number(self):
        count = 0
        for line in self.program:
            if isinstance(line, Instruction):
                line.lineno = count
                count += 1


