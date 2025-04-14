# Jupyviv

Jupyviv is a solution for working with and running Jupyter Notebooks from plain
text editors such as Neovim while using
[Vivify](https://github.com/jannis-baum/Vivify) as a live viewer of the full
Notebook in the browser.

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

Using Jupyviv requires [Vivify](github.com/jannis-baum/Vivify) and (somewhat
optionally) a plugin for integration with your editor. See below for a list of
existing editor integration.

Jupyviv itself is made up of two components:

- `agent`, responsible for computation
- `handler`, responsible for handling files locally, and communication between
  the `agent`, your editor, and Vivify

The `handler` is always run locally where your editor and Vivify are as well,
and should be taken care of by your editor plugin. The `agent` can be run
separately (optionally on a different machine), or can be launched and managed
by the handler. Use `jupyviv agent --help` to see how to run the `agent`
separately.

### Existing editor integration

- for Neovim: [jupyviv.nvim](https://github.com/jannis-baum/jupyviv.nvim)
