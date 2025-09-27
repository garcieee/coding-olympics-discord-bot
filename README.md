
````markdown
# // COMPILED BOT

A Discord bot for managing student rankings and leaderboards in coding olympics events.

---

## Getting Started

### Setup the Bot Token (macOS / Linux)

1. Open your shell config file:
   ```bash
   nano ~/.zshrc
````

2. Add the following line at the bottom (replace with your actual bot token):

   ```bash
   export COMPILED_TOKEN="your_actual_token_here"
   ```

3. Save and exit:

   * Press **CTRL + O** → Enter
   * Press **CTRL + X** to close

4. Reload your shell so the token is available:

   ```bash
   source ~/.zshrc
   ```

5. Verify it’s set:

   ```bash
   echo $COMPILED_TOKEN
   ```

   You should see your token printed in the terminal.

---

### Running the Bot

1. Install dependencies:

   ```bash
   python3 -m pip install -U discord.py
   ```

2. Start the bot:

   ```bash
   python3 main.py
   ```

3. If successful, you’ll see:

   ```
    Logged in as COMPILED BOT
   ```

---
```
