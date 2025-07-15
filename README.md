# Reddit User Persona Scraper

This tool scrapes a Reddit user's posts and comments (without using the Reddit API), builds a user persona using Google Gemini (Flash), and outputs the persona with citations to a text file.

## Features
- Scrapes posts and comments from any public Reddit user profile
- Builds a detailed user persona using Gemini LLM
- Cites posts/comments for each persona trait
- Outputs to a text file in the `output/` directory

## Setup
1. **Clone this repo**
2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
3. **Get a Gemini API Key**
   - Go to [Google AI Studio](https://aistudio.google.com/app/apikey) and create an API key.
   - Set it as an environment variable:
     ```bash
     export GEMINI_API_KEY=your-key-here
     ```
     On Windows (cmd):
     ```cmd
     set GEMINI_API_KEY=your-key-here
     ```

## Usage
```bash
python reddit_persona.py https://www.reddit.com/user/kojied/
```
- Output will be saved as `output/kojied_persona.txt`

## Notes
- This script uses web scraping, so it may be slower and is subject to Reddit's public site structure.
- For best results, use on users with public posts/comments.
- If you hit rate limits, try again after a few minutes.

## Example Output
See the `output/` directory for sample personas. 