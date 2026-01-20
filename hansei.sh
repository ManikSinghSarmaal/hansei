mkdir -p "/tmp/hansei"
hansei_demo="/tmp/hansei/demo.cast"

hansei() {
  # $1 is the first word you type after 'hansei' (e.g., 'on', 'send')
  command=$1

  if [ "$command" = "on" ]; then
    # 1. Check if we are ALREADY inside a recording to prevent nested loops
    if [ -n "$ASCIINEMA_REC" ]; then
      echo "Error: You are already inside a hansei session."
      return 1
    fi

    echo "Starting hansei recording..."
    echo "Type 'hansei send' to summarize your work."
    echo "Type 'exit' to stop recording."
    
    # 2. Start the recording. This pauses the script here and opens a NEW shell.
    asciinema rec "$hansei_demo" --overwrite

    # 3. This line runs ONLY after you type 'exit' and the recording closes.
    echo "Hansei session finished. Welcome back to the parent shell."
  
  elif [ "$command" = "send" ]; then
    # 4. Check if we are inside an asciinema session
    if [ -n "$ASCIINEMA_REC" ]; then
       echo "Processing recording..."
       
       # 5. Capture output, convert to base64 to safely send over JSON
       echo("Cat  into the variable and encoding in base64")       
       # macOS base64 doesn't wrap by default; Linux needs -w0
       if [[ "$OSTYPE" == "darwin"* ]]; then
         terminal_output="$(asciinema cat "$hansei_demo" | base64)"
       else
         terminal_output="$(asciinema cat "$hansei_demo" | base64 -w0)"
       fi
       
       # 6. Send to your LLM
       echo("sending it to the LLM")
       curl -X POST http://localhost:6040/chat \
         -H "Content-Type: application/json" \
         -d "{\"message_b64\": \"$terminal_output\"}"
    else
       echo "Error: You can only use 'send' while inside an active hansei session."
    fi

  else
    echo "Usage: hansei [on|send]"
  fi
}

# (Test functions remain the same...)
