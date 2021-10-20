config:
   environment.DISPLAY: :0
   user.user-data: |
       #cloud-config
       packages:
       - x11-apps
       - mesa-utils
description: GUI LXD profile
devices:
    X0:
       bind: container
       connect: unix:@/tmp/.X11-unix/X'REPLACE_ME_WITH_$DISPLAY_VALUE'
       listen: unix:@/tmp/.X11-unix/X0
       security.gid: "1000"
       security.uid: "1000"
       type: proxy
    mygpu:
       type: gpu
name: x11
used_by: []
