from setuptools import setup

setup(
    name="ghosts_nb_analysis",
    author="Johan Bregeon",
    author_email="bregeon@in2p3.fr",
    url = "https://github.com/lsst-camera-dh/ghosts_nb_analysis",
    packages=["ghosts_nb_analysis"],
    description="Analysis of real Rubin telescope ghost images",
    setup_requires=['setuptools_scm'],
    long_description=open("README.md").read(),
    package_data={"": ["README.md", "LICENSE"]},
    use_scm_version={"write_to":"ghosts_nb_analysis/_version.py"},
    include_package_data=True,
    classifiers=[
        "Development Status :: 1 - Beta",
        "License :: OSI Approved :: GPL License",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        ],
    install_requires=["matplotlib",
                      "numpy",
                      "scipy",
                      "pandas",
                      "setuptools_scm"]
)

