from setuptools import find_packages, setup


setup(
    name="excalibur-cli",
    version="1.0.0",
    description="Knowledge-driven Nmap orchestration with Ansible and structured reporting.",
    packages=find_packages(include=["excalibur*", "exegol_spector*"]),
    include_package_data=True,
    python_requires=">=3.9",
    install_requires=["requests>=2.31.0,<3.0.0"],
    entry_points={
        "console_scripts": [
            "excalibur=excalibur.cli:main",
        ]
    },
)
