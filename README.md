# ConfigBridge Dota 2

ConfigBridge Dota 2 is a tool designed to simplify the management and transfer of Dota 2 configurations between different accounts or computers. It allows users to easily import and export their Dota 2 settings, including keybinds, video settings, and other in-game configurations.

## Features

*   **Import/Export Configurations:**  Seamlessly transfer Dota 2 configurations from files (cbd2 or zip), between Steam accounts, or directly from the Steam userdata folder.
*   **Account Management:**  Automatically detects and lists available Steam accounts with Dota 2 configurations, displaying usernames and avatars.
*   **Cross-Platform Support:** Works on various Windows Steam installations (finds Steam userdata folder automatically).  Limited support for other common locations is also included.
*   **User-Friendly Interface:**  Uses a modern GUI built with CustomTkinter for a visually appealing and intuitive experience.
*   **Error Handling:** Includes robust error handling and logging to provide informative messages to the user.
*   **Automatic Dota 2 Closure:**  Automatically closes Dota 2 before configuration changes to prevent conflicts (with a countdown timer).
* **Language Support:** Application interface is available in English and Russian.
* **Avatar Display:** Downloads and displays Steam avatars for each detected account.
* **Metadata Export:** Includes metadata (exporter name, account ID, export date, version) in exported config files.
* **Console Logging:** Provides detailed logging to a separate window or console for debugging.

## Requirements

*   Python 3.7+
*   The following Python packages (listed in `requirements.txt`):

    ```
    customtkinter==5.2.1
    requests
    Pillow
    psutil
    vdf
    ```

## Installation

1.  **Clone the Repository:**

    ```bash
    git clone https://github.com/infikot/cbd2  # Replace with your repo URL
    cd cbd2
    ```

2.  **Install Dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  **Run the Application:**

    ```bash
    python main.py
    ```
    or, for more detailed console output, use the console mode:
    ```bash
    python main.py -console
    ```

2.  **Select a Steam Account:**  The application will automatically detect Steam accounts with Dota 2 configurations.  Select the account you want to manage.

3.  **Import/Export:**
    *   **Import:** Choose to import from a `.cbd2` file, a `.zip` file, or another Steam account.
    *   **Export:**  Save the current configuration to a `.cbd2` file.  The file will be named using the Steam username and will include metadata.

4. **Language Selection**: You can switch between English and Russian in the top right corner menu.

## Important Notes/Warnings

*   **Dota 2 Must Be Closed:** Ensure Dota 2 is closed *before* importing or exporting configurations. The application will automatically close Dota 2 (with a countdown) if it's running.
*   **Internet Connection:** An internet connection is required for downloading avatars and checking for updates (although the update check is not implemented in the provided code).
*   **Local Saves:** When launching Dota 2 after importing a configuration, make sure you load the *local* save, not the cloud save.
* **Steam userdata folder**: The program is designed to work with the default Steam userdata path.  If you've moved your userdata folder to a non-standard location, the automatic detection might not work.

## Troubleshooting

*   **"Steam folder not found":**  The application couldn't locate your Steam userdata folder. Check the `STEAM_PATHS` variable in `main.py` and add your custom path if necessary.
*   **"No accounts found":**  No Steam accounts with valid Dota 2 configurations were found in the detected Steam userdata folder. Make sure you have played Dota 2 on the accounts you expect to see.  Also, the application checks for the presence of configuration files within the `cfg`, `local/cfg`, and `remote/cfg` subfolders of the Dota 2 user data directory.
*   **"No config files":** No config files were found. Check that the selected folder contains the necessary config files.
*   **"Invalid zip file":** The selected .zip file is not a valid archive.
*   **Import/Export Errors:**  Check the console log (if running in `-console` mode) or the application's log window for detailed error messages.
* **Avatar Loading Issues:**  If avatars fail to load, ensure you have a stable internet connection.  The program will fall back to displaying the first letter of the username if the avatar cannot be downloaded.

## Contributing

Contributions are welcome!  Please submit pull requests or open issues for bug reports and feature requests.  Consider the following areas for contribution:

*   **More Robust Steam Path Detection:** Improve the logic for finding the Steam installation and userdata folders on different operating systems (especially Linux and macOS).
*   **Support for More Configuration Files:**  Extend the application to handle additional Dota 2 configuration files.
*   **Improved Error Messages:**  Provide more user-friendly and specific error messages.
*   **Update Functionality:** Implement a mechanism to check for and download updates to the application.
* **Testing:** Write comprehensive unit and integration tests.

## Acknowledgments

This project was developed with the assistance of the following AI tools and services:

*   **AI Models:**
    *   Google Gemini
    *   Anthropic Claude
    *   OpenAI ChatGPT
*   **Translation:**
    *   DeepL Translate
*   **Resources:**
    *   Stack Overflow

## Contact / Support

*   **GitHub Issues:** [cbd2/issues](https://github.com/infikot/cbd2/issues)
*   **Telegram:** [@infikot](https://t.me/infikot)
