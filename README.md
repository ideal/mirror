# Mirror

`Mirror` is an open source python application for mirror site (e.g. [mirror.bjtu.edu.cn](http://mirror.bjtu.edu.cn)) to sync files from upstreams (it uses rsync internally), it actually works like a cron, but has some differences. It has been served for mirror.bjtu.edu.cn with more than 40 rsync tasks.

You are welcome to send comments, patches and any others to [github](https://github.com/ideal/mirror/issues) or to [@idealities](http://twitter.com/idealities).

Homepage: http://mirror.bjtu.edu.cn

Authors
=======

* Shang Yuanchun
* Bob Gao

For contributors and past developers see: 
    AUTHORS

Installation Instructions
=========================

Build and install by running:

```
python setup.py build
sudo python setup.py install
```

Or to a custom directory:
```
sudo python setup.py install --root=/tmp
```

After that, you are going to set up environment, you are encouraged to add a specific user to run `mirrord`, here we suppose the username is `mirror` and its home directory is `/home/mirror`.

Make necessary directories:
```sh
sudo mkdir /var/log/mirrord /var/log/rsync
sudo chown mirror:mirror /var/log/mirrord /var/log/rsync
mkdir ~/.config/mirror
cp config/mirror.ini ~/.config/mirror/
```

Now you can edit mirror.ini to fit your needs and run:
```
mirrord
```
and that's done. Also you can use `man mirrord` to read the documents.

Also a command `mirror` is provided, if `mirrord` is running, you can run:
```
mirror -l
```
to show the current task queue.

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
