# Sinister Forge :: art.py
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
#
# Vault Boy ASCII art + boot animation frames. Matches the existing
# Start-Sinister-Session.bat boot logo. Per PH1, the boot sequence cycles
# through 4 rotating frames over ~1.2s before the main UI shows.

VAULT_BOY_FRAME_0 = r"""
                /\
               /  \
            /\/\/\/\
           /        \
       ___/__________\___
      /\                /\
     /  \              /  \
    /    \____________/    \
   |     /            \     |
   |    /   ___    ___ \    |
   |   |   /   \  /   \ |   |
   |   |  |  O  ||  O  ||   |
   |   |   \___/  \___/ |   |
    \   \      _/\_     /   /
     \   \    /    \   /   /
      \   \__/      \_/   /
       \  /\^/\^/\^/\^/  /
        \/  | | | | |  \/
         \__|_|_|_|_|__/

       S I N I S T E R     F O R G E
              operator console
"""

VAULT_BOY_FRAME_1 = r"""
                /\
               /  \
            /\/\/\/\
           /        \
       ___/__________\___
      /\                /\
     /  \              /  \
    /    \____________/    \
   |     /            \     |
   |    /   ___    ___ \    |
   |   |   /   \  /   \ |   |
   |   |  |  -  ||  -  ||   |
   |   |   \___/  \___/ |   |
    \   \      _/\_     /   /
     \   \    /    \   /   /
      \   \__/      \_/   /
       \  /\^/\^/\^/\^/  /
        \/  | | | | |  \/
         \__|_|_|_|_|__/

       S I N I S T E R     F O R G E
              operator console
"""

VAULT_BOY_FRAME_2 = r"""
                /\
               /  \
            /\/\/\/\
           /        \
       ___/__________\___
      /\                /\
     /  \              /  \
    /    \____________/    \
   |     /            \     |
   |    /   ___    ___ \    |
   |   |   /   \  /   \ |   |
   |   |  |  o  ||  o  ||   |
   |   |   \___/  \___/ |   |
    \   \      _//\\_   /   /
     \   \    /    \   /   /
      \   \__/      \_/   /
       \  /\^/\^/\^/\^/  /
        \/  | | | | |  \/
         \__|_|_|_|_|__/

       S I N I S T E R     F O R G E
              operator console
"""

VAULT_BOY_FRAME_3 = r"""
                /\
               /  \
            /\/\/\/\
           /        \
       ___/__________\___
      /\                /\
     /  \              /  \
    /    \____________/    \
   |     /            \     |
   |    /   ___    ___ \    |
   |   |   /   \  /   \ |   |
   |   |  |  *  ||  *  ||   |
   |   |   \___/  \___/ |   |
    \   \      _/\_     /   /
     \   \    /    \   /   /
      \   \__/      \_/   /
       \  /\^/\^/\^/\^/  /
        \/  | | | | |  \/
         \__|_|_|_|_|__/

       S I N I S T E R     F O R G E
              operator console
"""

BOOT_FRAMES = [
    VAULT_BOY_FRAME_0,
    VAULT_BOY_FRAME_1,
    VAULT_BOY_FRAME_2,
    VAULT_BOY_FRAME_3,
    VAULT_BOY_FRAME_2,
    VAULT_BOY_FRAME_1,
]

# Total animation duration in seconds. Each frame held for DURATION/len(BOOT_FRAMES).
BOOT_DURATION_SEC = 1.2
