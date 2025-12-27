# News Ticker

A Python script that displays a scrolling news ticker of the top headlines from NewsAPI.

## Setup

1.  **Get an API Key**:
    *   Go to [https://newsapi.org/register](https://newsapi.org/register) and sign up for a free API key.
    *   Create a file named `newsapikey.txt` in the same directory as the script.
    *   Paste your API key into this file.
    *   *Alternatively*, you can provide the API key via the `--api-key` command line argument.

2.  **Install Dependencies**:
    *   Use `pip` to install the required Python packages:
        ```bash
        pip install -r requirements.txt
        ```

## Usage

Run the script from the command line:

```bash
python news_ticker.py
```

### Arguments

The script supports parameters for the [NewsAPI Top Headlines endpoint](https://newsapi.org/docs/endpoints/top-headlines).

*   `--country`: The 2-letter ISO 3166-1 code of the country you want to get headlines for. Possible options: `ae`, `ar`, `at`, `au`, `be`, `bg`, `br`, `ca`, `ch`, `cn`, `co`, `cu`, `cz`, `de`, `eg`, `fr`, `gb`, `gr`, `hk`, `hu`, `id`, `ie`, `il`, `in`, `it`, `jp`, `kr`, `lt`, `lv`, `ma`, `mx`, `my`, `ng`, `nl`, `no`, `nz`, `ph`, `pl`, `pt`, `ro`, `rs`, `ru`, `sa`, `se`, `sg`, `si`, `sk`, `th`, `tr`, `tw`, `ua`, `us`, `ve`, `za`. Default: `us`.
*   `--category`: The category you want to get headlines for. Possible options: `business`, `entertainment`, `general`, `health`, `science`, `sports`, `technology`.
*   `--sources`: A comma-separated string of identifiers for the news sources or blogs you want headlines from.
*   `--q`: Keywords or a phrase to search for.
*   `--api-key`: Your NewsAPI key (if not in `newsapikey.txt`).
*   `--help`: Show help message and exit.

**Note**: You cannot mix the `sources` parameter with the `country` or `category` parameters.

## Features

*   **Scrolling Ticker**: Headlines scroll from right to left.
*   **Clickable**: Click on a headline to open the full article in your browser.
*   **Auto-Update**: The feed refreshes every hour.
*   **Caching**: Headlines and source metadata are cached locally to save API calls during development.

## License

Created and published by Ulaş Bardak.
This project is licensed under the Mozilla Public License 2.0.
