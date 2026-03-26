SWORD_BANNER = r"""
                /\
               /**\
              /****\
             /******\
            /********\
           /**********\
          /____  ____\
               ||
               ||
               ||
               ||
            ___||___
           /   ||   \
          /____||____\
               /\
              /  \
"""


def render_banner() -> str:
    return (
        f"{SWORD_BANNER}\n"
        "Excalibur\n"
        "Knowledge-driven Nmap orchestration with Ansible and structured reporting.\n"
    )
