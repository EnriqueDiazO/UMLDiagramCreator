from setuptools import find_packages, setup


setup(
    name="uml-diagram-creator",
    version="0.1.0",
    description="Static Python code graph explorer with interactive HTML output.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="EnriqueDO",
    license="MIT",
    package_dir={"": "src"},
    packages=find_packages("src"),
    python_requires=">=3.9",
    install_requires=[],
    extras_require={
        "dev": ["pytest>=8"],
        "pyreverse": ["pylint>=3"],
    },
    entry_points={
        "console_scripts": [
            "umlgraph=uml_diagram_creator.cli:main",
        ],
    },
)
