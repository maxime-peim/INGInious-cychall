# DOCKER-VERSION 1.1.0

ARG   VERSION=latest
FROM  ingi/inginious-c-cychall-base:${VERSION}
LABEL org.inginious.grading.name="cychall-binary"

RUN   yum install -y dnf-plugins-core &&\
      yum config-manager --set-enabled powertools

RUN   yum install -y sudo gdb gcc gcc-c++ cpp make cmake \
      valgrind binutils libstdc++ clang clang-analyzer \
      clang-devel llvm automake check check-devel zlib-devel \
      openssl-devel time jansson-devel radare2 wget which \
      expat-devel gmp-devel mpfr-devel git dnf nano binutils \
      sqlite sqlite-devel strace glibc-devel.i686 glibc-static \
      checksec && \
      yum clean all

RUN   python3 -m pip install --no-cache-dir --upgrade pwntools && \
      python3 -m pip install --no-cache-dir --upgrade ROPgadget

# ARG   GDB_VERSION=11.1
# RUN   mkdir /tools && cd /tools && \
#       wget "http://ftp.gnu.org/gnu/gdb/gdb-${GDB_VERSION}.tar.gz" && \
#       tar -xvzf gdb-${GDB_VERSION}.tar.gz && rm gdb-${GDB_VERSION}.tar.gz && \
#       cd gdb-${GDB_VERSION} && \
#       ./configure --with-python=$(which python3) && \
#       make && \
#       make install

# RUN   cd /tools && \
#       git clone https://github.com/pwndbg/pwndbg && \
#       cd pwndbg && \
#       dnf install -y 'dnf-command(debuginfo-install)' && \
#       ./setup.sh
