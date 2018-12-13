# Mirror

[![Build Status]][Travis CI] [![Python version]][PyPI] [![Release version]][Release url] [![PyPi version]][PyPI] [![AUR version]][AUR]

`Mirror` is an open source python application for mirror site (e.g. [mirror.bjtu.edu.cn](https://mirror.bjtu.edu.cn)) to sync files from upstreams (it uses [rsync](http://rsync.samba.org/) internally), it actually works like a [cron](http://en.wikipedia.org/wiki/Cron), but still has some differences. It has been served for mirror.bjtu.edu.cn with more than 40 rsync [tasks](https://mirror.bjtu.edu.cn).

You are welcome to send comments, patches and any others to [github](https://github.com/ideal/mirror/issues) or to [@idealities](http://twitter.com/idealities).

Homepage: https://mirror.bjtu.edu.cn

Authors
=======

* Shang Yuanchun
* Bob Gao

For contributors and past developers see: 
    AUTHORS

Installation Instructions
=========================

You can install `mirror` by running pip:

```bash
$ sudo pip install mirror
```

Or if you want to build and install from source:

```bash
$ python setup.py build
$ sudo python setup.py install
```

After that, you are going to set up environment, you are encouraged to add a specific user to run `mirrord`, here we suppose the username is `mirror` and its home directory is `/home/mirror`.

Make necessary directories:

```bash
$ sudo chown mirror:mirror /var/log/mirrord /var/log/rsync
mkdir ~/.config/mirror
cp config/mirror.ini ~/.config/mirror/
```

Now you can edit mirror.ini to fit your needs and run:
```bash
$ mirrord
```
and that's done. Also you can use `man mirrord` or `mirrord -h` to read the documents.

If `mirrord` is running, you can run:
```bash
$ mirrord -t
```
to show the current task queue.

<img src="http://ideal.github.io/mirror/images/tasks.png" alt="screenshot" />

Contact/Support
===============

Email: idealities@gmail.com

Features
========

 * It's simple and easy to add a mirror
 * You can set a priorty for each mirror, from 1 to 10, 1 is highest
 * And scheduler will schedule a task depending on current conditions
 * You can also set a timeout for each mirror
 * Support for two stage syncing (for ubuntu, debian)
 * You can also use it as another cron...

[Build Status]:    https://img.shields.io/travis/ideal/mirror/master.svg?logo=travis-ci
[Travis CI]:       https://travis-ci.org/ideal/mirror
[Release version]: https://img.shields.io/github/release/ideal/mirror.svg?logo=github
[Release url]:     https://github.com/ideal/mirror/releases/latest
[Python version]:  https://img.shields.io/pypi/pyversions/mirror.svg?logo=python
[PyPI version]:    https://img.shields.io/pypi/v/mirror.svg?logo=python
[PyPI]:            https://pypi.python.org/pypi/mirror
[AUR version]:     https://img.shields.io/aur/version/mirror.svg?logo=arch-linux
[AUR]:             https://aur.archlinux.org/packages/mirror
