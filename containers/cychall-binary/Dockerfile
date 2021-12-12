# DOCKER-VERSION 1.1.0

ARG   VERSION=latest
FROM  ingi/inginious-c-cychall-base:${VERSION}
LABEL org.inginious.grading.name="cychall-binary"



RUN   yum install -y gcc gcc-c++ cpp make cmake valgrind binutils libstdc++ clang clang-analyzer clang-devel llvm automake check check-devel zlib-devel openssl-devel time jansson-devel radare2 \
      wget which expat-devel gmp-devel mpfr-devel && \
      yum clean all

RUN   mkdir /tools && cd /tools

ARG   GDB_VERSION=11.1
RUN   wget "http://ftp.gnu.org/gnu/gdb/gdb-${GDB_VERSION}.tar.gz" && \
      tar -xvzf gdb-${GDB_VERSION}.tar.gz && rm gdb-${GDB_VERSION}.tar.gz && \
      cd gdb-${GDB_VERSION} && \
      ./configure --with-python=$(which python3) && \
      make && \
      make install
