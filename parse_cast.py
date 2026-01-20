#!/usr/bin/env python3
"""
Parse asciinema .cast files and send cleaned terminal output to Ollama for analysis.

Usage: python parse_cast.py <path_to_cast_file>
       python parse_cast.py <path_to_cast_file> --preview  (just show cleaned output, no LLM)
"""

import json
import re
import sys
from datetime import datetime

# Lazy import for Ollama - only when needed
def get_ollama_chain(model_name: str):
    """Lazy import and setup of Ollama chain."""
    from langchain_ollama import OllamaLLM
    from langchain_core.prompts import ChatPromptTemplate
    
    template = """
You are a highly intelligent assistant helping your master examine and introspect their terminal activity. 
You will be given a cleaned terminal session recording showing commands executed and their output.

Your task:
1. Understand the intent and workflow from the commands
2. Identify what tasks were attempted or completed
3. Note any errors or issues encountered
4. Provide a concise summary of the work session

Terminal Session:
{terminal_session}

Please provide:
1. A brief summary of what work was done
2. Key observations about the workflow
"""
    
    prompt = ChatPromptTemplate.from_template(template)
    model = OllamaLLM(model=model_name)
    return prompt | model


def parse_cast_file(filepath: str) -> tuple[dict, list]:
    """
    Parse an asciinema v2 cast file.
    
    Returns:
        tuple: (header_metadata, list_of_events)
        Events are tuples of (timestamp, event_type, data)
    """
    events = []
    header = None
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
                
            try:
                parsed = json.loads(line)
                if i == 0 and isinstance(parsed, dict):
                    # First line is the header
                    header = parsed
                elif isinstance(parsed, list) and len(parsed) >= 3:
                    # Event: [timestamp, event_type, data]
                    timestamp, event_type, data = parsed[0], parsed[1], parsed[2]
                    events.append((timestamp, event_type, data))
            except json.JSONDecodeError as e:
                print(f"Warning: Could not parse line {i}: {e}", file=sys.stderr)
                continue
    
    return header, events


def strip_ansi(text: str) -> str:
    """
    Remove ANSI escape sequences from text.
    
    Handles:
    - CSI sequences: \x1b[...X (colors, cursor movement, etc.)
    - OSC sequences: \x1b]...BEL (terminal titles, etc.)
    - Private mode sequences: \x1b[?...X
    """
    # Standard CSI sequences: ESC [ <params> <letter>
    # OSC sequences: ESC ] ... BEL (or ESC \)
    # Private sequences: ESC [ ? <params> <letter>
    ansi_patterns = [
        r'\x1b\[\?[0-9;]*[a-zA-Z]',  # Private mode (like ?2004h)
        r'\x1b\[[0-9;]*[a-zA-Z]',     # Standard CSI
        r'\x1b\][^\x07]*\x07',         # OSC ending with BEL
        r'\x1b\][^\x1b]*\x1b\\',       # OSC ending with ST
        r'\x1b[=>]',                   # Other escape sequences
    ]
    
    combined_pattern = '|'.join(ansi_patterns)
    clean = re.sub(combined_pattern, '', text)
    
    # Remove remaining control characters (except newline and tab)
    clean = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', clean)
    
    return clean


def process_backspaces(text: str) -> str:
    """
    Process backspace characters by actually deleting the preceding character.
    This simulates what the terminal shows after character-by-character typing.
    """
    result = []
    for char in text:
        if char == '\b':
            if result and result[-1] != '\n':
                result.pop()
        else:
            result.append(char)
    return ''.join(result)


def clean_command_echoes(text: str) -> str:
    """
    Clean up duplicate character echoes that occur during typing.
    When you type 'ls', the terminal might echo 'l' then 'ls', resulting in 'lls'.
    This function attempts to fix common patterns.
    """
    # Fix doubled first characters in common commands
    # This happens because asciinema captures both the keystroke and the echo
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Check if this looks like a prompt line with a doubled command
        if ' % ' in line or ' $ ' in line:
            # Find the command part after the prompt
            for separator in [' % ', ' $ ']:
                if separator in line:
                    prompt_part, cmd_part = line.rsplit(separator, 1)
                    # Fix common doubled-letter patterns at start of commands
                    # Pattern: if first two chars are same letter, remove one
                    if len(cmd_part) >= 2 and cmd_part[0] == cmd_part[1] and cmd_part[0].isalpha():
                        cmd_part = cmd_part[1:]
                    line = prompt_part + separator + cmd_part
                    break
        cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)


def process_terminal_output(events: list) -> str:
    """
    Process all output events into clean, readable terminal text.
    
    Args:
        events: List of (timestamp, event_type, data) tuples
    
    Returns:
        Cleaned terminal session text
    """
    # Only process output events
    output_chunks = []
    for timestamp, event_type, data in events:
        if event_type == 'o':  # output event
            output_chunks.append(data)
    
    # Concatenate all output
    raw_output = ''.join(output_chunks)
    
    # Strip ANSI escape codes
    clean = strip_ansi(raw_output)
    
    # Process backspaces
    clean = process_backspaces(clean)
    
    # Normalize line endings
    clean = clean.replace('\r\n', '\n').replace('\r', '\n')
    
    # Collapse multiple blank lines into one
    clean = re.sub(r'\n{3,}', '\n\n', clean)
    
    # Clean up prompt artifacts (the % character zsh shows)
    clean = re.sub(r'%\s+\n', '\n', clean)
    
    # Clean up command echo duplicates
    clean = clean_command_echoes(clean)
    
    return clean.strip()


def extract_session_info(header: dict, events: list) -> dict:
    """Extract useful metadata from the cast file."""
    info = {
        'shell': header.get('env', {}).get('SHELL', 'unknown'),
        'term': header.get('env', {}).get('TERM', 'unknown'),
        'width': header.get('width', 0),
        'height': header.get('height', 0),
    }
    
    # Calculate duration from timestamps
    if events:
        start_time = events[0][0]
        end_time = events[-1][0]
        info['duration_seconds'] = round(end_time - start_time, 2)
    
    # Parse timestamp if available
    if 'timestamp' in header:
        try:
            info['recorded_at'] = datetime.fromtimestamp(header['timestamp']).isoformat()
        except (ValueError, OSError):
            pass
    
    return info


def format_for_llm(session_info: dict, terminal_output: str) -> str:
    """
    Format the cleaned output in a structured way for the LLM.
    """
    lines = [
        "=== Terminal Session Recording ===",
        f"Shell: {session_info.get('shell', 'unknown')}",
        f"Duration: {session_info.get('duration_seconds', 'unknown')} seconds",
    ]
    
    if 'recorded_at' in session_info:
        lines.append(f"Recorded: {session_info['recorded_at']}")
    
    lines.extend([
        "",
        "--- Terminal Output ---",
        "",
        terminal_output
    ])
    
    return '\n'.join(lines)


def send_to_ollama(formatted_text: str, model_name: str = 'cogito:3b') -> str:
    """
    Send the formatted terminal session to Ollama for analysis.
    
    Args:
        formatted_text: The cleaned and structured terminal output
        model_name: The Ollama model to use
    
    Returns:
        The LLM's analysis/summary
    """
    chain = get_ollama_chain(model_name)
    result = chain.invoke({'terminal_session': formatted_text})
    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: python parse_cast.py <path_to_cast_file> [model_name] [--preview]")
        print("Example: python parse_cast.py demo.cast")
        print("         python parse_cast.py demo.cast llama3.2")
        print("         python parse_cast.py demo.cast --preview  (no LLM, just show cleaned output)")
        sys.exit(1)
    
    cast_file = sys.argv[1]
    preview_only = '--preview' in sys.argv
    
    # Get model name (skip --preview if present)
    model_name = 'cogito:3b'
    for arg in sys.argv[2:]:
        if arg != '--preview':
            model_name = arg
            break
    
    print(f"Parsing cast file: {cast_file}")
    import time
    time.sleep(1)
    
    # Parse the file
    header, events = parse_cast_file(cast_file)
    
    if not header:
        print("Error: Could not parse cast file header", file=sys.stderr)
        sys.exit(1)
    
    print(f"Found {len(events)} events in recording")
    
    # Extract metadata
    session_info = extract_session_info(header, events)
    seconds = session_info.get('duration_seconds', 'unknown')
    print(f"Session duration: {seconds/60:.2f} minutes")
    time.sleep(1)
    
    # Process terminal output
    terminal_output = process_terminal_output(events)
    
    # Format for LLM
    formatted = format_for_llm(session_info, terminal_output)
    
    if preview_only:
        # Just show the cleaned output
        print("\n=== Cleaned Terminal Output ===\n")
        print(formatted)
        print(f"\n[Total: {len(formatted)} characters]")
        return
    
    # Show a preview of the cleaned output
    # print("\n--- Preview of cleaned output (first 500 chars) ---")
    # print(formatted)
    print(".", end="", flush=True); time.sleep(0.7)
    print(".", end="", flush=True); time.sleep(0.7)
    print(".", end="", flush=True); time.sleep(0.7)
    print(".", end="", flush=True)
    # print(f"\nTotal cleaned output length: {len(formatted)} characters")
    
    # Send to Ollama
    print(f"\nSending to Model ({model_name})...")
    try:
        print("\n=== LLM Analysis ongoing... ===\n")
        result = send_to_ollama(formatted, model_name)
        print(result)
    except Exception as e:
        print(f"Error calling Ollama: {e}", file=sys.stderr)
        print("\nCleaned output saved. You can manually send it to an LLM.")
        # Optionally save the cleaned output
        output_file = cast_file.replace('.cast', '_cleaned.txt')
        with open(output_file, 'w') as f:
            f.write(formatted)
        print(f"Saved cleaned output to: {output_file}")
        sys.exit(1)


if __name__ == '__main__':
    main()
