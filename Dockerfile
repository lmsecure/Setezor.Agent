FROM ubuntu:24.04
RUN apt update
WORKDIR /
COPY setezoragent_*.deb setezoragent.deb
RUN apt install ./setezoragent.deb -y
ENTRYPOINT ["setezoragent"]