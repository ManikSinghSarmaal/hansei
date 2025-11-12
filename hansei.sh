mkdir -p "/tmp/hansei"
hansei_demo="/tmp/hansei/demo.cast"
hansei_control="/tmp/hansei/control"

hansei() {
  if [ $1 = "on" ]; then
    if [ "${CONTROL:-2}" -eq 2 ]; then
      export CONTROL=1
      echo "hansei is being turned on."
      asciinema rec $hansei_demo --overwrite    # this goes to a CHILD SUBSHELL.
      # when this line (yes, this comment) is executed, we have `exited` from the child subshell spawned in the above 'asciinema rec $hansei_demo'
      # this means that we must exit hansei now.
      echo "hansei is now off. bye..."
      # this logic is unsafe. probably many edge cases exist. will have to know bash internals to figure this one out.
      hansei off
    else
      echo "error: hansei is already recording inside parent shell. (CONTROL=1)"
    fi
  fi

  if [ $1 = "off" ]; then
    if [ "${CONTROL:-2}" -eq 1 ]; then
      echo "hansei off called => setting CONTROL=2 (using 'unset CONTROL') and exitting child shell..."
      unset CONTROL
    else
      echo "error: hansei has not been turned on. (CONTROL=2)"
    fi
  fi

  if [ $1 = "send" ]; then
    if [ "${CONTROL:-2}" -eq 1 ]; then
      terminal_output="$(asciinema cat ${hansei_demo} | base64 -w0)"
      echo $terminal_output > /tmp/hansei/debug.txt
      curl -X POST 192.168.1.12:8484/chat \
        -H "Content-Type: application/json" \
        -d "{\"message_b64\": \"$terminal_output\"}"
      # todo: append to /tmp/hansei.txt
    else
      echo "error: hansei has not been turned on. (CONTROL=2)"
    fi
  fi
}

test_post_hello() {
  curl -X POST http://192.168.1.12:8484/chat -H "Content-Type: application/json" -d '{"message": "echo hello"}'
}

test_random() {
  curl -X POST http://192.168.1.12:8484/chat -H "Content-Type: application/json" -d '$1'
}

test_any() {
  curl -X POST http://192.168.1.12:8484/chat -H "Content-Type: application/json" -d "{\"session_id\": \"test_random\", \"message_b64\": \"$1\"}"
}

test_health() {
  curl http://192.168.1.12:8484/health
}

