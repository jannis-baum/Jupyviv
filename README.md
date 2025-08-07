# Jupyviv

Jupyviv is a solution for working with and running Jupyter Notebooks from plain
text editors such as Neovim while using
[Vivify](https://github.com/jannis-baum/Vivify) as a live viewer of the full
Notebook in the browser.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jannis-baum/assets/refs/heads/main/Jupyviv/showcase-dark.gif">
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/jannis-baum/assets/refs/heads/main/Jupyviv/showcase-light.gif">
  <img alt="Showcase" src="https://raw.githubusercontent.com/jannis-baum/assets/refs/heads/main/Jupyviv/showcase-dark.gif">
</picture>

> [!NOTE]
> Jupyviv is very new. I have been using it myself in my daily workflow for a
> few months now but there may be bugs that make it hard for you to use it. If
> this happens, don't hesitate to open an issue, we'll find a solution and fix
> it!

## Features

Aside from allowing you to **use your favorite editor with Jupyter Notebooks**,
the main benefit of Jupyviv comes from the fact that computation is fully
decoupled from file handling and your editor:

- Edit and render your Notebooks locally and optionally run computation on a
  different machine through an SSH tunnel
- Disconnect and keep running: No need to keep the your local machine connected
  or even running to have the remote keep computing and saving all outputs. This
  is something Jupyter Notebooks [can't
  do](https://stackoverflow.com/a/36845963)
- Almost no setup on remote: Just install Jupyviv and the Kernel you need, open
  the SSH tunnel and you are good to go. No need to even clone your repository
  there or configure anything

## Install

```sh
pip install git+https://github.com/jannis-baum/Jupyviv.git
```

## Usage

Using Jupyviv requires [Vivify](github.com/jannis-baum/Vivify) and a plugin for
integration with your editor. See below for a list of existing editor
integration.

Jupyviv itself is made up of two components:

- Agent, responsible for computation
- Handler, responsible for handling files locally, and communication between the
  Agent, your editor, and Vivify

The Handler is always run locally where your editor and Vivify are as well, and
should be taken care of by your editor plugin. The Agent can be automatically
launched and managed by the Handler, or run separately (optionally on a
different machine).

To run the Agent either way, you need the Jupyter Kernel for the respective
language installed, e.g. `pip install ipykernel` for Python. If you want to run
the agent separately, use `jupyviv agent --help` for more information.

### Existing editor integration

- for Neovim: [jupyviv.nvim](https://github.com/jannis-baum/jupyviv.nvim)
