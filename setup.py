from setuptools import find_packages, setup

setup(
    name="zed",
    python_requires=">=3.8",
    packages=find_packages(),
    include_package_data=True,    
    install_requires=[
        "ndspy",
    ],
)
