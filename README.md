*This repository contains the code related to the master thesis: "Development of a modular task system for Cybersecurity teaching on INGInious".*

# Introduction
Cybersecurity is a fast-growing field that requires regular work to keep up-to-date. In university cybersecurity courses, students are required to solve practical exercises to better understand and master the concepts.
For teachers, creating and correcting exercises is often a repetitive and time-consuming task.
The Université Catholique de Louvain has an online platform, called INGInious, which allows teachers to give different types of exercises to their students and correct them automatically. This master thesis aims to extend the INGInious platform to include a modular task system for cybersecurity exercises, allowing teachers to automatically generate new exercises to save time.

# Installation
## INGInious
This plugin requires a specific version of INGInious to work properly. It can be found in this repository : *https://github.com/maxime-peim/INGInious/tree/master-thesis-cyber*
Follow the classic INGInious installation guide: *https://docs.inginious.org/en/latest/admin_doc/install_doc/installation.html*

## Containers
Make sure the INGInious base container *ingi/inginious-c-base* is built first (cf. installation guide).

The **cychall-base** container needs to be built for the system to work.
Build it using the following commands:
```console
cd containers/cychall-base
docker build -t ingi/inginious-c-cychall-base ./
```

## Install plugin
Move **cychall-problems** folder to *inginious_folder/inginious/frontend/plugins*

The plugin also needs to be added to the INGInious configuration file: *https://docs.inginious.org/en/latest/admin_doc/install_doc/config_reference.html?highlight=plugins#plugins*
An optional configuration field **templates_path** can be used to set the path to the public templates folder. By default, the templates are stored next to the **tasks** folder.

Example configuration:
```yaml
plugins:
    - plugin_module: inginious.frontend.plugins.cychall-problems
      templates_path: "/home/user/templates"
```

# Examples
## Templates
The **templates** folder contains a series of example exercise templates focused on binary exploitation.
Add the content of this folder to your **templates_path** to make them available to your plugin.

## Container
The **cychall-binary** container contains the tools required to solve the example exercises.
Build it using the following commands:
```console
cd containers/cychall-binary
docker build -t ingi/inginious-c-cychall-binary ./
```