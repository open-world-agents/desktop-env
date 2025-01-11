# ZType Game Agent with Vision Language Model

https://github.com/user-attachments/assets/4aee4580-179d-4e57-b876-0dd5256bb9c5

(4x speed video, works smoothly even with long sequences spanning multiple minutes)

An AI agent that plays [ZType](https://zty.pe/) - a typing game where you shoot down enemies by typing words. The agent uses [InternVL2.5-1B](https://huggingface.co/OpenGVLab/InternVL2_5-1B) Vision Language Model to detect words and simulates keyboard inputs to play the game.

## Key Features

- Real-time, (1B VLM)
- on-device, (RTX 4070 laptop)
- train-free, (no fine-tuning)
- interactive game agent! (ztype)

## How It Works

1. **Screen Capture**: Continuously captures frames from the ZType game window
2. **Word Detection**: Uses InternVL2 VLM to identify the lowest word on screen
3. **Keyboard Simulation**: Types detected words using virtual keyboard inputs

## System Architecture

![ZType Agent Sequence Diagram](assets/owa-ztype-sequence-uml.png)

The sequence diagram above illustrates the interaction between different components:

1. **Initialization Phase**

   - ZTypeAgent initializes OpenAI client with local VLM endpoint
   - ZtypeActor initializes with Desktop instance

2. **Main Game Loop**

   - Desktop Capture takes screenshots every 1 second
   - Agent processes frames through VLM every 1 second
   - Detected words are queued for typing
   - Actor types words using keyboard simulation

3. **Key Interactions**
   - Frame processing with duplicate prevention
   - Word expiration checking
   - Natural typing simulation with key press/release events

### Utilization of `desktop-env`

```python
args = DesktopArgs(
    submodules=[
        {
            "module": "desktop_env.windows_capture.WindowsCapture",
            "args": {
                "on_frame_arrived": on_frame_arrived,
                "pipeline_description": construct_pipeline(
                    window_name=ZTYPE_WINDOW_NAME,
                    framerate="4/1",  # Reduced framerate because VLM does not require high-frequency input, but you may specify 60+ fps
                ),
            },
        }
    ]
)
```
- Captures game window frames
- Configurable framerate to balance performance
- Queues frames for processing

```python
def type_word(self, word: str):
    for char in word.lower():
        vk = char_to_vk(char)
        # Simulate natural typing with small delays between key presses
        self.desktop.keyboard.press(vk)
        time.sleep(0.05)  # Delay between key press and release
        self.desktop.keyboard.release(vk)
        time.sleep(0.05)  # Delay between characters
```

- Maps characters to Windows virtual key codes
- Simulates natural typing with delays
- Handles keyboard press/release events

## Usage

### Docker (Recommended)

WSL + Docker + lmdeploy openai compatible server

1. [Install `desktop-env`](https://github.com/open-world-agents/desktop-env?tab=readme-ov-file#installation)

2. .env config & docker-compose
   - Copy `env.example` to `.env`
     ```bash
     cp .env.example .env
     ```
   - Edit `.env` and add your HF token:
     ```env
     HUGGING_FACE_HUB_TOKEN=your_actual_token_here
     ```

3. Now docker up

```bash
docker compose up -d
```

4. Open [ZType](https://zty.pe/) in your own browser. Adjust `ZTYPE_WINDOW_NAME` to your own if needed. Window is matched by substring match.

5. Then enjoy python!


The agent will:
- Start capturing the game window
- Detect and type words
- Type `Ctrl+C`(KeyboardInterrupt) to gracefully exit.

```bash
poetry install --no-root
python main.py
```

### Native Windows (Not recommended)

Pure windows installation guide (without WSL).

```bash
conda create -n owa python=3.11 -y
conda activate owa

conda install pytorch==2.4.0 torchvision==0.19.0 torchaudio==2.4.0 pytorch-cuda=12.4 -c pytorch -c nvidia
pip install packaging ninja
pip install flash-attn --no-build-isolation
pip install lmdeploy

poetry install --no-root
```

## Requirements

- Windows OS
- Python 3.11+
- Browser with ZType game open
- GPU recommended for VLM performance (tested on rtx 4070 laptop)
