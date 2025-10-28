# mirrord's Dockerfile

# You can run like this:
# docker run -d -v /path/to/host_dir_to_put_files:/home/mirror \
# -v /path/to/host_dir_put_log_files:/var/log/mirrord \
# -v /path/to/host_dir_contains_config_files:/etc/mirror ideal/mirror

# Please use docker ps and docker logs to view container logs.

FROM archlinux:latest

MAINTAINER ideal <idealities@gmail.com>

COPY docker/mirrorlist /etc/pacman.d/mirrorlist

COPY . mirror

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
    pacman -S --noconfirm unzip rsync python python-pip python-setuptools && \
    pacman -Scc --noconfirm && \
    rm -rf /etc/pacman.d/gnupg/{openpgp-revocs.d/,private-keys-v1.d/,pubring.gpg~}* && \
    rm -rf /var/cache/pacman/pkg/* /tmp/* && \
    cd mirror && python setup.py install && cd - && rm -rf mirror && \
    pip show mirror

CMD ["mirrord"]
