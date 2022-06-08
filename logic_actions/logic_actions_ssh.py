from colorama import Fore, Style
from .logic_actions_utils import install


def install_openssh_server(instance, args, verbose=True):
    """ Install and launch ssh server.
    Returns:
        int: Return 1 if the function works successfully, otherwise 0.
    """
    install(instance, {"module":"openssh-server"}, verbose=False)
    instance.execute(["systemctl","start","ssh"])
    return 0