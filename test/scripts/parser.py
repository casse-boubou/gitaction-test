# THANKS to asottile https://github.com/asottile https://github.com/asottile-archive/dockerfile/tree/main
# parser.py - Parse a Dockerfile
from scripts.enum_class import DockerCommand


class CommandLine:
    """Class representing the line found in Dockerfile"""
    def __init__(self, uid, cmd: DockerCommand, startline, endline, stage: dict[any], instructions):
        self.uid = uid
        self.cmd = cmd
        self.startline = startline
        self.endline = endline
        self.stage = stage
        self.instructions = instructions

    def __str__(self):
        # for use with print(t)
        return f"ID: {self.uid} Command:{self.cmd} StartLine:{self.startline} EndLine:{self.endline} Stage:{self.stage} Instruction:{self.instructions}"



class ParsingFile:
    """Class representing the Dockerfile"""
    def __init__(self):
        self.cmdlist = []

    def __str__(self):
        # for use with print(t)
        export = "Your object contain multiple Class Object:"
        for c in self.cmdlist:
            itemhumainreadable = f"(ID: {c.uid}, Command: {c.cmd}, StartLine: {c.startline}, EndLine: {c.endline}, Stage: {c.stage}, Instruction: {c.instructions})"
            export = f"{export}, {itemhumainreadable}"
        return export


    def add_cmd(self, command:CommandLine):
        """Add new command line"""
        self.cmdlist.append(command)

    def update_item(self, uid, endline, instructions):
        """Edit an existing command"""
        for i in self.cmdlist:
            if uid == i.uid:
                i.endline = endline
                newinstruction = f"{i.instructions} {instructions}"
                i.instructions = newinstruction
                return 1
        print("Item not found in command list")

    def check_cmd_details(self, uid):
        """Show an existing record command"""
        for u in self.cmdlist:
            if uid == u.uid:
                return print(f"ID: {u.uid}, Command: {u.cmd}, StartLine: {u.startline}, Endline: {u.endline}, Stage: {u.stage}, Instruction: {u.instructions}")
        print("Item not found in command list")

    def show_all(self):
        """Show all existing record command"""
        for c in self.cmdlist:
            print(f"(ID: {c.uid}, Command: {c.cmd}, StartLine: {c.startline}, EndLine: {c.endline}, Stage: {c.stage}, Instruction: {c.instructions})")



def parser(file):
    """Read Dockerfile line by line and get instructions"""
    parsing_lines = ParsingFile()
    try:
        with open(file, "r", encoding="utf-8") as f:
            linenumber = 0
            stagenumber = 0
            stageid = 0
            step_uid = 0
            for line in f:
                linenumber += 1
                linestrip = line.rstrip()
                # print(f"Processing line number: {linenumber} in the Dockerfile")
                # print(f"Processing line: {linestrip}")

                # Remove COMMENT and blank lines
                if linestrip.startswith("#") or linestrip == "":
                    continue
                # Remove "not end" line mark
                if linestrip.endswith(" \\"):
                    linestrip = linestrip.rstrip("\\")

                for command in DockerCommand.listkeys():
                    if linestrip.startswith(command):
                        cmd = command
                        break
                    cmd = None
                if cmd is not None and cmd == "FROM":
                    stagenumber += 1
                    stageid = step_uid
                if cmd is not None:
                    stagecontant = {"StageNumber":stagenumber, "StageStartAtID":stageid }
                    commandtoadd = CommandLine(uid=step_uid, cmd=cmd, startline=linenumber, endline=linenumber, stage=stagecontant, instructions=linestrip)
                    parsing_lines.add_cmd(commandtoadd)
                    # parsing_lines.check_cmd_details(uid=step_uid)
                    step_uid += 1
                else:
                    preview_step_uid=step_uid-1
                    parsing_lines.update_item(uid=preview_step_uid, endline=linenumber, instructions=linestrip)
                    # parsing_lines.check_cmd_details(uid=preview_step_uid)
    except FileNotFoundError:
        print("The file was not found.")
    except PermissionError:
        print("You don't have permission to access this file.")

    return parsing_lines
