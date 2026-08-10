# THANKS to asottile https://github.com/asottile https://github.com/asottile-archive/dockerfile/tree/main
# parser.py - Parses a Dockerfile into a flat, ordered list of instructions.

from scripts.enum_class import DockerCommand


class DockerfileInstruction:
    """A single Dockerfile instruction (FROM, RUN, ...)."""
    def __init__(self, instruction_id, command: DockerCommand, start_line, end_line, stage_infos: dict[any], instruction_text):
        self.instruction_id = instruction_id
        self.command = command
        self.start_line = start_line
        self.end_line = end_line
        self.stage_infos = stage_infos
        self.instruction_text = instruction_text

    def __str__(self):
        # for use with print(t)
        return f"ID: {self.instruction_id} Command:{self.command} StartLine:{self.start_line} EndLine:{self.end_line} Stage:{self.stage_infos} Instruction:{self.instruction_text}"



class DockerfileParsed:
    """Ordered collection of every instruction found while parsing a Dockerfile."""
    def __init__(self):
        self.instruction_list = []

    def __str__(self):
        # for use with print(t)
        export = "Your object contain multiple Class Object:"
        for c in self.instruction_list:
            itemhumainreadable = f"(ID: {c.instruction_id}, Command: {c.command}, StartLine: {c.start_line}, EndLine: {c.end_line}, Stage: {c.stage_infos}, Instruction: {c.instruction_text})"
            export = f"{export}, {itemhumainreadable}"
        return export


    def add_instruction(self, instruction: DockerfileInstruction):
        """Append a newly parsed instruction to the list"""
        self.instruction_list.append(instruction)

    def update_instruction(self, instruction_id, end_line, add_extras):
        """Extend an existing instruction with the next physical line."""
        for i in self.instruction_list:
            if instruction_id == i.instruction_id:
                i.end_line = end_line
                updated_text = f"{i.instruction_text} {add_extras}"
                i.instruction_text = updated_text
                return 1
        print("Item not found in command list")

    def print_instruction_details(self, instruction_id):
        """Print one instruction's details"""
        for u in self.instruction_list:
            if instruction_id == u.instruction_id:
                return print(f"ID: {u.instruction_id}, Command: {u.command}, StartLine: {u.start_line}, Endline: {u.end_line}, Stage: {u.stage_infos}, Instruction: {u.instruction_text}")
        print("Item not found in command list")

    def print_all_instructions(self):
        """Print every parsed instruction"""
        for c in self.instruction_list:
            print(f"(ID: {c.instruction_id}, Command: {c.command}, StartLine: {c.start_line}, EndLine: {c.end_line}, Stage: {c.stage_infos}, Instruction: {c.instruction_text})")



def parse_dockerfile(file_path):
    """Read a Dockerfile line by line
    (merge line-continued (`\\`) instructions back together)."""
    parse_result = DockerfileParsed()
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            line_number = 0
            stage_number = 0
            stage_start_id = 0
            instruction_id = 0
            for line in f:
                line_number += 1
                stripped_line = line.rstrip()

                # Remove COMMENT and blank lines
                if stripped_line.startswith("#") or stripped_line == "":
                    continue
                # Remove "not end" line mark
                if stripped_line.endswith(" \\"):
                    stripped_line = stripped_line.rstrip("\\")

                for command_name in DockerCommand.listkeys():
                    if stripped_line.startswith(command_name):
                        matched_command = command_name
                        break
                    matched_command = None
                if matched_command is not None and matched_command == "FROM":
                    stage_number += 1
                    stage_start_id = instruction_id
                if matched_command is not None:
                    build_stage_infos = {"StageNumber": stage_number, "StageStartAtID": stage_start_id}
                    new_instruction = DockerfileInstruction(instruction_id=instruction_id, command=matched_command, start_line=line_number, end_line=line_number, stage_infos=build_stage_infos, instruction_text=stripped_line)
                    parse_result.add_instruction(new_instruction)
                    # parse_result.print_instruction_details(instruction_id=instruction_id)
                    instruction_id += 1
                else:
                    previous_instruction_id = instruction_id - 1
                    parse_result.update_instruction(instruction_id=previous_instruction_id, end_line=line_number, add_extras=stripped_line)
                    # parse_result.print_instruction_details(instruction_id=previous_instruction_id)
    except FileNotFoundError:
        print("The file was not found.")
    except PermissionError:
        print("You don't have permission to access this file.")

    return parse_result
