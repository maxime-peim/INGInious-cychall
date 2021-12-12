import random
import string

def get_random_string(length):
    # choose from all lowercase letter
    letters = string.ascii_lowercase + string.digits
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str


buffer_size = random.randint(15, 256)
random_string = get_random_string(buffer_size - 1)

with open('/task/student/scripts/template.c') as template, \
     open('/task/student/challenge_to_compile.c', 'w') as challenge_to_compile, \
     open('/task/student/challenge.c', 'w') as challenge:
    template_code = template.read()

    challenge_code = template_code.replace('%buffer_size%', str(buffer_size)) \
                                  .replace('%hidden_random_string%', random_string)
    challenge_to_compile.write(challenge_code)

    hidden_challenge_code = template_code.replace('%buffer_size%', str(buffer_size)) \
                                  .replace('%hidden_random_string%', "--- EDITED ---")
    challenge.write(hidden_challenge_code)
