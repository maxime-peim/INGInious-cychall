import os
import re
import subprocess
import shlex

from randomness import Random
from inginious_container_api.utils import set_limits_user

class Environment:

    def __init__(self, env=None):
        self._env = env or {}

    @property
    def has_hidden(self):
        return any(var.is_hidden for var in self._env)

    def __getitem__(self, var_name):
        try:
            return self._env[var_name]
        except KeyError:
            raise ValueError(f'Variable \'{var_name}\' is not previously defined in the template.')

    def add(self, var):
        self._env[var.name] = var

    def remove(self, var_name):
        del self._env[var_name]


class Variable:

    def __init__(self, name, hidden, value, prefix, postfix):
        self._name = name
        self._hidden = hidden
        self._prefix = prefix
        self._postfix = postfix

        self._value = self._generate(value)

    @property
    def name(self):
        return self._name

    @property
    def is_hidden(self):
        return self._hidden

    def _generate(self, value):
        random_pattern = re.compile(r"random_([^(]+)\(([^)]*)\)")
        match = random_pattern.fullmatch(value)

        if match:
            code, parameters_str = match.groups()

            parameters_list = [
                parameter.split('=')
                for parameter in parameters_str.split(',')
                if '=' in parameter
            ]

            parameters = {
                pname.strip(): self._generate(pvalue.strip())
                for pname, pvalue in parameters_list
            }

            return Random.generate(code, **parameters)

        if value.isdigit():
            return int(value)
        
        if value.startswith("'"):
            return value[1:-1]

        raise ValueError('Variable value cannot be set.')

    def __str__(self):
        return "\n".join([self._prefix + v + self._postfix for v in str(self._value).splitlines()])


def parse_template(input_filename, output_filename='', command=''):
    """ Parses a template file
        Replaces all occurences of @@problem_id@@ by the value
        of the 'problem_id' key in data dictionary
        
        input_filename: file to parse
        output_filename: if not specified, overwrite input file
    """
    with open(input_filename, 'rb') as file:
        template = file.read().decode("utf-8")

    output_filename = output_filename or input_filename

    replacement_pattern = re.compile(r"@(?:([^}]+)})?[ \t]*((?:hidden_)?[a-zA-Z_]\w*){1}[ \t]*(?:=[ \t]*(\d+|\'[^']*\'|random_(?:\w+)\((?:(?:(?:[a-zA-Z_]\w*)[ \t]*=[ \t]*(?:\d+|\'[^']*\'),)*(?:(?:[a-zA-Z_]\w*)[ \t]*=[ \t]*(?:\d+|\'[^']*\')){1})?\)){1})?(?:{([^{]+))?@")
    environment = Environment()
    changes_to_make = []
    need_intermediary_step = False
    
    for match in replacement_pattern.finditer(template):
        prefix, name, value, postfix = match.groups('')

        if value:
            hidden = name.startswith('hidden_')
            if hidden: name = name[7:]
            
            var = Variable(name, hidden, value, prefix, postfix)
            environment.add(var)
        else:
            var = environment[declaration]

        need_intermediary_step |= var.is_hidden
        changes_to_make.append((match.start(), match.end(), str(var), var.is_hidden))

    intermediary_template = final_template = template
    for start, end, replacement, hidden in changes_to_make[::-1]:
        intermediary_template = intermediary_template[:start] + replacement + intermediary_template[end:]
        final_template = final_template[:start] + ('--- EDITED ---' if hidden else replacement) + final_template[end:]
    
    # Ensure directory of resulting file exists
    try:
        os.makedirs(os.path.dirname(output_filename))
    except OSError as e:
        pass

    # Write file
    with open(output_filename, 'wb') as file:
        file.write(intermediary_template.encode("utf-8"))

    if need_intermediary_step or command != '':
        if need_intermediary_step and not command:
            raise Exception('Cannot hide values if there is no intermediary step.')
        
        p = subprocess.run(shlex.split(command), bufsize=0, stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        with open(output_filename, 'wb') as file:
            file.write(final_template.encode("utf-8"))


