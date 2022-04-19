import os
import platform
import sys
import json

import click


def exception_with_msg(msg):
    return click.ClickException(msg)


def is_win8():
    return '8' in platform.win32_ver()[0] if sys.platform == 'win32' else False


def is_win10():
    return '10' in platform.win32_ver()[0] if sys.platform == 'win32' else False


def is_win10_professional():
    if is_win10():
        # for windows 10 only, we need to know if it's pro vs home
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion") as key:
            return winreg.QueryValueEx(key, "EditionID")[0] == 'Professional'

    return False


# error checking for docker; sadly this is a mess,
# especially b/c there's tons of ways to mess up your docker install
# especially on windows :(
def root_cause(std_out, err_msg):
    all = f'{std_out.decode("utf-8") }\n{err_msg.decode("utf-8") }'
    if (
        b'is not recognized as an internal or external command' in err_msg
        and sys.platform == 'win32'
        and (is_win10_professional() or not is_win10_professional())
    ):
        raise exception_with_msg(
            "Docker does not appear to be installed. Make sure to download/install docker from "
        )


    if b'command not found' in err_msg:
        if sys.platform == 'darwin':
            raise exception_with_msg(
                "Docker does not appear to be installed. You can install it with `brew cask install docker` or "
            )


        else:
            raise exception_with_msg("docker command not found. Please install docker ")

    if b'This error may also indicate that the docker daemon is not running' in err_msg or b'Is the docker daemon running' in err_msg:
        if (
            sys.platform == 'darwin'
            or sys.platform != 'linux2'
            and sys.platform == 'win32'
        ):
            raise exception_with_msg(
                "Docker daemon not running. Make sure you've started "
            )


        elif sys.platform == 'linux2':
            raise exception_with_msg(
                "Docker daemon not running or this user cannot acccess the docker socket. "
            )


    if b'invalid mode: /opt/plan' in err_msg and sys.platform == 'win32':
        raise exception_with_msg(
            "You're running Docker Toolbox, but you're not using the 'Docker Quickstart Terminal'. "
        )


    if b'Drive has not been shared' in err_msg:
        raise exception_with_msg(
            "You're running from a directory that isn't shared to your docker Daemon. "
        )


    if b'No configuration files' in err_msg:
        raise exception_with_msg(
            "You're running from a directory that isn't shared to your docker Daemon. \
            Try running from a directory under your HOME, e.g. C:\\Users\\$YOUR_NAME\\$ANY_FOLDER"
        )

    if b'returned non-zero exit status 137' in err_msg:
        raise exception_with_msg(
            "Your docker container ran out of memory. Please open the docker desktop UI"
            " and increase the memory allowance in the advanced settings."
        )

    if b'Temporary failure in name resolution' in err_msg:
        raise exception_with_msg("You network failed temporarily, please try again.")

    if b'No Fargate configuration exists for given values.' in std_out:
        raise exception_with_msg("Invalid size preset, report this to Numerai")

    if 'Can\'t add file' in all or b'Error processing tar file(exit status 1): unexpected EOF' in err_msg:
        err_files = [f for f in all.split('\n') if 'Can\'t add file' in f]
        raise exception_with_msg(
            "Docker was unable to access some files while trying to build,"
            "either another program is using them or docker does not have permissions"
            f"to access them: {json.dumps(err_files, indent=2)}"
        )

    if b'PermissionError: [Errno 13] Permission denied: \'modules.json\'' in err_msg:
        raise exception_with_msg(
            "It looks like Docker daemon is running as root, please restart in rootless"
            "mode: https://docs.docker.com/engine/security/rootless/"
        )

    # these are non-errors that either shouldn't be handled or are handled elsewhere
    if b'Can\'t update submission after deadline' in err_msg:
        return
    if b'ResourceNotFoundException' in std_out or b'NoSuchEntity' in std_out:
        return

    raise exception_with_msg(
        f'Numerai CLI was unable to identify an error, please try to use the '
        f'"--verbose|-v" option for more information before reporting this\n{all}'
    )
