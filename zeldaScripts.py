# Library for Zelda scripts

import struct


class Label:
    """
    Convenience class to represent a label.
    """

    bmg = 0
    index = 0

    def __init__(self, bmg, index):
        self.bmg, self.index = bmg, index

    def isNull(self):
        return self.index == -1 and self.bmg == -1


class Instruction:
    """
    Abstract base class for Zelda PH/ST script instructions.
    """

    type = None
    typeID = 0

    @property
    def bytestring(self):
        raise NotImplementedError

    @classmethod
    def disassemble(cls, value):
        raise NotImplementedError

    def assemble(self):
        raise NotImplementedError


class SayInstruction(Instruction):
    """
    Instruction type 1: "SAY". Causes a message to appear.
    """

    type: str = 'SAY'
    typeID: int = 1
    bytestring = '<BBHhbb'

    messageBMG: int
    messageID: int
    nextLabel: Label
    _extraData: int

    @classmethod
    def disassemble(cls, value: int):
        type, bmgID, messageID, gotoIndex, gotoBmg, extraData = struct.unpack(
            cls.bytestring, value.to_bytes(length=8, byteorder='little')
        )

        assert type == cls.typeID

        obj = cls()
        obj.messageBMG = bmgID
        obj.messageID = messageID
        obj.nextLabel = Label(gotoBmg, gotoIndex)
        obj._extraData = extraData
        return obj

    def assemble(self) -> int:
        byte_data = struct.pack(
            self.bytestring,
            self.typeID,
            self.messageBMG,
            self.messageID,
            self.nextLabel.index,
            self.nextLabel.bmg,
            self._extraData,
        )
        return int.from_bytes(byte_data, byteorder='little')


class SwitchInstruction(Instruction):
    """
    Instruction type 2: "SW" ("switch"). Causes execution to branch to
    one of any number of labels, depending on some condition.
    """

    type: str = 'SW'
    typeID: int = 2
    bytestring = '<BBHHH'

    condition: int
    firstLabel: int
    numLabels: int
    parameter: int

    @classmethod
    def disassemble(cls, value: int):
        type, numLabels, condition, parameter, firstLabel = struct.unpack(
            cls.bytestring, value.to_bytes(length=8, byteorder='little')
        )

        assert type == cls.typeID

        subclass = {
            1: SwitchResponse2Instruction,
            2: SwitchResponse3Instruction,
            3: SwitchResponse4Instruction,
            4: SwitchProgressFlagInstruction,
            6: SwitchTempFlagInstruction,
            8: SwitchTemp2FlagInstruction,
            27: SwitchShopInstruction,
        }.get(condition, cls)

        obj = subclass()
        obj.condition = condition
        obj.firstLabel = firstLabel
        obj.numLabels = numLabels
        obj.parameter = parameter
        return obj

    def assemble(self) -> int:
        byte_data = struct.pack(
            self.bytestring,
            self.typeID,
            self.numLabels,
            self.condition,
            self.parameter,
            self.firstLabel,
        )
        return int.from_bytes(byte_data, byteorder='little')

    def nameForBranch(self, i):
        return str(i)


class _SwitchInstruction_NoParameter(SwitchInstruction):
    """
    Convenience class that implements a SW instruction with no
    parameter.
    """

    @property
    def parameter(self):
        return 0

    @parameter.setter
    def parameter(self, value):
        pass


class SwitchResponse2Instruction(_SwitchInstruction_NoParameter):
    """
    A "SW" instruction that checks the player's response to a question
    message with 2 possible responses.
    """

    type = 'SW_RESP_2'

    def nameForBranch(self, i):
        return ['(first response)', '(second response)'][i]


class SwitchResponse3Instruction(_SwitchInstruction_NoParameter):
    """
    A "SW" instruction that checks the player's response to a question
    message with 3 possible responses.
    """

    type = 'SW_RESP_3'

    def nameForBranch(self, i):
        return ['(first response)', '(second response)', '(third response)'][i]


class SwitchResponse4Instruction(_SwitchInstruction_NoParameter):
    """
    A "SW" instruction that checks the player's response to a question
    message with 4 possible responses.
    """

    type = 'SW_RESP_4'

    def nameForBranch(self, i):
        return ['(first response)', '(second response)', '(third response)', '(fourth response)'][i]


class SwitchProgressFlagInstruction(SwitchInstruction):
    """
    A "SW" instruction that checks a progress flag.
    """

    type = 'SW_P_FLAG'

    # .flag is an alias for .parameter
    @property
    def flag(self):
        return self.parameter

    @flag.setter
    def flag(self, value):
        self.parameter = value

    def nameForBranch(self, i):
        return ['true', 'false'][i]


class SwitchTempFlagInstruction(SwitchInstruction):
    """
    A "SW" instruction that checks a temporary flag.
    """

    type = 'SW_T_FLAG'

    # .flag is an alias for .parameter
    @property
    def flag(self):
        return self.parameter

    @flag.setter
    def flag(self, value):
        self.parameter = value

    def nameForBranch(self, i):
        return ['true', 'false'][i]


class SwitchTemp2FlagInstruction(SwitchInstruction):
    """
    A "SW" instruction that checks a temporary 2 flag.
    """

    type = 'SW_T2_FLAG'

    # .flag is an alias for .parameter
    @property
    def flag(self):
        return self.parameter

    @flag.setter
    def flag(self, value):
        self.parameter = value

    def nameForBranch(self, i):
        return ['true', 'false'][i]


class SwitchShopInstruction(SwitchInstruction):
    """
    A "SW" instruction that switches based on the shop you're currently
    in (when parameter == 0).
    Parameter = 3 is used once, and... no clue what it's for.
    """

    type = 'SW_SHOP'

    def nameForBranch(self, i):
        return [
            'Castle Town Shop',
            "Forest's General Store",
            'Anouki General Store',
            'Papuchia Shop',
            'Goron Country Store',
        ][i]


class DoInstruction(Instruction):
    """
    Instruction type 3: "DO". Causes something to actually happen.
    """

    type = 'DO'
    typeID = 3
    bytestring = '<BBhI'

    action: int
    labelNumber: int
    parameter: int

    @classmethod
    def disassemble(cls, value: int):
        type, action, labelNumber, parameter = struct.unpack(
            cls.bytestring, value.to_bytes(length=8, byteorder='little')
        )

        assert type == cls.typeID

        subclass = {
            0: DoSetProgressFlagInstruction,
            1: DoClearProgressFlagInstruction,
            2: DoSetTemp2FlagInstruction,
            3: DoClearTemp2FlagInstruction,
            4: DoSetTempFlagInstruction,
            5: DoClearTempFlagInstruction,
            7: DoLaunchScriptInstruction,
        }.get(action, cls)

        if action == 9:
            print(parameter)

        obj = subclass()
        obj.action = action
        obj.labelNumber = labelNumber
        obj.parameter = parameter
        return obj

    def assemble(self) -> int:
        byte_data = struct.pack(
            self.bytestring, self.typeID, self.action, self.labelNumber, self.parameter
        )
        return int.from_bytes(byte_data, byteorder='little')


class DoSetProgressFlagInstruction(DoInstruction):
    """
    A "DO" instruction that sets a progress flag.
    """

    type = 'DO_SET_P_FLAG'

    # .flag is an alias for .parameter
    @property
    def flag(self):
        return self.parameter

    @flag.setter
    def flag(self, value):
        self.parameter = value


class DoClearProgressFlagInstruction(DoInstruction):
    """
    A "DO" instruction that clears a progress flag.
    """

    type = 'DO_CLR_P_FLAG'

    # .flag is an alias for .parameter
    @property
    def flag(self):
        return self.parameter

    @flag.setter
    def flag(self, value):
        self.parameter = value


class DoSetTemp2FlagInstruction(DoInstruction):
    """
    A "DO" instruction that sets a temp 2 flag.
    """

    type = 'DO_SET_T2_FLAG'

    # .flag is an alias for .parameter
    @property
    def flag(self):
        return self.parameter

    @flag.setter
    def flag(self, value):
        self.parameter = value


class DoClearTemp2FlagInstruction(DoInstruction):
    """
    A "DO" instruction that clears a temp 2 flag.
    """

    type = 'DO_CLR_T2_FLAG'

    # .flag is an alias for .parameter
    @property
    def flag(self):
        return self.parameter

    @flag.setter
    def flag(self, value):
        self.parameter = value


class DoSetTempFlagInstruction(DoInstruction):
    """
    A "DO" instruction that sets a temp flag.
    """

    type = 'DO_SET_T_FLAG'

    # .flag is an alias for .parameter
    @property
    def flag(self):
        return self.parameter

    @flag.setter
    def flag(self, value):
        self.parameter = value


class DoClearTempFlagInstruction(DoInstruction):
    """
    A "DO" instruction that clears a temp flag.
    """

    type = 'DO_CLR_T_FLAG'

    # .flag is an alias for .parameter
    @property
    def flag(self):
        return self.parameter

    @flag.setter
    def flag(self, value):
        self.parameter = value


class DoLaunchScriptInstruction(DoInstruction):
    """
    A "DO" instruction that immediately launches a different script.
    """

    type = 'DO_SCRPT'

    @property
    def parameter(self):
        return ((self.scriptID & 0xFFFF) << 16) | (self.scriptID >> 16)

    @parameter.setter
    def parameter(self, value):
        self.scriptID = ((value & 0xFFFF) << 16) | (value >> 16)


def disassembleInstruction(instruction: bytes):
    """
    Disassemble a single instruction value into an Instruction.
    """
    instruction: int = int.from_bytes(instruction, 'little')

    instID = instruction & 0xFF

    if instID not in (1, 2, 3):
        raise ValueError(f'Unknown instruction type: {instID}')

    disassembled = {
        1: SayInstruction,
        2: SwitchInstruction,
        3: DoInstruction,
    }[
        instID
    ].disassemble(instruction)

    # Double check that this works in reverse
    assert disassembled.assemble() == instruction

    return disassembled


def disassembleInstructions(instructions):
    """
    Given a list of instruction values, return a list of Instructions.
    """
    return [disassembleInstruction(inst) for inst in instructions]


def disassembleLabels(labels):
    """
    Given a list of label tuples, return a list of Labels.
    """
    return [Label(*L) for L in labels]
