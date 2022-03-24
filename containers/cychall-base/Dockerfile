# DOCKER-VERSION 1.1.0

ARG   VERSION=latest
FROM  ingi/inginious-c-base:${VERSION}
LABEL org.inginious.grading.name="cychall-base"

ADD     . /INGInious-cychall
RUN     chmod -R 755 /INGInious-cychall/bin && \
        mv /INGInious-cychall/bin/* /bin

RUN     chmod -R 644 /INGInious-cychall/cychall_container_api && \
        mkdir -p /usr/lib/python3.8/site-packages/cychall_container_api && \
        cp -R /INGInious-cychall/cychall_container_api/*.py  /usr/lib/python3.8/site-packages/cychall_container_api && \
        echo "cychall_container_api" > /usr/lib/python3.8/site-packages/cychall_container_api.pth

RUN     rm -R /INGInious-cychall

RUN     python3 -m pip install jinja2-ansible-filters