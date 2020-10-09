# mirrord's Dockerfile

FROM archlinux:latest

MAINTAINER ideal <idealities@gmail.com>

COPY mirrorlist /etc/pacman.d/mirrorlist

RUN echo -e '[archlinuxcn]\n\
Server = https://repo.archlinuxcn.org/$arch\n\
' >> /etc/pacman.conf

RUN pacman -Syyu --noconfirm && \
    pacman -S --noconfirm gettext grep wget awk && \
    rm -rf /var/cache/pacman/pkg/* /tmp/*

RUN pacman-key --init && \
    pacman-key -r F9F9FA97A403F63E --keyserver keyserver.ubuntu.com && \
    pacman-key -f F9F9FA97A403F63E && \
    pacman-key --lsign-key F9F9FA97A403F63E && \
    pacman -S --noconfirm unzip rsync mirror && \
    pacman -Scc --noconfirm && \
    rm -rf /etc/pacman.d/gnupg/{openpgp-revocs.d/,private-keys-v1.d/,pubring.gpg~}* && \
    rm -rf /var/cache/pacman/pkg/* /tmp/*

CMD ["mirrord"]
