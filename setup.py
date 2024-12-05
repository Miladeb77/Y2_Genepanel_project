from setuptools import setup, find_packages

setup(
    name="PanelGeneMapper",
    version="1.0.0",
    packages=find_packages(include=["PanelGeneMapper", "PanelGeneMapper.*"]),  # Correctly include the package and its submodules
    include_package_data=True,  # Includes non-code files like config files
    description="A tool for integrating PanelApp data with lab systems and generating reports.",
    author="Nour Mahfel",
    python_requires=">=3.9",  # Enforces minimum Python version
)
