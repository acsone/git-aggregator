#!/bin/sh

# Default to the gitaggregate command if we get an option as first argument
if [ "${1:0:1}" == - ]; then
    cmd="gitaggregate $@"
else
    cmd="$@"
fi

# Add SETUID & SETGUID to binaries to make them run with the same user as
# `/repos`'s owner. In case you mount `/repos` from your host computer. This is
# useful because otherwise all files and folders would be owned by `root`.
uid=$(stat -c %u /repos)
if [ $uid -ne $(id -u root) ]; then
    gid=$(stat -c %g /repos)
    addgroup -g $gid threpwood
    adduser -G threpwood -u $uid guybrush -DH -s /bin/sh

    exec su guybrush -c "$cmd"
else
    exec "$cmd"
fi
