# hansei: Terminal Memory Layer for Developer Workflows

```text
__                                         ____
      / /_   ____ _   ____    _____  ___  |___|
     / __ \ / __ `/  / __ \  / ___/ / _ \ |  | 
    / / / // /_/ /  / / / / (__  ) /  __/ |  |
   /_/ /_/ \__,_/  /_/ /_/ /____/  \___/  |__|
                                          
             [ Terminal Memory Layer ]
                
   >_  __________________________  <
      [oooooooooooooooooooooooooo]
      [oo   _       _          oo]
      [oo  | |___ _(_)_ __ ___ oo]
      [oo  | / -_) | | '  \___|oo]
      [oo  |_\___|_|_|_|_|_|   oo]
      [oo______________________oo]
       \________________________/
```
a tool that knows about your terminal sessions.

# setup
- make sure you are on linux.
- make sure `asciinema` is installed properly on your system.
- append the contents of `hansei.sh` to your `~/.bashrc`. replace the server IP for your ollama server. run the ollama server script.


# Description:

a lightweight terminal-memory layer that records developer workflows using asciinema, organizes terminal sessions into structured daily traces, and prepares the groundwork for a searchable RAG-style memory system/emdedding layer for advanced workdlows over command history, outputs, errors, and project context. 
The goal is to give you a persistent operational memory of what was done, why it was done, and what happened inside the terminal instead of manually tracking what you did 3 months ago

# Highlights:

Captures terminal activity as reusable execution traces instead of relying only on shell history.

Uses Python + Shell with your custom favourite llm for reasoning layer.

Organizes daily work into structured folders that can later be embedded, searched, and used as personal context.

Designed around the idea that developer workflows produce valuable telemetry: commands, failures, fixes, logs, and environment state.
